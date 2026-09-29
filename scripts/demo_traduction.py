import os
import sys
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(ROOT_DIR, "models", "nllb_lora_dioula", "final")

device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"Chargement du modèle sur {device}...", flush=True)

base_model_name = "facebook/nllb-200-1.3B"
tokenizer = AutoTokenizer.from_pretrained(base_model_name, src_lang="fra_Latn")
base_model = AutoModelForSeq2SeqLM.from_pretrained(base_model_name).to(device)
lora_model = PeftModel.from_pretrained(base_model, MODEL_PATH).to(device)
lora_model.eval()

tests = [
    "Bonjour, comment vas-tu ?",
    "Merci beaucoup pour ton aide.",
    "Où vas-tu aujourd'hui ?",
    "Je vais au marché pour acheter de la nourriture.",
    "Donne-moi un peu d'eau s'il te plaît.",
    "L'enfant dort dans la chambre.",
    "Le travail est difficile mais important.",
    "abeille",
    "amitié",
    "amour",
]

forced_bos_token_id = tokenizer.lang_code_to_id["dyu_Latn"]

print("\n" + "="*70, flush=True)
print(f"{'FRANÇAIS (Source)':<45} | {'NLLB ENTRAÎNÉ (Dioula)'}", flush=True)
print("="*70, flush=True)

for src in tests:
    inputs = tokenizer(src, return_tensors="pt").to(device)
    with torch.no_grad():
        out = lora_model.generate(
            **inputs,
            forced_bos_token_id=forced_bos_token_id,
            max_length=64,
            num_beams=4,
        )
    pred = tokenizer.batch_decode(out, skip_special_tokens=True)[0]
    print(f"{src:<45} | {pred}", flush=True)

print("="*70, flush=True)
