from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class InteractionType(str, Enum):
    COMMENT = "comment"
    ISSUE_OPEN_COMMENTED = "issue_open_commented"
    ISSUE_CLOSE = "issue_close"
    PR_REVIEW = "pr_review"
    PR_MERGE = "pr_merge"


# Pesos do grafo integrado (conforme enunciado)
INTEGRATED_WEIGHTS: dict[InteractionType, float] = {
    InteractionType.COMMENT: 2.0,
    InteractionType.ISSUE_OPEN_COMMENTED: 3.0,
    InteractionType.ISSUE_CLOSE: 2.0,
    InteractionType.PR_REVIEW: 4.0,
    InteractionType.PR_MERGE: 5.0,
}


@dataclass(frozen=True)
class Interaction:
    source: str
    target: str
    kind: InteractionType
    reference: str = ""
