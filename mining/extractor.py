from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .github_client import GitHubClient
from .models import Interaction, InteractionType


def _login(user_obj: Optional[Dict[str, Any]]) -> Optional[str]:
    if not user_obj:
        return None
    login = user_obj.get("login")
    return str(login) if login else None


class InteractionExtractor:
    """Extrai interações entre colaboradores a partir da API do GitHub."""

    def __init__(self, client: Optional[GitHubClient] = None):
        self.client = client or GitHubClient()

    def extract_from_repo(
        self,
        repo: str,
        max_issues: int = 30,
        max_pulls: int = 30,
    ) -> List[Interaction]:
        owner, name = GitHubClient.parse_repo(repo)
        interactions: List[Interaction] = []

        issue_pages = 0 if max_issues <= 0 else max(1, max_issues // self.client.per_page + 1)
        issues = self.client.fetch_issues(owner, name, max_pages=issue_pages)
        issues = [i for i in issues if "pull_request" not in i]
        if max_issues > 0:
            issues = issues[:max_issues]

        for issue in issues:
            number = issue["number"]
            author = _login(issue.get("user"))
            if not author:
                continue

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

        pull_pages = 0 if max_pulls <= 0 else max(1, max_pulls // self.client.per_page + 1)
        pulls = self.client.fetch_pulls(owner, name, max_pages=pull_pages)
        if max_pulls > 0:
            pulls = pulls[:max_pulls]
        for pr in pulls:
            number = pr["number"]
            author = _login(pr.get("user"))
            if not author:
                continue

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
