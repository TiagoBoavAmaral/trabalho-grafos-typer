from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Set, Tuple

from graph.abstract_graph import AbstractGraph
from graph.adjacency_list_graph import AdjacencyListGraph
from graph.adjacency_matrix_graph import AdjacencyMatrixGraph


@dataclass
class NetworkMetrics:
    degree_centrality: Dict[int, float]
    betweenness_centrality: Dict[int, float]
    closeness_centrality: Dict[int, float]
    pagerank: Dict[int, float]
    density: float
    clustering_coefficient: float
    assortativity: float
    communities: Dict[int, int]
    modularity: float
    bridging_ties: List[int]


@dataclass
class _GraphIndex:
    """Índices de adjacência pré-computados para evitar varreduras O(n) repetidas."""

    n: int
    edge_count: int
    out_neighbors: List[List[int]]
    undirected_neighbors: List[List[int]]
    undirected_sets: List[Set[int]]
    out_edges: List[List[Tuple[int, float]]]
    total_degree: List[int]

    @classmethod
    def from_graph(cls, g: AbstractGraph) -> _GraphIndex:
        n = g.getVertexCount()
        out_neighbors = cls._build_out_neighbors(g, n)
        undirected_neighbors, undirected_sets = cls._build_undirected(out_neighbors, n)
        out_edges: List[List[Tuple[int, float]]] = []
        total_degree = [0] * n

        for u in range(n):
            edges = [(v, g.getEdgeWeight(u, v)) for v in out_neighbors[u]]
            out_edges.append(edges)
            total_degree[u] = g.getVertexInDegree(u) + g.getVertexOutDegree(u)

        return cls(
            n=n,
            edge_count=g.getEdgeCount(),
            out_neighbors=out_neighbors,
            undirected_neighbors=undirected_neighbors,
            undirected_sets=undirected_sets,
            out_edges=out_edges,
            total_degree=total_degree,
        )

    @staticmethod
    def _build_out_neighbors(g: AbstractGraph, n: int) -> List[List[int]]:
        if isinstance(g, AdjacencyListGraph):
            return [list(g._adj[u].keys()) for u in range(n)]
        if isinstance(g, AdjacencyMatrixGraph):
            return [[v for v in range(n) if g._adj[u][v]] for u in range(n)]
        return [[v for v in range(n) if v != u and g.hasEdge(u, v)] for u in range(n)]

    @staticmethod
    def _build_undirected(
        out_neighbors: List[List[int]], n: int
    ) -> Tuple[List[List[int]], List[Set[int]]]:
        undirected_sets: List[Set[int]] = [set() for _ in range(n)]
        for u in range(n):
            for v in out_neighbors[u]:
                undirected_sets[u].add(v)
                undirected_sets[v].add(u)
        undirected_neighbors = [sorted(s) for s in undirected_sets]
        return undirected_neighbors, undirected_sets


def _bfs_distances(idx: _GraphIndex, source: int, undirected: bool = True) -> Dict[int, int]:
    dist = {source: 0}
    q: deque[int] = deque([source])
    neighbors = idx.undirected_neighbors if undirected else idx.out_neighbors
    while q:
        u = q.popleft()
        for v in neighbors[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist


def degree_centrality(idx: _GraphIndex) -> Dict[int, float]:
    n = idx.n
    if n <= 1:
        return {i: 0.0 for i in range(n)}
    denom = n - 1
    return {u: len(idx.out_neighbors[u]) / denom for u in range(n)}


def betweenness_centrality(idx: _GraphIndex) -> Dict[int, float]:
    n = idx.n
    neighbors = idx.undirected_neighbors
    cb = [0.0] * n
    for s in range(n):
        stack: List[int] = []
        pred: List[List[int]] = [[] for _ in range(n)]
        sigma = [0.0] * n
        sigma[s] = 1.0
        dist = [-1] * n
        dist[s] = 0
        q: deque[int] = deque([s])
        while q:
            v = q.popleft()
            stack.append(v)
            for w in neighbors[v]:
                if dist[w] < 0:
                    dist[w] = dist[v] + 1
                    q.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    pred[w].append(v)
        delta = [0.0] * n
        while stack:
            w = stack.pop()
            for v in pred[w]:
                if sigma[w] > 0:
                    delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])
            if w != s:
                cb[w] += delta[w]
    scale = 2.0 / ((n - 1) * (n - 2)) if n > 2 else 1.0
    return {i: cb[i] * scale for i in range(n)}


def closeness_centrality(idx: _GraphIndex) -> Dict[int, float]:
    n = idx.n
    out: Dict[int, float] = {}
    for u in range(n):
        dist = _bfs_distances(idx, u, undirected=True)
        total = sum(dist.values())
        reachable = len(dist) - 1
        if total == 0 or reachable == 0:
            out[u] = 0.0
        else:
            out[u] = reachable / total
    return out


