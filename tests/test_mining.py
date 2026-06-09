import unittest
from pathlib import Path

from mining.extractor import InteractionExtractor
from mining.graph_factory import build_graphs_from_interactions
from mining.models import Interaction, InteractionType


class MiningTests(unittest.TestCase):
    def test_load_sample_and_build_graphs(self):
        sample = Path(__file__).resolve().parents[1] / "data" / "sample_typer_interactions.json"
        interactions = InteractionExtractor.load_interactions_json(sample)
        self.assertGreaterEqual(len(interactions), 5)

        graph_set = build_graphs_from_interactions(interactions)
        self.assertGreater(graph_set.integrated_graph.getVertexCount(), 0)
        self.assertGreater(graph_set.integrated_graph.getEdgeCount(), 0)
        self.assertGreater(graph_set.comments_graph.getEdgeCount(), 0)

    def test_interaction_types_map_to_graphs(self):
        interactions = [
            Interaction("a", "b", InteractionType.COMMENT),
            Interaction("c", "b", InteractionType.ISSUE_CLOSE),
            Interaction("d", "b", InteractionType.PR_REVIEW),
        ]
        gs = build_graphs_from_interactions(interactions)
        self.assertEqual(gs.comments_graph.getEdgeCount(), 1)
        self.assertEqual(gs.closes_graph.getEdgeCount(), 1)
        self.assertEqual(gs.pr_actions_graph.getEdgeCount(), 1)
        self.assertEqual(gs.integrated_graph.getEdgeCount(), 3)


if __name__ == "__main__":
    unittest.main()
