"""
Tests for agents/recommendation_agent.py.

occasion_nlp / occasion_engine are mocked — this is a unit test for the
agent's control flow (confidence gating, no-results handling, error
handling), not an integration test against the real occasion data.

Run with: python -m unittest backend.tests.test_recommendation_agent -v
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.recommendation_agent import RecommendationAgent  # noqa: E402


class TestRecommendationAgent(unittest.TestCase):

    def setUp(self):
        self.agent = RecommendationAgent()

    @patch("agents.recommendation_agent.get_user_preferences", return_value={})
    @patch("agents.recommendation_agent.classify_occasion")
    def test_low_confidence_short_circuits_before_any_fetch(self, mock_classify, mock_prefs):
        mock_classify.return_value = {"occasion": None, "confidence": 0.05, "method": "keyword"}

        with patch("agents.recommendation_agent.fetch_outfit_set") as mock_outfit, \
             patch("agents.recommendation_agent.fetch_occasion_products") as mock_products:
            result = self.agent.process("hello", {"user_id": None, "user_context": {}, "history": []})

        self.assertEqual(result["status"], "low_confidence")
        mock_outfit.assert_not_called()
        mock_products.assert_not_called()

    @patch("agents.recommendation_agent.get_user_preferences", return_value={})
    @patch("agents.recommendation_agent.classify_occasion")
    @patch("agents.recommendation_agent.fetch_outfit_set")
    @patch("agents.recommendation_agent.fetch_occasion_products")
    @patch.object(RecommendationAgent, "generate_occasion_reply", return_value="Great pick for the gym!")
    def test_success_path_returns_products_and_outfit(
        self, mock_reply, mock_products, mock_outfit, mock_classify, mock_prefs
    ):
        mock_classify.return_value = {"occasion": "gym", "confidence": 0.9, "method": "keyword"}
        mock_outfit.return_value = {"top": {"name": "Tee", "brand": "Puma", "price": 999, "match_pct": 90}}
        mock_products.return_value = [
            {"name": "Shorts", "brand": "Nike", "price": 799, "rating": 4.2}
        ]

        result = self.agent.process("what to wear to the gym", {"user_id": 1, "user_context": {}, "history": []})

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["occasion"], "gym")
        self.assertTrue(len(result["products"]) >= 1)
        self.assertIn("top", result["outfit"])

    @patch("agents.recommendation_agent.get_user_preferences", return_value={})
    @patch("agents.recommendation_agent.classify_occasion")
    @patch("agents.recommendation_agent.fetch_outfit_set", return_value={})
    @patch("agents.recommendation_agent.fetch_occasion_products", return_value=[])
    def test_no_results_when_outfit_and_products_both_empty(
        self, mock_products, mock_outfit, mock_classify, mock_prefs
    ):
        mock_classify.return_value = {"occasion": "date_night", "confidence": 0.8, "method": "keyword"}

        result = self.agent.process("date night outfit", {"user_id": 1, "user_context": {}, "history": []})

        self.assertEqual(result["status"], "no_results")
        self.assertIn("reply", result)

    @patch("agents.recommendation_agent.get_user_preferences", return_value={})
    @patch("agents.recommendation_agent.classify_occasion")
    @patch("agents.recommendation_agent.fetch_outfit_set", side_effect=RuntimeError("db down"))
    def test_exception_returns_error_status_not_crash(self, mock_outfit, mock_classify, mock_prefs):
        mock_classify.return_value = {"occasion": "office", "confidence": 0.7, "method": "keyword"}

        result = self.agent.process("office wear", {"user_id": 1, "user_context": {}, "history": []})

        self.assertEqual(result["status"], "error")
        self.assertIn("db down", result["error"])


if __name__ == "__main__":
    unittest.main()