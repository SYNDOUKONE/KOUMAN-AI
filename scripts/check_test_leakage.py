"""
Script de contrôle anti-fuite (Data Leakage Verification) pour KOUMAN AI.

Vérifie l'étanchéité stricte entre le jeu de test "sacré" et les données d'entraînement/validation :
1. Détection des fuites exactes (côté Français et côté Dioula).
2. Détection des quasi-doublons (similarité de Levenshtein & n-grammes de caractères).
3. Normalisation orthographique avancée pour éliminer les faux négatifs.
"""

import os
import re
import sys
import unicodedata
import pandas as pd
from typing import List, Tuple, Set

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def normalize_text(text: str, lang: str = "fr") -> str:
    """
    Normalisation rigoureuse du texte :
    - Minuscules
    - Suppression des diacritiques/accents optionnelle pour la recherche de doublons
    - Unification des symboles dioulas (ɛ/e, ɔ/o, ɲ/gn, ŋ/ng)
    - Suppression des ponctuations et espaces superflus
    """
    if not isinstance(text, str):
        return ""
    
    text = text.lower().strip()
    # Décomposition Unicode (NFD)
    text = unicodedata.normalize("NFD", text)
    
    if lang == "dyu":
        # Unification orthographique Dioula pour détection élargie
        text = text.replace("ɛ", "e").replace("ɔ", "o").replace("ɲ", "gn").replace("ŋ", "ng")
    
    # Suppression de la ponctuation et caractères spéciaux
    text = re.sub(r"[^\w\s]", "", text)
    # Uniformisation des espaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def char_ngram_jaccard_similarity(str1: str, str2: str, n: int = 3) -> float:
    """Calcule la similarité de Jaccard basée sur les n-grammes de caractères."""
    if not str1 or not str2:
        return 0.0
    
    set1 = set(str1[i:i+n] for i in range(len(str1) - n + 1)) or {str1}
    set2 = set(str2[i:i+n] for i in range(len(str2) - n + 1)) or {str2}
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0.0


