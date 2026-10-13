# 🌍 Kouman AI — Traduction Automatique Français ↔ Dioula (NLLB-200)

Projet de traduction automatique neuronale haute performance spécialisé pour la langue **Dioula** (*dyu_Latn*) et le **Français** (*fra_Latn*), basé sur le modèle **NLLB-200-1.3B** de Meta, optimisé par **Fine-Tuning LoRA (PEFT)** et consolidé en **modèle autonome fusionné**.

---

## 🚀 Modèles Officiels Déployés (Hugging Face)

Le projet propose deux formats de modèles hébergés publiquement sur Hugging Face :

| Format | Identifiant Hugging Face | Révision figée | Taille | Description |
|:---|:---|:---:|:---:|:---|
| **Modèle Fusionné (Officiel Démo)** | [`syndou/nllb-200-dioula`](https://huggingface.co/syndou/nllb-200-dioula) | `5c36e48` | **2,6 Go** | Modèle complet autonome (`merge_and_unload`). Utilisable directement avec `transformers` sans dépendance `peft`. |
| **Adaptateur LoRA (Modulaire)** | [`syndou/nllb-lora-dioula`](https://huggingface.co/syndou/nllb-lora-dioula) | `5aff243` | **18 Mo** | Adaptateur léger PEFT appliqué sur `facebook/nllb-200-1.3B`. |

---

## 📁 Structure du Dépôt

```text
kouman_AI/
├── 📄 README.md                        # Documentation générale du projet
├── 📄 requirements.txt                 # Dépendances Python de base
├── 📄 requirements-model.txt           # Dépendances NMT, PEFT & LLM
│
├── 📂 backend/                         # 🌟 API Officielle de Démo (FastAPI, sessions, orchestrateur, LLM)
│   ├── 📄 README.md                    # Guide complet de déploiement de l'API de démo
│   ├── 📄 .env.example                 # Variables d'environnement & configuration modèles
│   ├── 📂 app/                         # Cœur applicatif (routes, services, traducteurs)
│   └── 📂 scripts/                     # Benchmarks LLM et scénarios de test
│
├── 📂 api/                             # 🧪 Prototype Multimodal V2 (Audio Whisper STT / MMS-TTS / Recherche)
│   ├── 📄 app.py                       # Serveur FastAPI prototype multimodal
│   ├── 📄 translation_service.py       # Service de traduction local / Hugging Face
│   └── 📄 audio_service.py             # Service de synthèse et reconnaissance vocale
│
├── 📂 data/                            # Datasets, glossaires et jeux d'évaluation
│   ├── 📄 test_sacre.csv               # Jeu de Test Sacré (144 phrases conversationnelles étanches)
│   ├── 📄 glossaire_dioula.json        # Glossaire bilingue (3 174 termes FR↔Dioula)
│   ├── 📄 custom_idioms.json           # Expressions courantes et formules de politesse
│   ├── 📄 processed_v2_train.json      # Dataset d'entraînement V2 étanche (17 674 exemples)
│   ├── 📄 processed_v2_val.json        # Dataset de validation V2 (940 exemples)
│   └── 📄 baselines_results.tsv        # Résultats comparatifs des baselines et modèles
│
├── 📂 scripts/                         # Scripts de préparation, entraînement et benchmarks
│   ├── 📄 prepare_dataset_v2.py        # Préparation du dataset V2 avec filtrage anti-fuite
│   ├── 📄 scrape_dioula.py             # Collecte Webonary PDF & Targumi
│   ├── 📄 integrate_scraped_data.py    # Fusion sécurisée des données scrapées
│   ├── 📄 check_test_leakage.py        # Contrôle d'étanchéité strict contre le Test Sacré
│   ├── 📄 finetune_nllb.py             # Pipeline d'entraînement NLLB LoRA bidirectionnel
│   └── 📄 upload_to_hf.py              # Publication des adaptateurs sur Hugging Face
│
└── 📂 docs/                            # Spécifications, cahier des charges et inventaires
```

---

## 📊 Performances & Résultats des Évaluations

Pour garantir une rigueur scientifique absolue, les métriques sont mesurées par **direction**, par **jeu de test** et avec des jeux **totalement étanches** (0 fuite de données) :

### 1. Jeu de Test Sacré (144 phrases conversationnelles étanches)
Le Test Sacré est un jeu de référence représentatif des échanges du quotidien (salutations, marché, santé, famille) avec **0 contamination** dans les données d'entraînement :

| Modèle | Direction | BLEU | chrF++ | Nombre de phrases |
|:---|:---:|:---:|:---:|:---:|
| **NLLB-200-1.3B (Zéro-Shot Base)** | Français ➔ Dioula | 12.03 | 33.76 | 144 |
| **NLLB-200-1.3B (Zéro-Shot Base)** | Dioula ➔ Français | 17.30 | 38.79 | 144 |
| **NLLB + LoRA v1 (Fine-Tuné)** | Français ➔ Dioula | **29.14** | **44.24** | 144 |
| **NLLB + LoRA v1 (Fine-Tuné)** | Dioula ➔ Français | **19.71** | **41.92** | 144 |

### 2. Validation V2 (940 phrases bilingues, split décorrélé)
| Modèle | Direction | BLEU | chrF++ | Nombre de phrases |
|:---|:---:|:---:|:---:|:---:|
| **NLLB-200-1.3B (Zéro-Shot Base)** | Français ➔ Dioula | 44.63 | 61.87 | 470 |
| **NLLB-200-1.3B (Zéro-Shot Base)** | Dioula ➔ Français | 30.52 | 53.53 | 470 |
| **NLLB + LoRA v1 (Fine-Tuné)** | Français ➔ Dioula | **45.84** | **63.05** | 470 |
| **NLLB + LoRA v1 (Fine-Tuné)** | Dioula ➔ Français | **31.27** | **54.23** | 470 |

### 3. Split de Test Consolidé Hugging Face (2 447 phrases bilingues)
Mesuré sur le modèle complet fusionné [`syndou/nllb-200-dioula`](https://huggingface.co/syndou/nllb-200-dioula) :

| Direction | BLEU | chrF | Vitesse d'inférence |
|:---|:---:|:---:|:---:|
| **Français ➔ Dioula** | **42.45** | **60.24** | ~11.8 ph/s |
| **Dioula ➔ Français** | **28.53** | **51.51** | ~10.5 ph/s |

---

## 📚 Données d'Entraînement & Inventaire des Sources

Le dataset d'entraînement V2 enrichi totalise **17 674 exemples bidirectionnels** (soit 8 837 paires uniques FR ⟷ Dioula), garanti sans fuite vers le Test Sacré :

| Source | Type de ressource | Langue | Paires nettes | Notes & Rôle |
|:---|:---|:---:|:---:|:---|
| **Corpus Consolidé (R008 / R006)** | Textes bibliques et dialogues | Dioula | ~4 700 | Domaine biblique rééquilibré à max 40% pour favoriser le conversationnel |
| **Glossaire Dioula** | Vocabulaire & locutions | Dioula | ~3 100 | Vocabulaire institutionnel, médical et usuel |
| **Guide Orthographe Webonary** | Lexique & grammaire | Dioula BF | 732 | Correspondances orthographiques standardisées |
| **Targumi Dioula** | Vocabulaire web structuré | Dioula | 196 | Paires conversationnelles extraites par JSON-LD |
| **Targumi Bambara** | Vocabulaire web proche | Bambara | 196 | Intégration justifiée par la proximité linguistique (~85% d'intercompréhension) |
| **Test Sacré** | Phrases de référence | Dioula | 144 | **Exclu à 100% de l'entraînement** (réservé à l'évaluation) |
| *AfriSpeech (R003)* | *Corpus audio transcrit* | *Baoulé* | *0* | *Classé Baoulé dans l'inventaire, exclu du modèle Dioula* |

---

## 🛠️ Utilisation Rapide

### 1. Inférence avec le Modèle Officiel Fusionné
```python
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

MODEL_ID = "syndou/nllb-200-dioula"
REVISION = "5c36e481ce9ce8d6f73a57181fb93d6900ddad89"

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=REVISION)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_ID, revision=REVISION)

# Traduction Français -> Dioula
tokenizer.src_lang = "fra_Latn"
forced_bos = tokenizer.lang_code_to_id["dyu_Latn"]

inputs = tokenizer("Bonjour, comment vas-tu ?", return_tensors="pt")
outputs = model.generate(**inputs, forced_bos_token_id=forced_bos, max_length=64)
print(tokenizer.batch_decode(outputs, skip_special_tokens=True)[0])
# Sortie : Aw ni sɔgɔma, i ka kɛnɛ wa?
```

### 2. Lancer l'API de Démo
Consultez le guide complet dans [`backend/README.md`](backend/README.md) :
```bash
cd backend
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### 3. Contrôle d'Étanchéité Anti-Fuite
Pour vérifier l'étanchéité stricte d'un nouveau jeu de données contre le Test Sacré :
```bash
python3 scripts/check_test_leakage.py
```
