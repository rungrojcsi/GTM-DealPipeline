"""Unit tests for scoring_agent.py (BANTi-F3 deal qualification agent).

รัน: python -m unittest tests.test_scoring_agent   (จาก GTM root)
     หรือ python tests/test_scoring_agent.py
"""
import json
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # GTM root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # tests/ (for _fakes)

from _fakes import FakeMessage, make_authentication_error  # noqa: E402

import scoring_agent  # noqa: E402

VALID_RESULT = {
    "banti": {"budget": 20, "authority": 20, "need": 20, "timing": 20, "interest": 20, "total": 100},
    "f3": {"solution_fit": 5, "competitive_force": 5, "feasibility": 5, "total": 15},
    "go_nogo": "Go",
    "tier": 3,
    "reasoning": "Strong budget and executive sponsorship.",
    "risk_flags": [],
}


class ScoreDealTests(unittest.TestCase):
    def test_parses_plain_json_response(self):
        with patch.object(scoring_agent.client.messages, "create", return_value=FakeMessage(json.dumps(VALID_RESULT))) as mock_create:
            result = scoring_agent.score_deal("Company X needs an ERP, budget confirmed, go-live in 60 days.")
        self.assertEqual(result, VALID_RESULT)
        _, kwargs = mock_create.call_args
        self.assertEqual(kwargs["model"], "claude-sonnet-4-6")
        self.assertEqual(kwargs["max_tokens"], 1000)
        self.assertEqual(kwargs["messages"], [{"role": "user", "content": "Company X needs an ERP, budget confirmed, go-live in 60 days."}])

    def test_strips_json_labeled_code_fence(self):
        fenced = "```json\n" + json.dumps(VALID_RESULT) + "\n```"
        with patch.object(scoring_agent.client.messages, "create", return_value=FakeMessage(fenced)):
            result = scoring_agent.score_deal("deal context")
        self.assertEqual(result, VALID_RESULT)

    def test_strips_unlabeled_code_fence(self):
        fenced = "```\n" + json.dumps(VALID_RESULT) + "\n```"
        with patch.object(scoring_agent.client.messages, "create", return_value=FakeMessage(fenced)):
            result = scoring_agent.score_deal("deal context")
        self.assertEqual(result, VALID_RESULT)

    def test_invalid_json_raises_systemexit(self):
        with patch.object(scoring_agent.client.messages, "create", return_value=FakeMessage("this is not json")):
            with self.assertRaises(SystemExit):
                scoring_agent.score_deal("deal context")

    def test_authentication_error_raises_systemexit_with_thai_message(self):
        with patch.object(scoring_agent.client.messages, "create", side_effect=make_authentication_error()):
            with self.assertRaises(SystemExit) as ctx:
                scoring_agent.score_deal("deal context")
        self.assertIn("API Key ไม่ถูกต้อง", str(ctx.exception))


class GetActivePromptTests(unittest.TestCase):
    def test_falls_back_to_default_system_prompt_when_no_optimized_file(self):
        with patch.object(os.path, "exists", return_value=False):
            self.assertEqual(scoring_agent.get_active_prompt(), scoring_agent.SYSTEM_PROMPT)

    def test_reads_optimized_prompt_file_when_present(self):
        with patch.object(os.path, "exists", return_value=True), \
             patch("builtins.open", unittest.mock.mock_open(read_data="OPTIMIZED PROMPT TEXT")):
            self.assertEqual(scoring_agent.get_active_prompt(), "OPTIMIZED PROMPT TEXT")


if __name__ == "__main__":
    unittest.main()
