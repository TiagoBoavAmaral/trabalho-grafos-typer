from __future__ import annotations

from .abstract_graph import AbstractGraph

# Função utilitária para adicionar ou acumular peso em uma aresta, usada na construção dos grafos a partir das interações. Se a aresta já existir, o peso é somado ao peso existente; caso contrário, a aresta é criada com o peso fornecido.
def add_or_accumulate_edge(g: AbstractGraph, u: int, v: int, weight: float) -> None:
    """Adiciona aresta direcionada u->v ou acumula peso se já existir."""
    if u == v:
        return
    if not g.hasEdge(u, v):
        g.addEdge(u, v)
        g.setEdgeWeight(u, v, float(weight))
    else:
        g.setEdgeWeight(u, v, g.getEdgeWeight(u, v) + float(weight))
