"""
Bitrix24 REST API Client.

Provides a unified interface for making REST API calls to Bitrix24,
supporting both Webhook and OAuth2 authentication strategies.
Implements batching, pagination, and error handling.
"""

import json
import time
import logging
import urllib.parse
import urllib.request
import urllib.error
from typing import Any, Dict, Iterator, List, Optional, Union

from .auth import WebhookAuth, OAuth2Auth
from .exceptions import APIError, RateLimitError, NotFoundError

logger = logging.getLogger(__name__)

# Bitrix24 rate limit: 2 requests/second per user, 50/second globally
DEFAULT_RETRY_DELAY = 0.5
MAX_RETRIES = 3
BATCH_SIZE = 50  # Max commands per batch request


class Bitrix24Client:
    """
    Unified Bitrix24 REST API client.

    Supports:
    - Webhook and OAuth2 authentication
    - All standard REST methods (call, batch, list)
    - Automatic pagination via get_all()
    - Batch execution with get_batch()
    - Rate-limit aware retry logic

    Example (webhook):
        client = Bitrix24Client(auth=WebhookAuth(
            domain="example.bitrix24.com",
            user_id=1,
            token="abc123"
        ))
        result = client.call("user.get", {"ID": 1})

    Example (env vars):
        # Set BX24_DOMAIN, BX24_USER_ID, BX24_WEBHOOK_TOKEN
        client = Bitrix24Client.from_env()
    """

    def __init__(self, auth: Union[WebhookAuth, OAuth2Auth]):
        self.auth = auth

    @classmethod
    def from_env(cls) -> "Bitrix24Client":
        """Creates a client from environment variables. Tries webhook auth first."""
        import os
        if os.environ.get("BX24_WEBHOOK_TOKEN"):
            return cls(auth=WebhookAuth())
        return cls(auth=OAuth2Auth())

    def _make_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        retries: int = MAX_RETRIES,
    ) -> Any:
        """
        Makes a single REST API call and returns the 'result' field.

        Args:
            method: Bitrix24 REST method name (e.g. 'user.get')
            params: Method parameters dict
            retries: Number of retry attempts on rate-limit / transient errors

        Returns:
            The 'result' value from the API response

        Raises:
            APIError: On API-level errors
            RateLimitError: When rate limit is exceeded and retries exhausted
        """
        endpoint = self.auth.get_endpoint(method)
        params = params or {}

        # For OAuth2, inject auth token
        if isinstance(self.auth, OAuth2Auth):
            params.update(self.auth.get_auth_params())

        # Encode parameters
        data = urllib.parse.urlencode(self._flatten_params(params), doseq=True).encode()
        req = urllib.request.Request(endpoint, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

        for attempt in range(retries + 1):
            try:
                logger.debug("Calling %s with %d params", method, len(params))
                with urllib.request.urlopen(req) as resp:
                    body = resp.read().decode("utf-8")
                    response = json.loads(body)

                if "error" in response:
                    self._handle_error(response, method)

                return response.get("result")

            except urllib.error.HTTPError as e:
                if e.code == 429:
                    # Rate limited
                    if attempt < retries:
                        delay = DEFAULT_RETRY_DELAY * (2 ** attempt)
                        logger.warning("Rate limited on %s, retrying in %.1fs", method, delay)
                        time.sleep(delay)
                        continue
                    raise RateLimitError("QUERY_LIMIT_EXCEEDED", "Rate limit exceeded") from e
                body = e.read().decode("utf-8", errors="replace")
                try:
                    response = json.loads(body)
                    self._handle_error(response, method)
                except (json.JSONDecodeError, APIError):
                    raise APIError("HTTP_ERROR", f"HTTP {e.code}: {body[:200]}") from e
            except urllib.error.URLError as e:
                if attempt < retries:
                    time.sleep(DEFAULT_RETRY_DELAY)
                    continue
                raise APIError("CONNECTION_ERROR", str(e)) from e

        raise APIError("MAX_RETRIES", f"Max retries exceeded for {method}")

    @staticmethod
    def _handle_error(response: dict, method: str) -> None:
        """Parses API error responses and raises appropriate exceptions."""
        error_code = response.get("error", "UNKNOWN_ERROR")
        error_desc = response.get("error_description", "Unknown error")

        if error_code in ("ERROR_CORE", "NOT_FOUND"):
            raise NotFoundError(error_code, error_desc, response)
        if error_code == "QUERY_LIMIT_EXCEEDED":
            raise RateLimitError(error_code, error_desc, response)
        raise APIError(error_code, error_desc, response)

    @staticmethod
    def _flatten_params(params: dict, prefix: str = "") -> dict:
        """
        Flattens nested dict params into Bitrix24's array-like format.
        e.g. {"fields": {"TITLE": "Test"}} -> {"fields[TITLE]": "Test"}
        """
        result = {}
        for key, value in params.items():
            full_key = f"{prefix}[{key}]" if prefix else key
            if isinstance(value, dict):
                result.update(Bitrix24Client._flatten_params(value, full_key))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        result.update(Bitrix24Client._flatten_params(item, f"{full_key}[{i}]"))
                    else:
                        result[f"{full_key}[{i}]"] = item
            else:
                result[full_key] = value
        return result

    def call(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Calls a single Bitrix24 REST method.

        Args:
            method: e.g. 'user.get', 'crm.deal.add', 'task.add'
            params: Method parameters

        Returns:
            API result (varies by method)
        """
        return self._make_request(method, params)

    def get_all(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        page_size: int = 50,
    ) -> List[Any]:
        """
        Fetches ALL records for list methods with automatic pagination.

        Bitrix24 returns max 50 items per page. This method handles
        pagination automatically using the 'start' parameter.

        Args:
            method: A list method (e.g. 'crm.deal.list', 'task.list')
            params: Filter/select/order params
            page_size: Items per page (default 50, max 50)

        Returns:
            Full list of all records
        """
        params = params or {}
        all_items = []
        start = 0

        while True:
            page_params = {**params, "start": start}
            result = self._make_request(method, page_params)

            if isinstance(result, dict):
                items = result.get("items", result.get("result", []))
                total = result.get("total", None)
            elif isinstance(result, list):
                items = result
                total = None
            else:
                break

            all_items.extend(items)
            logger.debug("Fetched %d/%s items from %s", len(all_items), total or "?", method)

            if not items or len(items) < page_size:
                break
            if total is not None and len(all_items) >= total:
                break

            start += page_size
            # Small delay to respect rate limits
            time.sleep(0.1)

        return all_items

    def get_batch(self, commands: Dict[str, str]) -> Dict[str, Any]:
        """
        Executes multiple commands in a single batch request (max 50).

        Args:
            commands: Dict of {request_id: "method?param=value"} or
                      {request_id: {"method": "...", "params": {...}}}

        Returns:
            Dict of {request_id: result}

        Example:
            results = client.get_batch({
                "get_user": "user.get?ID=1",
                "list_deals": "crm.deal.list?filter[STAGE_ID]=WON",
            })
        """
        if len(commands) > BATCH_SIZE:
            # Split into multiple batches
            all_results = {}
            items = list(commands.items())
            for i in range(0, len(items), BATCH_SIZE):
                chunk = dict(items[i : i + BATCH_SIZE])
                result = self._execute_batch(chunk)
                all_results.update(result)
            return all_results

        return self._execute_batch(commands)

    def _execute_batch(self, commands: Dict[str, str]) -> Dict[str, Any]:
        """Executes a single batch call (max 50 commands)."""
        params = {
            "halt": 0,
            "cmd": commands,
        }
        result = self._make_request("batch", params)
        if isinstance(result, dict):
            return result.get("result", result)
        return result or {}

    def iter_all(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        page_size: int = 50,
    ) -> Iterator[Any]:
        """
        Iterator version of get_all() for memory-efficient large dataset processing.
        """
        params = params or {}
        start = 0

        while True:
            page_params = {**params, "start": start}
            result = self._make_request(method, page_params)

            if isinstance(result, dict):
                items = result.get("items", result.get("result", []))
                total = result.get("total", None)
            elif isinstance(result, list):
                items = result
                total = None
            else:
                return

            for item in items:
                yield item

            if not items or len(items) < page_size:
                return
            if total is not None and start + page_size >= total:
                return

            start += page_size
            time.sleep(0.1)
