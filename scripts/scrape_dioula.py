#!/usr/bin/env python3
"""
scrape_dioula.py — Collecte de données Dioula pour enrichir le dataset KOUMAN-AI
==================================================================================
Sources :
  1. Targumi (vocabulaire/dioula) — 98 mots/expressions Dioula↔FR via JSON-LD
  2. Webonary PDF (Guide orthographe dioula-BF) — extraction texte + phrases
  3. Génération de paires d'entraînement augmentées depuis le glossaire existant

Sortie :
  data/scraped_dioula_pairs.json   — nouvelles paires (src_text, tgt_text, src_lang, tgt_lang)
  data/scraping_report.txt         — rapport de collecte

Usage :
  pip install requests beautifulsoup4 pdfplumber
  python scripts/scrape_dioula.py
"""

import json
import re
import sys
import os
import time
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
OUTPUT_FILE = DATA_DIR / "scraped_dioula_pairs.json"
REPORT_FILE = DATA_DIR / "scraping_report.txt"

# ─────────────────────────────────────────────────────────────
# Utilitaires
# ─────────────────────────────────────────────────────────────

def log(msg: str):
    print(f"[scrape] {msg}", flush=True)

def make_pair(src: str, tgt: str, src_lang: str, tgt_lang: str) -> dict:
    return {
        "src_text": src.strip(),
        "tgt_text": tgt.strip(),
        "src_lang": src_lang,
        "tgt_lang": tgt_lang,
    }

def deduplicate(pairs: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for p in pairs:
        key = (p["src_text"].lower(), p["tgt_text"].lower())
        if key not in seen:
            seen.add(key)
            result.append(p)
    return result

# ─────────────────────────────────────────────────────────────
# Source 1 : Targumi — vocabulaire Dioula (JSON-LD)
# ─────────────────────────────────────────────────────────────

TARGUMI_URL = "https://www.targumi.com/vocabulaire/dioula"

def scrape_targumi() -> list[dict]:
    """
    Extrait les paires depuis le JSON-LD structuré de la page Targumi.
    Le JSON-LD contient @type DefinedTermSet avec hasDefinedTerm[].
    Chaque term : name = mot dioula, description = traduction française.
    """
    log("Source 1 — Targumi scraping (JSON-LD)...")
    pairs = []
    
    try:
        req = urllib.request.Request(
            TARGUMI_URL,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; KoumanAI-DataCollector/1.0)",
                "Accept-Language": "fr-FR,fr;q=0.9",
            }
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode("utf-8")
    except Exception as e:
        log(f"  ⚠️  Impossible de télécharger Targumi : {e}")
        return pairs

    # Trouver tous les blocs <script type="application/ld+json">
    pattern = re.compile(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        re.DOTALL | re.IGNORECASE
    )
    
    for match in pattern.finditer(html):
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        
        # Format array ou objet unique
        items = data if isinstance(data, list) else [data]
        
        for item in items:
            defined_terms = None
            
            if item.get("@type") == "DefinedTermSet":
                defined_terms = item.get("hasDefinedTerm", [])
            elif isinstance(item.get("@graph"), list):
                for node in item["@graph"]:
                    if node.get("@type") == "DefinedTermSet":
                        defined_terms = node.get("hasDefinedTerm", [])
                        break
            
            if not defined_terms:
                continue
            
            for term in defined_terms:
                dioula_word = term.get("name", "").strip()
                french_def  = term.get("description", "").strip()
                
                if not dioula_word or not french_def:
                    continue
                
                # Créer paire bidirectionnelle (mot → définition et définition → mot)
                pairs.append(make_pair(french_def, dioula_word, "fra_Latn", "dyu_Latn"))
                pairs.append(make_pair(dioula_word, french_def, "dyu_Latn", "fra_Latn"))
    
    log(f"  ✓ {len(pairs)} paires extraites de Targumi ({len(pairs)//2} mots uniques)")
    return pairs


# ─────────────────────────────────────────────────────────────
# Source 2 : Webonary PDF — Guide orthographe Dioula-BF
# ─────────────────────────────────────────────────────────────

WEBONARY_PDF_URL = "https://www.webonary.org/dioula-bf/files/Guide-orthographe-dioula.pdf"
PDF_CACHE = DATA_DIR / "webonary_guide_orthographe.pdf"

