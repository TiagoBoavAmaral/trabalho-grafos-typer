# Construção de grafos de interação entre colaboradores a partir de uma lista de interações extraídas do GitHub.
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from graph import AdjacencyListGraph
from graph.utils import add_or_accumulate_edge

from .models import INTEGRATED_WEIGHTS, Interaction, InteractionType


@dataclass
class GraphSet:
    users: List[str]
    user_index: Dict[str, int]
    comments_graph: AdjacencyListGraph
    closes_graph: AdjacencyListGraph
    pr_actions_graph: AdjacencyListGraph
    integrated_graph: AdjacencyListGraph


def _index_users(interactions: List[Interaction]) -> List[str]:
    users = set()
    for it in interactions:
        users.add(it.source)
        users.add(it.target)
    return sorted(users)


def build_graphs_from_interactions(interactions: List[Interaction]) -> GraphSet:
    users = _index_users(interactions)
    if not users:
        raise ValueError("nenhuma interação para construir grafos")

    n = len(users)
    idx = {u: i for i, u in enumerate(users)}

    g_comments = AdjacencyListGraph(n)
    g_closes = AdjacencyListGraph(n)
    g_pr = AdjacencyListGraph(n)
    g_integrated = AdjacencyListGraph(n)

    for i, login in enumerate(users):
        g_comments.setVertexLabel(i, login)
        g_closes.setVertexLabel(i, login)
        g_pr.setVertexLabel(i, login)
        g_integrated.setVertexLabel(i, login)

    for it in interactions:
        u = idx[it.source]
        v = idx[it.target]
        w_int = INTEGRATED_WEIGHTS[it.kind]

        if it.kind in (InteractionType.COMMENT, InteractionType.ISSUE_OPEN_COMMENTED):
            add_or_accumulate_edge(g_comments, u, v, 1.0)
        elif it.kind == InteractionType.ISSUE_CLOSE:
            add_or_accumulate_edge(g_closes, u, v, 1.0)
        elif it.kind in (InteractionType.PR_REVIEW, InteractionType.PR_MERGE):
            add_or_accumulate_edge(g_pr, u, v, 1.0)

        add_or_accumulate_edge(g_integrated, u, v, w_int)

    return GraphSet(
        users=users,
        user_index=idx,
        comments_graph=g_comments,
        closes_graph=g_closes,
        pr_actions_graph=g_pr,
        integrated_graph=g_integrated,
    )
