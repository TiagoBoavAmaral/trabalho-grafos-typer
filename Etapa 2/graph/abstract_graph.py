from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
import xml.etree.ElementTree as ET


class AbstractGraph(ABC):
    """
    API comum exigida pelo enunciado (grafo simples e direcionado).
    - Vértices: 0..numVertices-1
    - Sem laços (u != v)
    - Sem múltiplas arestas (addEdge idempotente)
    """

    def __init__(self, numVertices: int):
        if not isinstance(numVertices, int):
            raise TypeError("numVertices deve ser int")
        if numVertices <= 0:
            raise ValueError("numVertices deve ser > 0")

        self._n = numVertices
        self._vertex_weights: list[float] = [0.0] * numVertices
        self._vertex_labels: list[str] = [str(i) for i in range(numVertices)]

    # ----------------------------
    # Validações auxiliares
    # ----------------------------
    def _check_vertex(self, v: int) -> None:
        if not isinstance(v, int):
            raise TypeError("índice de vértice deve ser int")
        if v < 0 or v >= self._n:
            raise IndexError("índice de vértice inválido")

    def _check_edge_vertices(self, u: int, v: int) -> None:
        self._check_vertex(u)
        self._check_vertex(v)
        if u == v:
            raise ValueError("grafo simples: laços não são permitidos (u == v)")

    def _require_edge_exists(self, u: int, v: int) -> None:
        if not self.hasEdge(u, v):
            raise ValueError("operação inconsistente: aresta não existe")

    # ----------------------------
    # API obrigatória
    # ----------------------------
    @abstractmethod
    def getVertexCount(self) -> int: ...

    @abstractmethod
    def getEdgeCount(self) -> int: ...

    @abstractmethod
    def hasEdge(self, u: int, v: int) -> bool: ...

    @abstractmethod
    def addEdge(self, u: int, v: int) -> None: ...

    @abstractmethod
    def removeEdge(self, u: int, v: int) -> None: ...

    def isSucessor(self, u: int, v: int) -> bool:
        self._check_edge_vertices(u, v)
        return self.hasEdge(u, v)

    def isPredessor(self, u: int, v: int) -> bool:
        self._check_edge_vertices(u, v)
        return self.hasEdge(v, u)

    def isDivergent(self, u1: int, v1: int, u2: int, v2: int) -> bool:
        self._check_edge_vertices(u1, v1)
        self._check_edge_vertices(u2, v2)
        # Considera "divergência" entre dois arcos existentes (u1,v1) e (u2,v2).
        return self.hasEdge(u1, v1) and self.hasEdge(u2, v2) and u1 == u2 and v1 != v2

    def isConvergent(self, u1: int, v1: int, u2: int, v2: int) -> bool:
        self._check_edge_vertices(u1, v1)
        self._check_edge_vertices(u2, v2)
        # Considera "convergência" entre dois arcos existentes (u1,v1) e (u2,v2).
        return self.hasEdge(u1, v1) and self.hasEdge(u2, v2) and v1 == v2 and u1 != u2

    def isIncident(self, u: int, v: int, x: int) -> bool:
        self._check_edge_vertices(u, v)
        self._check_vertex(x)
        # Um vértice é incidente ao arco existente (u,v) se for um de seus extremos.
        return self.hasEdge(u, v) and (x == u or x == v)

    def getVertexInDegree(self, u: int) -> int:
        self._check_vertex(u)
        deg = 0
        for src in range(self.getVertexCount()):
            if src != u and self.hasEdge(src, u):
                deg += 1
        return deg

    def getVertexOutDegree(self, u: int) -> int:
        self._check_vertex(u)
        deg = 0
        for dst in range(self.getVertexCount()):
            if dst != u and self.hasEdge(u, dst):
                deg += 1
        return deg

    def setVertexWeight(self, v: int, w: float) -> None:
        self._check_vertex(v)
        if not isinstance(w, (int, float)):
            raise TypeError("peso do vértice deve ser numérico")
        self._vertex_weights[v] = float(w)

    def getVertexWeight(self, v: int) -> float:
        self._check_vertex(v)
        return float(self._vertex_weights[v])

    def setVertexLabel(self, v: int, label: str) -> None:
        self._check_vertex(v)
        if not isinstance(label, str) or not label.strip():
            raise ValueError("rótulo do vértice inválido")
        self._vertex_labels[v] = label.strip()

    def getVertexLabel(self, v: int) -> str:
        self._check_vertex(v)
        return self._vertex_labels[v]

    @abstractmethod
    def setEdgeWeight(self, u: int, v: int, w: float) -> None: ...

    @abstractmethod
    def getEdgeWeight(self, u: int, v: int) -> float: ...

    def isConnected(self) -> bool:
        """
        Conectividade fraca: considera o grafo subjacente não-direcionado.
        """
        n = self.getVertexCount()
        if n == 0:
            return True

        visited = [False] * n
        q: deque[int] = deque([0])
        visited[0] = True

        while q:
            cur = q.popleft()
            for nxt in range(n):
                if nxt == cur:
                    continue
                if self.hasEdge(cur, nxt) or self.hasEdge(nxt, cur):
                    if not visited[nxt]:
                        visited[nxt] = True
                        q.append(nxt)

        return all(visited)

    def isEmptyGraph(self) -> bool:
        return self.getEdgeCount() == 0

    def isCompleteGraph(self) -> bool:
        n = self.getVertexCount()
        expected = n * (n - 1)
        if self.getEdgeCount() != expected:
            return False
        for u in range(n):
            for v in range(n):
                if u == v:
                    continue
                if not self.hasEdge(u, v):
                    return False
        return True

    def exportToGEPHI(self, path: str) -> None:
        """
        Exporta em GraphML (formato aceito pelo Gephi).
        Escreve pesos de vértice e aresta como atributos (double).
        """
        if not isinstance(path, str) or not path.strip():
            raise ValueError("path inválido")

        graphml = ET.Element("graphml", xmlns="http://graphml.graphdrawing.org/xmlns")
        key_vw = ET.SubElement(
            graphml, "key", id="v_weight", **{"for": "node", "attr.name": "weight", "attr.type": "double"}
        )
        _ = key_vw
        key_vl = ET.SubElement(
            graphml, "key", id="v_label", **{"for": "node", "attr.name": "label", "attr.type": "string"}
        )
        _ = key_vl
        key_ew = ET.SubElement(
            graphml, "key", id="e_weight", **{"for": "edge", "attr.name": "weight", "attr.type": "double"}
        )
        _ = key_ew

        g = ET.SubElement(graphml, "graph", id="G", edgedefault="directed")

        n = self.getVertexCount()
        for i in range(n):
            node = ET.SubElement(g, "node", id=str(i))
            data_w = ET.SubElement(node, "data", key="v_weight")
            data_w.text = str(self.getVertexWeight(i))
            data_l = ET.SubElement(node, "data", key="v_label")
            data_l.text = self.getVertexLabel(i)

        edge_id = 0
        for u in range(n):
            for v in range(n):
                if u == v:
                    continue
                if self.hasEdge(u, v):
                    e = ET.SubElement(g, "edge", id=str(edge_id), source=str(u), target=str(v))
                    data = ET.SubElement(e, "data", key="e_weight")
                    data.text = str(self.getEdgeWeight(u, v))
                    edge_id += 1

        tree = ET.ElementTree(graphml)
        tree.write(path, encoding="utf-8", xml_declaration=True)