def pagerank(
    idx: _GraphIndex, damping: float = 0.85, max_iter: int = 100, tol: float = 1e-6
) -> Dict[int, float]:
    n = idx.n
    if n == 0:
        return {}
    rank = [1.0 / n] * n
    out_w = [sum(w for _, w in edges) for edges in idx.out_edges]

    for _ in range(max_iter):
        new = [(1.0 - damping) / n] * n
        for u in range(n):
            if out_w[u] == 0:
                share = damping * rank[u] / n
                for v in range(n):
                    new[v] += share
                continue
            for v, w in idx.out_edges[u]:
                new[v] += damping * rank[u] * (w / out_w[u])
        diff = sum(abs(new[i] - rank[i]) for i in range(n))
        rank = new
        if diff < tol:
            break
    s = sum(rank) or 1.0
    return {i: rank[i] / s for i in range(n)}


def density(idx: _GraphIndex) -> float:
    n = idx.n
    if n <= 1:
        return 0.0
    return idx.edge_count / (n * (n - 1))


def global_clustering_coefficient(idx: _GraphIndex) -> float:
    triangles = 0
    triples = 0
    neighbor_sets = idx.undirected_sets
    for u in range(idx.n):
        nb = idx.undirected_neighbors[u]
        k = len(nb)
        if k < 2:
            continue
        triples += k * (k - 1) // 2
        for i in range(k):
            for j in range(i + 1, k):
                if nb[j] in neighbor_sets[nb[i]]:
                    triangles += 1
    if triples == 0:
        return 0.0
    return triangles / triples


def degree_assortativity(idx: _GraphIndex) -> float:
    """Correlação de Pearson entre graus (entrada+saída) dos extremos das arestas."""
    deg = idx.total_degree
    xs: List[float] = []
    ys: List[float] = []
    for u in range(idx.n):
        for v in idx.out_neighbors[u]:
            xs.append(float(deg[u]))
            ys.append(float(deg[v]))
    if len(xs) < 2:
        return 0.0
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    num = sum((xs[i] - mx) * (ys[i] - my) for i in range(len(xs)))
    den_x = sum((x - mx) ** 2 for x in xs) ** 0.5
    den_y = sum((y - my) ** 2 for y in ys) ** 0.5
    if den_x == 0 or den_y == 0:
        return 0.0
    return num / (den_x * den_y)


def label_propagation_communities(idx: _GraphIndex, max_iter: int = 50) -> Dict[int, int]:
    n = idx.n
    label = {i: i for i in range(n)}
    neighbor_degrees = [len(idx.undirected_neighbors[u]) for u in range(n)]
    for _ in range(max_iter):
        changed = False
        order = list(range(n))
        order.sort(key=lambda x: neighbor_degrees[x], reverse=True)
        for u in order:
            counts: Dict[int, int] = defaultdict(int)
            for v in idx.undirected_neighbors[u]:
                counts[label[v]] += 1
            if not counts:
                continue
            best = max(counts.items(), key=lambda kv: kv[1])[0]
            if label[u] != best:
                label[u] = best
                changed = True
        if not changed:
            break
    return label


def modularity(idx: _GraphIndex, communities: Dict[int, int]) -> float:
    m = idx.edge_count
    if m == 0:
        return 0.0
    deg = idx.total_degree
    q = 0.0
    for u in range(idx.n):
        for v in idx.out_neighbors[u]:
            if communities[u] == communities[v]:
                q += 1.0 - (deg[u] * deg[v]) / (2.0 * m)
    return q / (2.0 * m)


def bridging_ties(
    idx: _GraphIndex,
    communities: Dict[int, int],
    betweenness: Dict[int, float],
    top_k: int = 5,
) -> List[int]:
    scores: List[Tuple[float, int]] = []
    for u in range(idx.n):
        neighbor_comms = {communities[v] for v in idx.undirected_neighbors[u]}
        if len(neighbor_comms) >= 2:
            scores.append((betweenness.get(u, 0.0), u))
    scores.sort(reverse=True)
    return [u for _, u in scores[:top_k]]


def compute_metrics(
    g: AbstractGraph,
    *,
    verbose: bool = False,
    progress: Optional[Callable[[str], None]] = None,
) -> NetworkMetrics:
    def log(msg: str) -> None:
        if progress is not None:
            progress(msg)
        elif verbose:
            print(msg, flush=True)

    log("  Indexando adjacências do grafo...")
    idx = _GraphIndex.from_graph(g)
    log(f"  Grafo: {idx.n} vértices, {idx.edge_count} arestas")

    log("  Degree centrality...")
    deg = degree_centrality(idx)

    log("  Comunidades (label propagation)...")
    comm = label_propagation_communities(idx)

    log("  Betweenness centrality...")
    bet = betweenness_centrality(idx)

    log("  Closeness centrality...")
    close = closeness_centrality(idx)

    log("  PageRank...")
    pr = pagerank(idx)

    log("  Densidade, clustering e assortatividade...")
    dens = density(idx)
    clust = global_clustering_coefficient(idx)
    assort = degree_assortativity(idx)

    log("  Modularidade e bridging ties...")
    mod = modularity(idx, comm)
    bridges = bridging_ties(idx, comm, bet)

    log("  Métricas concluídas.")
    return NetworkMetrics(
        degree_centrality=deg,
        betweenness_centrality=bet,
        closeness_centrality=close,
        pagerank=pr,
        density=dens,
        clustering_coefficient=clust,
        assortativity=assort,
        communities=comm,
        modularity=mod,
        bridging_ties=bridges,
    )
