from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Tuple

from graph.abstract_graph import AbstractGraph


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


def _neighbors_out(g: AbstractGraph, u: int) -> List[int]:
    n = g.getVertexCount()
    return [v for v in range(n) if v != u and g.hasEdge(u, v)]


def _neighbors_undirected(g: AbstractGraph, u: int) -> List[int]:
    n = g.getVertexCount()
    nb = set()
    for v in range(n):
        if v == u:
            continue
        if g.hasEdge(u, v) or g.hasEdge(v, u):
            nb.add(v)
    return list(nb)


def _bfs_distances(g: AbstractGraph, source: int, undirected: bool = True) -> Dict[int, int]:
    n = g.getVertexCount()
    dist = {source: 0}
    q: deque[int] = deque([source])
    while q:
        u = q.popleft()
        for v in _neighbors_undirected(g, u) if undirected else _neighbors_out(g, u):
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist


def degree_centrality(g: AbstractGraph) -> Dict[int, float]:
    n = g.getVertexCount()
    if n <= 1:
        return {i: 0.0 for i in range(n)}
    denom = n - 1
    out: Dict[int, float] = {}
    for u in range(n):
        out[u] = g.getVertexOutDegree(u) / denom
    return out


def betweenness_centrality(g: AbstractGraph) -> Dict[int, float]:
    n = g.getVertexCount()
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
            for w in _neighbors_undirected(g, v):
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


def closeness_centrality(g: AbstractGraph) -> Dict[int, float]:
    n = g.getVertexCount()
    out: Dict[int, float] = {}
    for u in range(n):
        dist = _bfs_distances(g, u, undirected=True)
        total = sum(dist.values())
        reachable = len(dist) - 1
        if total == 0 or reachable == 0:
            out[u] = 0.0
        else:
            out[u] = reachable / total
    return out


def pagerank(g: AbstractGraph, damping: float = 0.85, max_iter: int = 100, tol: float = 1e-6) -> Dict[int, float]:
    n = g.getVertexCount()
    if n == 0:
        return {}
    rank = [1.0 / n] * n
    out_w = [0.0] * n
    for u in range(n):
        for v in _neighbors_out(g, u):
            out_w[u] += g.getEdgeWeight(u, v)

    for _ in range(max_iter):
        new = [(1.0 - damping) / n] * n
        for u in range(n):
            if out_w[u] == 0:
                for v in range(n):
                    new[v] += damping * rank[u] / n
                continue
            for v in _neighbors_out(g, u):
                w = g.getEdgeWeight(u, v)
                new[v] += damping * rank[u] * (w / out_w[u])
        diff = sum(abs(new[i] - rank[i]) for i in range(n))
        rank = new
        if diff < tol:
            break
    s = sum(rank) or 1.0
    return {i: rank[i] / s for i in range(n)}


def density(g: AbstractGraph) -> float:
    n = g.getVertexCount()
    if n <= 1:
        return 0.0
    return g.getEdgeCount() / (n * (n - 1))


def global_clustering_coefficient(g: AbstractGraph) -> float:
    n = g.getVertexCount()
    triangles = 0
    triples = 0
    for u in range(n):
        nb = _neighbors_undirected(g, u)
        k = len(nb)
        if k < 2:
            continue
        triples += k * (k - 1) // 2
        for i in range(k):
            for j in range(i + 1, k):
                if g.hasEdge(nb[i], nb[j]) or g.hasEdge(nb[j], nb[i]):
                    triangles += 1
    if triples == 0:
        return 0.0
    return triangles / triples


def degree_assortativity(g: AbstractGraph) -> float:
    """Correlação de Pearson entre graus (entrada+saída) dos extremos das arestas."""
    n = g.getVertexCount()
    deg = [g.getVertexInDegree(i) + g.getVertexOutDegree(i) for i in range(n)]
    xs: List[float] = []
    ys: List[float] = []
    for u in range(n):
        for v in _neighbors_out(g, u):
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


def label_propagation_communities(g: AbstractGraph, max_iter: int = 50) -> Dict[int, int]:
    n = g.getVertexCount()
    label = {i: i for i in range(n)}
    for _ in range(max_iter):
        changed = False
        order = list(range(n))
        order.sort(key=lambda x: len(_neighbors_undirected(g, x)), reverse=True)
        for u in order:
            counts: Dict[int, int] = defaultdict(int)
            for v in _neighbors_undirected(g, u):
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


def modularity(g: AbstractGraph, communities: Dict[int, int]) -> float:
    n = g.getVertexCount()
    m = g.getEdgeCount()
    if m == 0:
        return 0.0
    deg = [g.getVertexInDegree(i) + g.getVertexOutDegree(i) for i in range(n)]
    q = 0.0
    for u in range(n):
        for v in _neighbors_out(g, u):
            if communities[u] == communities[v]:
                q += 1.0 - (deg[u] * deg[v]) / (2.0 * m)
    return q / (2.0 * m)


def bridging_ties(g: AbstractGraph, communities: Dict[int, int], betweenness: Dict[int, float], top_k: int = 5) -> List[int]:
    n = g.getVertexCount()
    scores: List[Tuple[float, int]] = []
    for u in range(n):
        neighbor_comms = {communities[v] for v in _neighbors_undirected(g, u)}
        if len(neighbor_comms) >= 2:
            scores.append((betweenness.get(u, 0.0), u))
    scores.sort(reverse=True)
    return [u for _, u in scores[:top_k]]


def compute_metrics(g: AbstractGraph) -> NetworkMetrics:
    comm = label_propagation_communities(g)
    bet = betweenness_centrality(g)
    return NetworkMetrics(
        degree_centrality=degree_centrality(g),
        betweenness_centrality=bet,
        closeness_centrality=closeness_centrality(g),
        pagerank=pagerank(g),
        density=density(g),
        clustering_coefficient=global_clustering_coefficient(g),
        assortativity=degree_assortativity(g),
        communities=comm,
        modularity=modularity(g, comm),
        bridging_ties=bridging_ties(g, comm, bet),
    )
