#!/usr/bin/env python3
"""
integrate_scraped_data.py — Intégration des données scrapées dans le dataset V2
=================================================================================
Fusionne `data/scraped_dioula_pairs.json` dans `data/processed_v2_train.json`
en garantissant :
  ✅ Aucune fuite vers le Test Sacré
  ✅ Aucun doublon avec les données existantes
  ✅ Sauvegarde de l'original en backup

Usage :
  python scripts/integrate_scraped_data.py [--dry-run]
"""

import json
import sys
import shutil
import unicodedata
import re
import csv
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR  = ROOT_DIR / "data"

SCRAPED_PATH    = DATA_DIR / "scraped_dioula_pairs.json"
TRAIN_PATH      = DATA_DIR / "processed_v2_train.json"
TEST_SACRE_PATH = DATA_DIR / "test_sacre.csv"

DRY_RUN = "--dry-run" in sys.argv

def log(msg):
    print(f"[integrate] {msg}", flush=True)

def normalize_key(text: str) -> str:
    t = text.lower().strip()
    t = unicodedata.normalize("NFD", t)
    t = re.sub(r"[^\w\s]", "", t)
    return re.sub(r"\s+", " ", t)

def load_test_keys() -> set:
    keys = set()
    if not TEST_SACRE_PATH.exists():
        return keys
    with TEST_SACRE_PATH.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for field in ("fr", "dyu", "source", "target"):
                val = row.get(field, "").strip()
                if val:
                    keys.add(normalize_key(val))
    log(f"Test Sacré — {len(keys)} clés chargées")
    return keys

def main():
    log("=" * 55)
    log("INTÉGRATION DES DONNÉES SCRAPÉES — KOUMAN-AI")
    if DRY_RUN:
        log("⚠️  MODE DRY-RUN (aucune écriture)")
    log("=" * 55)

    # Vérifications
    if not SCRAPED_PATH.exists():
        log(f"❌ Fichier introuvable : {SCRAPED_PATH}")
        log("   Lancez d'abord : python scripts/scrape_dioula.py")
        return 1

    if not TRAIN_PATH.exists():
        log(f"❌ Dataset d'entraînement introuvable : {TRAIN_PATH}")
        return 1

    # Chargement
    log(f"Chargement des données scrapées : {SCRAPED_PATH.name}")
    new_pairs = json.loads(SCRAPED_PATH.read_text(encoding="utf-8"))
    log(f"  → {len(new_pairs)} paires scrapées")

    log(f"Chargement du dataset existant : {TRAIN_PATH.name}")
    existing = json.loads(TRAIN_PATH.read_text(encoding="utf-8"))
    log(f"  → {len(existing)} paires existantes")

    # Index des clés existantes
    existing_keys = set()
    for e in existing:
        k = (normalize_key(e.get("src_text", "")),
             normalize_key(e.get("tgt_text", "")))
        existing_keys.add(k)

    # Clés Test Sacré
    test_keys = load_test_keys()

    # Filtrage des nouvelles paires
    accepted = []
    rejected_test = 0
    rejected_dup  = 0

    for p in new_pairs:
        src_k = normalize_key(p.get("src_text", ""))
        tgt_k = normalize_key(p.get("tgt_text", ""))

        if src_k in test_keys or tgt_k in test_keys:
            rejected_test += 1
            continue

        key = (src_k, tgt_k)
        if key in existing_keys:
            rejected_dup += 1
            continue

        existing_keys.add(key)
        accepted.append(p)

    log(f"\nBilan du filtrage :")
    log(f"  Nouvelles paires acceptées : {len(accepted)}")
    log(f"  Rejetées (fuite test)      : {rejected_test}")
    log(f"  Rejetées (doublon)         : {rejected_dup}")

    if not accepted:
        log("\n⚠️  Aucune nouvelle paire à ajouter.")
        return 0

    if DRY_RUN:
        log(f"\n[DRY-RUN] Aurait ajouté {len(accepted)} paires au dataset.")
        log("[DRY-RUN] Aucun fichier modifié.")
        # Afficher un échantillon
        log("\nÉchantillon des paires qui seraient ajoutées :")
        for p in accepted[:10]:
            log(f"  [{p['src_lang']}→{p['tgt_lang']}] {p['src_text'][:50]} → {p['tgt_text'][:50]}")
        return 0

    # Backup du dataset original
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = TRAIN_PATH.with_name(f"processed_v2_train.backup_{timestamp}.json")
    shutil.copy2(TRAIN_PATH, backup_path)
    log(f"\n💾 Backup créé : {backup_path.name}")

    # Fusion et sauvegarde
    merged = existing + accepted
    TRAIN_PATH.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    log(f"\n✅ Dataset mis à jour : {TRAIN_PATH.name}")
    log(f"   Avant : {len(existing)} paires")
    log(f"   Après : {len(merged)} paires (+{len(accepted)})")

    # Rapport final
    print()
    print("=" * 55)
    print("RÉSUMÉ D'INTÉGRATION")
    print("=" * 55)
    print(f"Paires ajoutées          : {len(accepted):>6}")
    print(f"Rejetées (fuite test)    : {rejected_test:>6}")
    print(f"Rejetées (doublons)      : {rejected_dup:>6}")
    print(f"Total dataset train      : {len(merged):>6}")
    print("=" * 55)
    print()
    print("PROCHAINE ÉTAPE : Relancer le fine-tuning")
    print("  python scripts/finetune_nllb.py  (ou sur GPU)")
    print("=" * 55)

    return 0

if __name__ == "__main__":
    sys.exit(main())
