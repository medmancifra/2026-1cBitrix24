"""
Unit tests for core.client module (Bitrix24Client).
All API calls are mocked — no real HTTP requests made.
"""

import os
import json
import unittest
from unittest.mock import patch, MagicMock, call
from urllib.error import HTTPError

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.client import Bitrix24Client
from core.auth import WebhookAuth
from core.exceptions import APIError, RateLimitError, NotFoundError


def make_client():
    auth = WebhookAuth(domain="example.bitrix24.com", user_id=1, token="testtoken")
    return Bitrix24Client(auth=auth)


def mock_urlopen(response_data: dict):
    """Returns a context manager mock that returns JSON response."""
    resp_mock = MagicMock()
    resp_mock.read.return_value = json.dumps(response_data).encode()
    resp_mock.__enter__ = MagicMock(return_value=resp_mock)
    resp_mock.__exit__ = MagicMock(return_value=False)
    return resp_mock


class TestFlattenParams(unittest.TestCase):

    def test_flat_params(self):
        result = Bitrix24Client._flatten_params({"ID": 1, "TITLE": "test"})
        self.assertEqual(result, {"ID": 1, "TITLE": "test"})

    def test_nested_dict(self):
        result = Bitrix24Client._flatten_params({"fields": {"TITLE": "Test", "ID": 5}})
        self.assertIn("fields[TITLE]", result)
        self.assertIn("fields[ID]", result)
        self.assertEqual(result["fields[TITLE]"], "Test")

    def test_nested_list(self):
        result = Bitrix24Client._flatten_params({"select": ["ID", "TITLE"]})
        self.assertIn("select[0]", result)
        self.assertIn("select[1]", result)

    def test_deeply_nested(self):
        result = Bitrix24Client._flatten_params({"filter": {"STATUS": {"eq": "open"}}})
        self.assertIn("filter[STATUS][eq]", result)


class TestBitrix24ClientCall(unittest.TestCase):

    @patch("urllib.request.urlopen")
    def test_call_success(self, mock_urlopen_fn):
        mock_urlopen_fn.return_value = mock_urlopen({"result": {"ID": 1, "NAME": "Test"}})
        client = make_client()
        result = client.call("user.get", {"ID": 1})
        self.assertEqual(result, {"ID": 1, "NAME": "Test"})

    @patch("urllib.request.urlopen")
    def test_call_api_error(self, mock_urlopen_fn):
        mock_urlopen_fn.return_value = mock_urlopen({
            "error": "ACCESS_DENIED",
            "error_description": "Access denied",
        })
        client = make_client()
        with self.assertRaises(APIError) as ctx:
            client.call("user.get", {"ID": 1})
        self.assertEqual(ctx.exception.error_code, "ACCESS_DENIED")

    @patch("urllib.request.urlopen")
    def test_call_not_found(self, mock_urlopen_fn):
        mock_urlopen_fn.return_value = mock_urlopen({
            "error": "NOT_FOUND",
            "error_description": "Item not found",
        })
        client = make_client()
        with self.assertRaises(NotFoundError):
            client.call("crm.deal.get", {"id": 9999})

    @patch("urllib.request.urlopen")
    def test_call_list_result(self, mock_urlopen_fn):
        mock_urlopen_fn.return_value = mock_urlopen({"result": [1, 2, 3]})
        client = make_client()
        result = client.call("some.list", {})
        self.assertEqual(result, [1, 2, 3])

    def test_endpoint_construction(self):
        client = make_client()
        endpoint = client.auth.get_endpoint("user.get")
        self.assertEqual(endpoint, "https://example.bitrix24.com/rest/1/testtoken/user.get")


class TestGetAll(unittest.TestCase):

    @patch("urllib.request.urlopen")
    def test_single_page(self, mock_urlopen_fn):
        # Less than 50 items → single page
        items = [{"ID": i} for i in range(10)]
        mock_urlopen_fn.return_value = mock_urlopen({"result": items})
        client = make_client()
        result = client.get_all("task.item.list", {})
        self.assertEqual(len(result), 10)

    @patch("urllib.request.urlopen")
    @patch("time.sleep")
    def test_multi_page(self, mock_sleep, mock_urlopen_fn):
        # First page: 50 items, second page: 5 items
        page1 = [{"ID": i} for i in range(50)]
        page2 = [{"ID": i + 50} for i in range(5)]

        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            if call_count == 0:
                call_count += 1
                return mock_urlopen({"result": page1})
            return mock_urlopen({"result": page2})

        mock_urlopen_fn.side_effect = side_effect
        client = make_client()
        result = client.get_all("task.item.list", {})
        self.assertEqual(len(result), 55)


class TestBatch(unittest.TestCase):

    @patch("urllib.request.urlopen")
    def test_batch_call(self, mock_urlopen_fn):
        mock_urlopen_fn.return_value = mock_urlopen({
            "result": {
                "result": {
                    "get_user": {"ID": 1, "NAME": "Test"},
                    "list_tasks": [{"ID": 10}],
                },
                "result_error": {},
            }
        })
        client = make_client()
        result = client.get_batch({
            "get_user": "user.get?ID=1",
            "list_tasks": "task.item.list",
        })
        # Result should contain batch results
        self.assertIsInstance(result, dict)


class TestFromEnv(unittest.TestCase):

    @patch.dict(os.environ, {
        "BX24_DOMAIN": "test.bitrix24.com",
        "BX24_USER_ID": "1",
        "BX24_WEBHOOK_TOKEN": "testtoken",
    })
    def test_from_env_webhook(self):
        client = Bitrix24Client.from_env()
        self.assertIsInstance(client.auth, WebhookAuth)
        self.assertEqual(client.auth.domain, "test.bitrix24.com")


if __name__ == "__main__":
    unittest.main()
