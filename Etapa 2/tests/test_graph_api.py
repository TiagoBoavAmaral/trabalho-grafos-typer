import tempfile
import unittest
from pathlib import Path

from graph import AdjacencyListGraph, AdjacencyMatrixGraph


def export_and_check(graph) -> None:
    with tempfile.TemporaryDirectory() as td:
        out_path = Path(td) / "graph.graphml"
        graph.exportToGEPHI(str(out_path))
        assert out_path.exists()
        assert out_path.stat().st_size > 0


class GraphAPITestMixin:
    GraphClass = None

    def setUp(self):
        assert self.GraphClass is not None
        self.g = self.GraphClass(4)

    def test_add_edge_idempotent_and_counts(self):
        self.assertEqual(self.g.getEdgeCount(), 0)
        self.assertFalse(self.g.hasEdge(0, 1))

        self.g.addEdge(0, 1)
        self.assertTrue(self.g.hasEdge(0, 1))
        self.assertEqual(self.g.getEdgeCount(), 1)

        self.g.addEdge(0, 1)
        self.assertEqual(self.g.getEdgeCount(), 1)

    def test_remove_edge_inconsistent_raises(self):
        with self.assertRaises(ValueError):
            self.g.removeEdge(0, 1)

        self.g.addEdge(0, 1)
        self.g.removeEdge(0, 1)
        self.assertFalse(self.g.hasEdge(0, 1))

    def test_disallow_self_loops(self):
        with self.assertRaises(ValueError):
            self.g.addEdge(0, 0)

    def test_set_get_vertex_weights(self):
        self.g.setVertexWeight(2, 7.7)
        self.assertAlmostEqual(self.g.getVertexWeight(2), 7.7)

    def test_set_get_edge_weights_only_if_edge_exists(self):
        with self.assertRaises(ValueError):
            self.g.setEdgeWeight(0, 1, 1.1)

        self.g.addEdge(0, 1)
        self.g.setEdgeWeight(0, 1, 1.1)
        self.assertAlmostEqual(self.g.getEdgeWeight(0, 1), 1.1)

        with self.assertRaises(ValueError):
            self.g.getEdgeWeight(1, 0)

    def test_structural_relations(self):
        # Se os arcos não existem, as relações estruturais devem ser falsas.
        self.assertFalse(self.g.isDivergent(0, 1, 0, 2))
        self.assertFalse(self.g.isConvergent(0, 1, 2, 1))
        self.assertFalse(self.g.isIncident(0, 1, 0))

    def test_isSucessor_isPredessor(self):
        self.g.addEdge(0, 1)
        self.assertTrue(self.g.isSucessor(0, 1))
        self.assertFalse(self.g.isPredessor(0, 1))

        self.g.addEdge(2, 0)
        self.assertTrue(self.g.isPredessor(0, 2))  # (2,0) => predecessor de 0 é 2

    def test_isDivergent_isConvergent_isIncident(self):
        self.g.addEdge(0, 1)
        self.g.addEdge(0, 2)
        self.g.addEdge(3, 2)

        self.assertTrue(self.g.isDivergent(0, 1, 0, 2))
        self.assertFalse(self.g.isDivergent(0, 1, 1, 2))  # u diferente

        self.assertTrue(self.g.isConvergent(0, 2, 3, 2))
        self.assertFalse(self.g.isConvergent(0, 1, 3, 2))

        self.assertTrue(self.g.isIncident(0, 1, 0))
        self.assertTrue(self.g.isIncident(0, 1, 1))
        self.assertFalse(self.g.isIncident(0, 1, 2))

    def test_degrees(self):
        # 0->1, 0->2, 1->2
        self.g.addEdge(0, 1)
        self.g.addEdge(0, 2)
        self.g.addEdge(1, 2)

        self.assertEqual(self.g.getVertexOutDegree(0), 2)
        self.assertEqual(self.g.getVertexInDegree(2), 2)  # 0->2 e 1->2

    def test_isConnected_weak(self):
        # Caso desconectado: 0--1 , 2 isolado
        self.g.addEdge(0, 1)
        self.assertFalse(self.g.isConnected())

        # Conecta 2 via 1->2 e conecta o restante via 2->3
        self.g.addEdge(1, 2)
        self.g.addEdge(2, 3)
        self.assertTrue(self.g.isConnected())

    def test_empty_and_complete_graph(self):
        self.assertTrue(self.g.isEmptyGraph())
        self.assertFalse(self.g.isCompleteGraph())

        n = self.g.getVertexCount()
        # Complete dirigido: para todo u!=v
        for u in range(n):
            for v in range(n):
                if u != v:
                    self.g.addEdge(u, v)
        self.assertTrue(self.g.isCompleteGraph())
        self.assertEqual(self.g.getEdgeCount(), n * (n - 1))

    def test_exportToGEPHI_graphml(self):
        self.g.addEdge(0, 1)
        self.g.setVertexWeight(0, 1.5)
        self.g.setEdgeWeight(0, 1, 2.5)
        export_and_check(self.g)

    def test_getVertexCount(self):
        self.assertEqual(self.g.getVertexCount(), 4)

    def test_invalid_vertex_index_raises(self):
        for method, args in (
            (self.g.hasEdge, (-1, 0)),
            (self.g.hasEdge, (0, 4)),
            (self.g.addEdge, (0, 5)),
            (self.g.removeEdge, (3, -1)),
            (self.g.getVertexInDegree, (4,)),
            (self.g.getVertexOutDegree, (-1,)),
            (self.g.setVertexWeight, (4, 1.0)),
            (self.g.getVertexWeight, (-1,)),
            (self.g.isSucessor, (0, 4)),
            (self.g.isPredessor, (4, 0)),
            (self.g.isIncident, (0, 1, 4)),
        ):
            with self.subTest(method=method.__name__, args=args):
                with self.assertRaises(IndexError):
                    method(*args)

    def test_invalid_edge_index_on_weight_ops_raises(self):
        self.g.addEdge(0, 1)
        with self.assertRaises(IndexError):
            self.g.setEdgeWeight(0, 4, 1.0)
        with self.assertRaises(IndexError):
            self.g.getEdgeWeight(4, 1)

    def test_invalid_vertex_type_raises(self):
        with self.assertRaises(TypeError):
            self.g.addEdge(0.5, 1)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            self.g.setVertexWeight(0, "x")  # type: ignore[arg-type]

    def test_invalid_num_vertices_constructor(self):
        with self.assertRaises(ValueError):
            self.GraphClass(0)
        with self.assertRaises(ValueError):
            self.GraphClass(-1)
        with self.assertRaises(TypeError):
            self.GraphClass(3.5)  # type: ignore[arg-type]


class AdjacencyMatrixGraphAPITest(GraphAPITestMixin, unittest.TestCase):
    GraphClass = AdjacencyMatrixGraph


class AdjacencyListGraphAPITest(GraphAPITestMixin, unittest.TestCase):
    GraphClass = AdjacencyListGraph

