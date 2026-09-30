# 🌍 Kouman AI — Plateforme Multimodale de Traduction & Traitement de la Langue Dioula

Projet de traduction automatique neuronale et de traitement de la parole spécialisé pour la langue **Dioula** (*dyu_Latn*) et le **Français** (*fra_Latn*).

Kouman AI intègre :
1. **NMT (Traduction)** : Modèle **NLLB-200-1.3B** de Meta optimisé par **Fine-Tuning LoRA (PEFT)** (BLEU 46.88).
2. **TTS (Synthèse Vocale)** : Modèle **MMS-TTS Jula** de Meta (`facebook/mms-tts-dyu`) basé sur VITS.
3. **STT (Reconnaissance Vocale)** : Modèle **Whisper Tiny Dioula** (`Dama12/whisper-tiny-dioula`) affiné sur Mozilla Common Voice.
4. **Recherche & Intelligence** : API **Gemini** pour la recherche linguistique et contextuelle.

---

## 📁 Structure du Projet

```text
kouman_AI/
├── 📄 README.md                                    # Documentation générale du projet
├── 📄 requirements.txt                             # Dépendances Python
│
├── 📂 api/                                         # Serveur Backend FastAPI Multimodal
│   ├── 📄 app.py                                   # Endpoints API (/translate, /research, /smart, /tts, /stt)
│   ├── 📄 translation_service.py                   # Service NLLB LoRA (FR ↔ DYU)
│   ├── 📄 audio_service.py                         # Service Audio (STT Whisper & TTS MMS-TTS)
│   └── 📄 research_service.py                      # Service de recherche contextuelle Gemini
│
├── 📂 docs/                                        # Cahier des charges et gestion de projet
│   ├── 📄 Kouma_AI_Cahier_des_charges.docx.pdf
│   ├── 📄 Retroplanning_Projet_Traduction_NLP (1).xlsx
│   └── 📄 Inventaire_Ressources_Baoule_Dioula.xlsx
│
├── 📂 data/                                        # Données lexicales & dictionnaires
│   ├── 📄 petit_dictionnaire.pdf                   # Dictionnaire historique Français-Dioula
│   └── 📄 glossaire_dioula.json                    # Glossaire extrait (3 267 termes & locutions)
│
├── 📂 models/                                      # Modèle fine-tuné & adaptateurs LoRA
│   └── 📂 nllb_lora_dioula/
│       ├── 📂 checkpoint-1006/                     # Checkpoint Époque 1 (BLEU: 45.84)
│       ├── 📂 checkpoint-2012/                     # Checkpoint Époque 2 (BLEU: 46.54)
│       └── 📂 final/                               # Modèle Final Entraîné (BLEU: 46.88, chrF: 61.73)
│           ├── adapter_model.safetensors           # Poids légers LoRA (~19 Mo)
│           ├── adapter_config.json
│           └── tokenizer / vocabulaire
│
├── 📂 scripts/                                     # Scripts Python de traitement, audio & inférence
│   ├── 📄 demo_traduction.py                       # Démonstrateur de traduction rapide en direct
│   ├── 📄 demo_tts.py                              # Démonstrateur Text-To-Speech (NLLB -> MMS-TTS WAV)
│   ├── 📄 demo_stt.py                              # Démonstrateur Speech-To-Text (Whisper Tiny Audio -> Texte)
│   ├── 📄 benchmark_nllb.py                        # Benchmark standard sur corpus CSV
│   ├── 📄 test_and_benchmark.py                    # Benchmark comparatif Base vs Fine-tuné
│   ├── 📄 finetune_nllb.py                         # Script d'entraînement LoRA (PEFT)
│   └── 📄 extract_dictionary.py                    # Script d'extraction OCR/texte du dictionnaire PDF
│
└── 📂 LIVRABLE/                                    # Livrables de données et documentation
    ├── 📂 03_Donnees_Nettoyees/                    # Données brutes nettoyées et filtrées
    ├── 📂 05_Validation_Linguistique/              # Évaluations et retours linguistiques
    ├── 📂 06_Corpus_Final/                         # Corpus consolidé bilingue (13 674 paires)
    │   └── corpus_dioula_consolide.csv
    ├── 📂 07_Documentation/                        # Fiches techniques et guides
    └── 📂 08_Inventaire/                           # Inventaires détaillés
```

---

## 🚀 Installation & Prérequis

Le projet est optimisé pour tourner sous **macOS (Apple Silicon / Metal Performance Shaders - MPS)**, **CUDA** ou **CPU**.

```bash
pip install -r requirements.txt
```

---

## 🌐 Serveur Backend API (FastAPI Multimodal)

Pour lancer le serveur API complet :

```bash
export GEMINI_API_KEY="votre_cle_api_gemini"  # Optionnel
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

### Endpoints disponibles :
* `POST /api/v1/translate` : Traduction brute Français ↔ Dioula via **NLLB-1.3B LoRA**.
* `POST /api/v1/tts` : Synthèse vocale Dioula (FR -> NLLB -> MMS-TTS audio `.wav`).
* `POST /api/v1/stt` : Reconnaissance vocale Dioula (Audio `.wav` -> Whisper Tiny -> Texte Dioula & FR).
* `POST /api/v1/research` : Recherche linguistique, lexicale et explications culturelles via **Gemini API**.
* `POST /api/v1/smart` : Pipeline combiné — Traduction NLLB + Analyse grammaire & culturelle Gemini.

---

## 🛠️ Guide d'Utilisation des Scripts

### 1. Tester la Traduction Texte en Direct
```bash
python3 scripts/demo_traduction.py
```

### 2. Tester la Synthèse Vocale (TTS) : Texte FR -> Dioula Audio (.wav)
```bash
python3 scripts/demo_tts.py "Bonjour, comment allez-vous aujourd'hui ?"
```
*Génère le fichier `sortie_dioula.wav`.*

### 3. Tester la Reconnaissance Vocale (STT) : Audio Dioula -> Texte
```bash
python3 scripts/demo_stt.py chemin/vers/fichier_audio.wav
```

### 4. Lancer un Benchmark NLLB sur un Fichier CSV
```bash
python3 scripts/benchmark_nllb.py --samples 20
```

### 5. Extraire / Mettre à jour le Glossaire depuis le PDF
```bash
python3 scripts/extract_dictionary.py
```

### 6. Relancer le Fine-Tuning LoRA
```bash
python3 scripts/finetune_nllb.py
```

---

## 🧠 Modèles Utilisés

* **NMT (Traduction)** : `facebook/nllb-200-1.3B` + LoRA (PEFT, 4.7M paramètres entraînés).
* **TTS (Synthèse vocale)** : `facebook/mms-tts-dyu` (Meta VITS).
* **STT (Reconnaissance vocale)** : `Dama12/whisper-tiny-dioula` (Whisper Tiny sur Mozilla Common Voice).
* **Intelligence / Recherche** : `gemini-2.5-flash`.

---

## 📊 Résultats du Benchmark Traduction

| Modèle | Score BLEU | Score chrF | Loss de validation |
| :--- | :---: | :---: | :---: |
| **NLLB-200-1.3B (Zero-Shot)** | ~18.5 | ~34.2 | — |
| **NLLB-200-1.3B + LoRA (Époque 1)** | 45.84 | 61.16 | 0.972 |
| **NLLB-200-1.3B + LoRA (Époque 2)** | 46.54 | 61.57 | 0.951 |
| **NLLB-200-1.3B + LoRA + Glossaire (Final)** | **46.88** | **61.73** | **0.945** |
