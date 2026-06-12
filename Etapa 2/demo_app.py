from __future__ import annotations

from pathlib import Path

from graph import AdjacencyListGraph, AdjacencyMatrixGraph, AbstractGraph

# Este script é uma demonstração prática da implementação das classes de grafo, exercitando os métodos obrigatórios e exportando os resultados para arquivos GraphML que podem ser visualizados no Gephi. Ele inclui testes de funcionalidade, tratamento de exceções esperadas e uma estrutura organizada para facilitar a compreensão do comportamento dos grafos implementados.
def _section(title: str) -> None:
    print(f"\n--- {title} ---")


def _demo_exception(label: str, fn) -> None:
    try:
        fn()
        print(f"  {label}: ERRO (esperava exceção)")
    except Exception as exc:
        print(f"  {label}: {type(exc).__name__} - {exc}")


def exercise_graph(g: AbstractGraph, label: str, export_path: Path) -> None:
    print(f"\n{'=' * 60}")
    print(f"Demonstração: {label}")
    print(f"{'=' * 60}")

    _section("Contagem e estado inicial")
    print(f"  getVertexCount()  = {g.getVertexCount()}")
    print(f"  getEdgeCount()    = {g.getEdgeCount()}")
    print(f"  isEmptyGraph()    = {g.isEmptyGraph()}")
    print(f"  isCompleteGraph() = {g.isCompleteGraph()}")

    _section("Pesos de vértices")
    g.setVertexWeight(0, 2.5)
    print(f"  setVertexWeight(0, 2.5) -> getVertexWeight(0) = {g.getVertexWeight(0)}")

    _section("addEdge (idempotente) e hasEdge")
    g.addEdge(0, 1)
    g.addEdge(0, 1)
    print(f"  addEdge(0,1) duas vezes -> hasEdge(0,1)={g.hasEdge(0, 1)}, getEdgeCount()={g.getEdgeCount()}")

    _section("Pesos de arestas")
    g.setEdgeWeight(0, 1, 3.3)
    print(f"  setEdgeWeight(0,1,3.3) -> getEdgeWeight(0,1) = {g.getEdgeWeight(0, 1)}")

    _section("Relações estruturais")
    g.addEdge(0, 2)
    g.addEdge(1, 2)
    g.addEdge(2, 3)
    print(f"  isSucessor(0,1)   = {g.isSucessor(0, 1)}")
    print(f"  isPredessor(0,1)  = {g.isPredessor(0, 1)}")
    print(f"  isDivergent(0,1,0,2) = {g.isDivergent(0, 1, 0, 2)}")
    print(f"  isConvergent(0,2,1,2) = {g.isConvergent(0, 2, 1, 2)}")
    print(f"  isIncident(0,1,0) = {g.isIncident(0, 1, 0)}")
    print(f"  isIncident(0,1,2) = {g.isIncident(0, 1, 2)}")

    _section("Graus")
    print(f"  getVertexOutDegree(0) = {g.getVertexOutDegree(0)}")
    print(f"  getVertexInDegree(2)  = {g.getVertexInDegree(2)}")

    _section("Conectividade")
    print(f"  isConnected() = {g.isConnected()}")

    _section("removeEdge")
    g.removeEdge(0, 2)
    print(f"  removeEdge(0,2) -> hasEdge(0,2)={g.hasEdge(0, 2)}, isConnected()={g.isConnected()}")

    _section("Grafo completo (3 vértices)")
    g_complete = type(g)(3)
    for u in range(3):
        for v in range(3):
            if u != v:
                g_complete.addEdge(u, v)
    print(f"  isCompleteGraph() = {g_complete.isCompleteGraph()}")
    print(f"  getEdgeCount()    = {g_complete.getEdgeCount()} (esperado 6)")

    _section("Exceções esperadas")
    _demo_exception("laço addEdge(0,0)", lambda: g.addEdge(0, 0))
    _demo_exception("índice inválido addEdge(0,99)", lambda: g.addEdge(0, 99))
    _demo_exception("removeEdge inexistente", lambda: g.removeEdge(1, 3))
    _demo_exception("setEdgeWeight sem aresta", lambda: g.setEdgeWeight(1, 3, 1.0))

    _section("exportToGEPHI")
    export_path.parent.mkdir(parents=True, exist_ok=True)
    g.exportToGEPHI(str(export_path))
    size = export_path.stat().st_size
    print(f"  exportToGEPHI('{export_path}') -> {size} bytes")


def main() -> None:
    n = 4
    out1 = Path("gephi_export_adjacency_matrix.graphml")
    out2 = Path("gephi_export_adjacency_list.graphml")

    exercise_graph(AdjacencyMatrixGraph(n), "AdjacencyMatrixGraph", out1)
    exercise_graph(AdjacencyListGraph(n), "AdjacencyListGraph", out2)

    print("\n" + "=" * 60)
    print("Demo finalizada. Arquivos GraphML gerados para o Gephi:")
    print(f"  - {out1}")
    print(f"  - {out2}")
    print("=" * 60)


if __name__ == "__main__":
    main()
