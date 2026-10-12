"""scripts/run_scenarios.py contre l'application en mode stub (sans réseau)."""

from __future__ import annotations

import csv

from scripts.run_scenarios import COLUMNS, load_scenarios, run, summarize, write_csv


def _scenarios(tmp_path):
    path = tmp_path / "sc.csv"
    path.write_text(
        "# commentaire ignoré\nid,lang,message,categorie\n"
        "S01,dyu,I ni ce,salutation\nS02,dyu,Phrase test,question\nS03,xx,inconnue,erreur\n",
        encoding="utf-8",
    )
    return load_scenarios(path)


def test_run_records_texts_timings_and_config(api, tmp_path):
    _, client = api
    rows = run(client, _scenarios(tmp_path), label="stub", repeat=2)

    assert len(rows) == 6
    ok = [r for r in rows if r["status"] == 200]
    assert len(ok) == 4
    first = ok[0]
    assert first["fr_input"] and first["fr_reply"] and first["reply"]
    assert all(isinstance(first[f"{s}_ms"], float) for s in ("mt_in", "llm", "mt_out"))
    assert first["llm"] == "stub" and first["api_version"]
    # Chaque message a sa propre session (mesures indépendantes).
    assert len({r["session_id"] for r in rows}) == 6

    bad = [r for r in rows if r["status"] != 200]
    assert {r["error_code"] for r in bad} == {"langue_inconnue"}

    s = summarize(rows)
    assert (s["appels"], s["reussis"]) == (6, 4)
    assert s["client_total_ms"]["mediane"] >= 0


def test_chain_uses_one_session(api, tmp_path):
    _, client = api
    rows = run(client, _scenarios(tmp_path)[:2], label="chaine", chain=True)
    assert len({r["session_id"] for r in rows}) == 1


def test_csv_has_all_columns(api, tmp_path):
    _, client = api
    rows = run(client, _scenarios(tmp_path)[:1], label="csv")
    out = tmp_path / "res" / "r.csv"
    write_csv(rows, out)
    with out.open(encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == COLUMNS
        assert next(reader)["message"] == "I ni ce"


def test_health_exposes_llm_model_key(api):
    _, client = api
    assert "llm_model" in client.get("/health").json()