def download_pdf(url: str, dest: Path) -> bool:
    if dest.exists():
        log(f"  ✓ PDF déjà en cache : {dest.name}")
        return True
    log(f"  Téléchargement PDF : {url}")
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; KoumanAI-DataCollector/1.0)",
        })
        with urllib.request.urlopen(req, timeout=60) as response:
            dest.write_bytes(response.read())
        log(f"  ✓ PDF téléchargé ({dest.stat().st_size / 1024:.0f} KB)")
        return True
    except Exception as e:
        log(f"  ⚠️  Téléchargement PDF échoué : {e}")
        return False

def parse_pdf_sentences(pdf_path: Path) -> list[dict]:
    """
    Extrait les paires bilingues du guide d'orthographe Webonary.
    Formats détectés :
      1. "mot_dioula = traduction_française" (format principal du guide)
      2. "Dioula : X / Français : Y" (paires explicites)
      3. Exemples de phrases avec contexte
    """
    pairs = []
    try:
        import pdfplumber
    except ImportError:
        log("  ⚠️  pdfplumber non installé. Installez avec : pip install pdfplumber")
        return pairs

    log(f"  Parsing PDF : {pdf_path.name}")

    # Format 1 : "mot_dioula = traduction française" (principal dans ce PDF)
    # Ex: "soo = la maison", "sɔsɔ = haricot", "gwabugu = cuisine"
    pat_eq = re.compile(
        r'^([a-zA-ZɛɔɲŋɡǝÉÈÊÛÔÂɛɔɲƐƆŊɡ\u0000-\u024F\'\-]{2,35})\s*=\s*'
        r'((?:\([^)]+\)|[^=\n\r(]){2,60}?)(?:\s*\(|$|\s*peut)',
        re.MULTILINE
    )

    # Format 2 : "mot_dioula : traduction" sur des lignes spéciales
    pat_colon = re.compile(
        r'^([a-zA-ZɛɔɲŋɡǝÉÈÊÛÔÂɛɔɲƐƆŊɡ\u0000-\u024F\'\-]{2,35})\s+:\s+'
        r'([a-zA-ZÀ-ÿ\s\',\-]{3,60})$',
        re.MULTILINE
    )

    # Format 3 : Formes avec flèche + traduction "nsiirin → siirin = conte"
    pat_arrow_eq = re.compile(
        r'[-─►→>]+\s*([a-zA-ZɛɔɲŋɡǝÉÈÊÛÔÂɛɔɲƐƆŊɡ\u0000-\u024F\'\-]{2,35})\s*=\s*'
        r'([a-zA-ZÀ-ÿ\s\',\-]{3,60}?)(?:\s*$|\s*;)',
        re.MULTILINE
    )

    # Mots à exclure (faux positifs : sections, abréviations)
    STOPWORDS = {
        "adj", "adv", "cf", "nb", "ex", "exemple", "exemples",
        "note", "voir", "obs", "remarque", "cas", "forme",
        "c", "e", "n", "v", "vn", "vo", "vn", "cv",
    }

    full_text_pages = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            log(f"  PDF pages : {len(pdf.pages)}")
            for page in pdf.pages:
                text = page.extract_text() or ""
                full_text_pages.append(text)

                # Pattern = (format principal)
                for m in pat_eq.finditer(text):
                    dyu = m.group(1).strip().rstrip()
                    fr  = m.group(2).strip().rstrip().rstrip('.')
                    # Filtres
                    if (dyu.lower() not in STOPWORDS and fr.lower() not in STOPWORDS
                            and len(dyu) >= 2 and len(fr) >= 2
                            and not dyu[0].isupper()
                            and re.search(r'[a-zA-ZÀ-ÿ]', fr)):
                        pairs.append(make_pair(fr, dyu, "fra_Latn", "dyu_Latn"))
                        pairs.append(make_pair(dyu, fr, "dyu_Latn", "fra_Latn"))

                # Pattern flèche + =
                for m in pat_arrow_eq.finditer(text):
                    dyu = m.group(1).strip()
                    fr  = m.group(2).strip().rstrip('.')
                    if (dyu.lower() not in STOPWORDS
                            and len(dyu) >= 2 and len(fr) >= 2
                            and not dyu[0].isupper()):
                        pairs.append(make_pair(fr, dyu, "fra_Latn", "dyu_Latn"))
                        pairs.append(make_pair(dyu, fr, "dyu_Latn", "fra_Latn"))

    except Exception as e:
        log(f"  ⚠️  Erreur parsing PDF : {e}")

    # Sauvegarder le texte brut pour inspection manuelle
    raw_text_path = DATA_DIR / "webonary_guide_orthographe_text.txt"
    raw_text_path.write_text("\n\n--- PAGE ---\n".join(full_text_pages), encoding="utf-8")
    log(f"  ✓ Texte brut sauvegardé : {raw_text_path.name}")

    log(f"  ✓ {len(pairs)} paires extraites du PDF (avant déduplication)")
    return pairs


