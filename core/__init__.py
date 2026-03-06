"""
Bitrix24 Core Module
====================
Core boilerplate for Bitrix24 REST API integration.
Provides authentication, API client, and base utilities.
"""

from .client import Bitrix24Client
from .auth import WebhookAuth, OAuth2Auth
from .exceptions import Bitrix24Error, AuthError, APIError

__all__ = [
    "Bitrix24Client",
    "WebhookAuth",
    "OAuth2Auth",
    "Bitrix24Error",
    "AuthError",
    "APIError",
]
