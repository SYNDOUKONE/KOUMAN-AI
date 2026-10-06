import os
import torch
from api.translation_service import TranslationService

service = TranslationService()
service.load_model()

# Test 1: Français -> Dioula
res_dyu = service.translate("Où est le marché ?", src_lang="fra_Latn", tgt_lang="dyu_Latn")
print(f"FR -> DYU: 'Où est le marché ?' => {res_dyu}")

# Test 2: Dioula -> Français (pour tester le post-processing du "Sugu")
res_fr = service.translate("Sugu bɛ min ?", src_lang="dyu_Latn", tgt_lang="fra_Latn")
print(f"DYU -> FR: 'Sugu bɛ min ?' => {res_fr}")
