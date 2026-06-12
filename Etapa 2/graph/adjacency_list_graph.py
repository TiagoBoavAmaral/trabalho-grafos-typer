# Implementação de grafo usando listas de adjacência.
# Vantagens: uso O(V + E) de memória, eficiente para grafos esparsos.
# Desvantagens: acesso O(k) para hasEdge (k = grau de vértice), implementação um pouco mais complexa.

from __future__ import annotations

from typing import Dict, List

from .abstract_graph import AbstractGraph


class AdjacencyListGraph(AbstractGraph):
    """
    Implementação da API obrigatória usando listas de adjacência.
    Grafo simples e direcionado:
    - sem laços
    - sem múltiplas arestas (addEdge idempotente)
    """

    def __init__(self, numVertices: int):
        super().__init__(numVertices)
        # adj[u] = { v: weight(u,v) }
        self._adj: List[Dict[int, float]] = [dict() for _ in range(numVertices)]
        self._edge_count = 0

    def getVertexCount(self) -> int:
        return self._n

    def getEdgeCount(self) -> int:
        return self._edge_count

    def hasEdge(self, u: int, v: int) -> bool:
        self._check_edge_vertices(u, v)
        return v in self._adj[u]

    def addEdge(self, u: int, v: int) -> None:
        self._check_edge_vertices(u, v)
        if v not in self._adj[u]:
            self._adj[u][v] = 1.0  # peso padrão
            self._edge_count += 1

    def removeEdge(self, u: int, v: int) -> None:
        self._check_edge_vertices(u, v)
        self._require_edge_exists(u, v)
        del self._adj[u][v]
        self._edge_count -= 1

    def setEdgeWeight(self, u: int, v: int, w: float) -> None:
        self._check_edge_vertices(u, v)
        self._require_edge_exists(u, v)
        if not isinstance(w, (int, float)):
            raise TypeError("peso da aresta deve ser numérico")
        self._adj[u][v] = float(w)

    def getEdgeWeight(self, u: int, v: int) -> float:
        self._check_edge_vertices(u, v)
        self._require_edge_exists(u, v)
        return float(self._adj[u][v])

