"""
Kouman AI — Démonstrateur Reconnaissance Vocale (Speech-To-Text / STT)
Fichier Audio Dioula (.wav) -> Transcription Whisper Tiny Dioula (Dama12/whisper-tiny-dioula) -> Traduction NLLB (Français)
"""

import os
import sys
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(ROOT_DIR, "models", "nllb_lora_dioula", "final")
STT_MODEL_ID = "Dama12/whisper-tiny-dioula"

device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")

def transcribe_audio_dioula(audio_path: str) -> str:
    print(f"Chargement du modèle STT Whisper Dioula ({STT_MODEL_ID})...", flush=True)
    hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    
    dev = device if device != "mps" else "cpu"
    try:
        stt_pipeline = pipeline(
            "automatic-speech-recognition",
            model=STT_MODEL_ID,
            device=dev,
            token=hf_token
        )
    except Exception as e:
        if "GatedRepoError" in str(e) or "403" in str(e):
            print("\n⚠️ ATTENTION: Le modèle 'Dama12/whisper-tiny-dioula' est un dépôt sous accès restreint (gated repo) sur Hugging Face.")
            print("Pour y accéder :")
            print(" 1. Demandez l'accès sur : https://huggingface.co/Dama12/whisper-tiny-dioula")
            print(" 2. Exportez votre jeton HuggingFace : export HF_TOKEN=\"votre_jeton_hf\"\n")
        raise e

    print(f"Transcription de l'audio : {audio_path}...", flush=True)
    result = stt_pipeline(audio_path)
    return result.get("text", "")

def load_nllb_translator():
    print(f"Chargement du modèle NLLB LoRA sur {device}...", flush=True)
    base_model_name = "facebook/nllb-200-1.3B"
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, src_lang="dyu_Latn")
    base_model = AutoModelForSeq2SeqLM.from_pretrained(base_model_name).to(device)
    lora_model = PeftModel.from_pretrained(base_model, MODEL_PATH).to(device)
    lora_model.eval()
    return tokenizer, lora_model

def translate_dyu_to_fr(tokenizer, model, text: str) -> str:
    tokenizer.src_lang = "dyu_Latn"
    inputs = tokenizer(text, return_tensors="pt").to(device)
    forced_bos_token_id = tokenizer.lang_code_to_id["fra_Latn"]
    with torch.no_grad():
        out = model.generate(
            **inputs,
            forced_bos_token_id=forced_bos_token_id,
            max_length=128,
            num_beams=4,
        )
    return tokenizer.batch_decode(out, skip_special_tokens=True)[0]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python3 scripts/demo_stt.py <chemin_fichier_audio.wav>")
        sys.exit(1)
        
    audio_file = sys.argv[1]
    if not os.path.exists(audio_file):
        print(f"Erreur : le fichier {audio_file} n'existe pas.")
        sys.exit(1)

    print("=" * 70)
    try:
        dioula_transcript = transcribe_audio_dioula(audio_file)
        print(f"Transcription Dioula (STT) : {dioula_transcript}")
        
        tokenizer, nllb_model = load_nllb_translator()
        french_text = translate_dyu_to_fr(tokenizer, nllb_model, dioula_transcript)
        print(f"Traduction Français (NLLB)  : {french_text}")
    except Exception as err:
        print(f"Échec STT : {err}")
    print("=" * 70)