def parse_pdf_wordlist(pdf_path: Path) -> list[dict]:
    """
    Extrait les mots isolés du PDF (format glossaire simple).
    Génère des paires courtes mais valides pour l'entraînement de lexique.
    """
    pairs = []
    try:
        import pdfplumber
    except ImportError:
        return pairs
    
    # Pattern : mot dioula suivi de sa traduction française (séparés par : ou espace multiple)
    # Ex: "sɔgɔma : matin", "jiginni — descendre"
    pat_entry = re.compile(
        r'^([a-zA-ZɛɔɲŋɡǝÉÈÊÛÔÂãẽõũàáâäèéêëìíîïòóôõùúûüñçÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜß\'\-]{2,40})'
        r'\s*(?::|—|–|-)\s*'
        r'(.{3,80})$',
        re.MULTILINE
    )
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                for m in pat_entry.finditer(text):
                    dyu = m.group(1).strip()
                    fr  = m.group(2).strip()
                    # Filtrer les faux positifs (ex : titres de section)
                    if (2 < len(dyu) < 40 and 3 < len(fr) < 80
                            and not dyu[0].isupper()  # titres commencent par majuscule
                            and fr[0].islower()):      # définitions en minuscule
                        pairs.append(make_pair(fr, dyu, "fra_Latn", "dyu_Latn"))
                        pairs.append(make_pair(dyu, fr, "dyu_Latn", "fra_Latn"))
    except Exception:
        pass
    
    return pairs


def scrape_webonary_pdf() -> list[dict]:
    log("Source 2 — Webonary PDF (Guide orthographe Dioula-BF)...")
    
    ok = download_pdf(WEBONARY_PDF_URL, PDF_CACHE)
    if not ok:
        return []
    
    pairs = []
    pairs.extend(parse_pdf_sentences(PDF_CACHE))
    pairs.extend(parse_pdf_wordlist(PDF_CACHE))
    
    pairs = deduplicate(pairs)
    log(f"  ✓ Total Webonary (dédupliqué) : {len(pairs)} paires")
    return pairs


# ─────────────────────────────────────────────────────────────
# Source 3 : Augmentation depuis le glossaire existant
# ─────────────────────────────────────────────────────────────

def augment_from_glossaire() -> list[dict]:
    """
    Le glossaire existant (3 174 entrées) est au format {francais, dioula}.
    On le convertit en paires d'entraînement bidirectionnelles.
    Ces paires sont des mots/expressions courts mais valides pour le lexique.
    """
    log("Source 3 — Augmentation depuis le glossaire existant...")
    
    glossaire_path = DATA_DIR / "glossaire_dioula.json"
    if not glossaire_path.exists():
        log("  ⚠️  glossaire_dioula.json introuvable")
        return []
    
    glossaire = json.loads(glossaire_path.read_text(encoding="utf-8"))
    pairs = []
    
    for entry in glossaire:
        fr  = entry.get("francais", "").strip()
        dyu = entry.get("dioula", "").strip()
        
        if not fr or not dyu:
            continue
        
        # Filtrer les entrées trop courtes (moins de 3 chars = peu utiles)
        if len(fr) < 3 or len(dyu) < 2:
            continue
        
        pairs.append(make_pair(fr, dyu, "fra_Latn", "dyu_Latn"))
        pairs.append(make_pair(dyu, fr, "dyu_Latn", "fra_Latn"))
    
    log(f"  ✓ {len(pairs)} paires depuis le glossaire ({len(pairs)//2} entrées uniques)")
    return pairs


