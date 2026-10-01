"""
Fine-Tuning BIDIRECTIONNEL (Français ↔ Dioula) du modèle NLLB-200-1.3B avec LoRA.

Améliorations (Niveau 2) :
1. Entraînement bidirectionnel (FR -> DYU et DYU -> FR)
2. Sur-pondération du glossaire et des expressions courantes (custom_idioms.json + glossaire_dioula.json)
3. Adaptateurs LoRA optimisés sur attention (q, k, v, out_proj)
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
CSV_PATH       = os.path.join(ROOT_DIR, "LIVRABLE", "06_Corpus_Final", "corpus_dioula_consolide.csv")
GLOSSAIRE_PATH = os.path.join(ROOT_DIR, "data", "glossaire_dioula.json")
CUSTOM_IDIOMS  = os.path.join(ROOT_DIR, "data", "custom_idioms.json")
OUTPUT_DIR     = os.path.join(ROOT_DIR, "models", "nllb_lora_dioula")

MAX_LENGTH     = 48
BATCH_SIZE     = 2     # Ultra-léger pour garantir le support sur iMac (MPS)
GRAD_ACCUM     = 16    # Batch effectif = 32 (2 * 16)
EPOCHS         = 1.5   # Entraînement rapide et ciblé
LEARNING_RATE  = 5e-4  # LR adapté LoRA

LORA_CONFIG = LoraConfig(
    task_type=TaskType.SEQ_2_SEQ_LM,
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=["q_proj", "v_proj", "k_proj", "out_proj"],
    bias="none",
)


def load_custom_idioms(path, repeat=40):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data * repeat


def load_glossaire(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        items = [{"francais": k, "dioula": v} for k, v in data.items()
                 if len(k) > 2 and len(v) > 1 and not any(c.isdigit() for c in str(v))]
    else:
        items = [item for item in data
                 if isinstance(item, dict) and "francais" in item and "dioula" in item
                 and len(str(item["francais"])) > 1 and len(str(item["dioula"])) > 1]
    return items



def load_corpus(path, src_col="francais", tgt_col="dioula"):
    df = pd.read_csv(path).dropna(subset=[src_col, tgt_col])
    df = df[[src_col, tgt_col]].rename(columns={src_col: "francais", tgt_col: "dioula"})
    df = df[df["dioula"].str.split().str.len() <= 35]
    return df.to_dict(orient="records")


def make_bidirectional(pairs):
    bidi = []
    for p in pairs:
        # Direction 1: FR -> DYU
        bidi.append({
            "src_text": p["francais"],
            "tgt_text": p["dioula"],
            "src_lang": "fra_Latn",
            "tgt_lang": "dyu_Latn"
        })
        # Direction 2: DYU -> FR
        bidi.append({
            "src_text": p["dioula"],
            "tgt_text": p["francais"],
            "src_lang": "dyu_Latn",
            "tgt_lang": "fra_Latn"
        })
    return bidi


def build_dataset(csv_path, glossaire_path, custom_path, test_split=0.03):
    print("Chargement des données...", flush=True)
    corpus = load_corpus(csv_path)
    print(f"  → {len(corpus)} paires CSV.", flush=True)
    glossaire = load_glossaire(glossaire_path)
    print(f"  → {len(glossaire)} paires Glossaire.", flush=True)
    idioms = load_custom_idioms(custom_path, repeat=40)
    print(f"  → {len(idioms)} paires Expressions fondamentales (surpondérées x40).", flush=True)
    
    all_pairs = corpus + glossaire + idioms
    bidi_data = make_bidirectional(all_pairs)
    print(f"  → Total Bidirectionnel : {len(bidi_data)} exemples.", flush=True)
    
    dataset = Dataset.from_list(bidi_data)
    split = dataset.train_test_split(test_size=test_split, seed=42)
    return split["train"], split["test"]


def preprocess_batch(batch, tokenizer):
    input_ids = []
    attention_masks = []
    labels = []

    for src, tgt, s_lang, t_lang in zip(batch["src_text"], batch["tgt_text"], batch["src_lang"], batch["tgt_lang"]):
        tokenizer.src_lang = s_lang
        tokenizer.tgt_lang = t_lang
        inp = tokenizer(src, text_target=tgt, max_length=MAX_LENGTH, padding="max_length", truncation=True)
        
        input_ids.append(inp["input_ids"])
        attention_masks.append(inp["attention_mask"])
        
        label = [(t if t != tokenizer.pad_token_id else -100) for t in inp["labels"]]
        labels.append(label)

    return {
        "input_ids": input_ids,
        "attention_mask": attention_masks,
        "labels": labels
    }


def compute_metrics(eval_preds, tokenizer):
    preds, label_ids = eval_preds
    decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
    clean_labels = [[(t if t != -100 else tokenizer.pad_token_id) for t in l] for l in label_ids]
    decoded_labels = tokenizer.batch_decode(clean_labels, skip_special_tokens=True)
    
    bleu = sacrebleu.corpus_bleu(decoded_preds, [decoded_labels])
    chrf = sacrebleu.corpus_chrf(decoded_preds, [decoded_labels])
    return {"bleu": round(bleu.score, 4), "chrf": round(chrf.score, 4)}


def main():
    device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n{'='*65}", flush=True)
    print(f"  FINE-TUNING NLLB LoRA BIDIRECTIONNEL — Français ↔ Dioula", flush=True)
    print(f"  Modèle  : {MODEL_NAME}", flush=True)
    print(f"  Device  : {device}", flush=True)
    print(f"{'='*65}\n", flush=True)

    train_dataset, eval_dataset = build_dataset(CSV_PATH, GLOSSAIRE_PATH, CUSTOM_IDIOMS)

    print("Chargement du tokenizer et du modèle...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

    model = get_peft_model(model, LORA_CONFIG)
    model.print_trainable_parameters()
    model = model.to(device)

    print("Tokenisation du dataset bidirectionnel...", flush=True)
    tokenized_train = train_dataset.map(
        lambda batch: preprocess_batch(batch, tokenizer),
        batched=True,
        batch_size=500,
        remove_columns=["src_text", "tgt_text", "src_lang", "tgt_lang"]
    )
    tokenized_eval = eval_dataset.map(
        lambda batch: preprocess_batch(batch, tokenizer),
        batched=True,
        batch_size=500,
        remove_columns=["src_text", "tgt_text", "src_lang", "tgt_lang"]
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
        logging_steps=10,
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

    print("\nDébut du fine-tuning LoRA Bidirectionnel...\n", flush=True)
    start = time.time()
    trainer.train()
    elapsed = time.time() - start
    print(f"\nFine-tuning terminé en {elapsed/60:.1f} minutes !", flush=True)

    final_path = os.path.join(OUTPUT_DIR, "final")
    print(f"Sauvegarde des adaptateurs LoRA dans : {final_path}", flush=True)
    model.save_pretrained(final_path)
    tokenizer.save_pretrained(final_path)
    print("\n✅ Fine-tuning Niveau 2 achevé avec succès !", flush=True)


if __name__ == "__main__":
    main()
