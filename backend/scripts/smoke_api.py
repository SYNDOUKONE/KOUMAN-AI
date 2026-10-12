"""Test rapide d'un serveur lancé : /health, /translate (2 sens), /chat.

    python -m scripts.smoke_api --key kma_xxx [--url http://localhost:8000]

Les phrases dioula de test sont à fournir par un locuteur (--dyu "...").
"""

from __future__ import annotations

import argparse
import json
import time

import httpx


def call(client: httpx.Client, method: str, path: str, **kw) -> dict:
    t0 = time.perf_counter()
    r = client.request(method, path, **kw)
    ms = int((time.perf_counter() - t0) * 1000)
    print(f"\n{method} {path} -> {r.status_code} en {ms} ms")
    try:
        body = r.json()
    except ValueError:
        body = {"brut": r.text}
    print(json.dumps(body, ensure_ascii=False, indent=2))
    return body


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://localhost:8000")
    p.add_argument("--key", required=True)
    p.add_argument("--fr", default="Bonjour, comment allez-vous ?")
    p.add_argument("--dyu", default=None, help="Phrase dioula validée par un locuteur")
    a = p.parse_args()

    headers = {"X-API-Key": a.key}
    with httpx.Client(base_url=a.url, headers=headers, timeout=120) as c:
        call(c, "GET", "/health")
        call(c, "POST", "/api/v1/translate", json={"text": a.fr, "src": "fr", "tgt": "dyu"})
        if a.dyu:
            call(c, "POST", "/api/v1/translate", json={"text": a.dyu, "src": "dyu", "tgt": "fr"})
            call(
                c,
                "POST",
                "/api/v1/chat?debug=true",
                json={"session_id": "smoke", "lang": "dyu", "message": a.dyu},
            )
        else:
            print("\n(--dyu non fourni : /chat et le sens dyu→fr ne sont pas testés)")


if __name__ == "__main__":
    main()