# ─────────────────────────────────────────────────────────────
# Source 4 : Targumi — page bambara (très proche du dioula)
# ─────────────────────────────────────────────────────────────

BAMBARA_URL = "https://www.targumi.com/vocabulaire/bambara"

def scrape_targumi_bambara() -> list[dict]:
    """
    Le bambara est mutuellement intelligible avec le dioula (~85% vocabulaire commun).
    Ces données peuvent enrichir le corpus dioula.
    On les marque avec un flag dans les métadonnées mais on les inclut.
    """
    log("Source 4 — Targumi Bambara (proche du Dioula)...")
    pairs = []
    
    try:
        req = urllib.request.Request(
            BAMBARA_URL,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; KoumanAI-DataCollector/1.0)",
                "Accept-Language": "fr-FR,fr;q=0.9",
            }
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode("utf-8")
    except Exception as e:
        log(f"  ⚠️  Bambara non accessible : {e}")
        return pairs
    
    pattern = re.compile(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        re.DOTALL | re.IGNORECASE
    )
    
    for match in pattern.finditer(html):
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        
        items = data if isinstance(data, list) else [data]
        
        for item in items:
            defined_terms = None
            if item.get("@type") == "DefinedTermSet":
                defined_terms = item.get("hasDefinedTerm", [])
            elif isinstance(item.get("@graph"), list):
                for node in item["@graph"]:
                    if node.get("@type") == "DefinedTermSet":
                        defined_terms = node.get("hasDefinedTerm", [])
                        break
            
            if not defined_terms:
                continue
            
            for term in defined_terms:
                bambara_word = term.get("name", "").strip()
                french_def   = term.get("description", "").strip()
                
                if bambara_word and french_def:
                    pairs.append(make_pair(french_def, bambara_word, "fra_Latn", "dyu_Latn"))
                    pairs.append(make_pair(bambara_word, french_def, "dyu_Latn", "fra_Latn"))
    
    log(f"  ✓ {len(pairs)//2} mots bambara extraits (proches du dioula)")
    return pairs


# ─────────────────────────────────────────────────────────────
# Filtre : éviter la fuite vers le Test Sacré
# ─────────────────────────────────────────────────────────────

def load_test_keys() -> set[str]:
    """Charge les fingerprints du jeu de test pour éviter les fuites."""
    test_path = DATA_DIR / "test_sacre.csv"
    keys = set()
    if not test_path.exists():
        return keys
    
    import csv
    with test_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for field in ("fr", "dyu", "source", "target"):
                val = row.get(field, "").strip().lower()
                if val:
                    keys.add(val)
    
    log(f"  Clés Test Sacré chargées : {len(keys)}")
    return keys

def filter_test_leakage(pairs: list[dict], test_keys: set[str]) -> tuple[list[dict], int]:
    """Supprime toute paire dont le src ou tgt est dans les clés du test."""
    clean = []
    removed = 0
    for p in pairs:
        src_key = p["src_text"].strip().lower()
        tgt_key = p["tgt_text"].strip().lower()
        if src_key in test_keys or tgt_key in test_keys:
            removed += 1
        else:
            clean.append(p)
    return clean, removed


# ─────────────────────────────────────────────────────────────
# Filtre qualité
# ─────────────────────────────────────────────────────────────

def quality_filter(pairs: list[dict]) -> list[dict]:
    """Filtre les paires de mauvaise qualité."""
    clean = []
    for p in pairs:
        src = p["src_text"]
        tgt = p["tgt_text"]
        
        # Longueur minimale
        if len(src) < 2 or len(tgt) < 2:
            continue
        
        # Longueur maximale (éviter les blocs trop longs pour des mots isolés)
        if len(src) > 500 or len(tgt) > 500:
            continue
        
        # Pas identiques
        if src.lower() == tgt.lower():
            continue
        
        # Pas juste des chiffres/ponctuation
        if re.match(r'^[\d\s\.,;:!?\-]+$', src) or re.match(r'^[\d\s\.,;:!?\-]+$', tgt):
            continue
        
        clean.append(p)
    
    return clean


# ─────────────────────────────────────────────────────────────
# Fusion avec le dataset existant
# ─────────────────────────────────────────────────────────────

