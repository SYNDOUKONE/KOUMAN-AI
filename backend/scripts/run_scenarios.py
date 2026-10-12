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
DEFAULT_OUTPUT_DIR = ROOT / "docs" / "scenarios_results"

STAGES = ("mt_in", "llm", "mt_out")
COLUMNS = [
    "run_label", "run_at", "id", "categorie", "repetition", "session_id", "lang",
    "status", "error_code", "message", "fr_input", "fr_reply", "reply", "fallback_reason",
    "mt_in_ms", "llm_ms", "mt_out_ms", "server_total_ms", "client_total_ms",
    "translator_model", "translator_revision", "translator_mode", "num_beams",
    "max_new_tokens", "device", "llm", "llm_model", "api_version",
]  # fmt: skip


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
) -> list[dict]:
    """Joue les scénarios et renvoie une ligne par appel. `client` : httpx.Client ou TestClient."""
    health = client.get("/health").json()
    if health.get("status") != "ok":
        raise SystemExit(f"Serveur pas prêt : {health}")
    config = server_config(health)
    run_at = datetime.now().isoformat(timespec="seconds")
    chained_session = f"scen-{uuid.uuid4().hex[:8]}"
    results = []

    for rep in range(1, repeat + 1):
        for sc in scenarios:
            # Par défaut, une session neuve par message : les temps restent comparables.
            session_id = chained_session if chain else f"scen-{uuid.uuid4().hex[:8]}"
            t0 = time.perf_counter()
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
    summary = {
        "appels": len(rows),
        "reussis": len(ok),
        "replis": sum(bool(r["fallback_reason"]) for r in ok),
    }
    for col in (*[f"{s}_ms" for s in STAGES], "client_total_ms"):
        values = [float(r[col]) for r in ok if r[col] != ""]
        if values:
            summary[col] = {"mediane": round(statistics.median(values)), "max": round(max(values))}
    return summary


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig : le fichier s'ouvre correctement dans Excel / LibreOffice (accents, ɛ, ɔ).
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--url", default="http://localhost:8000")
    p.add_argument("--key", required=True, help="Clé d'API kma_...")
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--label", required=True, help="Nom du réglage testé, ex. beams4, rtx5090")
    p.add_argument("--repeat", type=int, default=1, help="Nombre de passages (latence plus fiable)")
    p.add_argument("--chain", action="store_true", help="Tous les messages dans UNE conversation")
    p.add_argument("--output", type=Path, default=None)
    a = p.parse_args()

    scenarios = load_scenarios(a.input)
    with httpx.Client(base_url=a.url, headers={"X-API-Key": a.key}, timeout=180) as client:
        rows = run(client, scenarios, a.label, repeat=a.repeat, chain=a.chain)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = a.output or DEFAULT_OUTPUT_DIR / f"{stamp}_{a.label}.csv"
    write_csv(rows, output)

    s = summarize(rows)
    print(f"\n{s['reussis']}/{s['appels']} réussis, {s['replis']} repli(s). Résultats : {output}")
    for col in (*[f"{st}_ms" for st in STAGES], "client_total_ms"):
        if col in s:
            print(f"  {col:<16} médiane {s[col]['mediane']:>6} ms   max {s[col]['max']:>6} ms")


if __name__ == "__main__":
    main()
