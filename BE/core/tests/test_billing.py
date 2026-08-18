"""Billing plan limit tests."""

from unittest.mock import patch

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

    def test_webhook_matches_by_customer_id_without_metadata(self):
        profile = billing_service.get_or_create_profile("u5")
        profile.dodo_customer_id = "cus_5"
        profile.save()

        class FakeCustomer:
            customer_id = "cus_5"

        class FakeSub:
            subscription_id = "sub_5"
            status = "active"
            customer = FakeCustomer()
            metadata = {}

        billing_service.apply_subscription_event(FakeSub())
        profile.reload()
        self.assertEqual(profile.plan, "pro")
        self.assertEqual(profile.dodo_subscription_id, "sub_5")
        self.assertEqual(billing_service.resolve_plan(profile), "pro")

    @patch("core.services.dodo_service.list_subscriptions_for_customer")
    @patch("core.services.dodo_service.retrieve_subscription")
    def test_sync_plan_from_dodo_activates_pro(self, mock_retrieve, mock_list):
        profile = billing_service.get_or_create_profile("u6")
        profile.dodo_customer_id = "cus_6"
        profile.save()

        class FakeCustomer:
            customer_id = "cus_6"

        class FakeSub:
            subscription_id = "sub_6"
            status = "active"
            customer = FakeCustomer()
            metadata = {}

        mock_retrieve.side_effect = Exception("none stored")
        mock_list.side_effect = lambda *args, **kwargs: (
            [FakeSub()] if kwargs.get("status") == "active" else []
        )

        payload = billing_service.sync_plan_from_dodo("u6")
        self.assertEqual(payload["plan"], "pro")
        profile.reload()
        self.assertEqual(profile.dodo_subscription_id, "sub_6")

    def test_apply_payment_event_pulls_subscription(self):
        class FakeCustomer:
            customer_id = "cus_7"

        class FakePayment:
            status = "succeeded"
            subscription_id = "sub_7"
            customer = FakeCustomer()
            metadata = {"clerk_user_id": "u7"}

        class FakeSub:
            subscription_id = "sub_7"
            status = "active"
            customer = FakeCustomer()
            metadata = {}

        with patch(
            "core.services.dodo_service.retrieve_subscription",
            return_value=FakeSub(),
        ):
            billing_service.apply_payment_event(FakePayment())

        profile = UserProfile.objects(user_id="u7").first()
        self.assertIsNotNone(profile)
        self.assertEqual(profile.plan, "pro")
        self.assertEqual(billing_service.resolve_plan(profile), "pro")

    def test_active_with_cancel_at_period_end_stays_pro(self):
        class FakeCustomer:
            customer_id = "cus_8"

        class FakeSub:
            subscription_id = "sub_8"
            status = "active"
            cancel_at_next_billing_date = True
            next_billing_date = "2026-09-18T00:00:00Z"
            customer = FakeCustomer()
            metadata = {"clerk_user_id": "u8"}

        billing_service.apply_subscription_event(FakeSub())
        profile = UserProfile.objects(user_id="u8").first()
        self.assertIsNotNone(profile)
        self.assertTrue(profile.cancel_at_period_end)
        self.assertEqual(profile.next_billing_date, "2026-09-18T00:00:00Z")
        self.assertEqual(billing_service.resolve_plan(profile), "pro")
        payload = billing_service.billing_status_payload("u8")
        self.assertTrue(payload["cancelAtPeriodEnd"])
        self.assertTrue(payload["canReactivate"])
        self.assertFalse(payload["canUpgradePro"])
        self.assertTrue(payload["canUpgradeBusiness"])
        self.assertTrue(payload["canUpgrade"])

    @patch("core.services.dodo_service.reactivate_subscription")
    def test_reactivate_clears_cancel_flag(self, mock_reactivate):
        profile = billing_service.get_or_create_profile("u9")
        profile.plan = "pro"
        profile.subscription_status = "active"
        profile.dodo_subscription_id = "sub_9"
        profile.dodo_customer_id = "cus_9"
        profile.cancel_at_period_end = True
        profile.next_billing_date = "2026-09-18T00:00:00Z"
        profile.save()

        class FakeCustomer:
            customer_id = "cus_9"

        class FakeSub:
            subscription_id = "sub_9"
            status = "active"
            cancel_at_next_billing_date = False
            next_billing_date = "2026-09-18T00:00:00Z"
            customer = FakeCustomer()
            metadata = {}

        mock_reactivate.return_value = FakeSub()
        payload = billing_service.reactivate_plan("u9")
        self.assertEqual(payload["plan"], "pro")
        self.assertFalse(payload["cancelAtPeriodEnd"])
        self.assertFalse(payload["canReactivate"])
        mock_reactivate.assert_called_once_with("sub_9")

    def test_downgrade_pauses_over_limit_and_requires_selection(self):
        profile = billing_service.get_or_create_profile("u10")
        profile.plan = "pro"
        profile.subscription_status = "active"
        profile.dodo_subscription_id = "sub_10"
        profile.save()

        k1 = self.create_keyword(user_id="u10", platform="reddit", keyword="a")
        k2 = self.create_keyword(user_id="u10", platform="reddit", keyword="b")
        k3 = self.create_keyword(user_id="u10", platform="reddit", keyword="c")
        tw = self.create_keyword(user_id="u10", platform="twitter", keyword="x")
        hn = self.create_keyword(user_id="u10", platform="hackernews", keyword="hn1")

        class FakeCustomer:
            customer_id = "cus_10"

        class FakeSub:
            subscription_id = "sub_10"
            status = "cancelled"
            customer = FakeCustomer()
            metadata = {"clerk_user_id": "u10"}

        billing_service.apply_subscription_event(FakeSub())
        profile.reload()
        self.assertEqual(profile.plan, "free")
        self.assertTrue(profile.needs_keyword_selection)

        for kw in (k1, k2, k3, tw):
            kw.reload()
            self.assertFalse(kw.is_active)
        # HN still within Free cap (2) — stays active
        hn.reload()
        self.assertTrue(hn.is_active)

        # Keep two reddit keywords; HN under-cap left alone when not in keepIds
        billing_service.apply_keyword_selection("u10", [str(k1.id), str(k2.id)])
        profile.reload()
        self.assertFalse(profile.needs_keyword_selection)

        k1.reload()
        k2.reload()
        k3.reload()
        tw.reload()
        hn.reload()
        self.assertTrue(k1.is_active)
        self.assertTrue(k2.is_active)
        self.assertFalse(k3.is_active)
        self.assertFalse(tw.is_active)
        self.assertTrue(hn.is_active)

    def test_business_product_maps_and_limits(self):
        profile = billing_service.get_or_create_profile("u12")
        profile.dodo_customer_id = "cus_12"
        profile.save()

        class FakeCustomer:
            customer_id = "cus_12"

        class FakeSub:
            subscription_id = "sub_12"
            status = "active"
            product_id = "pdt_business_test"
            customer = FakeCustomer()
            metadata = {"clerk_user_id": "u12"}

        with self.settings(DODO_BUSINESS_PRODUCT_ID="pdt_business_test"):
            billing_service.apply_subscription_event(FakeSub())
            profile.reload()
            self.assertEqual(profile.plan, "business")
            self.assertEqual(billing_service.resolve_plan(profile), "business")
            self.assertEqual(profile.dodo_product_id, "pdt_business_test")
            ok, err = billing_service.check_can_add_keyword("u12", "twitter")
            self.assertTrue(ok)
            payload = billing_service.billing_status_payload("u12")
            self.assertEqual(payload["limits"]["reddit"], 100)
            self.assertEqual(payload["limits"]["twitter"], 10)
            self.assertFalse(payload["canUpgradeBusiness"])
            self.assertFalse(payload["canUpgradePro"])

    def test_business_to_free_requires_selection(self):
        profile = billing_service.get_or_create_profile("u13")
        profile.plan = "business"
        profile.subscription_status = "active"
        profile.dodo_subscription_id = "sub_13"
        profile.dodo_product_id = "pdt_business_test"
        profile.save()

        for i in range(5):
            self.create_keyword(
                user_id="u13", platform="reddit", keyword=f"kw{i}"
            )

        class FakeCustomer:
            customer_id = "cus_13"

        class FakeSub:
            subscription_id = "sub_13"
            status = "cancelled"
            product_id = "pdt_business_test"
            customer = FakeCustomer()
            metadata = {"clerk_user_id": "u13"}

        with self.settings(DODO_BUSINESS_PRODUCT_ID="pdt_business_test"):
            billing_service.apply_subscription_event(FakeSub())
            profile.reload()
            self.assertEqual(profile.plan, "free")
            self.assertTrue(profile.needs_keyword_selection)

    def test_keyword_selection_rejects_over_cap(self):
        profile = billing_service.get_or_create_profile("u11")
        profile.plan = "free"
        profile.subscription_status = "cancelled"
        profile.needs_keyword_selection = True
        profile.save()

        k1 = self.create_keyword(
            user_id="u11", platform="reddit", keyword="a", is_active=False
        )
        k2 = self.create_keyword(
            user_id="u11", platform="reddit", keyword="b", is_active=False
        )
        k3 = self.create_keyword(
            user_id="u11", platform="reddit", keyword="c", is_active=False
        )

        with self.assertRaises(ValueError):
            billing_service.apply_keyword_selection(
                "u11", [str(k1.id), str(k2.id), str(k3.id)]
            )
