"""Rejoue une liste de messages sur un serveur lancé et enregistre tout dans un CSV.

    python -m scripts.run_scenarios --key kma_xxx --label beams4
    python -m scripts.run_scenarios --key kma_xxx --label beams2 --repeat 3
    python -m scripts.run_scenarios --key kma_xxx --input docs/scenarios_dyu.csv --chain

Fichier d'entrée (CSV, séparateur « , », lignes commençant par « # » ignorées) :
    id,lang,message,categorie
    S01,dyu,<phrase dioula validée par un locuteur>,salutation

Pour chaque message, le script appelle POST /api/v1/chat?debug=true et écrit une ligne :
textes (message, fr_input, fr_reply, reply), temps par étape, statut, repli éventuel,
plus la configuration du serveur lue dans /health (modèle, révision, num_beams, LLM).
Le même fichier rejoué avec un autre réglage donne deux CSV directement comparables.

Les phrases dioula doivent venir d'un locuteur natif (via Aicha) : jamais inventées.
"""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "docs" / "scenarios_dyu.csv"
DEFAULT_BIDI_INPUT = ROOT / "docs" / "scenarios_bidirectionnels.csv"
DEFAULT_OUTPUT_DIR = ROOT / "docs" / "scenarios_results"

STAGES = ("mt_in", "llm", "mt_out")
COLUMNS = [
    "run_label", "run_at", "id", "categorie", "repetition", "session_id", "lang",
    "status", "error_code", "message", "fr_input", "fr_reply", "reply", "fallback_reason",
    "mt_in_ms", "llm_ms", "mt_out_ms", "server_total_ms", "client_total_ms",
    "translator_model", "translator_revision", "translator_mode", "num_beams",
    "max_new_tokens", "device", "llm", "llm_model", "api_version",
]  # fmt: skip

BIDI_COLUMNS = [
    "run_label", "run_at", "id", "direction", "src_lang", "tgt_lang", "categorie",
    "repetition", "status", "error_code", "message", "translation", "reference_translation",
    "time_ms", "client_total_ms", "translator_model", "translator_revision",
    "translator_mode", "num_beams", "max_new_tokens", "device", "api_version",
]


