"""Thin wrapper around the Dodo Payments Python SDK."""

from __future__ import annotations

import logging
from typing import Any, Mapping

from django.conf import settings
from dodopayments import DodoPayments

logger = logging.getLogger(__name__)

_client: DodoPayments | None = None


def get_dodo_client() -> DodoPayments:
    global _client
    if _client is not None:
        return _client

    api_key = settings.DODO_PAYMENTS_API_KEY
    if not api_key:
        raise RuntimeError("DODO_PAYMENTS_API_KEY is not configured")

    environment = settings.DODO_PAYMENTS_ENVIRONMENT or "test_mode"
    _client = DodoPayments(
        bearer_token=api_key,
        webhook_key=settings.DODO_PAYMENTS_WEBHOOK_KEY or None,
        environment=environment,
    )
    return _client


def create_pro_checkout(
    *,
    customer_email: str,
    customer_name: str | None,
    clerk_user_id: str,
    dodo_customer_id: str | None,
    return_url: str,
    cancel_url: str | None = None,
) -> dict[str, str]:
    client = get_dodo_client()
    product_id = settings.DODO_PRO_PRODUCT_ID
    if not product_id:
        raise RuntimeError("DODO_PRO_PRODUCT_ID is not configured")

    metadata = {"clerk_user_id": clerk_user_id}
    customer_id = dodo_customer_id

    if not customer_id:
        try:
            created = client.customers.create(
                email=customer_email,
                name=customer_name or customer_email.split("@")[0],
                metadata=metadata,
            )
            customer_id = getattr(created, "customer_id", None)
        except Exception:
            logger.info(
                "Dodo customer create failed for %s; falling back to email checkout",
                customer_email,
                exc_info=True,
            )
            customer_id = None

    if customer_id:
        customer: dict[str, Any] = {"customer_id": customer_id}
    else:
        customer = {"email": customer_email}
        if customer_name:
            customer["name"] = customer_name

    session = client.checkout_sessions.create(
        product_cart=[{"product_id": product_id, "quantity": 1}],
        customer=customer,
        return_url=return_url,
        cancel_url=cancel_url or return_url,
        metadata=metadata,
        feature_flags={"redirect_immediately": True},
    )

    checkout_url = getattr(session, "checkout_url", None)
    session_id = getattr(session, "session_id", None)
    if not checkout_url:
        raise RuntimeError("Dodo checkout session did not return a checkout_url")

    return {
        "checkoutUrl": checkout_url,
        "sessionId": session_id or "",
        "customerId": customer_id or "",
    }


def create_customer_portal_link(
    *,
    dodo_customer_id: str,
    return_url: str | None = None,
) -> str:
    client = get_dodo_client()
    kwargs: dict[str, Any] = {}
    if return_url:
        kwargs["return_url"] = return_url
    portal = client.customers.customer_portal.create(dodo_customer_id, **kwargs)
    link = getattr(portal, "link", None)
    if not link:
        raise RuntimeError("Dodo customer portal did not return a link")
    return link


def unwrap_webhook(payload: str | bytes, headers: Mapping[str, str]) -> Any:
    client = get_dodo_client()
    body = payload.decode("utf-8") if isinstance(payload, (bytes, bytearray)) else payload
    return client.webhooks.unwrap(body, headers=headers)
