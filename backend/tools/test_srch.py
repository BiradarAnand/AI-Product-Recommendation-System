"""
Tests for tools/product_search.py and agents/search_agent.py.

All DB, HTTP, and Groq calls are mocked — these are unit tests for the
fallback logic and schema contract, not integration tests against a
live TiDB instance or the real BuyWhere/Groq services.

Run with: python -m unittest backend.tests.test_search_agent -v
(from the backend/ directory, or adjust sys.path as done below)
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import product_search  # noqa: E402


class TestSearchInternal(unittest.TestCase):

    @patch("tools.product_search.get_catalog_db")
    def test_returns_rows_tagged_internal(self, mock_get_db):
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [
            {"id": 1, "name": "Running Shoes", "description": "", "category": "Sports Shoes",
             "price": "2499.00", "stock": 5, "rating": "4.3", "reviews": "120",
             "image_url": "http://x/img.jpg", "brand": "Puma"}
        ]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_get_db.return_value = mock_conn

        results = product_search.search_internal({"keyword": "running shoes"}, limit=6)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source"], "internal")
        self.assertIsInstance(results[0]["price"], float)
        mock_cur.execute.assert_called_once()
        sql_used = mock_cur.execute.call_args[0][0]
        self.assertNotIn("?", sql_used)  # confirms the %s placeholder fix

    @patch("tools.product_search.get_catalog_db")
    def test_db_error_returns_empty_list_not_exception(self, mock_get_db):
        mock_get_db.side_effect = RuntimeError("connection refused")
        results = product_search.search_internal({"keyword": "x"})
        self.assertEqual(results, [])


class TestSearchExternal(unittest.TestCase):

    @patch("tools.product_search.requests.get")
    def test_returns_rows_tagged_external_with_currency(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [
                {"id": "bw_sg_123", "title": "Sony WH-1000XM5", "price": 429.0,
                 "currency": "SGD", "domain": "hifisolutions.sg",
                 "url": "http://x/product", "source": "shopify_hifisolutions",
                 "country_code": "SG"}
            ],
            "meta": {"total": 1, "limit": 6, "offset": 0},
        }
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        results = product_search.search_external("wireless headphones", limit=6)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source"], "external")
        self.assertEqual(results[0]["price"], 429.0)
        self.assertEqual(results[0]["currency"], "SGD")  # confirms non-INR isn't silently dropped

    @patch("tools.product_search.requests.get")
    def test_works_without_api_key_unauthenticated(self, mock_get):
        # BuyWhere's basic GET endpoint doesn't require a key — confirm no
        # key still results in a call, just without an Authorization header
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": [], "meta": {}}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        with patch("tools.product_search.BUYWHERE_API_KEY", None):
            product_search.search_external("shoes")

        _, kwargs = mock_get.call_args
        self.assertNotIn("Authorization", kwargs.get("headers", {}))

    def test_empty_query_returns_empty_list_without_calling_api(self):
        with patch("tools.product_search.requests.get") as mock_get:
            results = product_search.search_external("")
            self.assertEqual(results, [])
            mock_get.assert_not_called()

    @patch("tools.product_search.requests.get")
    def test_api_error_returns_empty_list_not_exception(self, mock_get):
        mock_get.side_effect = Exception("timeout")
        results = product_search.search_external("shoes")
        self.assertEqual(results, [])


class TestSearchAgentFallback(unittest.TestCase):

    def setUp(self):
        # Import here so the mocked env vars / module state don't leak
        from agents.search_agent import SearchAgent
        self.SearchAgent = SearchAgent

    @patch("agents.search_agent.search_external")
    @patch("agents.search_agent.search_internal")
    @patch.object(__import__("agents.search_agent", fromlist=["SearchAgent"]).SearchAgent,
                   "extract_filters", return_value={"keyword": "running shoes"})
    @patch.object(__import__("agents.search_agent", fromlist=["SearchAgent"]).SearchAgent,
                   "generate_general_reply", return_value="Here are some picks!")
    def test_uses_internal_when_available_does_not_call_external(
        self, mock_reply, mock_extract, mock_internal, mock_external
    ):
        mock_internal.return_value = [{"id": 1, "name": "Shoe", "price": 1000, "source": "internal"}]

        agent = self.SearchAgent()
        result = agent.process("running shoes", {"user_context": {}, "history": []})

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["source"], "internal")
        mock_external.assert_not_called()

    @patch("agents.search_agent.search_external")
    @patch("agents.search_agent.search_internal")
    @patch.object(__import__("agents.search_agent", fromlist=["SearchAgent"]).SearchAgent,
                   "extract_filters", return_value={"keyword": "flying carpet"})
    @patch.object(__import__("agents.search_agent", fromlist=["SearchAgent"]).SearchAgent,
                   "generate_general_reply", return_value="Found something online!")
    def test_falls_back_to_external_when_internal_empty(
        self, mock_reply, mock_extract, mock_internal, mock_external
    ):
        mock_internal.return_value = []
        mock_external.return_value = [{"id": None, "name": "Magic Carpet", "price": 999, "source": "external"}]

        agent = self.SearchAgent()
        result = agent.process("flying carpet", {"user_context": {}, "history": []})

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["source"], "external")
        mock_external.assert_called_once()

    @patch("agents.search_agent.search_external")
    @patch("agents.search_agent.search_internal")
    @patch.object(__import__("agents.search_agent", fromlist=["SearchAgent"]).SearchAgent,
                   "extract_filters", return_value={"keyword": "nonexistent item xyz"})
    def test_no_results_when_both_empty(self, mock_extract, mock_internal, mock_external):
        mock_internal.return_value = []
        mock_external.return_value = []

        agent = self.SearchAgent()
        result = agent.process("nonexistent item xyz", {"user_context": {}, "history": []})

        self.assertEqual(result["status"], "no_results")


if __name__ == "__main__":
    unittest.main()