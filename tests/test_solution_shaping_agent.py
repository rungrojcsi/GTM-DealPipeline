"""Unit tests for solution_shaping_agent.py (module/function breakdown + Go/No-Go gate agent).

รัน: python -m unittest tests.test_solution_shaping_agent   (จาก GTM root)
"""
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # GTM root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # tests/ (for _fakes)

from _fakes import FakeMessage, make_authentication_error  # noqa: E402

import solution_shaping_agent  # noqa: E402

VALID_RESULT = {
    "solution_design": [],
    "function_summary": {
        "total_functions": 10, "standard_count": 7, "custom_count": 2, "integration_count": 1,
        "must_have_count": 6, "customization_ratio": 30,
    },
    "out_of_scope": [],
    "f3_assessment": {
        "solution_fit": {"score": 4, "reasoning": "covers most requirements"},
        "competitive_force": {"score": 3, "reasoning": "one competitor shortlisted"},
        "feasibility": {"score": 4, "reasoning": "team and timeline ready"},
        "total": 11, "tier_confirm": 2,
    },
    "risk_assessment": {"technical_risks": [], "business_risks": []},
    "go_nogo": {"decision": "Go", "gate": "Solution Fit (PPS)", "conditions": []},
}

SCORING = {"go_nogo": "Go", "banti": {"total": 80}, "tier": 3}

DISCOVERY = {
    "overall_fit": "Partial Fit",
    "overall_difficulty": "Medium",
    "recommended_approach": "Deploy WMS with custom putaway module.",
    "matched_solutions": [
        {"solution_name": "WMS", "fit_level": "Partial Fit", "fit_reasoning": "Covers core ops"},
        {"solution_name": "BI", "fit_level": "Full Fit", "fit_reasoning": "Out of the box dashboards"},
    ],
    "out_of_scope": ["Machine automation control", "Legacy payroll integration"],
}


class ShapeSolutionTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8")
        self._tmp.write("# Solution Master (test fixture)\n## WMS\nCapabilities: ...\n")
        self._tmp.close()
        self.addCleanup(os.unlink, self._tmp.name)

    def test_parses_plain_json_response(self):
        with patch.object(solution_shaping_agent.client.messages, "create", return_value=FakeMessage(json.dumps(VALID_RESULT))) as mock_create:
            result = solution_shaping_agent.shape_solution("deal ctx", SCORING, DISCOVERY, self._tmp.name)
        self.assertEqual(result, VALID_RESULT)
        _, kwargs = mock_create.call_args
        self.assertEqual(kwargs["model"], "claude-sonnet-4-6")
        self.assertEqual(kwargs["max_tokens"], 8192)

    def test_matched_solutions_summary_lists_every_solution(self):
        with patch.object(solution_shaping_agent.client.messages, "create", return_value=FakeMessage(json.dumps(VALID_RESULT))) as mock_create:
            solution_shaping_agent.shape_solution("deal ctx", SCORING, DISCOVERY, self._tmp.name)
        user_message = mock_create.call_args.kwargs["messages"][0]["content"]
        self.assertIn("- WMS: Partial Fit | Covers core ops", user_message)
        self.assertIn("- BI: Full Fit | Out of the box dashboards", user_message)

    def test_out_of_scope_items_are_bulleted(self):
        with patch.object(solution_shaping_agent.client.messages, "create", return_value=FakeMessage(json.dumps(VALID_RESULT))) as mock_create:
            solution_shaping_agent.shape_solution("deal ctx", SCORING, DISCOVERY, self._tmp.name)
        user_message = mock_create.call_args.kwargs["messages"][0]["content"]
        self.assertIn("- Machine automation control", user_message)
        self.assertIn("- Legacy payroll integration", user_message)

    def test_empty_discovery_result_does_not_crash(self):
        with patch.object(solution_shaping_agent.client.messages, "create", return_value=FakeMessage(json.dumps(VALID_RESULT))) as mock_create:
            result = solution_shaping_agent.shape_solution("deal ctx", SCORING, {}, self._tmp.name)
        self.assertEqual(result, VALID_RESULT)
        user_message = mock_create.call_args.kwargs["messages"][0]["content"]
        self.assertIn("Overall Fit: N/A", user_message)

    def test_strips_json_labeled_code_fence(self):
        fenced = "```json\n" + json.dumps(VALID_RESULT) + "\n```"
        with patch.object(solution_shaping_agent.client.messages, "create", return_value=FakeMessage(fenced)):
            result = solution_shaping_agent.shape_solution("deal ctx", SCORING, DISCOVERY, self._tmp.name)
        self.assertEqual(result, VALID_RESULT)

    def test_invalid_json_raises_runtimeerror(self):
        with patch.object(solution_shaping_agent.client.messages, "create", return_value=FakeMessage("not json")):
            with self.assertRaises(RuntimeError):
                solution_shaping_agent.shape_solution("deal ctx", SCORING, DISCOVERY, self._tmp.name)

    def test_authentication_error_wrapped_as_runtimeerror(self):
        with patch.object(solution_shaping_agent.client.messages, "create", side_effect=make_authentication_error()):
            with self.assertRaises(RuntimeError) as ctx:
                solution_shaping_agent.shape_solution("deal ctx", SCORING, DISCOVERY, self._tmp.name)
        self.assertIn("API Key ไม่ถูกต้อง", str(ctx.exception))

    def test_generic_exception_wrapped_as_runtimeerror(self):
        with patch.object(solution_shaping_agent.client.messages, "create", side_effect=ValueError("boom")):
            with self.assertRaises(RuntimeError) as ctx:
                solution_shaping_agent.shape_solution("deal ctx", SCORING, DISCOVERY, self._tmp.name)
        self.assertIn("boom", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
