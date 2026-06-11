import unittest
from unittest.mock import MagicMock

from mining.extractor import InteractionExtractor
from mining.graph_factory import build_graphs_from_interactions
from mining.models import Interaction, InteractionType


class ExtractorMockTests(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.extractor = InteractionExtractor(client=self.client)

    def test_issue_comment_generates_comment_and_issue_open_commented(self):
        self.client.fetch_issue_comments.return_value = [
            {"user": {"login": "bob"}},
        ]
        self.client.fetch_issue_events.return_value = []

        issue = {"number": 10, "user": {"login": "alice"}}
        interactions = self.extractor._extract_issue_interactions("org", "repo", issue)

        kinds = [i.kind for i in interactions]
        self.assertEqual(kinds.count(InteractionType.COMMENT), 1)
        self.assertEqual(kinds.count(InteractionType.ISSUE_OPEN_COMMENTED), 1)
        self.assertEqual(interactions[0].source, "bob")
        self.assertEqual(interactions[0].target, "alice")

    def test_issue_comment_ignores_self_comment(self):
        self.client.fetch_issue_comments.return_value = [
            {"user": {"login": "alice"}},
        ]
        self.client.fetch_issue_events.return_value = []

        issue = {"number": 10, "user": {"login": "alice"}}
        interactions = self.extractor._extract_issue_interactions("org", "repo", issue)
        self.assertEqual(interactions, [])

    def test_issue_close_event(self):
        self.client.fetch_issue_comments.return_value = []
        self.client.fetch_issue_events.return_value = [
            {"event": "closed", "actor": {"login": "closer"}},
        ]

        issue = {"number": 11, "user": {"login": "author"}}
        interactions = self.extractor._extract_issue_interactions("org", "repo", issue)

        self.assertEqual(len(interactions), 1)
        self.assertEqual(interactions[0].kind, InteractionType.ISSUE_CLOSE)
        self.assertEqual(interactions[0].source, "closer")
        self.assertEqual(interactions[0].target, "author")

    def test_pr_comment_generates_only_comment(self):
        self.client.fetch_pr_comments.return_value = [
            {"user": {"login": "reviewer"}},
        ]
        self.client.fetch_pr_reviews.return_value = []

        pr = {"number": 20, "user": {"login": "author"}, "merged_at": None}
        interactions = self.extractor._extract_pr_interactions("org", "repo", pr)

        self.assertEqual(len(interactions), 1)
        self.assertEqual(interactions[0].kind, InteractionType.COMMENT)
        self.assertNotIn(InteractionType.ISSUE_OPEN_COMMENTED, [i.kind for i in interactions])

    def test_pr_review_approved(self):
        self.client.fetch_pr_comments.return_value = []
        self.client.fetch_pr_reviews.return_value = [
            {"user": {"login": "rev"}, "state": "APPROVED"},
        ]

        pr = {"number": 21, "user": {"login": "author"}, "merged_at": None}
        interactions = self.extractor._extract_pr_interactions("org", "repo", pr)

        self.assertEqual(len(interactions), 1)
        self.assertEqual(interactions[0].kind, InteractionType.PR_REVIEW)

    def test_pr_merge(self):
        self.client.fetch_pr_comments.return_value = []
        self.client.fetch_pr_reviews.return_value = []

        pr = {
            "number": 22,
            "user": {"login": "author"},
            "merged_at": "2024-01-01T00:00:00Z",
            "merged_by": {"login": "merger"},
        }
        interactions = self.extractor._extract_pr_interactions("org", "repo", pr)

        self.assertEqual(len(interactions), 1)
        self.assertEqual(interactions[0].kind, InteractionType.PR_MERGE)
        self.assertEqual(interactions[0].source, "merger")

    def test_issue_without_author_returns_empty(self):
        self.client.fetch_issue_comments.return_value = [{"user": {"login": "bob"}}]
        self.client.fetch_issue_events.return_value = []

        issue = {"number": 1, "user": None}
        interactions = self.extractor._extract_issue_interactions("org", "repo", issue)
        self.assertEqual(interactions, [])


class GraphFactoryWeightTests(unittest.TestCase):
    def test_integrated_weights_accumulate_on_same_edge(self):
        interactions = [
            Interaction("a", "b", InteractionType.COMMENT),
            Interaction("a", "b", InteractionType.ISSUE_OPEN_COMMENTED),
        ]
        gs = build_graphs_from_interactions(interactions)
        self.assertEqual(gs.integrated_graph.getEdgeCount(), 1)
        self.assertAlmostEqual(gs.integrated_graph.getEdgeWeight(0, 1), 5.0)

    def test_integrated_weight_per_kind(self):
        interactions = [
            Interaction("a", "b", InteractionType.PR_MERGE),
            Interaction("c", "b", InteractionType.PR_REVIEW),
            Interaction("d", "b", InteractionType.COMMENT),
        ]
        gs = build_graphs_from_interactions(interactions)
        idx = gs.user_index
        self.assertAlmostEqual(
            gs.integrated_graph.getEdgeWeight(idx["a"], idx["b"]), 5.0
        )
        self.assertAlmostEqual(
            gs.integrated_graph.getEdgeWeight(idx["c"], idx["b"]), 4.0
        )
        self.assertAlmostEqual(
            gs.integrated_graph.getEdgeWeight(idx["d"], idx["b"]), 2.0
        )


if __name__ == "__main__":
    unittest.main()
