from __future__ import annotations

from .abstract_graph import AbstractGraph


def add_or_accumulate_edge(g: AbstractGraph, u: int, v: int, weight: float) -> None:
    """Adiciona aresta direcionada u->v ou acumula peso se já existir."""
    if u == v:
        return
    if not g.hasEdge(u, v):
        g.addEdge(u, v)
        g.setEdgeWeight(u, v, float(weight))
    else:
        g.setEdgeWeight(u, v, g.getEdgeWeight(u, v) + float(weight))
