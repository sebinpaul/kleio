"""
Filter and matching tests for platform monitoring.

Each platform monitor builds a MatchContext and calls GenericMatchingEngine.should_create_mention.
These tests mirror that wiring so filter behavior can be verified without live API calls.
"""

from types import SimpleNamespace

from django.test import SimpleTestCase

from core.enums import ContentType, MatchMode, Platform
from core.services.matching_engine import GenericMatchingEngine, MatchContext


def keyword(**overrides):
    """Lightweight Keyword stand-in for matching-engine tests."""
    defaults = {
        "keyword": "kleio",
        "content_types": [
            ContentType.TITLES.value,
            ContentType.BODY.value,
            ContentType.COMMENTS.value,
        ],
        "case_sensitive": False,
        "match_mode": MatchMode.CONTAINS.value,
        "platform_specific_filters": [],
        "excluded_keywords": [],
        "excluded_subreddits": [],
        "included_users": [],
        "excluded_users": [],
        "included_languages": [],
        "excluded_languages": [],
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class MonitoringTestMixin:
    engine = GenericMatchingEngine()

    def assert_matches(self, kw, content, content_type, context, msg="expected match"):
        result = self.engine.should_create_mention(kw, content, content_type, context)
        self.assertTrue(bool(result), msg)

    def assert_no_match(self, kw, content, content_type, context, msg="expected no match"):
        result = self.engine.should_create_mention(kw, content, content_type, context)
        self.assertFalse(bool(result), msg)


class RedditMonitoringFilterTests(MonitoringTestMixin, SimpleTestCase):
    """Reddit realtime monitor: MatchContext(author, subreddit)."""

    def _ctx(self, *, author="alice", subreddit="python"):
        return MatchContext(author=author, subreddit=subreddit)

    def test_title_match_default(self):
        self.assert_matches(
            keyword(),
            "Discussion about kleio monitoring tools",
            ContentType.TITLES.value,
            self._ctx(),
        )

    def test_comment_match(self):
        self.assert_matches(
            keyword(content_types=[ContentType.COMMENTS.value]),
            "I use kleio every day for alerts",
            ContentType.COMMENTS.value,
            self._ctx(subreddit="startups"),
        )

    def test_skips_unmonitored_content_type(self):
        self.assert_no_match(
            keyword(content_types=[ContentType.TITLES.value]),
            "kleio in a comment body",
            ContentType.COMMENTS.value,
            self._ctx(),
            "comments not in content_types",
        )

    def test_excluded_subreddit_blocks_match(self):
        self.assert_no_match(
            keyword(excluded_subreddits=["spam"]),
            "kleio launch thread",
            ContentType.TITLES.value,
            self._ctx(subreddit="spam"),
        )

    def test_excluded_subreddit_normalizes_r_prefix(self):
        self.assert_no_match(
            keyword(excluded_subreddits=["r/spam"]),
            "kleio thread",
            ContentType.TITLES.value,
            self._ctx(subreddit="spam"),
        )

    def test_included_user_allows_listed_author(self):
        self.assert_matches(
            keyword(included_users=["alice"]),
            "kleio update",
            ContentType.TITLES.value,
            self._ctx(author="alice"),
        )

    def test_included_user_blocks_other_authors(self):
        self.assert_no_match(
            keyword(included_users=["alice"]),
            "kleio update",
            ContentType.TITLES.value,
            self._ctx(author="bob"),
        )

    def test_excluded_user_blocks_author(self):
        self.assert_no_match(
            keyword(excluded_users=["spammer"]),
            "kleio mention",
            ContentType.TITLES.value,
            self._ctx(author="spammer"),
        )

    def test_excluded_keyword_suppresses_match(self):
        self.assert_no_match(
            keyword(excluded_keywords=["giveaway"]),
            "kleio giveaway event today",
            ContentType.BODY.value,
            self._ctx(),
        )

    def test_word_boundary_rejects_partial_word(self):
        self.assert_no_match(
            keyword(match_mode=MatchMode.WORD_BOUNDARY.value),
            "kleiomatic tools are great",
            ContentType.BODY.value,
            self._ctx(),
        )

    def test_word_boundary_accepts_whole_word(self):
        self.assert_matches(
            keyword(match_mode=MatchMode.WORD_BOUNDARY.value),
            "We launched kleio yesterday",
            ContentType.BODY.value,
            self._ctx(),
        )

    def test_case_sensitive_requires_exact_casing(self):
        self.assert_no_match(
            keyword(case_sensitive=True, keyword="Kleio"),
            "discussion about kleio",
            ContentType.TITLES.value,
            self._ctx(),
        )

    def test_included_language_blocks_non_english(self):
        self.assert_no_match(
            keyword(included_languages=["en"]),
            "Me encanta usar kleio para monitorear menciones en español cada día.",
            ContentType.BODY.value,
            self._ctx(),
        )


class HackerNewsMonitoringFilterTests(MonitoringTestMixin, SimpleTestCase):
    """HN service: MatchContext(author) only — no platform source filters at match time."""

    def _ctx(self, *, author="pg"):
        return MatchContext(author=author)

    def test_story_title_match(self):
        self.assert_matches(
            keyword(),
            "Show HN: kleio – social mention monitoring",
            ContentType.TITLES.value,
            self._ctx(),
        )

    def test_story_url_body_match(self):
        self.assert_matches(
            keyword(content_types=[ContentType.BODY.value]),
            "https://example.com/kleio-release",
            ContentType.BODY.value,
            self._ctx(),
        )

    def test_comment_match(self):
        self.assert_matches(
            keyword(content_types=[ContentType.COMMENTS.value]),
            "We switched to kleio last month",
            ContentType.COMMENTS.value,
            self._ctx(author="dang"),
        )

    def test_included_user_filter(self):
        self.assert_matches(
            keyword(included_users=["pg"]),
            "kleio on the front page",
            ContentType.TITLES.value,
            self._ctx(author="pg"),
        )

    def test_excluded_user_filter(self):
        self.assert_no_match(
            keyword(excluded_users=["bot_account"]),
            "kleio automated post",
            ContentType.TITLES.value,
            self._ctx(author="bot_account"),
        )

    def test_platform_filters_ignored_without_source_label(self):
        """HN monitor does not set source_label; subreddit-style filters do not apply here."""
        self.assert_matches(
            keyword(platform_specific_filters=["showhn"]),
            "kleio is useful",
            ContentType.TITLES.value,
            self._ctx(),
        )


class TwitterMonitoringFilterTests(MonitoringTestMixin, SimpleTestCase):
    """Twitter service: MatchContext(author, source_label=author)."""

    def _ctx(self, *, author="brand"):
        return MatchContext(author=author, source_label=author)

    def test_tweet_body_match(self):
        self.assert_matches(
            keyword(content_types=[ContentType.BODY.value]),
            "Excited to share kleio updates with everyone today!",
            ContentType.BODY.value,
            self._ctx(),
        )

    def test_platform_filter_allows_listed_handle(self):
        self.assert_matches(
            keyword(platform_specific_filters=["brand"]),
            "kleio launch tweet",
            ContentType.BODY.value,
            self._ctx(author="brand"),
        )

    def test_platform_filter_blocks_other_handles(self):
        self.assert_no_match(
            keyword(platform_specific_filters=["brand"]),
            "kleio mention from random account",
            ContentType.BODY.value,
            self._ctx(author="random"),
        )

    def test_platform_filter_normalizes_at_prefix(self):
        self.assert_matches(
            keyword(platform_specific_filters=["@brand"]),
            "kleio news",
            ContentType.BODY.value,
            self._ctx(author="brand"),
        )

    def test_included_users_and_platform_filter_both_apply(self):
        self.assert_no_match(
            keyword(platform_specific_filters=["brand"], included_users=["ceo"]),
            "kleio post",
            ContentType.BODY.value,
            self._ctx(author="brand"),
            "author not in included_users",
        )

    def test_excluded_keyword_on_tweet(self):
        self.assert_no_match(
            keyword(excluded_keywords=["sponsored"]),
            "Sponsored: kleio is the best tool",
            ContentType.BODY.value,
            self._ctx(),
        )


class YouTubeMonitoringFilterTests(MonitoringTestMixin, SimpleTestCase):
    """YouTube service: MatchContext(author, source_label=channel name)."""

    def _ctx(self, *, channel="TechReviews"):
        return MatchContext(author=channel, source_label=channel)

    def test_video_title_match(self):
        self.assert_matches(
            keyword(content_types=[ContentType.TITLES.value]),
            "kleio review – best mention monitoring?",
            ContentType.TITLES.value,
            self._ctx(),
        )

    def test_video_description_match(self):
        self.assert_matches(
            keyword(content_types=[ContentType.BODY.value]),
            "In this video we explore kleio and its keyword filters in depth.",
            ContentType.BODY.value,
            self._ctx(),
        )

    def test_channel_filter_allows_listed_channel(self):
        self.assert_matches(
            keyword(
                content_types=[ContentType.TITLES.value],
                platform_specific_filters=["TechReviews"],
            ),
            "kleio tutorial",
            ContentType.TITLES.value,
            self._ctx(channel="TechReviews"),
        )

    def test_channel_filter_blocks_other_channels(self):
        self.assert_no_match(
            keyword(
                content_types=[ContentType.TITLES.value],
                platform_specific_filters=["TechReviews"],
            ),
            "kleio tutorial",
            ContentType.TITLES.value,
            self._ctx(channel="OtherChannel"),
        )

    def test_comments_content_type_does_not_match_video_title(self):
        """Comments-only keywords should not match title/body checks."""
        self.assert_no_match(
            keyword(content_types=[ContentType.COMMENTS.value]),
            "kleio in video title",
            ContentType.TITLES.value,
            self._ctx(),
        )

    def test_video_comment_match(self):
        self.assert_matches(
            keyword(content_types=[ContentType.COMMENTS.value]),
            "I've been using kleio for months and it works great for alerts.",
            ContentType.COMMENTS.value,
            MatchContext(author="viewer123", source_label="TechReviews"),
        )

    def test_channel_filter_applies_to_comment_via_source_label(self):
        self.assert_no_match(
            keyword(
                content_types=[ContentType.COMMENTS.value],
                platform_specific_filters=["TechReviews"],
            ),
            "kleio is awesome in the comments",
            ContentType.COMMENTS.value,
            MatchContext(author="viewer123", source_label="OtherChannel"),
        )


class CrossPlatformMatchingModeTests(MonitoringTestMixin, SimpleTestCase):
    """Match-mode behavior shared by all platform monitors."""

    def test_exact_mode_requires_full_content(self):
        kw = keyword(match_mode=MatchMode.EXACT.value)
        self.assert_matches(kw, "kleio", ContentType.BODY.value, MatchContext())
        self.assert_no_match(kw, "about kleio", ContentType.BODY.value, MatchContext())

    def test_starts_with_mode(self):
        kw = keyword(match_mode=MatchMode.STARTS_WITH.value)
        self.assert_matches(kw, "kleio monitoring platform", ContentType.BODY.value, MatchContext())
        self.assert_no_match(kw, "my kleio", ContentType.BODY.value, MatchContext())

    def test_ends_with_mode(self):
        kw = keyword(match_mode=MatchMode.ENDS_WITH.value)
        self.assert_matches(kw, "monitoring with kleio", ContentType.BODY.value, MatchContext())
        self.assert_no_match(kw, "kleio rocks", ContentType.BODY.value, MatchContext())


class PlatformMonitoringScenarioTableTests(MonitoringTestMixin, SimpleTestCase):
    """
    Table-driven scenarios documenting expected filter outcomes per platform.
    Run with subTest for readable failure output.
    """

    SCENARIOS = [
        # platform, description, keyword overrides, content, content_type, context kwargs, expect
        (
            Platform.REDDIT.value,
            "post title in allowed subreddit",
            {},
            "kleio release notes",
            ContentType.TITLES.value,
            {"author": "mod", "subreddit": "python"},
            True,
        ),
        (
            Platform.REDDIT.value,
            "blocked by excluded subreddit",
            {"excluded_subreddits": ["python"]},
            "kleio thread",
            ContentType.TITLES.value,
            {"subreddit": "python"},
            False,
        ),
        (
            Platform.HACKERNEWS.value,
            "story title by allowed author",
            {"included_users": ["pg"]},
            "kleio on HN",
            ContentType.TITLES.value,
            {"author": "pg"},
            True,
        ),
        (
            Platform.TWITTER.value,
            "tweet from filtered account",
            {"platform_specific_filters": ["brand"]},
            "kleio update",
            ContentType.BODY.value,
            {"author": "brand", "source_label": "brand"},
            True,
        ),
        (
            Platform.TWITTER.value,
            "tweet from non-filtered account",
            {"platform_specific_filters": ["brand"]},
            "kleio update",
            ContentType.BODY.value,
            {"author": "other", "source_label": "other"},
            False,
        ),
        (
            Platform.YOUTUBE.value,
            "video on allowed channel",
            {"platform_specific_filters": ["DemoChannel"], "content_types": [ContentType.TITLES.value]},
            "kleio demo",
            ContentType.TITLES.value,
            {"author": "DemoChannel", "source_label": "DemoChannel"},
            True,
        ),
        (
            Platform.YOUTUBE.value,
            "video on wrong channel",
            {"platform_specific_filters": ["DemoChannel"], "content_types": [ContentType.TITLES.value]},
            "kleio demo",
            ContentType.TITLES.value,
            {"author": "Other", "source_label": "Other"},
            False,
        ),
    ]

    def test_documented_scenarios(self):
        for platform, description, kw_overrides, content, content_type, ctx_kwargs, expect in self.SCENARIOS:
            with self.subTest(platform=platform, scenario=description):
                kw = keyword(**kw_overrides)
                ctx = MatchContext(**ctx_kwargs)
                if expect:
                    self.assert_matches(kw, content, content_type, ctx, description)
                else:
                    self.assert_no_match(kw, content, content_type, ctx, description)
