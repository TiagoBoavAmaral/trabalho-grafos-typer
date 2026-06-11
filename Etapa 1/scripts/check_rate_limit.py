"""Consulta o rate limit da API do GitHub usando o token do .env."""
from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def load_token() -> str:
    for line in Path(".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("GITHUB_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("GITHUB_TOKEN não encontrado no .env")


def fmt_reset(ts: int | None) -> str:
    if not ts:
        return "N/A"
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def main() -> None:
    token = load_token()
    req = urllib.request.Request(
        "https://api.github.com/rate_limit",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "trabalho-grafos-pucminas",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())

    resources = data.get("resources", {})
    core = resources.get("core", {})
    search = resources.get("search", {})
    graphql = resources.get("graphql", {})

    print("=== GitHub Rate Limit ===")
    print(f"Core API:    {core.get('remaining', '?')}/{core.get('limit', '?')} restantes")
    print(f"  Usado:     {core.get('used', '?')}")
    print(f"  Reset em:  {fmt_reset(core.get('reset'))}")
    print(f"Search API:  {search.get('remaining', '?')}/{search.get('limit', '?')} restantes")
    print(f"GraphQL API: {graphql.get('remaining', '?')}/{graphql.get('limit', '?')} restantes")

    remaining = core.get("remaining", 0)
    if remaining == 0:
        print("\n>>> LIMITE ZERADO — mineracao vai pausar ate o reset.")
    elif remaining < 50:
        print("\n>>> LIMITE BAIXO — pode haver pausas longas durante a mineracao.")
    else:
        print("\n>>> Limite OK para minerar normalmente.")


if __name__ == "__main__":
    main()
