# Implementação de grafo usando matriz de adjacência.
# Vantagens: acesso O(1) para hasEdge, fácil implementação.
# Desvantagens: uso O(V^2) de memória, ineficiente para grafos esparsos.

from __future__ import annotations

from typing import List

from .abstract_graph import AbstractGraph


class AdjacencyMatrixGraph(AbstractGraph):
    """
    Implementação da API obrigatória usando matriz de adjacência.
    Grafo simples e direcionado:
    - sem laços
    - sem múltiplas arestas (addEdge idempotente)
    """

    def __init__(self, numVertices: int):
        super().__init__(numVertices)
        self._adj: List[List[bool]] = [[False] * numVertices for _ in range(numVertices)]
        self._edge_weights: List[List[float]] = [[0.0] * numVertices for _ in range(numVertices)]
        self._edge_count = 0

    def getVertexCount(self) -> int:
        return self._n

    def getEdgeCount(self) -> int:
        return self._edge_count

    def hasEdge(self, u: int, v: int) -> bool:
        self._check_edge_vertices(u, v)
        return self._adj[u][v]

    def addEdge(self, u: int, v: int) -> None:
        self._check_edge_vertices(u, v)
        if not self._adj[u][v]:
            self._adj[u][v] = True
            self._edge_weights[u][v] = 1.0  # peso padrão
            self._edge_count += 1

    def removeEdge(self, u: int, v: int) -> None:
        self._check_edge_vertices(u, v)
        self._require_edge_exists(u, v)
        self._adj[u][v] = False
        self._edge_weights[u][v] = 0.0
        self._edge_count -= 1

    def setEdgeWeight(self, u: int, v: int, w: float) -> None:
        self._check_edge_vertices(u, v)
        self._require_edge_exists(u, v)
        if not isinstance(w, (int, float)):
            raise TypeError("peso da aresta deve ser numérico")
        self._edge_weights[u][v] = float(w)

    def getEdgeWeight(self, u: int, v: int) -> float:
        self._check_edge_vertices(u, v)
        self._require_edge_exists(u, v)
        return float(self._edge_weights[u][v])

