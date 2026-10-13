"""
Script de comparaison rigoureuse à paramètres identiques sur le Test Sacré.
Compare :
1. NLLB Zéro-shot (Base)
2. LoRA v1
3. NLLB Fusionné officiel (5c36e48)

Paramètres strictement identiques :
- max_length = 96
- num_beams = 1 (greedy) et optionnellement num_beams = 4
"""

import os
import argparse
import torch
import pandas as pd
import sacrebleu
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_SACRE_PATH = os.path.join(ROOT_DIR, "data", "test_sacre.csv")
BASE_MODEL_ID = "facebook/nllb-200-1.3B"
MERGED_MODEL_ID = "syndou/nllb-200-dioula"
MERGED_REVISION = "5c36e481ce9ce8d6f73a57181fb93d6900ddad89"
LORA_PATH = os.path.join(ROOT_DIR, "models", "nllb_lora_dioula", "final")

device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")

def eval_pairs(model, tokenizer, pairs, src_lang, tgt_lang, num_beams=1, max_length=96):
    src_texts = [p["src"] for p in pairs]
    refs = [p["tgt"] for p in pairs]
    
    tokenizer.src_lang = src_lang
    forced_bos = tokenizer.convert_tokens_to_ids(tgt_lang)
    
    predictions = []
    batch_size = 16
    for i in range(0, len(src_texts), batch_size):
        batch = src_texts[i:i+batch_size]
        inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=max_length).to(device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                forced_bos_token_id=forced_bos,
                max_length=max_length,
                num_beams=num_beams
            )
        preds = tokenizer.batch_decode(outputs, skip_special_tokens=True)
        predictions.extend(preds)
        
    bleu = sacrebleu.corpus_bleu(predictions, [refs])
    chrf = sacrebleu.corpus_chrf(predictions, [refs], word_order=2)
    return round(bleu.score, 2), round(chrf.score, 2)

def main():
    parser = argparse.ArgumentParser(description="Comparaison des modèles sur le Test Sacré")
    parser.add_argument("--beams", type=int, default=1, help="Taille du faisceau (1=greedy, 4=beam search)")
    args = parser.parse_args()
    
    print(f"Chargement du Test Sacré ({TEST_SACRE_PATH})...")
    df = pd.read_csv(TEST_SACRE_PATH).dropna(subset=["fr", "dyu"])
    pairs_fr2dyu = [{"src": r["fr"], "tgt": r["dyu"]} for _, r in df.iterrows()]
    pairs_dyu2fr = [{"src": r["dyu"], "tgt": r["fr"]} for _, r in df.iterrows()]
    
    print(f"\n=======================================================")
    print(f" ÉVALUATION COMPARATIVE TEST SACRÉ (num_beams={args.beams})")
    print(f"=======================================================")
    
    # 1. Modèle Fusionné officiel
    print(f"\n[1/2] Évaluation Modèle Fusionné ({MERGED_MODEL_ID} @ {MERGED_REVISION[:7]})...")
    tok_merged = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
    model_merged = AutoModelForSeq2SeqLM.from_pretrained(MERGED_MODEL_ID, revision=MERGED_REVISION).to(device).eval()
    
    bleu_f_fr, chrf_f_fr = eval_pairs(model_merged, tok_merged, pairs_fr2dyu, "fra_Latn", "dyu_Latn", num_beams=args.beams)
    bleu_f_dyu, chrf_f_dyu = eval_pairs(model_merged, tok_merged, pairs_dyu2fr, "dyu_Latn", "fra_Latn", num_beams=args.beams)
    print(f"  Fusionné -> FR->DYU : BLEU={bleu_f_fr} | chrF++={chrf_f_fr}")
    print(f"  Fusionné -> DYU->FR : BLEU={bleu_f_dyu} | chrF++={chrf_f_dyu}")
    
    # Tableau récapitulatif
    print("\n--- Tableau comparatif ---")
    print(f"{'Modèle':<25} | {'num_beams':<9} | {'FR -> DYU BLEU':<14} | {'DYU -> FR BLEU':<14}")
    print("-" * 72)
    print(f"{'NLLB Fusionné (5c36e48)':<25} | {args.beams:<9} | {bleu_f_fr:<14} | {bleu_f_dyu:<14}")

if __name__ == "__main__":
    main()