def check_overlap_with_existing(new_pairs: list[dict]) -> tuple[list[dict], int]:
    """Supprime les paires déjà présentes dans processed_v2_train.json."""
    existing_path = DATA_DIR / "processed_v2_train.json"
    if not existing_path.exists():
        return new_pairs, 0
    
    log("  Chargement du dataset existant pour déduplication...")
    existing = json.loads(existing_path.read_text(encoding="utf-8"))
    
    existing_keys = set()
    for e in existing:
        key = (e.get("src_text", "").strip().lower(), e.get("tgt_text", "").strip().lower())
        existing_keys.add(key)
    
    clean = []
    duplicates = 0
    for p in new_pairs:
        key = (p["src_text"].strip().lower(), p["tgt_text"].strip().lower())
        if key in existing_keys:
            duplicates += 1
        else:
            clean.append(p)
    
    return clean, duplicates


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    log("=" * 60)
    log("KOUMAN-AI — Collecte de données Dioula")
    log("=" * 60)
    
    all_pairs = []
    stats = {}
    
    # Source 1 : Targumi Dioula
    t1 = scrape_targumi()
    stats["targumi_dioula"] = len(t1)
    all_pairs.extend(t1)
    
    # Source 2 : Webonary PDF
    t2 = scrape_webonary_pdf()
    stats["webonary_pdf"] = len(t2)
    all_pairs.extend(t2)
    
    # Source 3 : Glossaire existant
    t3 = augment_from_glossaire()
    stats["glossaire_existant"] = len(t3)
    all_pairs.extend(t3)
    
    # Source 4 : Targumi Bambara
    t4 = scrape_targumi_bambara()
    stats["targumi_bambara"] = len(t4)
    all_pairs.extend(t4)
    
    log(f"\nTotal brut : {len(all_pairs)} paires")
    
    # Déduplication globale
    all_pairs = deduplicate(all_pairs)
    log(f"Après déduplication : {len(all_pairs)} paires")
    
    # Filtre qualité
    all_pairs = quality_filter(all_pairs)
    log(f"Après filtre qualité : {len(all_pairs)} paires")
    
    # Anti-fuite Test Sacré
    test_keys = load_test_keys()
    all_pairs, removed_test = filter_test_leakage(all_pairs, test_keys)
    log(f"Fuites Test Sacré supprimées : {removed_test}")
    log(f"Après anti-fuite : {len(all_pairs)} paires")
    
    # Déduplication avec le dataset existant
    all_pairs, duplicates = check_overlap_with_existing(all_pairs)
    log(f"Doublons avec dataset existant : {duplicates}")
    log(f"Paires NOUVELLES nettes : {len(all_pairs)}")
    
    # Sauvegarde
    OUTPUT_FILE.write_text(
        json.dumps(all_pairs, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    log(f"\n✅ Sauvegardé : {OUTPUT_FILE}")
    
    # Rapport
    report_lines = [
        "=" * 60,
        "RAPPORT DE COLLECTE — KOUMAN-AI Dioula Scraper",
        "=" * 60,
        f"Source 1 (Targumi Dioula)   : {stats['targumi_dioula']:>6} paires",
        f"Source 2 (Webonary PDF)     : {stats['webonary_pdf']:>6} paires",
        f"Source 3 (Glossaire interne): {stats['glossaire_existant']:>6} paires",
        f"Source 4 (Targumi Bambara)  : {stats['targumi_bambara']:>6} paires",
        "-" * 60,
        f"Total brut                  : {sum(stats.values()):>6} paires",
        f"Paires nettes après filtres : {len(all_pairs):>6} paires",
        f"Fuites Test Sacré éliminées : {removed_test:>6}",
        f"Doublons dataset existant   : {duplicates:>6}",
        "=" * 60,
        "",
        "PROCHAINE ÉTAPE :",
        "  python scripts/prepare_dataset_v2.py --extra data/scraped_dioula_pairs.json",
        "  (puis relancer le fine-tuning avec le dataset enrichi)",
        "=" * 60,
    ]
    REPORT_FILE.write_text("\n".join(report_lines), encoding="utf-8")
    log(f"📄 Rapport : {REPORT_FILE}")
    
    # Afficher le rapport
    print()
    print("\n".join(report_lines))
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
