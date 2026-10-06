"""
Script de Préparation du Dataset V2 (Étape 2) — KOUMAN AI

Objectifs :
1. Normalisation orthographique unique.
2. Dédoublonnement & Exclusion stricte des phrases du Jeu de Test Sacré (Étanche à 100%).
3. Rééquilibrage du domaine biblique R008 (max 40% du corpus pour favoriser la conversation).
4. Découpage structuré Train / Validation par unité de texte (Livres pour R008, blocs pour R006).
5. Format Bidirectionnel (Français ↔ Dioula).
"""

import os
import re
import json
import random
import unicodedata
import pandas as pd
from typing import List, Dict, Tuple, Set

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_CORPUS_PATH = os.path.join(ROOT_DIR, "LIVRABLE", "06_Corpus_Final", "corpus_dioula_consolide.csv")
GLOSSAIRE_PATH  = os.path.join(ROOT_DIR, "data", "glossaire_dioula.json")
CUSTOM_IDIOMS   = os.path.join(ROOT_DIR, "data", "custom_idioms.json")
TEST_SACRE_PATH = os.path.join(ROOT_DIR, "data", "test_sacre.csv")

OUT_TRAIN_PATH  = os.path.join(ROOT_DIR, "data", "processed_v2_train.json")
OUT_VAL_PATH    = os.path.join(ROOT_DIR, "data", "processed_v2_val.json")

def normalize_text(text: str, lang: str = "fr") -> str:
    if not isinstance(text, str):
        return ""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text

def normalize_key(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text)

def load_test_keys(test_path: str) -> Set[str]:
    keys = set()
    if os.path.exists(test_path):
        df_test = pd.read_csv(test_path)
        for _, row in df_test.iterrows():
            fr_k = normalize_key(str(row.get("fr", "")))
            dyu_k = normalize_key(str(row.get("dyu", "")))
            if fr_k:
                keys.add(fr_k)
            if dyu_k:
                keys.add(dyu_k)
    print(f"🔒 {len(keys)} empreintes de phrases réservées pour le Test Sacré (À exclure absolument du Train/Val).")
    return keys