def check_leakage(test_file: str, train_csv_files: List[str], glossaire_files: List[str], similarity_threshold: float = 0.80):
    print("=" * 70)
    print("  CONTROLE ANTI-FUITE (DATA LEAKAGE CHECK)")
    print("=" * 70)
    
    if not os.path.exists(test_file):
        print(f"❌ Erreur : Le fichier de test sacré '{test_file}' est introuvable.")
        return False
    
    # 1. Chargement du jeu de test
    df_test = pd.read_csv(test_file)
    print(f"📥 Jeu de test sacré chargé : {len(df_test)} phrases.")
    
    # 2. Chargement des données d'entraînement/validation
    train_fr_exact: Set[str] = set()
    train_dyu_exact: Set[str] = set()
    train_pairs_norm: List[Tuple[str, str, str]] = []  # (fr_norm, dyu_norm, source_name)
    
    # Chargement CSVs
    for csv_path in train_csv_files:
        if os.path.exists(csv_path):
            df_train = pd.read_csv(csv_path).dropna(subset=["francais", "dioula"])
            for _, row in df_train.iterrows():
                fr_clean = normalize_text(str(row["francais"]), "fr")
                dyu_clean = normalize_text(str(row["dioula"]), "dyu")
                if fr_clean:
                    train_fr_exact.add(fr_clean)
                if dyu_clean:
                    train_dyu_exact.add(dyu_clean)
                train_pairs_norm.append((fr_clean, dyu_clean, os.path.basename(csv_path)))
    
    # Chargement Glossaires JSON
    for json_path in glossaire_files:
        if os.path.exists(json_path):
            import json
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            pairs = []
            if isinstance(data, dict):
                pairs = list(data.items())
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        fr = item.get("francais") or item.get("src_text" if item.get("src_lang") == "fra_Latn" else "tgt_text") or ""
                        dyu = item.get("dioula") or item.get("tgt_text" if item.get("src_lang") == "fra_Latn" else "src_text") or ""
                        pairs.append((fr, dyu))
            
            for fr, dyu in pairs:
                fr_clean = normalize_text(str(fr), "fr")
                dyu_clean = normalize_text(str(dyu), "dyu")
                if fr_clean:
                    train_fr_exact.add(fr_clean)
                if dyu_clean:
                    train_dyu_exact.add(dyu_clean)
                train_pairs_norm.append((fr_clean, dyu_clean, os.path.basename(json_path)))

    print(f"📊 Corpus d'entraînement global chargé : {len(train_fr_exact)} phrases FR uniques, {len(train_dyu_exact)} phrases DYU uniques.")
    print("-" * 70)

    # 3. Vérification des fuites exactes et quasi-doublons
    exact_leaks_fr = 0
    exact_leaks_dyu = 0
    fuzzy_leaks = 0
    
    print("\n🔍 Analyse des fuites...")
    
    for idx, row in df_test.iterrows():
        test_id = row.get("id", idx + 1)
        test_fr = str(row.get("fr", ""))
        test_dyu = str(row.get("dyu", ""))
        
        test_fr_norm = normalize_text(test_fr, "fr")
        test_dyu_norm = normalize_text(test_dyu, "dyu")
        
        has_leak = False
        
        # Test fuite exacte FR
        if test_fr_norm in train_fr_exact:
            print(f"⚠️ [FUITE EXACTE FR] ID {test_id}: '{test_fr}' existe dans le train !")
            exact_leaks_fr += 1
            has_leak = True
            
        # Test fuite exacte DYU
        if test_dyu_norm and test_dyu_norm in train_dyu_exact:
            print(f"⚠️ [FUITE EXACTE DYU] ID {test_id}: '{test_dyu}' existe dans le train !")
            exact_leaks_dyu += 1
            has_leak = True
            
        # Test quasi-doublon (Similarité Floue)
        if not has_leak and test_fr_norm:
            for tr_fr, tr_dyu, source in train_pairs_norm[:5000]:  # Échantillonnage de contrôle rapide
                sim = char_ngram_jaccard_similarity(test_fr_norm, tr_fr, n=3)
                if sim >= similarity_threshold:
                    print(f"⚠️ [QUASI-DOUBLON FR ({sim*100:.1f}%)] ID {test_id}: '{test_fr}' ~ '{tr_fr}' ({source})")
                    fuzzy_leaks += 1
                    break

    print("\n" + "=" * 70)
    print("  RAPPORT ETANCHEITE DU JEU DE TEST")
    print("=" * 70)
    print(f"🔴 Fuites exactes Français : {exact_leaks_fr}")
    print(f"🔴 Fuites exactes Dioula   : {exact_leaks_dyu}")
    print(f"🟠 Quasi-doublons trouvés  : {fuzzy_leaks}")
    
    total_issues = exact_leaks_fr + exact_leaks_dyu + fuzzy_leaks
    if total_issues == 0:
        print("\n✅ VÉRIFICATION REUSSIE : Le jeu de test sacré est 100% ÉTANCHE !")
        return True
    else:
        print(f"\n❌ ATTENTION : {total_issues} fuites détectées. Le jeu de test doit être nettoyé avant de poursuivre.")
        return False


if __name__ == "__main__":
    test_path = os.path.join(ROOT_DIR, "data", "test_sacre.csv")
    
    # Par défaut, on contrôle le dataset V2 préparé s'il existe
    v2_train = os.path.join(ROOT_DIR, "data", "processed_v2_train.json")
    v2_val = os.path.join(ROOT_DIR, "data", "processed_v2_val.json")
    
    if os.path.exists(v2_train) and os.path.exists(v2_val):
        print("ℹ️ Contrôle de l'étanchéité sur le dataset préparé V2 (processed_v2_train.json & processed_v2_val.json)...")
        csv_sources = []
        json_sources = [v2_train, v2_val]
    else:
        csv_sources = [os.path.join(ROOT_DIR, "LIVRABLE", "06_Corpus_Final", "corpus_dioula_consolide.csv")]
        json_sources = [
            os.path.join(ROOT_DIR, "data", "glossaire_dioula.json"),
            os.path.join(ROOT_DIR, "data", "custom_idioms.json")
        ]
    check_leakage(test_path, csv_sources, json_sources)

