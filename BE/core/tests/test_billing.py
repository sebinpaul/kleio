"""Billing plan limit tests."""

from core.services import billing_service
from core.models import UserProfile
from core.tests.base import MongoTestCase, NO_THROTTLE


@NO_THROTTLE
class BillingLimitsTests(MongoTestCase):
    def setUp(self):
        super().setUp()
        UserProfile.drop_collection()

    def test_free_blocks_twitter(self):
        ok, err = billing_service.check_can_add_keyword("u1", "twitter")
        self.assertFalse(ok)
        self.assertIn("Pro", err or "")

    def test_free_allows_two_reddit(self):
        self.create_keyword(user_id="u1", platform="reddit", keyword="a")
        self.create_keyword(user_id="u1", platform="reddit", keyword="b")
        ok, err = billing_service.check_can_add_keyword("u1", "reddit")
        self.assertFalse(ok)
        self.assertIn("limit", (err or "").lower())

    def test_pro_allows_twitter(self):
        profile = billing_service.get_or_create_profile("u2")
        profile.plan = "pro"
        profile.subscription_status = "active"
        profile.dodo_subscription_id = "sub_test"
        profile.save()
        ok, err = billing_service.check_can_add_keyword("u2", "twitter")
        self.assertTrue(ok)
        self.assertIsNone(err)

    def test_webhook_activates_pro(self):
        class FakeCustomer:
            customer_id = "cus_1"

        class FakeSub:
            subscription_id = "sub_1"
            status = "active"
            customer = FakeCustomer()
            metadata = {"clerk_user_id": "u3"}

        billing_service.apply_subscription_event(FakeSub())
        profile = UserProfile.objects(user_id="u3").first()
        self.assertIsNotNone(profile)
        self.assertEqual(profile.plan, "pro")
        self.assertEqual(billing_service.resolve_plan(profile), "pro")

    def test_webhook_cancels_to_free(self):
        profile = billing_service.get_or_create_profile("u4")
        profile.plan = "pro"
        profile.subscription_status = "active"
        profile.dodo_subscription_id = "sub_2"
        profile.save()

        class FakeCustomer:
            customer_id = "cus_2"

        class FakeSub:
            subscription_id = "sub_2"
            status = "cancelled"
            customer = FakeCustomer()
            metadata = {"clerk_user_id": "u4"}

        billing_service.apply_subscription_event(FakeSub())
        profile.reload()
        self.assertEqual(profile.plan, "free")
        self.assertEqual(billing_service.resolve_plan(profile), "free")
