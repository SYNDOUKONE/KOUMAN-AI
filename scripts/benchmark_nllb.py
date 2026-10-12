import os
import time
import argparse
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel
import sacrebleu

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CSV = os.path.join(ROOT_DIR, "LIVRABLE", "06_Corpus_Final", "corpus_dioula_consolide.csv")
DEFAULT_LORA = os.path.join(ROOT_DIR, "models", "nllb_lora_dioula", "final")

def main(csv_path=DEFAULT_CSV, source_col="francais", target_col="dioula", max_samples=10, use_lora=True):
    print(f"Chargement du dataset depuis {csv_path}...")
    df = pd.read_csv(csv_path)
    
    df_sample = df.dropna(subset=[source_col, target_col]).head(max_samples)
    
    base_model_name = "facebook/nllb-200-1.3B"
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Chargement du modèle {base_model_name} sur {device}...")
    
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, src_lang="fra_Latn")
    model = AutoModelForSeq2SeqLM.from_pretrained(base_model_name).to(device)
    
    if use_lora and os.path.exists(DEFAULT_LORA):
        print(f"Application des poids fine-tunés LoRA depuis {DEFAULT_LORA}...")
        model = PeftModel.from_pretrained(model, DEFAULT_LORA).to(device)
        model_label = "NLLB-200-1.3B (Fine-tuné LoRA + Glossaire)"
    else:
        model_label = "NLLB-200-1.3B (Base Zero-shot)"
        
    model.eval()
    
    tgt_lang = "dyu_Latn"
    forced_bos_token_id = tokenizer.lang_code_to_id[tgt_lang]
    
    predictions = []
    references = df_sample[target_col].tolist()
    sources = df_sample[source_col].tolist()
    
    start_time = time.time()
    
    print("\nDébut des traductions...")
    for i, text in enumerate(sources):
        inputs = tokenizer(text, return_tensors="pt").to(device)
        with torch.no_grad():
            translated_tokens = model.generate(
                **inputs, 
                forced_bos_token_id=forced_bos_token_id, 
                max_length=64,
                num_beams=4
            )
        
        translated_text = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]
        predictions.append(translated_text)
        print(f"[{i+1}/{len(sources)}] Source: {text}")
        print(f"[{i+1}/{len(sources)}] Traduit (Dioula) : {translated_text}")
        print(f"[{i+1}/{len(sources)}] Référence (Dioula): {references[i]}\n")
        
    end_time = time.time()
    
    bleu = sacrebleu.corpus_bleu(predictions, [references])
    chrf = sacrebleu.corpus_chrf(predictions, [references])
    
    print("=" * 60)
    print("=== RÉSULTATS DU BENCHMARK ===")
    print("=" * 60)
    print(f"Modèle : {model_label}")
    print(f"Temps pour {max_samples} phrases : {end_time - start_time:.2f} secondes")
    print(f"Score BLEU : {bleu.score:.2f}")
    print(f"Score chrF : {chrf.score:.2f}")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark de traduction NLLB vers le Dioula")
    parser.add_argument("--csv", default=DEFAULT_CSV, help="Chemin vers le fichier CSV du corpus")
    parser.add_argument("--src_col", default="francais", help="Nom de la colonne source (ex: 'francais')")
    parser.add_argument("--tgt_col", default="dioula", help="Nom de la colonne cible (ex: 'dioula')")
    parser.add_argument("--samples", type=int, default=10, help="Nombre de phrases à tester")
    parser.add_argument("--base_only", action="store_true", help="Tester uniquement le modèle de base sans LoRA")
    args = parser.parse_args()
    
    main(args.csv, args.src_col, args.tgt_col, args.samples, use_lora=(not args.base_only))
