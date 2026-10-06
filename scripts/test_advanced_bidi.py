import os
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(ROOT_DIR, "models", "nllb_lora_dioula", "final")

device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"Chargement du modèle sur {device}...", flush=True)

base_model_name = "facebook/nllb-200-1.3B"
tokenizer = AutoTokenizer.from_pretrained(base_model_name)
base_model = AutoModelForSeq2SeqLM.from_pretrained(base_model_name).to(device)
lora_model = PeftModel.from_pretrained(base_model, MODEL_PATH).to(device)
lora_model.eval()

def translate(text, src_lang, tgt_lang):
    tokenizer.src_lang = src_lang
    inputs = tokenizer(text, return_tensors="pt").to(device)
    forced_bos_token_id = tokenizer.lang_code_to_id[tgt_lang]
    with torch.no_grad():
        out = lora_model.generate(
            **inputs,
            forced_bos_token_id=forced_bos_token_id,
            max_length=64,
            num_beams=4,
        )
    return tokenizer.batch_decode(out, skip_special_tokens=True)[0]

# Tests plus diversifiés
test_sets = [
    # Phrases complexes / vie quotidienne
    {"fr": "Je veux manger du riz avec de la sauce.", "dyu": "N b'a fɛ ka duman duman sɔrɔ."}, 
    {"fr": "L'eau est très froide aujourd'hui.", "dyu": "Ji bɛ gni kosɛbɛ isi."},
    {"fr": "Mon père travaille au champ.", "dyu": "N ba bɛ baan la baara."},
    # Expressions de politesse et besoins
    {"fr": "S'il vous plaît, aidez-moi.", "dyu": "I dɛm n, i s'il i y'a."},
    {"fr": "Je ne comprends pas ce que tu dis.", "dyu": "N tɛ o munu."},
    # Mots isolés (Vérification glossaire)
    {"fr": "la famille", "dyu": "denya"},
    {"fr": "la santé", "dyu": "kɛnɛya"},
]

print("\n" + "="*90, flush=True)
print(f"{'DIRECTION':<20} | {'SOURCE':<35} | {'TRADUCTION'}", flush=True)
print("="*90, flush=True)

for pair in test_sets:
    # FR -> DYU
    res_dyu = translate(pair["fr"], "fra_Latn", "dyu_Latn")
    print(f"{'FR -> DYU':<20} | {pair['fr']:<35} | {res_dyu}", flush=True)
    
    # DYU -> FR
    res_fr = translate(pair["dyu"], "dyu_Latn", "fra_Latn")
    print(f"{'DYU -> FR':<20} | {pair['dyu']:<35} | {res_fr}", flush=True)
    print("-" * 90, flush=True)

print("="*90, flush=True)
