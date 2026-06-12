# Testes para a funcionalidade de cache do extrator de interações, garantindo que o cache seja carregado corretamente quando válido e rejeitado quando inválido.

import json
import tempfile
import unittest
from pathlib import Path

from mining.extractor import InteractionExtractor
from mining.models import Interaction, InteractionType


class CacheTests(unittest.TestCase):
    def test_load_cache_if_valid_matches_meta(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "interactions_cache.json"
            interactions = [
                Interaction("a", "b", InteractionType.COMMENT, "issue#1"),
                Interaction("c", "b", InteractionType.ISSUE_CLOSE, "issue#2"),
            ]
            InteractionExtractor.save_interactions_json(cache, interactions)
            InteractionExtractor.save_cache_meta(cache, "fastapi/typer", 0, 0, len(interactions))

            loaded = InteractionExtractor.load_cache_if_valid(cache, "fastapi/typer", 0, 0)
            self.assertIsNotNone(loaded)
            self.assertEqual(len(loaded), 2)

    def test_load_cache_if_valid_rejects_mismatched_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "interactions_cache.json"
            InteractionExtractor.save_interactions_json(
                cache, [Interaction("a", "b", InteractionType.COMMENT)]
            )
            InteractionExtractor.save_cache_meta(cache, "fastapi/typer", 0, 0, 1)

            loaded = InteractionExtractor.load_cache_if_valid(cache, "other/repo", 0, 0)
            self.assertIsNone(loaded)

    def test_load_cache_if_valid_requires_meta_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "interactions_cache.json"
            cache.write_text(json.dumps([]), encoding="utf-8")
            self.assertIsNone(InteractionExtractor.load_cache_if_valid(cache, "fastapi/typer", 0, 0))


if __name__ == "__main__":
    unittest.main()
