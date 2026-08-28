"""Unit tests for discovery_agent.py (Solution Master fit-mapping agent).

รัน: python -m unittest tests.test_discovery_agent   (จาก GTM root)
"""
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # GTM root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # tests/ (for _fakes)

from _fakes import FakeMessage  # noqa: E402

import discovery_agent  # noqa: E402

VALID_RESULT = {
    "matched_solutions": [
        {
            "solution_name": "WMS",
            "fit_level": "Partial Fit",
            "fit_reasoning": "Covers core warehouse ops, needs custom putaway logic.",
            "customization_needed": ["custom putaway rules"],
            "difficulty": "Medium",
        }
    ],
    "overall_fit": "Partial Fit",
    "overall_difficulty": "Medium",
    "recommended_approach": "Deploy WMS with custom putaway module.",
    "out_of_scope": [],
    "next_step": "Proceed to Solution Shaping",
}

FULL_SCORING = {
    "banti": {"total": 80},
    "f3": {"total": 12},
    "tier": 3,
    "go_nogo": "Go",
    "reasoning": "Clear budget and executive sponsor.",
}


class DiscoverDealTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8")
        self._tmp.write("# Solution Master (test fixture)\n## WMS\nCapabilities: ...\n")
        self._tmp.close()
        self.addCleanup(os.unlink, self._tmp.name)

    def test_parses_plain_json_response(self):
        with patch.object(discovery_agent.client.messages, "create", return_value=FakeMessage(json.dumps(VALID_RESULT))) as mock_create:
            result = discovery_agent.discover_deal("Need WMS for 3 warehouses.", FULL_SCORING, self._tmp.name)
        self.assertEqual(result, VALID_RESULT)
        _, kwargs = mock_create.call_args
        self.assertEqual(kwargs["model"], "claude-sonnet-4-6")
        self.assertEqual(kwargs["max_tokens"], 2000)

    def test_scoring_summary_is_substituted_into_user_message(self):
        with patch.object(discovery_agent.client.messages, "create", return_value=FakeMessage(json.dumps(VALID_RESULT))) as mock_create:
            discovery_agent.discover_deal("Need WMS.", FULL_SCORING, self._tmp.name)
        user_message = mock_create.call_args.kwargs["messages"][0]["content"]
        self.assertIn("Go/No-Go: Go", user_message)
        self.assertIn("BANTi Total: 80 / 100", user_message)
        self.assertIn("F³ Total: 12 / 15", user_message)
        self.assertIn("Tier: 3", user_message)
        self.assertIn("Clear budget and executive sponsor.", user_message)

    def test_missing_scoring_fields_default_to_NA(self):
        with patch.object(discovery_agent.client.messages, "create", return_value=FakeMessage(json.dumps(VALID_RESULT))) as mock_create:
            discovery_agent.discover_deal("Need WMS.", {}, self._tmp.name)
        user_message = mock_create.call_args.kwargs["messages"][0]["content"]
        self.assertIn("Go/No-Go: N/A", user_message)
        self.assertIn("BANTi Total: N/A / 100", user_message)
        self.assertIn("F³ Total: N/A / 15", user_message)
        self.assertIn("Tier: N/A", user_message)

    def test_solution_master_file_content_is_read_and_embedded_in_system_prompt(self):
        with patch.object(discovery_agent.client.messages, "create", return_value=FakeMessage(json.dumps(VALID_RESULT))) as mock_create:
            discovery_agent.discover_deal("Need WMS.", FULL_SCORING, self._tmp.name)
        system_prompt = mock_create.call_args.kwargs["system"]
        self.assertIn("Solution Master (test fixture)", system_prompt)

    def test_defaults_to_DEFAULT_SOLUTION_MASTER_when_path_omitted(self):
        with patch("builtins.open", unittest.mock.mock_open(read_data="# real master")) as mock_open, \
             patch.object(discovery_agent.client.messages, "create", return_value=FakeMessage(json.dumps(VALID_RESULT))):
            discovery_agent.discover_deal("Need WMS.", FULL_SCORING)
        mock_open.assert_called_once_with(discovery_agent.DEFAULT_SOLUTION_MASTER, "r", encoding="utf-8")

    def test_strips_json_labeled_code_fence(self):
        fenced = "```json\n" + json.dumps(VALID_RESULT) + "\n```"
        with patch.object(discovery_agent.client.messages, "create", return_value=FakeMessage(fenced)):
            result = discovery_agent.discover_deal("Need WMS.", FULL_SCORING, self._tmp.name)
        self.assertEqual(result, VALID_RESULT)

    def test_invalid_json_raises_runtimeerror(self):
        with patch.object(discovery_agent.client.messages, "create", return_value=FakeMessage("not json")):
            with self.assertRaises(RuntimeError):
                discovery_agent.discover_deal("Need WMS.", FULL_SCORING, self._tmp.name)


if __name__ == "__main__":
    unittest.main()
