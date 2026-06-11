from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .github_client import GitHubClient
from .models import Interaction, InteractionType

DEFAULT_WORKERS = 8


def _login(user_obj: Optional[Dict[str, Any]]) -> Optional[str]:
    if not user_obj:
        return None
    login = user_obj.get("login")
    return str(login) if login else None


def _cache_meta_path(cache_path: Path) -> Path:
    return cache_path.with_name(f"{cache_path.stem}.meta.json")


class InteractionExtractor:
    """Extrai interações entre colaboradores a partir da API do GitHub."""

    def __init__(self, client: Optional[GitHubClient] = None, workers: int = DEFAULT_WORKERS):
        self.client = client or GitHubClient()
        self.workers = max(1, workers)

    def _extract_issue_interactions(
        self, owner: str, name: str, issue: Dict[str, Any]
    ) -> List[Interaction]:
        interactions: List[Interaction] = []
        number = issue["number"]
        author = _login(issue.get("user"))
        if not author:
            return interactions

        for comment in self.client.fetch_issue_comments(owner, name, number):
            commenter = _login(comment.get("user"))
            if commenter and commenter != author:
                interactions.append(
                    Interaction(
                        source=commenter,
                        target=author,
                        kind=InteractionType.COMMENT,
                        reference=f"issue#{number}",
                    )
                )
                interactions.append(
                    Interaction(
                        source=commenter,
                        target=author,
                        kind=InteractionType.ISSUE_OPEN_COMMENTED,
                        reference=f"issue#{number}",
                    )
                )

        for event in self.client.fetch_issue_events(owner, name, number):
            if event.get("event") == "closed":
                closer = _login(event.get("actor"))
                if closer and closer != author:
                    interactions.append(
                        Interaction(
                            source=closer,
                            target=author,
                            kind=InteractionType.ISSUE_CLOSE,
                            reference=f"issue#{number}",
                        )
                    )

        return interactions

    def _extract_pr_interactions(self, owner: str, name: str, pr: Dict[str, Any]) -> List[Interaction]:
        interactions: List[Interaction] = []
        number = pr["number"]
        author = _login(pr.get("user"))
        if not author:
            return interactions

        for comment in self.client.fetch_pr_comments(owner, name, number):
            commenter = _login(comment.get("user"))
            if commenter and commenter != author:
                interactions.append(
                    Interaction(
                        source=commenter,
                        target=author,
                        kind=InteractionType.COMMENT,
                        reference=f"pr#{number}",
                    )
                )

        for review in self.client.fetch_pr_reviews(owner, name, number):
            reviewer = _login(review.get("user"))
            state = (review.get("state") or "").upper()
            if reviewer and reviewer != author and state in {"APPROVED", "CHANGES_REQUESTED", "COMMENTED"}:
                interactions.append(
                    Interaction(
                        source=reviewer,
                        target=author,
                        kind=InteractionType.PR_REVIEW,
                        reference=f"pr#{number}",
                    )
                )

        if pr.get("merged_at"):
            merger = _login(pr.get("merged_by")) or _login(pr.get("user"))
            if merger and merger != author:
                interactions.append(
                    Interaction(
                        source=merger,
                        target=author,
                        kind=InteractionType.PR_MERGE,
                        reference=f"pr#{number}",
                    )
                )

        return interactions

    def _parallel_extract(
        self,
        items: List[Dict[str, Any]],
        worker_fn,
        owner: str,
        name: str,
        label: str,
    ) -> List[Interaction]:
        if not items:
            return []

        interactions: List[Interaction] = []
        total = len(items)
        completed = 0

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(worker_fn, owner, name, item): item for item in items}
            for future in as_completed(futures):
                interactions.extend(future.result())
                completed += 1
                if completed % 50 == 0 or completed == total:
                    print(f"  {label}: {completed}/{total} processados")

        return interactions

    def extract_from_repo(
        self,
        repo: str,
        max_issues: int = 30,
        max_pulls: int = 30,
    ) -> List[Interaction]:
        owner, name = GitHubClient.parse_repo(repo)
        interactions: List[Interaction] = []

        issue_pages = 0 if max_issues <= 0 else max(1, max_issues // self.client.per_page + 1)
        print("Listando issues...")
        issues = self.client.fetch_issues(owner, name, max_pages=issue_pages)
        issues = [i for i in issues if "pull_request" not in i]
        if max_issues > 0:
            issues = issues[:max_issues]
        print(f"  {len(issues)} issues encontradas")

        interactions.extend(
            self._parallel_extract(issues, self._extract_issue_interactions, owner, name, "Issues")
        )

        pull_pages = 0 if max_pulls <= 0 else max(1, max_pulls // self.client.per_page + 1)
        print("Listando pull requests...")
        pulls = self.client.fetch_pulls(owner, name, max_pages=pull_pages)
        if max_pulls > 0:
            pulls = pulls[:max_pulls]
        print(f"  {len(pulls)} PRs encontrados")

        interactions.extend(self._parallel_extract(pulls, self._extract_pr_interactions, owner, name, "PRs"))

        return interactions

    @staticmethod
    def load_interactions_json(path: str | Path) -> List[Interaction]:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        out: List[Interaction] = []
        for item in data:
            out.append(
                Interaction(
                    source=item["source"],
                    target=item["target"],
                    kind=InteractionType(item["kind"]),
                    reference=item.get("reference", ""),
                )
            )
        return out

    @staticmethod
    def save_interactions_json(path: str | Path, interactions: List[Interaction]) -> None:
        payload = [
            {
                "source": i.source,
                "target": i.target,
                "kind": i.kind.value,
                "reference": i.reference,
            }
            for i in interactions
        ]
        Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def save_cache_meta(
        cache_path: str | Path,
        repo: str,
        max_issues: int,
        max_pulls: int,
        interaction_count: int,
    ) -> None:
        meta = {
            "repo": repo,
            "max_issues": max_issues,
            "max_pulls": max_pulls,
            "interaction_count": interaction_count,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }
        _cache_meta_path(Path(cache_path)).write_text(
            json.dumps(meta, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @staticmethod
    def load_cache_if_valid(
        cache_path: str | Path,
        repo: str,
        max_issues: int,
        max_pulls: int,
    ) -> Optional[List[Interaction]]:
        cache_path = Path(cache_path)
        meta_path = _cache_meta_path(cache_path)
        if not cache_path.exists() or not meta_path.exists():
            return None

        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if (
            meta.get("repo") != repo
            or meta.get("max_issues") != max_issues
            or meta.get("max_pulls") != max_pulls
        ):
            return None

        interactions = InteractionExtractor.load_interactions_json(cache_path)
        if meta.get("interaction_count") != len(interactions):
            return None

        return interactions
