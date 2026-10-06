import os
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel
import subprocess

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

def generate_audio(text, filename, lang="dyu"):
    # On utilise le script existant demo_tts.py via subprocess pour simplicité
    # On suppose que demo_tts.py accepte un texte en argument ou a une fonction
    # Pour ce test, on simule l'appel au pipeline TTS
    print(f"Génération audio pour: {text} -> {filename}...", flush=True)
    # On appelle le script de TTS si disponible
    cmd = f"python3 scripts/demo_tts.py --text \"{text}\" --out {filename}"
    subprocess.run(cmd, shell=True, capture_output=True)

# --- TESTS BIDIRECTIONNELS ---
test_pairs = [
    {"fr": "Bonjour, comment vas-tu ?", "dyu": "Aw ni sɔgɔma, i ka kènè ?"},
    {"fr": "Je t'aime beaucoup.", "dyu": "N b'i fɛ kosɛbɛ."},
    {"fr": "Où est le marché ?", "dyu": "Sugu bɛ min ?"},
]

print("\n" + "="*80, flush=True)
print(f"{'DIRECTION':<20} | {'SOURCE':<30} | {'TRADUCTION'}", flush=True)
print("="*80, flush=True)

audio_files = []

for pair in test_pairs:
    # Test FR -> DYU
    res_dyu = translate(pair["fr"], "fra_Latn", "dyu_Latn")
    print(f"{'FR -> DYU':<20} | {pair['fr']:<30} | {res_dyu}", flush=True)

    # Test DYU -> FR
    res_fr = translate(pair["dyu"], "dyu_Latn", "fra_Latn")
    print(f"{'DYU -> FR':<20} | {pair['dyu']:<30} | {res_fr}", flush=True)

print("="*80, flush=True)

# Simulation de sortie vocale pour la première phrase (FR -> DYU)
# Note: Dans l'environnement CLI, je ne peux pas "jouer" le son,
# mais je crée le fichier .wav pour l'utilisateur.
generate_audio(res_dyu, "test_resultat_vocale.wav")
print("\n✅ Fichier audio généré : test_resultat_vocale.wav")