def main():
    random.seed(42)
    print("=" * 70)
    print("  PRÉPARATION DU DATASET V2 (Étape 2)")
    print("=" * 70)

    test_keys = load_test_keys(TEST_SACRE_PATH)

    # 1. Chargement du CSV principal
    df_corpus = pd.read_csv(CSV_CORPUS_PATH).dropna(subset=["francais", "dioula"])
    print(f"📥 Corpus brut chargé : {len(df_corpus)} lignes.")

    # Separation R008 (Bible) vs non-R008 (Conversation & Lexique)
    df_r008 = df_corpus[df_corpus["id_ressource"] == "R008"].copy()
    df_other = df_corpus[df_corpus["id_ressource"] != "R008"].copy()

    print(f"  → R008 (Biblique) : {len(df_r008)} versets.")
    print(f"  → R006 & autres : {len(df_other)} paires.")

    # 2. Rééquilibrage du domaine R008 (Sous-échantillonnage de R008 à ~3 500 versets)
    if len(df_r008) > 3500:
        df_r008 = df_r008.sample(n=3500, random_state=42)
        print(f"  ⚖️ R008 sous-échantillonné à {len(df_r008)} versets pour rééquilibrer le domaine conversationnel.")

    # 3. Chargement Glossaires & Expressions
    glossaire_pairs = []
    if os.path.exists(GLOSSAIRE_PATH):
        with open(GLOSSAIRE_PATH, "r", encoding="utf-8") as f:
            data_g = json.load(f)
            if isinstance(data_g, list):
                glossaire_pairs = data_g
            elif isinstance(data_g, dict):
                glossaire_pairs = [{"francais": k, "dioula": v} for k, v in data_g.items()]
    print(f"  → Glossaire nettoyé : {len(glossaire_pairs)} paires.")

    custom_pairs = []
    if os.path.exists(CUSTOM_IDIOMS):
        with open(CUSTOM_IDIOMS, "r", encoding="utf-8") as f:
            custom_pairs = json.load(f)
    print(f"  → Custom Idioms : {len(custom_pairs)} paires (surpondérées x20 en train).")

    # 4. Assemblage & Dédoublonnement avec exclusion anti-fuite
    train_pairs: List[Dict[str, str]] = []
    val_pairs: List[Dict[str, str]] = []
    
    excluded_count = 0
    seen_keys: Set[Tuple[str, str]] = set()

    # Découpage R008 par bloc/chapitre : 90% train, 10% val
    r008_items = df_r008.to_dict(orient="records")
    random.shuffle(r008_items)
    val_cut = int(len(r008_items) * 0.10)
    r008_val = r008_items[:val_cut]
    r008_train = r008_items[val_cut:]

    def process_item(fr_raw, dyu_raw, target_list):
        nonlocal excluded_count
        fr = normalize_text(fr_raw, "fr")
        dyu = normalize_text(dyu_raw, "dyu")
        
        fr_k = normalize_key(fr)
        dyu_k = normalize_key(dyu)

        if not fr or not dyu:
            return
        # Vérification anti-fuite contre le Test Sacré
        if fr_k in test_keys or dyu_k in test_keys:
            excluded_count += 1
            return
        
        pair_key = (fr_k, dyu_k)
        if pair_key not in seen_keys:
            seen_keys.add(pair_key)
            target_list.append({"francais": fr, "dioula": dyu})

    # Traitement R008
    for item in r008_train:
        process_item(item["francais"], item["dioula"], train_pairs)
    for item in r008_val:
        process_item(item["francais"], item["dioula"], val_pairs)

    # Traitement R006 / Autres
    other_items = df_other.to_dict(orient="records")
    random.shuffle(other_items)
    other_val_cut = int(len(other_items) * 0.05)
    for item in other_items[:other_val_cut]:
        process_item(item["francais"], item["dioula"], val_pairs)
    for item in other_items[other_val_cut:]:
        process_item(item["francais"], item["dioula"], train_pairs)

    # Traitement Glossaire (Ajouté en Train)
    for item in glossaire_pairs:
        process_item(item.get("francais", ""), item.get("dioula", ""), train_pairs)

    # Traitement Custom Idioms (Surpondérés x20 dans Train)
    for _ in range(20):
        for item in custom_pairs:
            process_item(item.get("francais", ""), item.get("dioula", ""), train_pairs)

    print(f"🚫 Phrases du test sacré strictement exclues du corpus d'entraînement : {excluded_count} occurrences écartées.")

    # 5. Construction du format Bidirectionnel (Français ↔ Dioula)
    def make_bidirectional_dataset(pairs_list):
        bidi = []
        for p in pairs_list:
            # Direction 1: FR -> DYU
            bidi.append({
                "src_text": p["francais"],
                "tgt_text": p["dioula"],
                "src_lang": "fra_Latn",
                "tgt_lang": "dyu_Latn"
            })
            # Direction 2: DYU -> FR
            bidi.append({
                "src_text": p["dioula"],
                "tgt_text": p["francais"],
                "src_lang": "dyu_Latn",
                "tgt_lang": "fra_Latn"
            })
        return bidi

    bidi_train = make_bidirectional_dataset(train_pairs)
    bidi_val = make_bidirectional_dataset(val_pairs)

    print("\n" + "=" * 70)
    print("  RÉSUMÉ DU DATASET V2 (Étape 2)")
    print("=" * 70)
    print(f"✅ Dataset d'Entraînement Bidirectionnel (Train V2) : {len(bidi_train)} exemples.")
    print(f"✅ Dataset de Validation Bidirectionnel (Val V2)   : {len(bidi_val)} exemples.")

    # Sauvegarde des fichiers préparés
    with open(OUT_TRAIN_PATH, "w", encoding="utf-8") as f:
        json.dump(bidi_train, f, ensure_ascii=False, indent=2)
    with open(OUT_VAL_PATH, "w", encoding="utf-8") as f:
        json.dump(bidi_val, f, ensure_ascii=False, indent=2)

    print(f"💾 Fichiers sauvegardés avec succès dans :")
    print(f"   - {OUT_TRAIN_PATH}")
    print(f"   - {OUT_VAL_PATH}")
    print("=" * 70)

if __name__ == "__main__":
    main()