def load_scenarios(path: Path) -> list[dict]:
    lines = [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    rows = list(csv.DictReader(lines))
    missing = {"id", "lang", "message"} - set(rows[0] if rows else {})
    if not rows or missing:
        raise SystemExit(
            f"{path} : en-tête id,lang,message[,categorie] attendu ({missing or 'vide'})"
        )
    return rows


def server_config(health: dict) -> dict:
    tr = health.get("translator") or {}
    gen = tr.get("generation") or {}
    return {
        "translator_model": tr.get("base_model", tr.get("name")),
        "translator_revision": tr.get("revision"),
        "translator_mode": tr.get("mode"),
        "num_beams": gen.get("num_beams"),
        "max_new_tokens": gen.get("max_new_tokens"),
        "device": tr.get("device"),
        "llm": health.get("llm"),
        "llm_model": health.get("llm_model"),
        "api_version": health.get("version"),
    }


def run(
    client: httpx.Client,
    scenarios: list[dict],
    label: str,
    repeat: int = 1,
    chain: bool = False,
    mode: str = "auto",
) -> list[dict]:
    """Joue les scénarios et renvoie une ligne par appel. `client` : httpx.Client ou TestClient."""
    health = client.get("/health").json()
    if health.get("status") != "ok":
        raise SystemExit(f"Serveur pas prêt : {health}")
    config = server_config(health)
    run_at = datetime.now().isoformat(timespec="seconds")
    chained_session = f"scen-{uuid.uuid4().hex[:8]}"
    results = []

    # Détection automatique du mode traduction si le jeu de données contient des directions ou src_lang=fr
    is_bidi_dataset = bool(
        scenarios
        and any(sc.get("src_lang") and sc.get("tgt_lang") for sc in scenarios)
        and any(sc.get("src_lang") == "fr" for sc in scenarios)
    )
    effective_mode = "translate" if (mode == "translate" or (mode == "auto" and is_bidi_dataset)) else "chat"

    for rep in range(1, repeat + 1):
        for sc in scenarios:
            session_id = chained_session if chain else f"scen-{uuid.uuid4().hex[:8]}"
            t0 = time.perf_counter()

            if effective_mode == "translate":
                src = sc.get("src_lang", sc.get("lang", "dyu"))
                tgt = sc.get("tgt_lang", "fr" if src == "dyu" else "dyu")
                r = client.post(
                    "/api/v1/translate",
                    json={"text": sc["message"], "src": src, "tgt": tgt},
                )
                client_ms = round((time.perf_counter() - t0) * 1000, 1)
                body = (
                    r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
                )
                row = {
                    "run_label": label,
                    "run_at": run_at,
                    "id": sc["id"],
                    "direction": sc.get("direction", f"{src}->{tgt}"),
                    "src_lang": src,
                    "tgt_lang": tgt,
                    "categorie": sc.get("categorie", ""),
                    "repetition": rep,
                    "status": r.status_code,
                    "error_code": (body.get("error") or {}).get("code", ""),
                    "message": sc["message"],
                    "translation": body.get("translation", ""),
                    "reference_translation": sc.get("reference_translation", ""),
                    "time_ms": body.get("time_ms", client_ms),
                    "client_total_ms": client_ms,
                    "translator_model": config.get("translator_model"),
                    "translator_revision": config.get("translator_revision"),
                    "translator_mode": config.get("translator_mode"),
                    "num_beams": config.get("num_beams"),
                    "max_new_tokens": config.get("max_new_tokens"),
                    "device": config.get("device"),
                    "api_version": config.get("api_version"),
                }
                results.append(row)
                dir_str = sc.get("direction", f"{src}->{tgt}")
                print(
                    f"[{rep}/{repeat}] {sc['id']:<6} ({dir_str}) {r.status_code}  "
                    f"total {client_ms:6.1f} ms",
                    file=sys.stderr,
                )
            else:
                r = client.post(
                    "/api/v1/chat?debug=true",
                    json={"session_id": session_id, "lang": sc["lang"], "message": sc["message"]},
                )
                client_ms = round((time.perf_counter() - t0) * 1000, 1)
                body = (
                    r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
                )
                debug = body.get("debug") or {}
                timings = debug.get("timings_ms") or {}
                row = {
                    "run_label": label,
                    "run_at": run_at,
                    "id": sc["id"],
                    "categorie": sc.get("categorie", ""),
                    "repetition": rep,
                    "session_id": session_id,
                    "lang": sc["lang"],
                    "status": r.status_code,
                    "error_code": (body.get("error") or {}).get("code", ""),
                    "message": sc["message"],
                    "fr_input": debug.get("fr_input", ""),
                    "fr_reply": debug.get("fr_reply", ""),
                    "reply": body.get("reply", ""),
                    "fallback_reason": debug.get("fallback_reason") or "",
                    **{f"{s}_ms": timings.get(s, "") for s in STAGES},
                    "server_total_ms": round(sum(timings.get(s, 0) for s in STAGES), 1)
                    if timings
                    else "",
                    "client_total_ms": client_ms,
                    **config,
                }
                results.append(row)
                print(
                    f"[{rep}/{repeat}] {sc['id']:<6} {r.status_code}  "
                    f"total {client_ms / 1000:6.2f} s  "
                    + "  ".join(f"{s} {timings[s] / 1000:5.2f}" for s in STAGES if s in timings),
                    file=sys.stderr,
                )
    return results


def summarize(rows: list[dict]) -> dict:
    """Médiane et maximum par étape, sur les appels réussis."""
    ok = [r for r in rows if r["status"] == 200]
    is_bidi = bool(rows and "direction" in rows[0])
    summary = {
        "appels": len(rows),
        "reussis": len(ok),
        "replis": sum(bool(r.get("fallback_reason")) for r in ok),
    }

    if is_bidi:
        # Analyse détaillée par direction (fr->dyu et dyu->fr)
        directions = {}
        for d in sorted({r.get("direction", "") for r in rows}):
            d_rows = [r for r in rows if r.get("direction") == d]
            d_ok = [r for r in d_rows if r["status"] == 200]
            latencies = [float(r["client_total_ms"]) for r in d_ok if r.get("client_total_ms") != ""]
            directions[d] = {
                "total": len(d_rows),
                "reussis": len(d_ok),
                "mediane_ms": round(statistics.median(latencies), 1) if latencies else 0,
                "max_ms": round(max(latencies), 1) if latencies else 0,
            }
        summary["directions"] = directions
        values = [float(r["client_total_ms"]) for r in ok if r.get("client_total_ms") != ""]
        if values:
            summary["client_total_ms"] = {"mediane": round(statistics.median(values)), "max": round(max(values))}
        return summary

    for col in (*[f"{s}_ms" for s in STAGES], "client_total_ms"):
        values = [float(r[col]) for r in ok if r[col] != ""]
        if values:
            summary[col] = {"mediane": round(statistics.median(values)), "max": round(max(values))}
    return summary


def write_csv(rows: list[dict], path: Path, fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        if rows and "direction" in rows[0]:
            fieldnames = BIDI_COLUMNS
        else:
            fieldnames = COLUMNS
    # utf-8-sig : le fichier s'ouvre correctement dans Excel / LibreOffice (accents, ɛ, ɔ).
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--url", default="http://localhost:8000")
    p.add_argument("--key", required=True, help="Clé d'API kma_...")
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--bidi", action="store_true", help="Utiliser directement le fichier des scénarios bidirectionnels")
    p.add_argument("--mode", choices=["auto", "chat", "translate"], default="auto", help="Mode de test (auto, chat, translate)")
    p.add_argument("--direction", choices=["all", "fr->dyu", "dyu->fr"], default="all", help="Filtrer les scénarios par direction")
    p.add_argument("--label", required=True, help="Nom du réglage testé, ex. beams4, bidi_eval")
    p.add_argument("--repeat", type=int, default=1, help="Nombre de passages (latence plus fiable)")
    p.add_argument("--chain", action="store_true", help="Tous les messages dans UNE conversation (mode chat)")
    p.add_argument("--output", type=Path, default=None)
    a = p.parse_args()

    input_path = DEFAULT_BIDI_INPUT if a.bidi else a.input
    scenarios = load_scenarios(input_path)

    if a.direction != "all":
        scenarios = [s for s in scenarios if s.get("direction") == a.direction]
        if not scenarios:
            raise SystemExit(f"Aucun scénario trouvé pour la direction {a.direction}")

    with httpx.Client(base_url=a.url, headers={"X-API-Key": a.key}, timeout=180) as client:
        rows = run(client, scenarios, a.label, repeat=a.repeat, chain=a.chain, mode=a.mode)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = a.output or DEFAULT_OUTPUT_DIR / f"{stamp}_{a.label}.csv"
    write_csv(rows, output)

    s = summarize(rows)
    print(f"\n{s['reussis']}/{s['appels']} réussis, {s['replis']} repli(s). Résultats : {output}")
    if "directions" in s:
        print("  Détail par direction :")
        for d, stats in s["directions"].items():
            print(f"    • {d:<10} : {stats['reussis']}/{stats['total']} réussis | médiane {stats['mediane_ms']} ms | max {stats['max_ms']} ms")
    for col in (*[f"{st}_ms" for st in STAGES], "client_total_ms"):
        if col in s and isinstance(s[col], dict):
            print(f"  {col:<16} médiane {s[col]['mediane']:>6} ms   max {s[col]['max']:>6} ms")


if __name__ == "__main__":
    main()
