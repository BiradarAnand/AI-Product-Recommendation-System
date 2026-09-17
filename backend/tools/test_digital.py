"""
Tests for tools/digital_twin_tools.py and agents/digital_twin_agent.py.

DB and Groq calls are mocked — unit tests for persona-building and the
agent's control flow, not integration tests against live services.

Run with: python -m unittest backend.tests.test_digital_twin_agent -v
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import digital_twin_tools  # noqa: E402
from agents.digital_twin_agent import DigitalTwinAgent  # noqa: E402


class TestDigitalTwinTools(unittest.TestCase):

    def test_no_user_id_returns_guest_persona(self):
        result = digital_twin_tools.fetch_user_persona(None)
        self.assertEqual(result["demographics"], "Guest User")

    @patch("tools.digital_twin_tools.get_db")
    def test_builds_persona_from_user_and_wishlist(self, mock_get_db):
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {"email": "a@x.com", "name": "Anand"}
        mock_cur.fetchall.return_value = [
            {"category": "Sneakers", "brand": "Puma"},
            {"category": "Watches", "brand": "Fossil"},
        ]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_get_db.return_value = mock_conn

        result = digital_twin_tools.fetch_user_persona(user_id=1)

        self.assertEqual(result["name"], "Anand")
        self.assertIn("Sneakers", result["preferences"])
        self.assertIn("Puma", result["preferences"])

    @patch("tools.digital_twin_tools.get_db")
    def test_db_error_returns_unknown_persona_not_exception(self, mock_get_db):
        mock_get_db.side_effect = RuntimeError("connection refused")
        result = digital_twin_tools.fetch_user_persona(user_id=1)
        self.assertEqual(result["demographics"], "Unknown")


class TestDigitalTwinAgent(unittest.TestCase):

    def setUp(self):
        self.agent = DigitalTwinAgent()

    def test_no_products_short_circuits(self):
        result = self.agent.process("query", {"user_id": 1, "products": []})
        self.assertEqual(result["status"], "no_products")

    @patch("agents.digital_twin_agent.fetch_user_persona")
    @patch.object(DigitalTwinAgent, "evaluate_products")
    def test_success_path_combines_persona_and_evaluation(self, mock_eval, mock_persona):
        mock_persona.return_value = {"name": "Anand", "preferences": "Sneakers"}
        mock_eval.return_value = {"overall_rating": 8, "feedback": "Good fit", "approved_product_ids": [1, 2]}

        products = [{"id": 1, "name": "Shoe", "brand": "Puma", "price": 2499, "category": "Sneakers"}]
        result = self.agent.process("find me shoes", {"user_id": 1, "products": products})

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["persona"]["name"], "Anand")
        self.assertEqual(result["evaluation"]["overall_rating"], 8)
        mock_persona.assert_called_once_with(1)

    @patch("agents.digital_twin_agent.groq_client")
    @patch("agents.digital_twin_agent.fetch_user_persona", return_value={})
    def test_evaluate_products_falls_back_on_bad_json(self, mock_persona, mock_groq_client):
        mock_message = MagicMock()
        mock_message.content = "not valid json at all"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_groq_client.chat.completions.create.return_value = mock_response

        products = [{"id": 1, "name": "Shoe", "brand": "Puma", "price": 2499, "category": "Sneakers"}]
        result = self.agent.process("find me shoes", {"user_id": 1, "products": products})

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["evaluation"]["overall_rating"], 5)
        self.assertEqual(result["evaluation"]["approved_product_ids"], [])


if __name__ == "__main__":
    unittest.main()