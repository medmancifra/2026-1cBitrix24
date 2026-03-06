"""
Authentication strategies for Bitrix24 REST API.

Supports:
- Incoming Webhooks (simple, permanent tokens)
- OAuth 2.0 (with access/refresh token management)
"""

import os
import time
import logging
import urllib.parse
import urllib.request
import json
from typing import Optional

from .exceptions import AuthError

logger = logging.getLogger(__name__)


class WebhookAuth:
    """
    Authenticates via a local incoming webhook (permanent token embedded in URL).

    Usage:
        auth = WebhookAuth(
            domain="your-domain.bitrix24.com",
            user_id=1,
            token="your_webhook_token"
        )

    Or via environment variables:
        BX24_DOMAIN, BX24_USER_ID, BX24_WEBHOOK_TOKEN
    """

    def __init__(
        self,
        domain: Optional[str] = None,
        user_id: Optional[int] = None,
        token: Optional[str] = None,
    ):
        self.domain = domain or os.environ.get("BX24_DOMAIN")
        self.user_id = user_id or int(os.environ.get("BX24_USER_ID", "1"))
        self.token = token or os.environ.get("BX24_WEBHOOK_TOKEN")

        if not self.domain:
            raise AuthError("BX24_DOMAIN is not set")
        if not self.token:
            raise AuthError("BX24_WEBHOOK_TOKEN is not set")

    def get_base_url(self) -> str:
        """Returns the base webhook URL for REST calls."""
        domain = self.domain.rstrip("/")
        if not domain.startswith("http"):
            domain = f"https://{domain}"
        return f"{domain}/rest/{self.user_id}/{self.token}"

    def get_endpoint(self, method: str) -> str:
        """Returns the full endpoint URL for a given REST method."""
        return f"{self.get_base_url()}/{method}"


class OAuth2Auth:
    """
    Authenticates via OAuth 2.0 with access/refresh token management.

    Usage:
        auth = OAuth2Auth(
            domain="your-domain.bitrix24.com",
            client_id="your_client_id",
            client_secret="your_client_secret",
            access_token="...",
            refresh_token="...",
        )

    Or via environment variables:
        BX24_DOMAIN, BX24_CLIENT_ID, BX24_CLIENT_SECRET,
        BX24_ACCESS_TOKEN, BX24_REFRESH_TOKEN
    """

    OAUTH_URL = "https://oauth.bitrix.info/oauth/token/"

    def __init__(
        self,
        domain: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[float] = None,
    ):
        self.domain = domain or os.environ.get("BX24_DOMAIN")
        self.client_id = client_id or os.environ.get("BX24_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("BX24_CLIENT_SECRET")
        self.access_token = access_token or os.environ.get("BX24_ACCESS_TOKEN")
        self.refresh_token = refresh_token or os.environ.get("BX24_REFRESH_TOKEN")
        self.token_expires_at = token_expires_at or 0.0

        if not self.domain:
            raise AuthError("BX24_DOMAIN is not set")

    def get_base_url(self) -> str:
        domain = self.domain.rstrip("/")
        if not domain.startswith("http"):
            domain = f"https://{domain}"
        return f"{domain}/rest"

    def get_endpoint(self, method: str) -> str:
        return f"{self.get_base_url()}/{method}"

    def is_token_expired(self) -> bool:
        """Returns True if the access token is expired or about to expire (within 60s)."""
        return time.time() >= self.token_expires_at - 60

    def refresh_access_token(self) -> None:
        """Refreshes the access token using the refresh token."""
        if not self.refresh_token:
            raise AuthError("No refresh_token available for OAuth2 token refresh")
        if not self.client_id or not self.client_secret:
            raise AuthError("client_id and client_secret are required for token refresh")

        params = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
        }
        data = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(self.OAUTH_URL, data=data, method="POST")

        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read())
        except Exception as e:
            raise AuthError(f"Token refresh failed: {e}") from e

        if "access_token" not in result:
            raise AuthError(f"Token refresh failed: {result}")

        self.access_token = result["access_token"]
        self.refresh_token = result.get("refresh_token", self.refresh_token)
        expires_in = int(result.get("expires_in", 3600))
        self.token_expires_at = time.time() + expires_in
        logger.debug("OAuth2 access token refreshed successfully")

    def get_auth_params(self) -> dict:
        """Returns dict with auth parameter for API requests."""
        if self.is_token_expired():
            self.refresh_access_token()
        return {"auth": self.access_token}
