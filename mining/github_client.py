from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Iterator, List, Optional, Tuple


class GitHubClient:
    """Cliente mínimo da API REST do GitHub (sem bibliotecas de grafos)."""

    API_BASE = "https://api.github.com"

    def __init__(self, token: Optional[str] = None, per_page: int = 100):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.per_page = per_page

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

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else []
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API {e.code} em {path}: {detail}") from e

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
            time.sleep(0.2)

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
