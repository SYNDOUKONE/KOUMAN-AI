"""Gestion des clés d'API.

    python -m scripts.manage_keys create appli-demo
    python -m scripts.manage_keys revoke appli-demo
    python -m scripts.manage_keys list

La clé en clair n'est affichée qu'UNE fois, à la création : notez-la.
"""

from __future__ import annotations

import argparse
import sys
import time

from app.core.config import get_settings
from app.core.security import ApiKeyStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Clés d'API KOUMA AI")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("create").add_argument("client")
    sub.add_parser("revoke").add_argument("client")
    sub.add_parser("list")
    args = parser.parse_args()

    store = ApiKeyStore(get_settings().api_keys_db)
    if args.cmd == "create":
        key = store.create(args.client)
        print(f"Clé créée pour {args.client!r} (affichée une seule fois) :\n{key}")
    elif args.cmd == "revoke":
        n = store.revoke(args.client)
        print(f"{n} clé(s) révoquée(s) pour {args.client!r}.")
        sys.exit(0 if n else 1)
    else:
        for client, created, revoked in store.list_clients():
            date = time.strftime("%Y-%m-%d %H:%M", time.localtime(created))
            print(f"{client:<25} {date}  {'RÉVOQUÉE' if revoked else 'active'}")


if __name__ == "__main__":
    main()
