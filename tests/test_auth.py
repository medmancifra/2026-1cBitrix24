"""
Unit tests for core.auth module.
Tests WebhookAuth and OAuth2Auth without making real API calls.
"""

import os
import time
import unittest
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.auth import WebhookAuth, OAuth2Auth
from core.exceptions import AuthError


class TestWebhookAuth(unittest.TestCase):

    def test_init_with_params(self):
        auth = WebhookAuth(domain="example.bitrix24.com", user_id=1, token="mytoken")
        self.assertEqual(auth.domain, "example.bitrix24.com")
        self.assertEqual(auth.user_id, 1)
        self.assertEqual(auth.token, "mytoken")

    def test_init_from_env(self):
        with patch.dict(os.environ, {
            "BX24_DOMAIN": "env.bitrix24.com",
            "BX24_USER_ID": "2",
            "BX24_WEBHOOK_TOKEN": "envtoken",
        }):
            auth = WebhookAuth()
        self.assertEqual(auth.domain, "env.bitrix24.com")
        self.assertEqual(auth.user_id, 2)
        self.assertEqual(auth.token, "envtoken")

    def test_get_base_url_no_scheme(self):
        auth = WebhookAuth(domain="example.bitrix24.com", user_id=1, token="tok")
        self.assertEqual(auth.get_base_url(), "https://example.bitrix24.com/rest/1/tok")

    def test_get_base_url_with_https(self):
        auth = WebhookAuth(domain="https://example.bitrix24.com", user_id=1, token="tok")
        self.assertEqual(auth.get_base_url(), "https://example.bitrix24.com/rest/1/tok")

    def test_get_endpoint(self):
        auth = WebhookAuth(domain="example.bitrix24.com", user_id=1, token="tok")
        self.assertEqual(auth.get_endpoint("user.get"), "https://example.bitrix24.com/rest/1/tok/user.get")

    def test_missing_domain_raises_auth_error(self):
        with patch.dict(os.environ, {}, clear=True):
            # Remove relevant env vars
            env = {k: v for k, v in os.environ.items()
                   if k not in ("BX24_DOMAIN", "BX24_WEBHOOK_TOKEN", "BX24_USER_ID")}
            with patch.dict(os.environ, env, clear=True):
                with self.assertRaises(AuthError):
                    WebhookAuth()

    def test_missing_token_raises_auth_error(self):
        with patch.dict(os.environ, {"BX24_DOMAIN": "example.bitrix24.com"}, clear=True):
            # BX24_WEBHOOK_TOKEN not set
            env = {"BX24_DOMAIN": "example.bitrix24.com"}
            with patch.dict(os.environ, env, clear=True):
                with self.assertRaises(AuthError):
                    WebhookAuth()

    def test_trailing_slash_stripped(self):
        auth = WebhookAuth(domain="example.bitrix24.com/", user_id=1, token="tok")
        self.assertNotIn("//rest", auth.get_base_url())


class TestOAuth2Auth(unittest.TestCase):

    def test_init_with_params(self):
        auth = OAuth2Auth(
            domain="example.bitrix24.com",
            client_id="my_client",
            client_secret="my_secret",
            access_token="access123",
            refresh_token="refresh123",
            token_expires_at=time.time() + 3600,
        )
        self.assertEqual(auth.domain, "example.bitrix24.com")
        self.assertFalse(auth.is_token_expired())

    def test_token_not_expired(self):
        auth = OAuth2Auth(
            domain="example.bitrix24.com",
            access_token="tok",
            token_expires_at=time.time() + 3600,
        )
        self.assertFalse(auth.is_token_expired())

    def test_token_expired(self):
        auth = OAuth2Auth(
            domain="example.bitrix24.com",
            access_token="tok",
            token_expires_at=time.time() - 100,  # Expired 100s ago
        )
        self.assertTrue(auth.is_token_expired())

    def test_token_about_to_expire(self):
        # Within 60-second window
        auth = OAuth2Auth(
            domain="example.bitrix24.com",
            access_token="tok",
            token_expires_at=time.time() + 30,  # Expires in 30s
        )
        self.assertTrue(auth.is_token_expired())

    def test_get_auth_params_non_expired(self):
        auth = OAuth2Auth(
            domain="example.bitrix24.com",
            access_token="my_access_token",
            token_expires_at=time.time() + 3600,
        )
        params = auth.get_auth_params()
        self.assertEqual(params, {"auth": "my_access_token"})

    def test_get_endpoint(self):
        auth = OAuth2Auth(domain="example.bitrix24.com", access_token="tok",
                          token_expires_at=time.time() + 3600)
        self.assertEqual(auth.get_endpoint("crm.deal.list"),
                         "https://example.bitrix24.com/rest/crm.deal.list")

    def test_missing_domain_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(AuthError):
                OAuth2Auth()

    def test_refresh_without_refresh_token_raises(self):
        auth = OAuth2Auth(
            domain="example.bitrix24.com",
            access_token="tok",
            token_expires_at=time.time() - 100,
        )
        with self.assertRaises(AuthError):
            auth.refresh_access_token()


if __name__ == "__main__":
    unittest.main()
