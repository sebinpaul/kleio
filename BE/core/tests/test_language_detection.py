from types import SimpleNamespace

from django.test import SimpleTestCase

from core.services.language_detection import MIN_DETECT_LENGTH, detect_language
from core.services.matching_engine import GenericMatchingEngine, MatchContext


class LanguageDetectionTests(SimpleTestCase):
    def test_returns_empty_for_short_text(self):
        self.assertEqual(detect_language("too short"), "")
        self.assertEqual(detect_language(" " * MIN_DETECT_LENGTH), "")

    def test_detects_english(self):
        text = "This is a longer English sentence used for language detection."
        self.assertEqual(detect_language(text), "en")

    def test_detects_spanish(self):
        text = "Este es un texto más largo en español para probar la detección automática."
        self.assertEqual(detect_language(text), "es")


class MatchingEngineLanguageFilterTests(SimpleTestCase):
    def setUp(self):
        self.engine = GenericMatchingEngine()

    def _keyword(self, **overrides):
        defaults = {
            "keyword": "python",
            "content_types": ["body"],
            "case_sensitive": False,
            "match_mode": "contains",
            "included_languages": [],
            "excluded_languages": [],
        }
        defaults.update(overrides)
        return SimpleNamespace(**defaults)

    def test_included_language_allows_match(self):
        keyword = self._keyword(included_languages=["en"])
        content = "I really enjoy learning python programming every single day."
        result = self.engine.should_create_mention(
            keyword,
            content,
            "body",
            MatchContext(),
        )
        self.assertTrue(result)

    def test_included_language_blocks_other_language(self):
        keyword = self._keyword(included_languages=["en"])
        content = "Me encanta programar en python todos los días sin parar."
        result = self.engine.should_create_mention(
            keyword,
            content,
            "body",
            MatchContext(),
        )
        self.assertFalse(result)

    def test_excluded_language_blocks_match(self):
        keyword = self._keyword(excluded_languages=["es"])
        content = "Me encanta programar en python todos los días sin parar."
        result = self.engine.should_create_mention(
            keyword,
            content,
            "body",
            MatchContext(),
        )
        self.assertFalse(result)

    def test_included_language_blocks_when_text_too_short_to_detect(self):
        keyword = self._keyword(included_languages=["en"])
        result = self.engine.should_create_mention(
            keyword,
            "python!",
            "body",
            MatchContext(),
        )
        self.assertFalse(result)

    def test_no_language_filters_skips_detection(self):
        keyword = self._keyword()
        result = self.engine.should_create_mention(
            keyword,
            "python!",
            "body",
            MatchContext(),
        )
        self.assertTrue(result)
