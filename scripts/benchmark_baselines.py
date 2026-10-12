"""
Script d'Évaluation des Baselines (Étape 3) — KOUMAN AI

Mesure les performances chrF++ et BLEU sur :
1. NLLB-1.3B Zéro-Shot (Modèle de base sans adaptateur)
2. Adaptateur LoRA v1 (Modèle actuel)

Évaluations effectuées :
- Jeu de Validation V2 (940 phrases)
- Jeu de Test Sacré (144 phrases conversationnelles)
Dans les 2 sens : Français -> Dioula (FR->DYU) et Dioula -> Français (DYU->FR).

Enregistre les résultats dans data/baselines_results.tsv
"""

import os
import sys
import torch
import pandas as pd
import json
import sacrebleu
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_MODEL_NAME = "facebook/nllb-200-1.3B"
V1_ADAPTER_PATH = os.path.join(ROOT_DIR, "models", "nllb_lora_dioula", "final")

VAL_V2_PATH  = os.path.join(ROOT_DIR, "data", "processed_v2_val.json")
TEST_SACRE_PATH = os.path.join(ROOT_DIR, "data", "test_sacre.csv")
OUT_TSV_PATH = os.path.join(ROOT_DIR, "data", "baselines_results.tsv")

device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")

def load_data():
    with open(VAL_V2_PATH, "r", encoding="utf-8") as f:
        val_data = json.load(f)
    
    df_test = pd.read_csv(TEST_SACRE_PATH)
    test_fr2dyu = [{"src_text": row["fr"], "tgt_text": row["dyu"], "src_lang": "fra_Latn", "tgt_lang": "dyu_Latn"} 
                   for _, row in df_test.iterrows() if pd.notna(row["fr"]) and pd.notna(row["dyu"])]
    test_dyu2fr = [{"src_text": row["dyu"], "tgt_text": row["fr"], "src_lang": "dyu_Latn", "tgt_lang": "fra_Latn"} 
                   for _, row in df_test.iterrows() if pd.notna(row["fr"]) and pd.notna(row["dyu"])]
    
    val_fr2dyu = [item for item in val_data if item["src_lang"] == "fra_Latn"]
    val_dyu2fr = [item for item in val_data if item["src_lang"] == "dyu_Latn"]
    
    return {
        "val_fr2dyu": val_fr2dyu,
        "val_dyu2fr": val_dyu2fr,
        "test_fr2dyu": test_fr2dyu,
        "test_dyu2fr": test_dyu2fr
    }

def evaluate_model(model, tokenizer, items, model_label, dataset_label, direction):
    src_texts = [item["src_text"] for item in items]
    tgt_references = [item["tgt_text"] for item in items]
    
    src_lang = items[0]["src_lang"]
    tgt_lang = items[0]["tgt_lang"]
    
    tokenizer.src_lang = src_lang
    forced_bos_token_id = tokenizer.lang_code_to_id[tgt_lang]
    
    predictions = []
    batch_size = 16
    total_batches = (len(src_texts) + batch_size - 1) // batch_size
    
    for idx, i in enumerate(range(0, len(src_texts), batch_size), start=1):
        batch_src = src_texts[i:i+batch_size]
        inputs = tokenizer(batch_src, return_tensors="pt", padding=True, truncation=True, max_length=96).to(device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                forced_bos_token_id=forced_bos_token_id,
                max_length=96,
                num_beams=1  # Greedy decoding pour une évaluation baseline rapide
            )
        preds = tokenizer.batch_decode(outputs, skip_special_tokens=True)
        predictions.extend(preds)
        print(f"    [{dataset_label} - {direction}] Lot {idx}/{total_batches} traité ({len(predictions)}/{len(src_texts)})...", flush=True)


        
    bleu = sacrebleu.corpus_bleu(predictions, [tgt_references])
    chrf = sacrebleu.corpus_chrf(predictions, [tgt_references])
    
    return {
        "Modèle": model_label,
        "Dataset": dataset_label,
        "Direction": direction,
        "chrF++": round(chrf.score, 2),
        "BLEU": round(bleu.score, 2),
        "Échantillons": len(items)
    }

def main():
    print("=" * 70)
    print("  ÉVALUATION DES BASELINES (Étape 3)")
    print(f"  Device : {device}")
    print("=" * 70)
    
    datasets = load_data()
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME)
    
    results = []

    # 1. Modèle de Base Zéro-Shot
    print("\n🔹 Chargement de NLLB-1.3B Zéro-Shot...")
    base_model = AutoModelForSeq2SeqLM.from_pretrained(BASE_MODEL_NAME).to(device)
    base_model.eval()

    print("  → Évaluation Zéro-shot...")
    results.append(evaluate_model(base_model, tokenizer, datasets["val_fr2dyu"], "NLLB Zéro-Shot", "Val V2", "FR -> DYU"))
    results.append(evaluate_model(base_model, tokenizer, datasets["val_dyu2fr"], "NLLB Zéro-Shot", "Val V2", "DYU -> FR"))
    results.append(evaluate_model(base_model, tokenizer, datasets["test_fr2dyu"], "NLLB Zéro-Shot", "Test Sacré", "FR -> DYU"))
    results.append(evaluate_model(base_model, tokenizer, datasets["test_dyu2fr"], "NLLB Zéro-Shot", "Test Sacré", "DYU -> FR"))

    # 2. Modèle LoRA v1 (Actuel)
    if os.path.exists(V1_ADAPTER_PATH):
        print("\n🔹 Chargement de l'adaptateur LoRA v1...")
        v1_model = PeftModel.from_pretrained(base_model, V1_ADAPTER_PATH).to(device)
        v1_model.eval()

        print("  → Évaluation Adaptateur v1...")
        results.append(evaluate_model(v1_model, tokenizer, datasets["val_fr2dyu"], "LoRA v1 (Actuel)", "Val V2", "FR -> DYU"))
        results.append(evaluate_model(v1_model, tokenizer, datasets["val_dyu2fr"], "LoRA v1 (Actuel)", "Val V2", "DYU -> FR"))
        results.append(evaluate_model(v1_model, tokenizer, datasets["test_fr2dyu"], "LoRA v1 (Actuel)", "Test Sacré", "FR -> DYU"))
        results.append(evaluate_model(v1_model, tokenizer, datasets["test_dyu2fr"], "LoRA v1 (Actuel)", "Test Sacré", "DYU -> FR"))

    df_res = pd.DataFrame(results)
    df_res.to_csv(OUT_TSV_PATH, sep="\t", index=False)
    
    print("\n" + "=" * 70)
    print("  TABLEAU DES BASELINES (Étape 3)")
    print("=" * 70)
    print(df_res.to_string(index=False))
    print(f"\n💾 Résultats détaillés enregistrés dans : {OUT_TSV_PATH}")
    print("=" * 70)

if __name__ == "__main__":
    main()
