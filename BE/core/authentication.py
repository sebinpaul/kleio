import logging

from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from clerk_backend_api.security import authenticate_request
from clerk_backend_api.security.types import AuthenticateRequestOptions

logger = logging.getLogger(__name__)


class ClerkUser:
    """Lightweight user object backed by a verified Clerk session token."""

    def __init__(self, clerk_id: str, payload: dict):
        self.clerk_id = clerk_id
        self.payload = payload

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False

    @property
    def pk(self) -> str:
        return self.clerk_id


class ClerkAuthentication(BaseAuthentication):
    """Verify Clerk session JWT from Authorization: Bearer <token>."""

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise AuthenticationFailed("Authentication credentials were not provided.")

        state = authenticate_request(
            request,
            AuthenticateRequestOptions(
                secret_key=settings.CLERK_SECRET_KEY,
                jwt_key=settings.CLERK_JWT_KEY or None,
                authorized_parties=settings.CLERK_AUTHORIZED_PARTIES or None,
                accepts_token=["session_token"],
            ),
        )

        if not state.is_signed_in:
            message = state.message or "Invalid or expired Clerk session token."
            logger.info("Clerk authentication failed: %s", message)
            raise AuthenticationFailed(message)

        clerk_id = state.payload.get("sub")
        if not clerk_id:
            raise AuthenticationFailed("Clerk token is missing a user id.")

        return ClerkUser(clerk_id=clerk_id, payload=state.payload), state

    def authenticate_header(self, request):
        return "Bearer"
