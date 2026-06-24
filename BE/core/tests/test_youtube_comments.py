from django.test import SimpleTestCase

from platforms.youtube.services.youtube_service import YouTubeService


class YouTubeCommentHelperTests(SimpleTestCase):
    def test_flatten_invidious_comments_includes_replies(self):
        payload = [
            {
                "commentId": "c1",
                "author": "alice",
                "content": "top-level",
                "replies": {
                    "comments": [
                        {"commentId": "c2", "author": "bob", "content": "reply"},
                    ]
                },
            }
        ]
        flat = YouTubeService._flatten_invidious_comments(payload)
        self.assertEqual(len(flat), 2)
        self.assertEqual(flat[0]["commentId"], "c1")
        self.assertEqual(flat[1]["commentId"], "c2")
