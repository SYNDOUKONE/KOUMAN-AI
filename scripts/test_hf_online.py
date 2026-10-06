import os
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel

# CONFIGURATION
HF_MODEL_ID = "syndou/nllb-lora-dioula"
BASE_MODEL = "facebook/nllb-200-1.3B"
device = "mps" if torch.backends.mps.is_available() else "cpu"

print(f"--- TEST DU MODÈLE EN LIGNE (HF) ---")
print(f"Chargement depuis Hugging Face : {HF_MODEL_ID}...", flush=True)

try:
    # 1. Chargement du tokenizer et modèle de base
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    base_model = AutoModelForSeq2SeqLM.from_pretrained(BASE_MODEL).to(device)

    # 2. Chargement de l'adaptateur LoRA directement depuis le Hub
    model = PeftModel.from_pretrained(base_model, HF_MODEL_ID).to(device)
    model.eval()
    print("✅ Modèle chargé avec succès depuis Hugging Face !\n", flush=True)

    def translate(text, src_lang, tgt_lang):
        tokenizer.src_lang = src_lang
        inputs = tokenizer(text, return_tensors="pt").to(device)
        forced_bos_token_id = tokenizer.lang_code_to_id[tgt_lang]
        with torch.no_grad():
            out = model.generate(
                **inputs,
                forced_bos_token_id=forced_bos_token_id,
                max_length=64,
                num_beams=4,
            )
        return tokenizer.batch_decode(out, skip_special_tokens=True)[0]

    # Test rapide
    test_phrases = [
        ("Je vais au marché.", "fra_Latn", "dyu_Latn"),
        ("Sugu bɛ min ?", "dyu_Latn", "fra_Latn"),
    ]

    for src, s_lang, t_lang in test_phrases:
        res = translate(src, s_lang, t_lang)
        print(f"Source: {src} => Traduction: {res}")

except Exception as e:
    print(f"❌ Erreur : {e}")
