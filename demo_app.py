from __future__ import annotations

from pathlib import Path

from graph import AdjacencyListGraph, AdjacencyMatrixGraph, AbstractGraph


def exercise_graph(g: AbstractGraph, export_path: Path) -> None:
    # Básicos
    assert g.getVertexCount() > 0
    assert g.getEdgeCount() == 0
    assert g.isEmptyGraph() is True
    assert g.isCompleteGraph() is False

    # Pesos de vértices
    g.setVertexWeight(0, 2.5)
    assert abs(g.getVertexWeight(0) - 2.5) < 1e-9

    # Adição idempotente
    g.addEdge(0, 1)
    g.addEdge(0, 1)
    assert g.hasEdge(0, 1) is True
    assert g.getEdgeCount() == 1

    # Pesos de arestas
    g.setEdgeWeight(0, 1, 3.3)
    assert abs(g.getEdgeWeight(0, 1) - 3.3) < 1e-9

    # Relações estruturais
    assert g.isSucessor(0, 1) is True
    assert g.isPredessor(0, 1) is False

    g.addEdge(0, 2)
    assert g.isDivergent(0, 1, 0, 2) is True  # mesmo "u", destinos diferentes

    g.addEdge(1, 2)
    assert g.isConvergent(0, 2, 1, 2) is True  # mesmo "v", origens diferentes

    # Garante que o grafo fique (fracamente) conectado.
    g.addEdge(2, 3)

    assert g.isIncident(0, 1, 0) is True
    assert g.isIncident(0, 1, 1) is True
    assert g.isIncident(0, 1, 2) is False

    # Graus
    assert g.getVertexOutDegree(0) == 2
    assert g.getVertexInDegree(2) == 2  # 0->2 e 1->2

    # Conectividade fraca
    assert g.isConnected() is True

    # Remoção e exceções
    g.removeEdge(0, 2)
    assert g.hasEdge(0, 2) is False
    assert g.isConnected() is True  # ainda 0--1--2 via 0->1 e 1->2

    export_path.parent.mkdir(parents=True, exist_ok=True)
    g.exportToGEPHI(str(export_path))
    assert export_path.exists() and export_path.stat().st_size > 0


def main() -> None:
    n = 4

    g1 = AdjacencyMatrixGraph(n)
    g2 = AdjacencyListGraph(n)

    out1 = Path("gephi_export_adjacency_matrix.graphml")
    out2 = Path("gephi_export_adjacency_list.graphml")

    exercise_graph(g1, out1)
    exercise_graph(g2, out2)

    print("Demo finalizada. Arquivos GraphML gerados para o Gephi.")
    print(f"- {out1}")
    print(f"- {out2}")


if __name__ == "__main__":
    main()

