import os
import torch
from api.translation_service import TranslationService

# Setup
service = TranslationService()
service.load_model()

# 10 phrases : 5 FR->DYU et 5 DYU->FR
test_cases = [
    # Français -> Dioula
    {"src": "Bonjour, comment vas-tu ?", "lang": ("fra_Latn", "dyu_Latn"), "expected": "Aw ni sɔgɔma, i ka kɛnɛ wa?"},
    {"src": "Je vais au marché pour acheter du riz.", "lang": ("fra_Latn", "dyu_Latn"), "expected": "N bɛ taa sugu la rizi san."},
    {"src": "L'enfant dort dans la chambre.", "lang": ("fra_Latn", "dyu_Latn"), "expected": "Denmisɛn bɛ sunɔgɔ sô la."},
    {"src": "S'il vous plaît, donnez-moi de l'eau.", "lang": ("fra_Latn", "dyu_Latn"), "expected": "Jii di n ma, i s'il i y'a."},
    {"src": "L'amitié est très importante.", "lang": ("fra_Latn", "dyu_Latn"), "expected": "Tériya ka gɛlɛn kosɛbɛ."},
    
    # Dioula -> Français
    {"src": "Aw ni sɔgɔma, i ka kɛnɛ wa ?", "lang": ("dyu_Latn", "fra_Latn"), "expected": "Bonjour, comment vas-tu ?"},
    {"src": "Sugu bɛ min ?", "lang": ("dyu_Latn", "fra_Latn"), "expected": "Où est le marché ?"},
    {"src": "N b'i fɛ kosɛbɛ.", "lang": ("dyu_Latn", "fra_Latn"), "expected": "Je t'aime beaucoup."},
    {"src": "N ba bɛ baan la baara.", "lang": ("dyu_Latn", "fra_Latn"), "expected": "Mon père travaille au champ."},
    {"src": "An bɛ bɛn sini.", "lang": ("dyu_Latn", "fra_Latn"), "expected": "À demain."},
]

print("\n" + "="*100)
print(f"{'DIRECTION':<15} | {'SOURCE':<35} | {'TRADUCTION':<35} | {'SENS'}")
print("="*100)

for case in test_cases:
    src_lang, tgt_lang = case["lang"]
    res = service.translate(case["src"], src_lang=src_lang, tgt_lang=tgt_lang)
    
    direction = "FR -> DYU" if src_lang == "fra_Latn" else "DYU -> FR"
    print(f"{direction:<15} | {case['src']:<35} | {res:<35} | {case['expected']}")
    print("-" * 100)

print("="*100)
