"""
Fine-Tuning EFFICACE du modèle NLLB-200-1.3B avec LoRA (PEFT).
LoRA entraîne seulement ~1% des paramètres → 20x plus rapide, adapté à un iMac.

Prérequis:
    pip install transformers datasets accelerate peft sentencepiece sacrebleu pandas
"""

import json
import os
import time
import torch
import pandas as pd
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    DataCollatorForSeq2Seq,
)
from peft import LoraConfig, get_peft_model, TaskType
import sacrebleu

ROOT_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_NAME     = "facebook/nllb-200-1.3B"
SRC_LANG       = "fra_Latn"
TGT_LANG       = "dyu_Latn"
CSV_PATH       = os.path.join(ROOT_DIR, "LIVRABLE", "06_Corpus_Final", "corpus_dioula_consolide.csv")
GLOSSAIRE_PATH = os.path.join(ROOT_DIR, "data", "glossaire_dioula.json")
OUTPUT_DIR     = os.path.join(ROOT_DIR, "models", "nllb_lora_dioula")
MAX_LENGTH     = 64   # Phrases courtes → entraînement plus rapide
BATCH_SIZE     = 4    # LoRA libère beaucoup de mémoire
GRAD_ACCUM     = 4    # Batch effectif = 4 * 4 = 16
EPOCHS         = 3
LEARNING_RATE  = 3e-4  # LoRA accepte un LR plus élevé

# ==============================
# CONFIG LORA
# ==============================
LORA_CONFIG = LoraConfig(
    task_type=TaskType.SEQ_2_SEQ_LM,
    r=16,            # Rang des matrices LoRA (16 = bon compromis)
    lora_alpha=32,   # Scaling LoRA
    lora_dropout=0.1,
    target_modules=["q_proj", "v_proj"],  # Couches d'attention ciblées
    bias="none",
)


def load_glossaire(path):
    with open(path, "r", encoding="utf-8") as f:
        glossaire = json.load(f)
    return [{"francais": k, "dioula": v} for k, v in glossaire.items()
            if len(k) > 2 and len(v) > 1 and not any(c.isdigit() for c in v)]


def load_corpus(path, src_col="francais", tgt_col="dioula"):
    df = pd.read_csv(path).dropna(subset=[src_col, tgt_col])
    df = df[[src_col, tgt_col]].rename(columns={src_col: "francais", tgt_col: "dioula"})
    # On filtre les phrases trop longues (> 50 mots) pour accélérer
    df = df[df["dioula"].str.split().str.len() <= 50]
    return df.to_dict(orient="records")


def build_dataset(csv_path, glossaire_path, test_split=0.05):
    print("Chargement du corpus CSV...")
    corpus = load_corpus(csv_path)
    print(f"  → {len(corpus)} paires depuis le CSV.")
    print("Chargement du glossaire...")
    glossaire = load_glossaire(glossaire_path)
    print(f"  → {len(glossaire)} paires depuis le glossaire.")
    all_data = corpus + glossaire
    print(f"  → Total : {len(all_data)} paires.")
    dataset = Dataset.from_list(all_data)
    split = dataset.train_test_split(test_size=test_split, seed=42)
    return split["train"], split["test"]


def preprocess(examples, tokenizer):
    tokenizer.src_lang = SRC_LANG
    tokenizer.tgt_lang = TGT_LANG
    model_inputs = tokenizer(
        examples["francais"],
        text_target=examples["dioula"],
        max_length=MAX_LENGTH,
        padding="max_length",
        truncation=True,
    )
    model_inputs["labels"] = [
        [(t if t != tokenizer.pad_token_id else -100) for t in label]
        for label in model_inputs["labels"]
    ]
    return model_inputs


def compute_metrics(eval_preds, tokenizer):
    preds, labels = eval_preds
    decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
    labels = [[t if t != -100 else tokenizer.pad_token_id for t in l] for l in labels]
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
    bleu = sacrebleu.corpus_bleu(decoded_preds, [decoded_labels])
    chrf = sacrebleu.corpus_chrf(decoded_preds, [decoded_labels])
    return {"bleu": round(bleu.score, 4), "chrf": round(chrf.score, 4)}


def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"\n{'='*55}")
    print(f"  FINE-TUNING NLLB avec LoRA — Français → Dioula")
    print(f"  Modèle  : {MODEL_NAME}")
    print(f"  Méthode : LoRA (r={LORA_CONFIG.r}, alpha={LORA_CONFIG.lora_alpha})")
    print(f"  Device  : {device}")
    print(f"{'='*55}\n")

    train_dataset, eval_dataset = build_dataset(CSV_PATH, GLOSSAIRE_PATH)

    print("Chargement du tokenizer et du modèle...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

    # Applique LoRA : seul ~1% des paramètres sera entraîné
    model = get_peft_model(model, LORA_CONFIG)
    model.print_trainable_parameters()
    model = model.to(device)

    print("Tokenisation du dataset...")
    tokenized_train = train_dataset.map(
        lambda x: preprocess(x, tokenizer),
        batched=True, remove_columns=["francais", "dioula"]
    )
    tokenized_eval = eval_dataset.map(
        lambda x: preprocess(x, tokenizer),
        batched=True, remove_columns=["francais", "dioula"]
    )

    training_args = Seq2SeqTrainingArguments(
        output_dir=OUTPUT_DIR,
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=LEARNING_RATE,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM,
        num_train_epochs=EPOCHS,
        predict_with_generate=True,
        fp16=False,
        logging_dir=os.path.join(OUTPUT_DIR, "logs"),
        logging_steps=20,
        load_best_model_at_end=True,
        metric_for_best_model="bleu",
        report_to="none",
    )

    data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model, padding=True)

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_eval,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=lambda p: compute_metrics(p, tokenizer),
    )

    print("\nDébut du fine-tuning LoRA...\n")
    start = time.time()
    trainer.train()
    elapsed = time.time() - start
    print(f"\nFine-tuning terminé en {elapsed/60:.1f} minutes !")

    # Sauvegarde du modèle LoRA (seulement les adaptateurs, ~100 Mo au lieu de 5 Go !)
    print(f"Sauvegarde des adaptateurs LoRA dans : {OUTPUT_DIR}/final")
    model.save_pretrained(os.path.join(OUTPUT_DIR, "final"))
    tokenizer.save_pretrained(os.path.join(OUTPUT_DIR, "final"))
    print("\nTerminé ! Pour l'utiliser dans benchmark_nllb.py :")
    print(f'  model_name = "{OUTPUT_DIR}/final"')


if __name__ == "__main__":
    main()
