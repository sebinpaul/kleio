"""Shared test helpers for MongoEngine-backed API tests."""

import mongoengine
import mongomock
from django.test import TestCase, override_settings

from core.authentication import ClerkUser
from core.models import Keyword, Mention


NO_THROTTLE = override_settings(
    REST_FRAMEWORK={
        "DEFAULT_AUTHENTICATION_CLASSES": [],
        "DEFAULT_PERMISSION_CLASSES": [
            "rest_framework.permissions.IsAuthenticated",
        ],
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {},
    }
)


class MongoTestCase(TestCase):
    """Use an in-memory MongoDB so keyword CRUD tests do not need a live cluster."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        mongoengine.disconnect_all()
        mongoengine.connect(
            "kleio_test",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )

    @classmethod
    def tearDownClass(cls):
        mongoengine.disconnect_all()
        super().tearDownClass()

    def setUp(self):
        Keyword.drop_collection()
        Mention.drop_collection()

    @staticmethod
    def auth_user(clerk_id: str = "test-user-1") -> ClerkUser:
        return ClerkUser(clerk_id=clerk_id, payload={"sub": clerk_id})

    def create_keyword(self, user_id: str = "test-user-1", **kwargs) -> Keyword:
        from django.utils import timezone

        defaults = {
            "user_id": user_id,
            "keyword": "kleio",
            "platform": "reddit",
            "created_at": timezone.now(),
            "updated_at": timezone.now(),
        }
        defaults.update(kwargs)
        keyword = Keyword(**defaults)
        keyword.save()
        return keyword
