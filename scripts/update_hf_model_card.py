"""
Script pour mettre à jour la carte de modèle Hugging Face de syndou/nllb-200-dioula
Alignement : 8 837 paires réelles (17 674 exemples bidirectionnels) et traçabilité de révision.
"""

from huggingface_hub import HfApi

MODEL_CARD_CONTENT = """---
base_model: facebook/nllb-200-1.3B
library_name: transformers
pipeline_tag: translation
language:
- dyu
- fr
tags:
- translation
- nllb
- nllb-200
- dioula
- jula
- french
- african-languages
- kouman-ai
metrics:
- bleu
- chrf
---

# 🌍 Kouman AI — NLLB-200-1.3B Complet Fusionné (Français ⟷ Dioula / Jula)

Modèle complet et autonome de traduction automatique bidirectionnelle **Français ⟷ Dioula (Jula)** basé sur **[facebook/nllb-200-1.3B](https://huggingface.co/facebook/nllb-200-1.3B)**.

Les adaptateurs LoRA ont été fusionnés (`merge_and_unload`) directement dans les poids de base du modèle. Vous pouvez l'utiliser directement avec la bibliothèque standard `transformers` sans avoir besoin d'installer `peft`.

Développé dans le cadre du projet **Kouman AI** dédié au traitement automatique des langues de Côte d'Ivoire et d'Afrique de l'Ouest (Baoulé, Dioula).

---

## 📊 Performances & Évaluations Scientifiques

### 1. Jeu de Test Sacré (144 phrases conversationnelles étanches — 0 contamination)
Mesuré sur le modèle officiel fusionné (`5c36e48`) avec les métriques standard SacreBLEU et chrF++ :

| Direction | Langue Source (`src_lang`) | Langue Cible (`tgt_lang`) | Échantillons | Score BLEU | Score chrF++ |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Français ➔ Dioula** | `fra_Latn` | `dyu_Latn` | 144 | **25.59** *(vs 14.63 en Zéro-Shot)* | **43.29** *(vs 33.40 en Zéro-Shot)* |
| **Dioula ➔ Français** | `dyu_Latn` | `fra_Latn` | 144 | **17.40** *(vs 17.34 en Zéro-Shot)* | **40.42** *(vs 38.76 en Zéro-Shot)* |

### 2. Validation V2 Décorrélée (940 exemples bidirectionnels)
| Direction | Langue Source (`src_lang`) | Langue Cible (`tgt_lang`) | Échantillons | Score BLEU | Score chrF++ |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Français ➔ Dioula** | `fra_Latn` | `dyu_Latn` | 470 | **45.84** | **63.05** |
| **Dioula ➔ Français** | `dyu_Latn` | `fra_Latn` | 470 | **31.27** | **54.23** |

---

## 📚 Données d'Entraînement & Traçabilité (Révision `6763611` / `5c36e48`)

Le modèle a été entraîné sur le **Dataset V2 Nettoyé & Équilibré** totalisant **17 674 exemples bidirectionnels** (soit **8 837 paires uniques** FR ⟷ Dioula), garanti **100% sans fuite** vers le Jeu de Test Sacré :

| Source | Type de ressource | Paires nettes | Description & Traitement |
|:---|:---|:---:|:---|
| **Corpus Consolidé (R008 / R006)** | Textes bibliques et dialogues | ~4 700 | Domaine biblique rééquilibré à max 40% pour privilégier le registre conversationnel |
| **Glossaire Dioula** | Vocabulaire institutionnel & usuel | ~3 100 | Vocabulaire administratif, médical et expressions courantes |
| **Guide Orthographe Webonary** | Lexique & grammaire | 732 | Correspondances orthographiques standardisées |
| **Targumi Dioula & Bambara** | Paires web conversationnelles | 392 | Enrichissement conversationnel & proximité linguistique (~85%) |
| **Test Sacré (144 phrases)** | Phrases étalons | *0 inclus* | **Exclu à 100% de l'entraînement** (réservé exclusivement à l'évaluation) |
| *AfriSpeech (R003)* | *Corpus audio transcrit* | *0 inclus* | *Classé Baoulé dans l'inventaire, exclu du modèle Dioula* |

### Scripts & Procédure de Reproduction :
- **Préparation du dataset** : `scripts/prepare_dataset_v2.py` générant `data/processed_v2_train.json` (8 837 paires uniques / 17 674 exemples bidirectionnels).
- **Fine-tuning LoRA** : `scripts/finetune_nllb.py` (LoRA `r=16`, `alpha=32`, `target_modules=["q_proj", "v_proj", "k_proj", "out_proj"]`, batch effectif 32, LR 5e-4).
- **Fusion des poids** : `merge_and_unload()` exporté sous le commit initial `6763611` et ajusté avec `max_length=64` sous le commit `5c36e48`.
- **Vérification d'étanchéité** : `scripts/check_test_leakage.py` (0 fuite constatée).

---

## 🛠️ Utilisation Rapide (Python)

### Installation
```bash
pip install torch transformers sentencepiece
```

### Exemple d'inférence (Français ➔ Dioula)

```python
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

MODEL_ID = "syndou/nllb-200-dioula"
REVISION = "5c36e481ce9ce8d6f73a57181fb93d6900ddad89"
device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=REVISION)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_ID, revision=REVISION).to(device)
model.eval()

# Traduction FR -> DYU
texte_fr = "Bonjour, comment allez-vous aujourd'hui ?"
tokenizer.src_lang = "fra_Latn"
forced_bos_token_id = tokenizer.convert_tokens_to_ids("dyu_Latn")

inputs = tokenizer(texte_fr, return_tensors="pt").to(device)

with torch.no_grad():
    generated_tokens = model.generate(
        **inputs,
        forced_bos_token_id=forced_bos_token_id,
        max_new_tokens=64,
        num_beams=4,
    )

traduction = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
print("Traduction :", traduction)
```

### Exemple d'inférence (Dioula ➔ Français)

```python
# Traduction DYU -> FR
texte_dyu = "I ni sogoma, i ka kɛnɛ wa ?"
tokenizer.src_lang = "dyu_Latn"
forced_bos_token_id = tokenizer.convert_tokens_to_ids("fra_Latn")

inputs = tokenizer(texte_dyu, return_tensors="pt").to(device)

with torch.no_grad():
    generated_tokens = model.generate(
        **inputs,
        forced_bos_token_id=forced_bos_token_id,
        max_new_tokens=64,
        num_beams=4,
    )

traduction = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
print("Traduction :", traduction)
```

---

## 📖 Dictionnaires & Ressources Linguistiques
- 📕 [Petit Dictionnaire Français - Dioula (PDF)](https://huggingface.co/syndou/nllb-200-dioula/resolve/main/docs/petit_dictionnaire.pdf)
- 📗 [Guide Orthographe Dioula (Webonary)](https://www.webonary.org/dioula-bf/files/Guide-orthographe-dioula.pdf)

---

## 📜 Citation & Remerciements

Projet **Kouman AI** — Préservation et valorisation numérique des langues de Côte d'Ivoire.
Base NLLB fournie par Meta AI.
"""

