# Cliente mínimo da API REST do GitHub, sem dependências externas, para extrair dados de issues e pull requests.

from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from email.message import Message
from typing import Any, Dict, Iterator, List, Optional, Tuple


class GitHubClient:
    """Cliente mínimo da API REST do GitHub (sem bibliotecas de grafos)."""

    API_BASE = "https://api.github.com"
    RATE_LIMIT_BUFFER = 10
    MAX_RETRIES = 5

    def __init__(self, token: Optional[str] = None, per_page: int = 100):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.per_page = per_page
        self._lock = threading.Lock()
        self._rate_remaining: Optional[int] = None
        self._rate_reset: Optional[int] = None

    @staticmethod
    def parse_repo(repo: str) -> Tuple[str, str]:
        repo = repo.strip().rstrip("/")
        if repo.endswith(".git"):
            repo = repo[:-4]
        if repo.startswith("https://github.com/"):
            repo = repo[len("https://github.com/") :]
        parts = repo.split("/")
        if len(parts) < 2:
            raise ValueError("repositório inválido; use owner/name")
        return parts[0], parts[1]

    def _header_int(self, headers: Message, name: str) -> Optional[int]:
        value = headers.get(name)
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _update_rate_limit(self, headers: Message) -> None:
        remaining = self._header_int(headers, "X-RateLimit-Remaining")
        reset = self._header_int(headers, "X-RateLimit-Reset")
        with self._lock:
            if remaining is not None:
                self._rate_remaining = remaining
            if reset is not None:
                self._rate_reset = reset

    def _wait_for_rate_limit(self) -> None:
        with self._lock:
            if self._rate_remaining is None or self._rate_remaining >= self.RATE_LIMIT_BUFFER:
                return
            reset_at = self._rate_reset
        if reset_at is not None:
            wait = max(0.0, reset_at - time.time()) + 1.0
            if wait > 0:
                print(f"\n[Aviso] Aproximando-se do Rate Limit. Aguardando {wait:.0f}s para resetar...")
                time.sleep(wait)

    def _sleep_until_reset(self, headers: Message) -> None:
        reset = self._header_int(headers, "X-RateLimit-Reset")
        if reset is not None:
            wait = max(0.0, reset - time.time()) + 1.0
            if wait > 0:
                print(f"\n[Aviso] Rate Limit do GitHub esgotado! Pausando por {wait:.0f}s até o reset...")
                time.sleep(wait)
                return
        print("\n[Aviso] Rate Limit do GitHub esgotado! Pausando por 60s...")
        time.sleep(60.0)

    def _request(self, path: str, params: Optional[Dict[str, str]] = None) -> Any:
        url = f"{self.API_BASE}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)

        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "trabalho-grafos-pucminas",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        for attempt in range(self.MAX_RETRIES):
            self._wait_for_rate_limit()
            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    self._update_rate_limit(resp.headers)
                    body = resp.read().decode("utf-8")
                    return json.loads(body) if body else []
            except urllib.error.HTTPError as e:
                if e.code in (403, 429) and attempt < self.MAX_RETRIES - 1:
                    self._sleep_until_reset(e.headers)
                    continue
                detail = e.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"GitHub API {e.code} em {path}: {detail}") from e

        raise RuntimeError(f"GitHub API: esgotadas tentativas em {path}")

    def _paginate(
        self, path: str, params: Optional[Dict[str, str]] = None, max_pages: int = 10
    ) -> Iterator[Dict[str, Any]]:
        page = 1
        base_params = dict(params or {})
        base_params["per_page"] = str(self.per_page)

        while max_pages <= 0 or page <= max_pages:
            base_params["page"] = str(page)
            batch = self._request(path, base_params)
            if not isinstance(batch, list) or not batch:
                break
            for item in batch:
                yield item
            if len(batch) < self.per_page:
                break
            page += 1

    def fetch_issues(self, owner: str, repo: str, max_pages: int = 5) -> List[Dict[str, Any]]:
        path = f"/repos/{owner}/{repo}/issues"
        return list(self._paginate(path, {"state": "all"}, max_pages=max_pages))

    def fetch_issue_comments(self, owner: str, repo: str, number: int) -> List[Dict[str, Any]]:
        path = f"/repos/{owner}/{repo}/issues/{number}/comments"
        return list(self._paginate(path, max_pages=5))

    def fetch_issue_events(self, owner: str, repo: str, number: int) -> List[Dict[str, Any]]:
        path = f"/repos/{owner}/{repo}/issues/{number}/events"
        return list(self._paginate(path, max_pages=3))

    def fetch_pulls(self, owner: str, repo: str, max_pages: int = 5) -> List[Dict[str, Any]]:
        path = f"/repos/{owner}/{repo}/pulls"
        return list(self._paginate(path, {"state": "all"}, max_pages=max_pages))

    def fetch_pr_reviews(self, owner: str, repo: str, number: int) -> List[Dict[str, Any]]:
        path = f"/repos/{owner}/{repo}/pulls/{number}/reviews"
        return list(self._paginate(path, max_pages=3))

    def fetch_pr_comments(self, owner: str, repo: str, number: int) -> List[Dict[str, Any]]:
        path = f"/repos/{owner}/{repo}/issues/{number}/comments"
        return list(self._paginate(path, max_pages=5))
