import unittest

from analysis.metrics import compute_metrics
from graph import AdjacencyListGraph
from graph.utils import add_or_accumulate_edge


class MetricsTests(unittest.TestCase):
    def test_metrics_on_small_graph(self):
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
        self.assertEqual(len(m.communities), 4)


if __name__ == "__main__":
    unittest.main()
