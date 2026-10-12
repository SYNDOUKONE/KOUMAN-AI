import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from api.translation_service import TranslationService

translator = TranslationService()
translator.load_model()

dioula_phrases = [
    "Aw ni sɔgɔma.",
    "I ka kɛnɛ wa?",
    "I tɔgɔ bi di?",
    "N bɛ taa sugu la.",
    "Jii di n ma.",
    "I ni cɛ kosɛbɛ.",
    "Ne bɛ dioula kan mɛn.",
    "Denmisɛn bɛ sunɔgɔ.",
    "Baara ka gɛlɛn nka a ka ɲi.",
    "An bɛ ben sini."
]

print("\n" + "="*75, flush=True)
print(f"{'DIOULA (Source)':<35} | {'NLLB + GLOSSAIRE (Français)'}", flush=True)
print("="*75, flush=True)

for src in dioula_phrases:
    res = translator.translate(src, src_lang="dyu_Latn", tgt_lang="fra_Latn")
    print(f"{src:<35} | {res}", flush=True)

print("="*75, flush=True)
