# 🌍 Kouman AI — Traduction Automatique Français ↔ Dioula (NLLB-200)

Projet de traduction automatique neuronale haute performance spécialisé pour la langue **Dioula** (*dyu_Latn*) à partir du **Français** (*fra_Latn*), basé sur le modèle **NLLB-200-1.3B** de Meta optimisé par **Fine-Tuning LoRA (PEFT)**, enrichi d'un corpus consolidé et d'un glossaire lexical.

---

## 📁 Structure du Projet

```text
kouman_AI/
├── 📄 README.md                                    # Documentation générale du projet
├── 📄 requirements.txt                             # Dépendances Python
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
├── 📂 scripts/                                     # Scripts Python de traitement & inférence
│   ├── 📄 demo_traduction.py                       # Démonstrateur de traduction rapide en direct
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

Le projet est optimisé pour tourner sous **macOS (Apple Silicon / Metal Performance Shaders - MPS)** ou **Linux/CUDA**.

```bash
pip install -r requirements.txt
```

---

## 🛠️ Guide d'Utilisation

### 1. Tester une traduction en direct (Modèle Fine-Tuné)
Pour traduire des phrases françaises en Dioula avec le modèle entraîné :
```bash
python3 scripts/demo_traduction.py
```

### 2. Lancer un Benchmark sur un fichier CSV
Pour évaluer la précision sur un jeu de test avec calcul des scores **BLEU** et **chrF** :
```bash
python3 scripts/benchmark_nllb.py --samples 20
```

### 3. Extraire / Mettre à jour le Glossaire depuis le PDF
Pour extraire de nouveaux termes d'un dictionnaire PDF vers le format JSON :
```bash
python3 scripts/extract_dictionary.py
```

### 4. Relancer le Fine-Tuning LoRA
Pour ré-entraîner les adaptateurs LoRA sur le corpus et le glossaire mis à jour :
```bash
python3 scripts/finetune_nllb.py
```

---

## 🧠 Architecture du Modèle & Méthode

* **Modèle de base** : `facebook/nllb-200-1.3B` (1,3 milliard de paramètres).
* **Fine-Tuning PEFT / LoRA** :
  * **Rang ($r$)** : 16, **Alpha** : 32, **Dropout** : 0.1.
  * **Modules ciblés** : Matrices de projection d'attention (`q_proj`, `v_proj`).
  * **Paramètres entraînés** : ~4,7 Millions (seulement **0.34%** du modèle total), garantissant une sauvegarde ultra-légère (~19 Mo) et une exécution rapide sans saturation mémoire.
* **Jeu de données combiné** :
  * Corpus de phrases consolidé : **13 674 paires**
  * Glossaire lexical extrait du dictionnaire : **3 267 paires**
  * **Total** : **16 941 paires bilingues**.

---

## 📊 Résultats du Benchmark

| Modèle | Score BLEU | Score chrF | Loss de validation |
| :--- | :---: | :---: | :---: |
| **NLLB-200-1.3B (Zero-Shot)** | ~18.5 | ~34.2 | — |
| **NLLB-200-1.3B + LoRA (Époque 1)** | 45.84 | 61.16 | 0.972 |
| **NLLB-200-1.3B + LoRA (Époque 2)** | 46.54 | 61.57 | 0.951 |
| **NLLB-200-1.3B + LoRA + Glossaire (Final)** | **46.88** | **61.73** | **0.945** |

---

## 📝 Exemples de Traductions Obtenues

| Français (Source) | Dioula (Traduction du Modèle) | Note Linguistique |
| :--- | :--- | :--- |
| *Merci beaucoup pour ton aide.* | `I ka dɛmɛ kosɔn, ne bɛ barika da i ye kosɛbɛ.` | *barika da* (remercier), *kosɛbɛ* (beaucoup) |
| *Où vas-tu aujourd'hui ?* | `I bɛ taga min bi?` | Structure interrogative exacte |
| *Je vais au marché pour acheter de la nourriture.* | `Ne bɛ taga lɔgɔfiyɛ la ka dumuni san.` | *lɔgɔfiyɛ* (marché), *dumuni* (nourriture) |
| *Donne-moi un peu d'eau s'il te plaît.* | `Aw ye ji dɔɔnin di ne ma, ne bɛ aw deli.` | *ji dɔɔnin* (un peu d'eau), *deli* (prière) |
| *L'enfant dort dans la chambre.* | `Den bɛ sinɔgɔ la bon kɔnɔ.` | *sinɔgɔ* (dormir), *bon kɔnɔ* (en chambre) |
| *Le travail est difficile mais important.* | `Baara ka gɛlɛn nka a nafa ka bon.` | *baara* (travail), *nafa* (utilité/valeur) |
| *amitié* (Glossaire) | `teriya` | Traduction lexicale exacte |
| *amour* (Glossaire) | `kanu` | Traduction lexicale exacte |
