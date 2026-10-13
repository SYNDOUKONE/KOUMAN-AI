"""
Script de comparaison rigoureuse des modèles sur le Test Sacré.

Modèles comparés :
1. base      : facebook/nllb-200-1.3B (Zéro-Shot)
2. v1        : NLLB-200-1.3B + Adaptateur LoRA v1 (récupéré depuis commit 7fdb16e)
3. fusionne  : syndou/nllb-200-dioula @ révision 5c36e48 (Modèle officiel complet)
4. v2        : NLLB-200-1.3B + Adaptateur LoRA v2 (syndou/nllb-lora-dioula sur Hugging Face)

Usage :
    python3 scripts/compare_models_test_sacre.py --models base,v1,fusionne,v2 --limit 10
    python3 scripts/compare_models_test_sacre.py --models base,v1,fusionne,v2
"""

import os
import sys
import argparse
import subprocess
import torch
import pandas as pd
import sacrebleu
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel, LoraConfig

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_SACRE_PATH = os.path.join(ROOT_DIR, "data", "test_sacre.csv")
V1_DIR = os.path.join(ROOT_DIR, "models", "v1_adapter")
BASE_MODEL_ID = "facebook/nllb-200-1.3B"
FUSIONNE_ID = "syndou/nllb-200-dioula"
FUSIONNE_REV = "5c36e481ce9ce8d6f73a57181fb93d6900ddad89"
HF_LORA_V2_ID = "syndou/nllb-lora-dioula"

device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")

def ensure_v1_adapter():
    """Extrait l'adaptateur LoRA v1 depuis l'historique git (commit 7fdb16e) si absent."""
    weights_path = os.path.join(V1_DIR, "adapter_model.safetensors")
    if os.path.exists(weights_path):
        return True
    
    print(f"📦 Extraction de l'adaptateur LoRA v1 depuis le commit 7fdb16e...", flush=True)
    os.makedirs(V1_DIR, exist_ok=True)
    cmd = (
        f"git archive 7fdb16e models/nllb_lora_dioula/final | "
        f"tar -x -C '{V1_DIR}' --strip-components=3"
    )
    res = subprocess.run(cmd, shell=True, cwd=ROOT_DIR, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"⚠️ Impossible d'extraire l'adaptateur depuis git: {res.stderr}", file=sys.stderr)
        return False
    return True

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

def load_model(name: str):
    """Charge le modèle et le tokenizer demandés."""
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
    
    if name == "base":
        print(f"🔹 Chargement de NLLB Zéro-Shot ({BASE_MODEL_ID})...", flush=True)
        model = AutoModelForSeq2SeqLM.from_pretrained(BASE_MODEL_ID).to(device).eval()
        return model, tokenizer
        
    elif name == "fusionne":
        print(f"🔹 Chargement de NLLB Fusionné officiel ({FUSIONNE_ID} @ {FUSIONNE_REV[:7]})...", flush=True)
        model = AutoModelForSeq2SeqLM.from_pretrained(FUSIONNE_ID, revision=FUSIONNE_REV).to(device).eval()
        return model, tokenizer
        
    elif name == "v1":
        print(f"🔹 Chargement de LoRA v1 (local via 7fdb16e)...", flush=True)
        ensure_v1_adapter()
        base_model = AutoModelForSeq2SeqLM.from_pretrained(BASE_MODEL_ID).to(device)
        model = PeftModel.from_pretrained(base_model, V1_DIR).to(device).eval()
        return model, tokenizer
        
    elif name == "v2":
        print(f"🔹 Chargement de LoRA v2 ({HF_LORA_V2_ID} sur Hugging Face)...", flush=True)
        import json, inspect
        from huggingface_hub import snapshot_download
        folder = snapshot_download(HF_LORA_V2_ID)
        cfg_file = os.path.join(folder, "adapter_config.json")
        with open(cfg_file) as f:
            d = json.load(f)
        valid_keys = set(inspect.signature(LoraConfig.__init__).parameters.keys())
        clean_d = {k: v for k, v in d.items() if k in valid_keys}
        with open(cfg_file, "w") as f:
            json.dump(clean_d, f, indent=2)
            
        base_model = AutoModelForSeq2SeqLM.from_pretrained(BASE_MODEL_ID).to(device)
        model = PeftModel.from_pretrained(base_model, folder).to(device).eval()
        return model, tokenizer
        
    else:
        raise ValueError(f"Modèle inconnu : {name}")

def main():
    parser = argparse.ArgumentParser(description="Comparaison des modèles sur le Test Sacré")
    parser.add_argument("--models", type=str, default="base,v1,fusionne,v2",
                        help="Modèles à évaluer (séparés par virgules : base,v1,fusionne,v2)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limiter le nombre de phrases (ex: 10 pour un test rapide)")
    parser.add_argument("--beams", type=int, default=1,
                        help="Taille du faisceau (1=greedy, 4=beam search). Défaut: 1")
    args = parser.parse_args()
    
    model_keys = [m.strip().lower() for m in args.models.split(",") if m.strip()]
    
    print(f"Chargement du Test Sacré ({TEST_SACRE_PATH})...", flush=True)
    df = pd.read_csv(TEST_SACRE_PATH).dropna(subset=["fr", "dyu"])
    if args.limit:
        df = df.head(args.limit)
        print(f"⚡ Mode rapide activé : limitation à {len(df)} phrases.")
    else:
        print(f"📊 Mode complet : {len(df)} phrases étalons.")
        
    pairs_fr2dyu = [{"src": r["fr"], "tgt": r["dyu"]} for _, r in df.iterrows()]
    pairs_dyu2fr = [{"src": r["dyu"], "tgt": r["fr"]} for _, r in df.iterrows()]
    
    results = []
    
    for name in model_keys:
        print(f"\n=======================================================")
        print(f" Évaluation : {name.upper()} (num_beams={args.beams})")
        print(f"=======================================================")
        
        try:
            model, tokenizer = load_model(name)
            
            print(f"  Traduction FR -> DYU ({len(pairs_fr2dyu)} ph)...", flush=True)
            bleu_fr, chrf_fr = eval_pairs(model, tokenizer, pairs_fr2dyu, "fra_Latn", "dyu_Latn", num_beams=args.beams)
            print(f"    FR -> DYU : BLEU = {bleu_fr} | chrF++ = {chrf_fr}")
            
            print(f"  Traduction DYU -> FR ({len(pairs_dyu2fr)} ph)...", flush=True)
            bleu_dyu, chrf_dyu = eval_pairs(model, tokenizer, pairs_dyu2fr, "dyu_Latn", "fra_Latn", num_beams=args.beams)
            print(f"    DYU -> FR : BLEU = {bleu_dyu} | chrF++ = {chrf_dyu}")
            
            results.append({
                "Modèle": name,
                "num_beams": args.beams,
                "FR -> DYU BLEU": bleu_fr,
                "FR -> DYU chrF++": chrf_fr,
                "DYU -> FR BLEU": bleu_dyu,
                "DYU -> FR chrF++": chrf_dyu,
                "Phrases": len(df)
            })
            
            # Nettoyage mémoire
            del model
            del tokenizer
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
        except Exception as e:
            print(f"❌ Erreur lors de l'évaluation de {name} : {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print(" 🏆 TABLEAU RÉCAPITULATIF COMPARATIF")
    print("=" * 80)
    df_res = pd.DataFrame(results)
    print(df_res.to_string(index=False))
    print("=" * 80)

if __name__ == "__main__":
    main()
