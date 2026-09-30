"""
Kouman AI — Démonstrateur Synthèse Vocale (Text-To-Speech / TTS)
Français -> Traduction NLLB LoRA (Dioula) -> Synthèse Vocale MMS-TTS (facebook/mms-tts-dyu) -> Fichier WAV
"""

import os
import sys
import torch
import scipy.io.wavfile as wavfile
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, VitsModel
from peft import PeftModel

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(ROOT_DIR, "models", "nllb_lora_dioula", "final")
TTS_MODEL_ID = "facebook/mms-tts-dyu"

device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")

def load_nllb_translator():
    print(f"Chargement du modèle NLLB LoRA sur {device}...", flush=True)
    base_model_name = "facebook/nllb-200-1.3B"
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, src_lang="fra_Latn")
    base_model = AutoModelForSeq2SeqLM.from_pretrained(base_model_name).to(device)
    lora_model = PeftModel.from_pretrained(base_model, MODEL_PATH).to(device)
    lora_model.eval()
    return tokenizer, lora_model

def translate_fr_to_dyu(tokenizer, model, text: str) -> str:
    inputs = tokenizer(text, return_tensors="pt").to(device)
    forced_bos_token_id = tokenizer.lang_code_to_id["dyu_Latn"]
    with torch.no_grad():
        out = model.generate(
            **inputs,
            forced_bos_token_id=forced_bos_token_id,
            max_length=128,
            num_beams=4,
        )
    return tokenizer.batch_decode(out, skip_special_tokens=True)[0]

def speak_dioula(text_dioula: str, output_path: str = "sortie_dioula.wav"):
    print(f"Chargement de MMS-TTS ({TTS_MODEL_ID})...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(TTS_MODEL_ID)
    model = VitsModel.from_pretrained(TTS_MODEL_ID).to(device)
    
    # MMS-TTS attend du texte en minuscules
    inputs = tokenizer(text_dioula.lower(), return_tensors="pt").to(device)
    torch.manual_seed(555)
    with torch.no_grad():
        waveform = model(**inputs).waveform[0].cpu().numpy()
    
    wavfile.write(output_path, model.config.sampling_rate, waveform)
    print(f"✅ Fichier audio généré avec succès : {output_path}", flush=True)

if __name__ == "__main__":
    text_fr = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Bonjour, comment allez-vous aujourd'hui ?"
    print("=" * 70)
    print(f"Texte Source (Français) : {text_fr}")
    
    tokenizer, nllb_model = load_nllb_translator()
    dioula_text = translate_fr_to_dyu(tokenizer, nllb_model, text_fr)
    print(f"Traduction (Dioula)     : {dioula_text}")
    
    output_file = os.path.join(ROOT_DIR, "sortie_dioula.wav")
    speak_dioula(dioula_text, output_file)
    print("=" * 70)
