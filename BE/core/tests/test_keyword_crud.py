"""API tests for keyword create, list, update, and delete."""

from bson import ObjectId
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from core.models import Keyword
from core.views import get_keywords, update_keyword, toggle_keyword

from .base import MongoTestCase, NO_THROTTLE


@NO_THROTTLE
class KeywordCrudApiTests(MongoTestCase):
    def setUp(self):
        super().setUp()
        self.factory = APIRequestFactory()

    def _request(self, method: str, path: str, data=None, user_id: str = "test-user-1"):
        user = self.auth_user(user_id)
        if method == "GET":
            request = self.factory.get(path)
        elif method == "POST":
            request = self.factory.post(path, data or {}, format="json")
        elif method == "PUT":
            request = self.factory.put(path, data or {}, format="json")
        elif method == "PATCH":
            request = self.factory.patch(path, data or {}, format="json")
        elif method == "DELETE":
            request = self.factory.delete(path)
        else:
            raise ValueError(method)
        force_authenticate(request, user=user)
        return request

    def test_create_keyword_minimal(self):
        request = self._request(
            "POST",
            "/api/keywords",
            {"keyword": "python", "platform": "reddit"},
        )
        response = get_keywords(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["keyword"], "python")
        self.assertEqual(response.data["platform"], "reddit")
        self.assertTrue(response.data["enabled"])
        self.assertEqual(Keyword.objects.count(), 1)

    def test_create_keyword_with_all_filters(self):
        payload = {
            "keyword": "kleio",
            "platform": "twitter",
            "platformSpecificFilters": ["@brand", "competitor"],
            "excludedKeywords": ["spam"],
            "excludedSubreddits": ["test"],
            "includedUsers": ["gooduser"],
            "excludedUsers": ["baduser"],
            "includedLanguages": ["en"],
            "excludedLanguages": ["es"],
            "caseSensitive": True,
            "matchMode": "word_boundary",
            "contentTypes": ["body"],
            "emailNotifications": False,
            "slackNotifications": False,
            "enabled": True,
        }
        response = get_keywords(self._request("POST", "/api/keywords", payload))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["platformSpecificFilters"], ["@brand", "competitor"])
        self.assertEqual(response.data["excludedKeywords"], ["spam"])
        self.assertEqual(response.data["includedUsers"], ["gooduser"])
        self.assertEqual(response.data["excludedUsers"], ["baduser"])
        self.assertEqual(response.data["includedLanguages"], ["en"])
        self.assertEqual(response.data["excludedLanguages"], ["es"])
        self.assertTrue(response.data["caseSensitive"])
        self.assertEqual(response.data["matchMode"], "word_boundary")
        self.assertEqual(response.data["contentTypes"], ["body"])
        self.assertFalse(response.data["emailNotifications"])

    def test_create_rejects_missing_keyword(self):
        response = get_keywords(self._request("POST", "/api/keywords", {"platform": "reddit"}))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("keyword", response.data["error"].lower())

    def test_create_rejects_blank_keyword(self):
        response = get_keywords(self._request("POST", "/api/keywords", {"keyword": "   "}))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_rejects_invalid_platform(self):
        response = get_keywords(
            self._request("POST", "/api/keywords", {"keyword": "x", "platform": "linkedin"})
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_rejects_invalid_match_mode(self):
        response = get_keywords(
            self._request(
                "POST",
                "/api/keywords",
                {"keyword": "x", "matchMode": "fuzzy"},
            )
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_rejects_empty_content_types(self):
        response = get_keywords(
            self._request(
                "POST",
                "/api/keywords",
                {"keyword": "x", "contentTypes": []},
            )
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_platform_scoped_create_uses_url_platform(self):
        request = self._request("POST", "/api/platforms/youtube/keywords", {"keyword": "django"})
        response = get_keywords(request, platform="youtube")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["platform"], "youtube")

    def test_platform_scoped_create_rejects_body_platform_mismatch(self):
        request = self._request(
            "POST",
            "/api/platforms/youtube/keywords",
            {"keyword": "django", "platform": "reddit"},
        )
        response = get_keywords(request, platform="youtube")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_keywords_returns_only_current_user(self):
        self.create_keyword(user_id="test-user-1", keyword="mine")
        self.create_keyword(user_id="other-user", keyword="theirs")
        response = get_keywords(self._request("GET", "/api/keywords"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["keyword"], "mine")

    def test_list_keywords_filters_by_platform(self):
        self.create_keyword(keyword="r-kw", platform="reddit")
        self.create_keyword(keyword="yt-kw", platform="youtube")
        request = self._request("GET", "/api/platforms/reddit/keywords")
        response = get_keywords(request, platform="reddit")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["keyword"], "r-kw")

    def test_update_keyword_text_and_filters(self):
        keyword = self.create_keyword(
            keyword="old",
            platform_specific_filters=["python"],
            excluded_keywords=["noise"],
        )
        payload = {
            "keyword": "new-name",
            "platformSpecificFilters": ["javascript"],
            "excludedKeywords": [],
            "includedUsers": ["alice"],
            "matchMode": "contains",
            "emailNotifications": False,
        }
        request = self._request("PUT", f"/api/keywords/{keyword.id}", payload)
        response = update_keyword(request, str(keyword.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["keyword"], "new-name")
        self.assertEqual(response.data["platformSpecificFilters"], ["javascript"])
        self.assertEqual(response.data["excludedKeywords"], [])
        self.assertEqual(response.data["includedUsers"], ["alice"])
        self.assertFalse(response.data["emailNotifications"])

        keyword.reload()
        self.assertEqual(keyword.keyword, "new-name")
        self.assertEqual(keyword.excluded_keywords, [])

    def test_update_returns_404_for_other_users_keyword(self):
        keyword = self.create_keyword(user_id="owner")
        request = self._request("PUT", f"/api/keywords/{keyword.id}", {"keyword": "hack"}, user_id="intruder")
        response = update_keyword(request, str(keyword.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_returns_404_for_missing_keyword(self):
        missing_id = str(ObjectId())
        request = self._request("PUT", f"/api/keywords/{missing_id}", {"keyword": "x"})
        response = update_keyword(request, missing_id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_rejects_invalid_keyword_id(self):
        request = self._request("PUT", "/api/keywords/not-an-object-id", {"keyword": "x"})
        response = update_keyword(request, "not-an-object-id")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_keyword(self):
        keyword = self.create_keyword()
        request = self._request("DELETE", f"/api/keywords/{keyword.id}")
        response = update_keyword(request, str(keyword.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Keyword.objects.count(), 0)

    def test_delete_returns_404_when_not_found(self):
        missing_id = str(ObjectId())
        request = self._request("DELETE", f"/api/keywords/{missing_id}")
        response = update_keyword(request, missing_id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_toggle_keyword_enabled_state(self):
        keyword = self.create_keyword(is_active=True)
        request = self._request("PATCH", f"/api/keywords/{keyword.id}/toggle", {"enabled": False})
        response = toggle_keyword(request, str(keyword.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["enabled"])
        keyword.reload()
        self.assertFalse(keyword.is_active)