LORA_CARD_CONTENT = """---
base_model: facebook/nllb-200-1.3B
library_name: peft
pipeline_tag: translation
language:
- dyu
- fr
tags:
- translation
- nllb
- nllb-200
- lora
- peft
- dioula
- jula
- french
- african-languages
- kouman-ai
metrics:
- bleu
- chrf
---

# 🌍 Kouman AI — NLLB-200-1.3B LoRA v2 (Français ⟷ Dioula / Jula)

Modèle de traduction automatique bidirectionnelle **Français ⟷ Dioula (Jula)** basé sur **[facebook/nllb-200-1.3B](https://huggingface.co/facebook/nllb-200-1.3B)** et optimisé avec **LoRA (PEFT)**.

Développé dans le cadre du projet **Kouman AI** dédié au traitement automatique des langues de Côte d'Ivoire et d'Afrique de l'Ouest (Baoulé, Dioula).

> ℹ️ **Note** : Une version entièrement fusionnée et autonome (`merge_and_unload`) est disponible sur [`syndou/nllb-200-dioula`](https://huggingface.co/syndou/nllb-200-dioula). Les poids fusionnés et cet adaptateur LoRA v2 produisent des inférences strictement identiques.

---

## 📊 Performances & Évaluations Scientifiques

### 1. Jeu de Test Sacré (144 phrases étanches — 0 fuite)
| Direction | Langue Source | Langue Cible | Échantillons | Score BLEU | Score chrF++ |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Français ➔ Dioula** | `fra_Latn` | `dyu_Latn` | 144 | **25.59** *(vs 14.63 en Zéro-Shot)* | **43.29** *(vs 33.40 en Zéro-Shot)* |
| **Dioula ➔ Français** | `dyu_Latn` | `fra_Latn` | 144 | **17.40** *(vs 17.34 en Zéro-Shot)* | **40.42** *(vs 38.76 en Zéro-Shot)* |

### 2. Validation V2 Décorrélée (940 exemples bidirectionnels)
| Direction | Langue Source | Langue Cible | Échantillons | Score BLEU | Score chrF++ |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Français ➔ Dioula** | `fra_Latn` | `dyu_Latn` | 470 | **45.84** | **63.05** |
| **Dioula ➔ Français** | `dyu_Latn` | `fra_Latn` | 470 | **31.27** | **54.23** |

---

## 🛠️ Utilisation Rapide (Python)

### Installation
```bash
pip install torch transformers peft sentencepiece
```

### Exemple d'inférence (Français ➔ Dioula)

```python
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel

BASE_MODEL = "facebook/nllb-200-1.3B"
LORA_MODEL = "syndou/nllb-lora-dioula"

device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
dtype = torch.float32

tokenizer = AutoTokenizer.from_pretrained(LORA_MODEL)
base_model = AutoModelForSeq2SeqLM.from_pretrained(BASE_MODEL, torch_dtype=dtype)
model = PeftModel.from_pretrained(base_model, LORA_MODEL).to(device)
model.eval()

# Traduction FR -> DYU
texte_fr = "Bonjour, comment allez-vous aujourd'hui ?"
tokenizer.src_lang = "fra_Latn"
forced_bos = tokenizer.convert_tokens_to_ids("dyu_Latn")

inputs = tokenizer(texte_fr, return_tensors="pt").to(device)

with torch.no_grad():
    generated = model.generate(
        **inputs,
        forced_bos_token_id=forced_bos,
        max_new_tokens=64,
        num_beams=4,
    )

traduction = tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
print("Traduction :", traduction)
```

---

## 📚 Données d'Entraînement

Le modèle a été entraîné sur le **Dataset V2 Nettoyé & Équilibré** totalisant **17 674 exemples bidirectionnels** (soit **8 837 paires uniques** FR ⟷ Dioula), garanti **100% sans fuite** vers le Jeu de Test Sacré :
- Corpus Consolidé (textes bibliques équilibrés à max 40%) : ~4 700 paires
- Glossaire Dioula institutionnel & usuel : ~3 100 paires
- Guide Orthographe Webonary : 732 paires
- Targumi Dioula & Bambara : 392 paires
- *Test Sacré : exclu à 100% de l'entraînement.*
- *AfriSpeech : classé Baoulé dans l'inventaire, exclu du modèle Dioula.*

---

## 📖 Dictionnaires & Ressources Linguistiques
- 📕 [Petit Dictionnaire Français - Dioula (PDF)](https://huggingface.co/syndou/nllb-200-dioula/resolve/main/docs/petit_dictionnaire.pdf)
- 📗 [Guide Orthographe Dioula (Webonary)](https://www.webonary.org/dioula-bf/files/Guide-orthographe-dioula.pdf)

---

## 📜 Citation & Remerciements

Projet **Kouman AI** — Préservation et valorisation numérique des langues de Côte d'Ivoire.
Base NLLB fournie par Meta AI.
"""

def main():
    api = HfApi()
    
    # 1. Modèle fusionné officiel
    api.upload_file(
        path_or_fileobj=MODEL_CARD_CONTENT.encode("utf-8"),
        path_in_repo="README.md",
        repo_id="syndou/nllb-200-dioula",
        commit_message="docs: 8 837 paires réelles, liens dictionnaires PDF & métriques test sacré (S4)",
    )
    print("✅ Carte Hugging Face syndou/nllb-200-dioula mise à jour avec succès !")

    # 2. Modèle LoRA
    api.upload_file(
        path_or_fileobj=LORA_CARD_CONTENT.encode("utf-8"),
        path_in_repo="README.md",
        repo_id="syndou/nllb-lora-dioula",
        commit_message="docs: 8 837 paires réelles, liens dictionnaires PDF & métriques test sacré",
    )
    print("✅ Carte Hugging Face syndou/nllb-lora-dioula mise à jour avec succès !")

if __name__ == "__main__":
    main()
