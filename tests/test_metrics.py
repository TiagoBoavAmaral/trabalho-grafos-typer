import unittest

from analysis.metrics import (
    betweenness_centrality,
    compute_metrics,
    degree_centrality,
    density,
    eigenvector_centrality,
    pagerank,
    _GraphIndex,
)
from graph import AdjacencyListGraph
from graph.utils import add_or_accumulate_edge


class MetricsTests(unittest.TestCase):
    def _index(self, g: AdjacencyListGraph) -> _GraphIndex:
        return _GraphIndex.from_graph(g)

    def test_density_directed_triangle(self):
        g = AdjacencyListGraph(3)
        g.addEdge(0, 1)
        g.addEdge(1, 2)
        g.addEdge(2, 0)
        self.assertAlmostEqual(density(self._index(g)), 3 / 6)

    def test_degree_centrality_star_out(self):
        g = AdjacencyListGraph(4)
        g.addEdge(0, 1)
        g.addEdge(0, 2)
        g.addEdge(0, 3)
        deg = degree_centrality(self._index(g))
        self.assertAlmostEqual(deg[0], 1.0)
        self.assertAlmostEqual(deg[1], 0.0)

    def test_eigenvector_star_center_highest(self):
        g = AdjacencyListGraph(4)
        g.addEdge(0, 1)
        g.addEdge(0, 2)
        g.addEdge(0, 3)
        eig = eigenvector_centrality(self._index(g))
        self.assertGreater(eig[0], eig[1])
        self.assertGreater(eig[0], eig[2])
        self.assertGreater(eig[0], eig[3])

    def test_pagerank_positive_and_normalized(self):
        g = AdjacencyListGraph(3)
        g.addEdge(0, 1)
        g.addEdge(1, 2)
        g.addEdge(2, 0)
        pr = pagerank(self._index(g))
        self.assertAlmostEqual(sum(pr.values()), 1.0, places=5)
        self.assertTrue(all(v > 0 for v in pr.values()))

    def test_betweenness_path_middle_highest(self):
        g = AdjacencyListGraph(3)
        g.addEdge(0, 1)
        g.addEdge(1, 2)
        bet = betweenness_centrality(self._index(g))
        self.assertGreater(bet[1], bet[0])
        self.assertGreater(bet[1], bet[2])

    def test_compute_metrics_includes_eigenvector(self):
        g = AdjacencyListGraph(4)
        add_or_accumulate_edge(g, 0, 1, 2)
        add_or_accumulate_edge(g, 1, 2, 3)
        add_or_accumulate_edge(g, 2, 3, 1)
        add_or_accumulate_edge(g, 0, 3, 1)

        m = compute_metrics(g)
        self.assertGreaterEqual(m.density, 0.0)
        self.assertLessEqual(m.density, 1.0)
        self.assertEqual(len(m.degree_centrality), 4)
        self.assertEqual(len(m.pagerank), 4)
        self.assertEqual(len(m.eigenvector_centrality), 4)
        self.assertEqual(len(m.communities), 4)
        self.assertTrue(all(v >= 0 for v in m.eigenvector_centrality.values()))
        self.assertGreater(sum(m.eigenvector_centrality.values()), 0.0)


if __name__ == "__main__":
    unittest.main()
