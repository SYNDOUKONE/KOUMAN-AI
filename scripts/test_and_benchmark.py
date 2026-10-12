"""
Benchmark comparatif : NLLB-200-1.3B Base vs NLLB-200-1.3B Fine-tuné (LoRA + Glossaire).
"""

import os
import glob
import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel
import sacrebleu

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_LANG = "fra_Latn"
TGT_LANG = "dyu_Latn"
BASE_MODEL_NAME = "facebook/nllb-200-1.3B"
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

def get_latest_checkpoint(base_dir=None):
    if base_dir is None:
        base_dir = os.path.join(ROOT_DIR, "models", "nllb_lora_dioula")
    final_dir = os.path.join(base_dir, "final")
    if os.path.exists(os.path.join(final_dir, "adapter_model.safetensors")):
        return final_dir
    checkpoints = sorted(glob.glob(os.path.join(base_dir, "checkpoint-*")), key=lambda x: int(x.split("-")[-1]) if x.split("-")[-1].isdigit() else 0)
    if checkpoints:
        return checkpoints[-1]
    return base_dir

def translate(text, model, tokenizer, device):
    inputs = tokenizer(text, return_tensors="pt").to(device)
    forced_bos_token_id = tokenizer.lang_code_to_id[TGT_LANG]
    with torch.no_grad():
        translated_tokens = model.generate(
            **inputs,
            forced_bos_token_id=forced_bos_token_id,
            max_length=64,
            num_beams=4,
        )
    return tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]

def main():
    print("=" * 65)
    print("  BENCHMARK COMPARATIF NLLB 1.3B : Base vs Fine-tuné (LoRA)")
    print("=" * 65)
    
    adapter_path = get_latest_checkpoint()
    print(f"Chargement du checkpoint : {adapter_path}")
    print(f"Device : {DEVICE}")
    
    # 1. Chargement Tokenizer & Modèle de Base
    print("\n1. Chargement du modèle de base...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME, src_lang=SRC_LANG)
    base_model = AutoModelForSeq2SeqLM.from_pretrained(BASE_MODEL_NAME).to(DEVICE)
    base_model.eval()
    
    # 2. Test direct de phrases qualitatives
    test_phrases = [
        {"src": "Bonjour, comment vas-tu ?", "ref": "I ni sogoma, i ka kéné wa ?"},
        {"src": "Merci beaucoup pour ton aide.", "ref": "I ni tché kosobè i ka dèmè la."},
        {"src": "Où vas-tu aujourd'hui ?", "ref": "I bɛ taga min bi ?"},
        {"src": "Je vais au marché pour acheter de la nourriture.", "ref": "N'bɛ taga sugu la ka dumuni san."},
        {"src": "Donne-moi un peu d'eau s'il te plaît.", "ref": "Ji dɔ di n'ma s'il vous plaît."},
        {"src": "L'enfant dort dans la chambre.", "ref": "Denin bɛ sunɔgɔ so kɔnɔ."},
        {"src": "Le travail est difficile mais important.", "ref": "Baara ka gèlèn nka a nafa ka bon."},
        {"src": "abeille", "ref": "n'di-kisé"},
        {"src": "amitié", "ref": "tériya"},
        {"src": "amour", "ref": "kanou"},
    ]
    
    print("\n" + "=" * 65)
    print("  TESTS COMPARATIFS QUALITATIFS (PHRASES & VOCABULAIRE)")
    print("=" * 65)
    
    base_preds = []
    for item in test_phrases:
        pred_base = translate(item["src"], base_model, tokenizer, DEVICE)
        base_preds.append(pred_base)
        
    # 3. Chargement du Modèle Fine-tuné LoRA
    print("\n2. Application des poids LoRA fine-tunés...")
    lora_model = PeftModel.from_pretrained(base_model, adapter_path).to(DEVICE)
    lora_model.eval()
    
    lora_preds = []
    for item in test_phrases:
        pred_lora = translate(item["src"], lora_model, tokenizer, DEVICE)
        lora_preds.append(pred_lora)
        
    print("\n" + "-" * 85)
    print(f"{'FRANÇAIS (Source)':<35} | {'NLLB BASE (Avant)':<22} | {'NLLB FINE-TUNÉ (Après)'}")
    print("-" * 85)
    for i, item in enumerate(test_phrases):
        print(f"{item['src']:<35} | {base_preds[i]:<22} | {lora_preds[i]}")
    print("-" * 85)
    
    # 4. Benchmark quantitatif sur un échantillon du corpus
    csv_path = os.path.join(ROOT_DIR, "LIVRABLE", "06_Corpus_Final", "corpus_dioula_consolide.csv")
    if os.path.exists(csv_path):
        print("\n" + "=" * 65)
        print("  BENCHMARK QUANTITATIF (Score BLEU & chrF sur Corpus)")
        print("=" * 65)
        df = pd.read_csv(csv_path).dropna(subset=["francais", "dioula"])
        # Prendre 30 phrases de test
        sample = df.sample(30, random_state=42)
        
        refs = sample["dioula"].tolist()
        srcs = sample["francais"].tolist()
        
        preds_lora_eval = []
        preds_base_eval = []
        
        print("Évaluation en cours sur 30 phrases du corpus...")
        for src in srcs:
            preds_lora_eval.append(translate(src, lora_model, tokenizer, DEVICE))
            
        bleu_lora = sacrebleu.corpus_bleu(preds_lora_eval, [refs])
        chrf_lora = sacrebleu.corpus_chrf(preds_lora_eval, [refs])
        
        print("\n--- RÉSULTATS DU MODÈLE FINE-TUNÉ ---")
        print(f"  Score BLEU : {bleu_lora.score:.2f}")
        print(f"  Score chrF : {chrf_lora.score:.2f}")
        print("=" * 65)

if __name__ == "__main__":
    main()
