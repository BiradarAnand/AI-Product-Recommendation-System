"""
Tests for tools/memory_tools.py and agents/memory_agent.py.

DB calls are mocked — unit tests for query shape and dispatch logic,
not integration tests against a live TiDB instance.

Run with: python -m unittest backend.tests.test_memory_agent -v
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import memory_tools  # noqa: E402
from agents.memory_agent import MemoryAgent  # noqa: E402


class TestMemoryTools(unittest.TestCase):

    def test_fetch_user_context_no_user_id_returns_empty_dict(self):
        self.assertEqual(memory_tools.fetch_user_context(None), {})

    @patch("tools.memory_tools.get_db")
    def test_fetch_user_context_builds_expected_shape(self, mock_get_db):
        mock_cur = MagicMock()
        # first execute() -> search_history, second -> wishlist
        mock_cur.fetchall.side_effect = [
            [{"search_query": "running shoes"}, {"search_query": "watches"}],
            [{"category": "Sports Shoes", "brand": "Puma"},
             {"category": "Watches", "brand": "Fossil"}],
        ]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_get_db.return_value = mock_conn

        result = memory_tools.fetch_user_context(user_id=42)

        self.assertEqual(result["recent_searches"], ["running shoes", "watches"])
        self.assertIn("Sports Shoes", result["wishlist_categories"])
        self.assertIn("Puma", result["wishlist_brands"])
        self.assertEqual(mock_cur.execute.call_count, 2)

    @patch("tools.memory_tools.get_db")
    def test_fetch_user_context_db_error_returns_empty_dict(self, mock_get_db):
        mock_get_db.side_effect = RuntimeError("connection refused")
        result = memory_tools.fetch_user_context(user_id=42)
        self.assertEqual(result, {})

    def test_save_search_noop_without_user_id_or_query(self):
        # should not raise, and should never touch the DB
        with patch("tools.memory_tools.get_db") as mock_get_db:
            memory_tools.save_search(None, "some query")
            memory_tools.save_search(42, "")
            mock_get_db.assert_not_called()

    @patch("tools.memory_tools.get_db")
    def test_save_search_inserts_and_commits(self, mock_get_db):
        mock_cur = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_get_db.return_value = mock_conn

        memory_tools.save_search(42, "running shoes")

        mock_cur.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    @patch("tools.memory_tools.get_db")
    def test_save_search_db_error_does_not_raise(self, mock_get_db):
        mock_get_db.side_effect = RuntimeError("connection refused")
        try:
            memory_tools.save_search(42, "running shoes")
        except Exception as e:
            self.fail(f"save_search raised unexpectedly: {e}")


class TestMemoryAgentDispatch(unittest.TestCase):

    def setUp(self):
        self.agent = MemoryAgent()

    @patch("agents.memory_agent.fetch_user_context", return_value={"recent_searches": ["x"]})
    def test_retrieve_action_calls_fetch(self, mock_fetch):
        result = self.agent.process("ignored", {"user_id": 42}, action="retrieve")
        mock_fetch.assert_called_once_with(42)
        self.assertEqual(result, {"recent_searches": ["x"]})

    @patch("agents.memory_agent.save_search")
    def test_save_action_calls_save_and_returns_status(self, mock_save):
        result = self.agent.process("running shoes", {"user_id": 42}, action="save")
        mock_save.assert_called_once_with(42, "running shoes")
        self.assertEqual(result, {"status": "saved"})

    def test_unknown_action_returns_empty_dict(self):
        result = self.agent.process("x", {"user_id": 42}, action="something_else")
        self.assertEqual(result, {})

    @patch("agents.memory_agent.fetch_user_context", return_value={})
    def test_default_action_is_retrieve(self, mock_fetch):
        # no action kwarg passed at all
        self.agent.process("x", {"user_id": 42})
        mock_fetch.assert_called_once_with(42)


if __name__ == "__main__":
    unittest.main()