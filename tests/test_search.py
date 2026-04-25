import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

import unidecode
from bot import REMOVE_CHARS, search_sounds

SAMPLE_SOUNDS = [
    {"id": 1, "filename": "cuanto_peor.ogg", "text": "Cuanto peor mejor", "tags": "cuanto peor mejor todos"},
    {"id": 2, "filename": "es_el_vecino.ogg", "text": "Es el vecino", "tags": "vecino alcalde"},
    {"id": 3, "filename": "somos.ogg", "text": "Somos sentimientos", "tags": "somos sentimientos humanos"},
    {"id": 4, "filename": "vino.ogg", "text": "Vino aqui", "tags": "vino aqui tinto"},
    {"id": 5, "filename": "divino.ogg", "text": "Divino", "tags": "divino santo"},
]


class TestSearchSounds:
    def test_exact_word_match(self):
        results = search_sounds("vino", SAMPLE_SOUNDS)
        filenames = [r["filename"] for r in results]
        assert "vino.ogg" in filenames

    def test_partial_word_match(self):
        """'vino' should match 'divino' since 'vino' is a substring of 'divino'."""
        results = search_sounds("vino", SAMPLE_SOUNDS)
        filenames = [r["filename"] for r in results]
        assert "divino.ogg" in filenames

    def test_no_match(self):
        results = search_sounds("xyz", SAMPLE_SOUNDS)
        assert len(results) == 0

    def test_multi_word_query(self):
        results = search_sounds("cuanto peor", SAMPLE_SOUNDS)
        assert len(results) == 1
        assert results[0]["filename"] == "cuanto_peor.ogg"

    def test_empty_query(self):
        # Empty queries are routed to query_empty in bot.py; search_sounds itself
        # returns nothing so callers don't accidentally serve everything.
        assert search_sounds("", SAMPLE_SOUNDS) == []
        assert search_sounds("   ", SAMPLE_SOUNDS) == []

    def test_result_limit(self):
        """Ensure results are capped at TELEGRAM_INLINE_MAX_RESULTS, exactly."""
        from bot import TELEGRAM_INLINE_MAX_RESULTS
        many_sounds = [{"id": i, "filename": f"s{i}.ogg", "text": f"Sound {i}", "tags": "common tag"}
                       for i in range(100)]
        results = search_sounds("common", many_sounds)
        assert len(results) == TELEGRAM_INLINE_MAX_RESULTS

    def test_single_character_query(self):
        results = search_sounds("a", SAMPLE_SOUNDS)
        # 'a' is substring of 'alcalde', 'aqui', 'santo'
        assert len(results) >= 1

    def test_all_words_must_match(self):
        """Multi-word query requires ALL words to match in some tag word."""
        results = search_sounds("vino santo", SAMPLE_SOUNDS)
        # 'divino' contains 'vino' and tags include 'santo' -> matches
        assert len(results) == 1
        assert results[0]["filename"] == "divino.ogg"

    def test_multi_word_no_match(self):
        """Multi-word query with no sound matching all words."""
        results = search_sounds("vecino tinto", SAMPLE_SOUNDS)
        assert len(results) == 0


class TestSearchPipeline:
    """Test the full query preprocessing: translate(REMOVE_CHARS) + unidecode + lower."""

    def _preprocess(self, query: str) -> str:
        """Simulate the preprocessing done in bot.py query_text handler."""
        return unidecode.unidecode(query).translate(REMOVE_CHARS).lower()

    def test_punctuation_stripped(self):
        result = self._preprocess("¿Cuánto peor?")
        # unidecode converts ¿ to ? and removes it via translate, á -> a
        assert "cuanto" in result
        assert "peor" in result
        # Whitespace preserved for multi-word matching
        assert " " in result

    def test_accents_normalized(self):
        result = self._preprocess("café")
        assert result == "cafe"

    def test_whitespace_preserved(self):
        """Whitespace must be preserved so multi-word search works."""
        result = self._preprocess("cuanto peor")
        words = result.split()
        assert len(words) == 2

    def test_pipeline_then_search(self):
        """Full pipeline: preprocess query then search."""
        query = "¿Cuánto peor?"
        processed = self._preprocess(query)
        results = search_sounds(processed, SAMPLE_SOUNDS)
        assert len(results) == 1
        assert results[0]["filename"] == "cuanto_peor.ogg"

    def test_remove_chars_only_strips_punctuation(self):
        """Verify REMOVE_CHARS does NOT strip whitespace."""
        test = "hello, world!"
        result = test.translate(REMOVE_CHARS)
        assert result == "hello world"
