"""Unit tests for the testable business logic in app.py (Gradio UI for the Discovery RAG pipeline).

ครอบคลุม: CSV logging helpers, HTML render helpers, and the tab callback functions
(submit/run_discovery/run_shaping/load_history/analyze_feedback_fn/...).

ไม่ครอบคลุม: การสร้าง gr.Blocks()/Tabs()/event wiring เอง (บรรทัด 776+ ของ app.py) — ต้องมี
browser/Gradio server จริงถึงจะตรวจ UI rendering ได้ (อยู่นอกขอบเขต unit test).

รัน: python -m unittest tests.test_app   (จาก GTM root)
"""
import csv
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # GTM root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # tests/ (for _fakes -> sets dummy API key)

import _fakes  # noqa: F401,E402 — ตั้ง ANTHROPIC_API_KEY dummy ก่อน import app

import app  # noqa: E402
import render  # noqa: E402


def _tmpfile(suffix=".csv"):
    f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    f.close()
    os.unlink(f.name)  # ให้ _ensure_log สร้างใหม่เอง (ทดสอบ path "ยังไม่มีไฟล์")
    return f.name


# =====================================================================
# Pure string/HTML helpers
# =====================================================================
class ScoreBarTests(unittest.TestCase):
    def test_zero_score_is_all_empty_blocks(self):
        self.assertEqual(app._score_bar(0, 100), "░" * 20)

    def test_full_score_is_all_filled_blocks(self):
        self.assertEqual(app._score_bar(100, 100), "█" * 20)

    def test_half_score_splits_evenly(self):
        self.assertEqual(app._score_bar(10, 20), "█" * 10 + "░" * 10)


class BadgeTests(unittest.TestCase):
    def test_includes_text_and_color(self):
        html = app._badge("GO", "#16a34a")
        self.assertIn("GO", html)
        self.assertIn("#16a34a", html)


class BuildDealContextTests(unittest.TestCase):
    def test_all_fields_interpolated_with_labels(self):
        ctx = app.build_deal_context("ACME", "Alex - CTO", "2M THB", "ERP slow", "60 days", "none", "champion pushing")
        self.assertIn("Company: ACME", ctx)
        self.assertIn("Contact & Role: Alex - CTO", ctx)
        self.assertIn("Budget: 2M THB", ctx)
        self.assertIn("Need & Pain: ERP slow", ctx)
        self.assertIn("Timeline: 60 days", ctx)
        self.assertIn("Competitors: none", ctx)
        self.assertIn("Interest Level: champion pushing", ctx)


class GetCurrentPromptTests(unittest.TestCase):
    def test_uses_default_when_no_optimized_file(self):
        with patch.object(app.os.path, "exists", return_value=False):
            prompt, msg = app.get_current_prompt()
        self.assertEqual(prompt, app.SYSTEM_PROMPT)
        self.assertIn("default", msg)

    def test_uses_optimized_file_when_present(self):
        with patch.object(app.os.path, "exists", return_value=True), \
             patch("builtins.open", unittest.mock.mock_open(read_data="OPTIMIZED")):
            prompt, msg = app.get_current_prompt()
        self.assertEqual(prompt, "OPTIMIZED")
        self.assertIn("optimized", msg)


# =====================================================================
# Shaping render helpers — pure HTML builders
# =====================================================================
class RenderShapingDesignTests(unittest.TestCase):
    def test_empty_list_shows_placeholder(self):
        self.assertIn("ไม่มีข้อมูล", app._render_shaping_design([]))

    def test_renders_solution_module_and_function_names(self):
        design = [{
            "solution_name": "WMS",
            "modules": [{
                "module_name": "Inbound", "module_purpose": "Receive goods",
                "estimated_complexity": "Medium",
                "function_list": [{"function_name": "Scan barcode", "description": "scan",
                                    "type": "Standard", "priority": "Must Have", "pain_addressed": "manual entry"}],
            }],
        }]
        html = app._render_shaping_design(design)
        self.assertIn("WMS", html)
        self.assertIn("Inbound", html)
        self.assertIn("Scan barcode", html)


class RenderFunctionSummaryTests(unittest.TestCase):
    def test_zero_total_does_not_divide_by_zero(self):
        html = app._render_function_summary({"total_functions": 0})
        self.assertIn("0%", html)

    def test_ratio_color_thresholds(self):
        self.assertIn("#16a34a", app._render_function_summary({"total_functions": 10, "customization_ratio": 20}))
        self.assertIn("#d97706", app._render_function_summary({"total_functions": 10, "customization_ratio": 45}))
        self.assertIn("#dc2626", app._render_function_summary({"total_functions": 10, "customization_ratio": 80}))


class RenderF3Tests(unittest.TestCase):
    def test_int_tier_uses_tier_label(self):
        html = app._render_f3({"tier_confirm": 2, "total": 10})
        self.assertIn(app.TIER_LABELS[2], html)

    def test_non_int_tier_falls_back_to_dash(self):
        html = app._render_f3({"tier_confirm": "—", "total": 0})
        self.assertIn(">—<", html)


class RenderRisksTests(unittest.TestCase):
    def test_empty_risks_show_none_placeholder(self):
        html = app._render_risks({})
        self.assertIn("ไม่มี", html)

    def test_risk_rows_include_severity_badge(self):
        html = app._render_risks({"technical_risks": [{"risk": "legacy integration", "severity": "High", "mitigation": "poc first"}]})
        self.assertIn("legacy integration", html)
        self.assertIn(render.SEVERITY_COLORS["High"], html)


class RenderGoNoGoTests(unittest.TestCase):
    def test_go_decision_is_green_with_checkmark(self):
        html = app._render_gonogo({"decision": "Go", "gate": "Solution Fit"})
        self.assertIn("✅", html)
        self.assertIn("#16a34a", html)

    def test_nogo_decision_is_red_with_cross(self):
        html = app._render_gonogo({"decision": "No-Go", "gate": "Solution Fit"})
        self.assertIn("❌", html)
        self.assertIn("#dc2626", html)

    def test_empty_conditions_shows_placeholder(self):
        html = app._render_gonogo({"decision": "Go", "gate": "x", "conditions": []})
        self.assertIn("ไม่มีเงื่อนไข", html)


# =====================================================================
# CSV logging helpers
# =====================================================================
class EnsureLogTests(unittest.TestCase):
    def test_creates_file_with_header_when_missing(self):
        path = _tmpfile()
        try:
            app._ensure_log(path, ["a", "b"])
            with open(path, encoding="utf-8") as f:
                self.assertEqual(f.readline().strip(), "a,b")
        finally:
            os.unlink(path)

    def test_does_not_overwrite_existing_file(self):
        path = _tmpfile()
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("a,b\n1,2\n")
            app._ensure_log(path, ["a", "b"])
            with open(path, encoding="utf-8") as f:
                self.assertEqual(f.read(), "a,b\n1,2\n")
        finally:
            os.unlink(path)


class GenerateDealIdTests(unittest.TestCase):
    def test_first_deal_of_the_day_gets_seq_001(self):
        path = _tmpfile()
        try:
            with patch.object(app, "DEALS_LOG_FILE", path):
                deal_id = app._generate_deal_id()
            today = app.datetime.now().strftime("%Y%m%d")
            self.assertEqual(deal_id, f"GTM-{today}-001")
        finally:
            os.unlink(path)

    def test_increments_sequence_for_existing_deals_today(self):
        path = _tmpfile()
        today = app.datetime.now().strftime("%Y%m%d")
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=app.DEALS_LOG_COLUMNS)
                w.writeheader()
                w.writerow({**{c: "" for c in app.DEALS_LOG_COLUMNS}, "deal_id": f"GTM-{today}-001"})
                w.writerow({**{c: "" for c in app.DEALS_LOG_COLUMNS}, "deal_id": f"GTM-{today}-002"})
            with patch.object(app, "DEALS_LOG_FILE", path):
                deal_id = app._generate_deal_id()
            self.assertEqual(deal_id, f"GTM-{today}-003")
        finally:
            os.unlink(path)


class LogScoringTests(unittest.TestCase):
    def test_writes_row_with_correct_banti_f3_mapping(self):
        path = _tmpfile()
        result = {
            "banti": {"budget": 20, "authority": 20, "need": 20, "timing": 20, "interest": 20, "total": 100},
            "f3": {"solution_fit": 5, "competitive_force": 5, "feasibility": 5, "total": 15},
            "go_nogo": "Go", "tier": 3, "reasoning": "strong", "risk_flags": ["flag1", "flag2"],
        }
        try:
            with patch.object(app, "DEALS_LOG_FILE", path):
                app._log_scoring("GTM-1", "ACME", "CTO", "2M", "need", "60d", "none", "high", result)
            with open(path, encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(rows[0]["banti_total"], "100")
            self.assertEqual(rows[0]["risk_flags"], "flag1; flag2")
            self.assertEqual(rows[0]["stage"], "Scoring")
        finally:
            os.unlink(path)


class UpdateDiscoveryLogTests(unittest.TestCase):
    def test_updates_matching_deal_id_row(self):
        path = _tmpfile()
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=app.DEALS_LOG_COLUMNS)
                w.writeheader()
                w.writerow({**{c: "" for c in app.DEALS_LOG_COLUMNS}, "deal_id": "GTM-1"})
            with patch.object(app, "DEALS_LOG_FILE", path):
                app._update_discovery_log("GTM-1", {
                    "overall_fit": "Partial Fit", "overall_difficulty": "Medium",
                    "matched_solutions": [{"solution_name": "WMS"}], "next_step": "Proceed to Solution Shaping",
                })
            with open(path, encoding="utf-8") as f:
                row = list(csv.DictReader(f))[0]
            self.assertEqual(row["discovery_overall_fit"], "Partial Fit")
            self.assertEqual(row["discovery_matched_solutions"], "WMS")
            self.assertEqual(row["stage"], "Discovery")
        finally:
            os.unlink(path)

    def test_empty_deal_id_is_a_no_op(self):
        path = _tmpfile()
        try:
            with patch.object(app, "DEALS_LOG_FILE", path):
                app._update_discovery_log("", {"overall_fit": "Full Fit"})
            self.assertFalse(os.path.exists(path))  # _ensure_log ไม่เคยถูกเรียกด้วยซ้ำ
        finally:
            if os.path.exists(path):
                os.unlink(path)


# =====================================================================
# Tab 0: Scoring — submit()
# =====================================================================
class SubmitTests(unittest.TestCase):
    def test_blank_company_returns_warning_without_calling_score_deal(self):
        with patch.object(app, "score_deal") as mock_score:
            result = app.submit("  ", "c", "b", "n", "t", "comp", "i")
        self.assertIn("กรุณากรอก Company", result[2]["value"])
        mock_score.assert_not_called()

    def test_score_deal_exception_returns_error_tuple(self):
        with patch.object(app, "score_deal", side_effect=RuntimeError("API down")):
            result = app.submit("ACME", "c", "b", "n", "t", "comp", "i")
        self.assertIn("Error", result[2]["value"])

    def test_go_result_shows_go_badge_and_proceed_button(self):
        result_data = {
            "banti": {"budget": 20, "authority": 20, "need": 20, "timing": 20, "interest": 20, "total": 100},
            "f3": {"solution_fit": 5, "competitive_force": 5, "feasibility": 5, "total": 15},
            "go_nogo": "Go", "tier": 3, "reasoning": "strong", "risk_flags": [],
        }
        path = _tmpfile()
        try:
            with patch.object(app, "score_deal", return_value=result_data), \
                 patch.object(app, "DEALS_LOG_FILE", path), \
                 patch.object(app, "_generate_deal_id", return_value="GTM-1"):
                result = app.submit("ACME", "c", "2M", "n", "t", "comp", "i")
        finally:
            if os.path.exists(path):
                os.unlink(path)
        self.assertIn("GO", result[2]["value"])
        self.assertEqual(result[3], app.TIER_LABELS[3])
        self.assertTrue(result[7]["visible"])   # feedback_group
        self.assertTrue(result[8]["visible"])   # proceed_btn (is_go)
        self.assertFalse(result[9]["visible"])  # nogo_msg

    def test_nogo_result_hides_proceed_button_shows_nogo_message(self):
        result_data = {
            "banti": {"budget": 0, "authority": 0, "need": 0, "timing": 0, "interest": 0, "total": 0},
            "f3": {"solution_fit": 0, "competitive_force": 0, "feasibility": 0, "total": 0},
            "go_nogo": "No-Go", "tier": None, "reasoning": "weak", "risk_flags": ["no budget"],
        }
        path = _tmpfile()
        try:
            with patch.object(app, "score_deal", return_value=result_data), \
                 patch.object(app, "DEALS_LOG_FILE", path), \
                 patch.object(app, "_generate_deal_id", return_value="GTM-1"):
                result = app.submit("ACME", "c", "0", "n", "t", "comp", "i")
        finally:
            if os.path.exists(path):
                os.unlink(path)
        self.assertFalse(result[8]["visible"])  # proceed_btn hidden
        self.assertTrue(result[9]["visible"])   # nogo_msg shown


class ProceedToDiscoveryTests(unittest.TestCase):
    def test_no_prior_result_shows_warning(self):
        tab_update, msg = app.proceed_to_discovery(None, "")
        self.assertIn("ยังไม่มีผล scoring", msg)

    def test_with_result_shows_summary_values(self):
        result = {"banti": {"total": 80}, "f3": {"total": 12}, "tier": 2}
        _, msg = app.proceed_to_discovery(result, "ctx")
        self.assertIn("80/100", msg)
        self.assertIn("12/15", msg)


class SubmitFeedbackTests(unittest.TestCase):
    def test_no_prior_result_shows_warning(self):
        self.assertIn("ยังไม่มีผล", app.submit_feedback("Go", "3", "note", None, "ctx"))

    def test_writes_row_with_null_tier_string_when_tier_falsy(self):
        path = _tmpfile()
        result = {"go_nogo": "Go", "banti": {"total": 80}, "f3": {"total": 12}, "tier": None, "reasoning": "r"}
        try:
            with patch.object(app, "LOG_FILE", path):
                app.submit_feedback("Go", "N/A", "note", result, "ctx")
            with open(path, encoding="utf-8") as f:
                row = list(csv.DictReader(f))[0]
            self.assertEqual(row["ai_tier"], "null")
        finally:
            os.unlink(path)


# =====================================================================
# Tab 1: Discovery — run_discovery()
# =====================================================================
class RunDiscoveryTests(unittest.TestCase):
    def test_no_prior_context_shows_warning(self):
        result = app.run_discovery(None, "", "", "", "")
        self.assertIn("กรุณา Score Deal", result[0])

    def test_discover_deal_exception_returns_error(self):
        with patch.object(app, "discover_deal", side_effect=RuntimeError("boom")):
            result = app.run_discovery({"go_nogo": "Go"}, "ctx", "", "", "")
        self.assertIn("Error", result[0])

    def test_success_includes_solution_and_next_step(self):
        disc_result = {
            "overall_fit": "Partial Fit", "overall_difficulty": "Medium", "next_step": "Proceed to Solution Shaping",
            "recommended_approach": "deploy WMS", "out_of_scope": ["legacy payroll"],
            "matched_solutions": [{"solution_name": "WMS", "fit_level": "Partial Fit",
                                    "fit_reasoning": "covers core", "difficulty": "Medium", "customization_needed": []}],
        }
        with patch.object(app, "discover_deal", return_value=disc_result) as mock_discover:
            header, solutions, oos, nextstep, json_str, result = app.run_discovery(
                {"go_nogo": "Go"}, "ctx", "extra pain", "", "")
        self.assertIn("WMS", solutions)
        self.assertIn("Proceed to Solution Shaping", nextstep)
        enhanced_context = mock_discover.call_args[0][0]
        self.assertIn("Additional Pains", enhanced_context)
        self.assertEqual(result, disc_result)


class SubmitDiscoveryFeedbackTests(unittest.TestCase):
    def test_empty_json_shows_warning(self):
        self.assertIn("ยังไม่มีผล", app.submit_discovery_feedback("Full Fit", "Medium", "note", ""))

    def test_malformed_json_shows_error(self):
        self.assertIn("Error", app.submit_discovery_feedback("Full Fit", "Medium", "note", "not json"))

    def test_success_writes_row(self):
        path = _tmpfile()
        try:
            with patch.object(app, "DISCOVERY_LOG_FILE", path):
                msg = app.submit_discovery_feedback("Full Fit", "Medium", "note",
                                                      json.dumps({"overall_fit": "Partial Fit"}))
            self.assertIn("บันทึก", msg)
            with open(path, encoding="utf-8") as f:
                row = list(csv.DictReader(f))[0]
            self.assertEqual(row["ai_overall_fit"], "Partial Fit")
        finally:
            os.unlink(path)


# =====================================================================
# Tab 2: Solution Shaping — run_shaping()
# =====================================================================
class RunShapingTests(unittest.TestCase):
    def test_no_discovery_json_shows_warning(self):
        result = app.run_shaping("", None, "", "")
        self.assertIn("กรุณา Run Discovery", result[0])

    def test_malformed_discovery_json_shows_error(self):
        result = app.run_shaping("not json", None, "", "")
        self.assertIn("Error", result[0])

    def test_shape_solution_exception_returns_error(self):
        with patch.object(app, "shape_solution", side_effect=RuntimeError("boom")):
            result = app.run_shaping(json.dumps({}), {}, "ctx", "GTM-1")
        self.assertIn("Error", result[0])

    def test_success_updates_shaping_log_and_returns_rendered_sections(self):
        shaping_result = {
            "solution_design": [], "function_summary": {"total_functions": 0},
            "f3_assessment": {"total": 0}, "risk_assessment": {},
            "go_nogo": {"decision": "Go"}, "out_of_scope": [],
        }
        path = _tmpfile()
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=app.DEALS_LOG_COLUMNS)
                w.writeheader()
                w.writerow({**{c: "" for c in app.DEALS_LOG_COLUMNS}, "deal_id": "GTM-1"})
            with patch.object(app, "shape_solution", return_value=shaping_result), \
                 patch.object(app, "DEALS_LOG_FILE", path):
                result = app.run_shaping(json.dumps({}), {}, "ctx", "GTM-1")
            with open(path, encoding="utf-8") as f:
                row = list(csv.DictReader(f))[0]
            self.assertEqual(row["stage"], "Solution Shaping")
        finally:
            os.unlink(path)
        self.assertEqual(result[0], "")  # warning cleared


class SubmitShapingFeedbackTests(unittest.TestCase):
    def test_empty_json_shows_warning(self):
        self.assertIn("ยังไม่มีผล", app.submit_shaping_feedback("Go", "note", "", "GTM-1"))

    def test_success_extracts_nested_fields(self):
        path = _tmpfile()
        shaping_result = {
            "f3_assessment": {"solution_fit": {"score": 4}, "feasibility": {"score": 3}, "total": 10, "tier_confirm": 2},
            "function_summary": {"customization_ratio": 25},
            "go_nogo": {"decision": "Go"},
        }
        try:
            with patch.object(app, "SHAPING_LOG_FILE", path):
                app.submit_shaping_feedback("Go", "note", json.dumps(shaping_result), "GTM-1")
            with open(path, encoding="utf-8") as f:
                row = list(csv.DictReader(f))[0]
            self.assertEqual(row["ai_solution_fit"], "4")
            self.assertEqual(row["ai_customization_ratio"], "25")
        finally:
            os.unlink(path)


# =====================================================================
# Tab 3: History
# =====================================================================
class LoadHistoryTests(unittest.TestCase):
    def test_no_data_shows_placeholder(self):
        path = _tmpfile()
        try:
            with patch.object(app, "DEALS_LOG_FILE", path):
                df, summary = app.load_history()
            self.assertEqual(summary, "ยังไม่มีข้อมูล")
            self.assertTrue(df.empty)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_computes_go_rate_and_avg_banti(self):
        path = _tmpfile()
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=app.DEALS_LOG_COLUMNS)
                w.writeheader()
                base = {c: "" for c in app.DEALS_LOG_COLUMNS}
                w.writerow({**base, "deal_id": "GTM-1", "go_nogo": "Go", "banti_total": "80",
                            "discovery_overall_fit": "Full Fit"})
                w.writerow({**base, "deal_id": "GTM-2", "go_nogo": "No-Go", "banti_total": "40",
                            "discovery_overall_fit": "Partial Fit"})
            with patch.object(app, "DEALS_LOG_FILE", path):
                df, summary = app.load_history()
            self.assertIn("Total deals:** 2", summary)
            self.assertIn("Go rate:** 50.0%", summary)
            self.assertIn("Avg BANTi:** 60.0", summary)
        finally:
            os.unlink(path)


# =====================================================================
# Tab 4: Prompt Optimizer
# =====================================================================
class AnalyzeFeedbackFnTests(unittest.TestCase):
    def test_no_log_data_shows_warning(self):
        path = _tmpfile()
        try:
            with patch.object(app, "LOG_FILE", path):
                prompt, msg = app.analyze_feedback_fn()
            self.assertIn("ยังไม่มีข้อมูล", msg)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_no_wrong_cases_reports_perfect_accuracy(self):
        path = _tmpfile()
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=app.LOG_COLUMNS)
                w.writeheader()
                w.writerow({**{c: "" for c in app.LOG_COLUMNS}, "ai_gonogo": "Go", "correct_gonogo": "Go",
                            "ai_tier": "3", "correct_tier": "3"})
            with patch.object(app, "LOG_FILE", path):
                _, msg = app.analyze_feedback_fn()
            self.assertIn("ไม่มีเคสที่ผิดเลย", msg)
        finally:
            os.unlink(path)

    def test_wrong_cases_calls_llm_and_splits_analysis_from_prompt(self):
        path = _tmpfile()
        fake_resp = MagicMock()
        fake_resp.content = [MagicMock(text="ANALYSIS:\nAI over-scored budget.\n\nIMPROVED PROMPT:\nNew system prompt here")]
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=app.LOG_COLUMNS)
                w.writeheader()
                w.writerow({**{c: "" for c in app.LOG_COLUMNS}, "ai_gonogo": "Go", "correct_gonogo": "No-Go",
                            "ai_tier": "3", "correct_tier": "1", "deal_context": "ctx", "feedback_note": "wrong"})
            with patch.object(app, "LOG_FILE", path), \
                 patch.object(app.scoring_agent.client.messages, "create", return_value=fake_resp):
                improved, status = app.analyze_feedback_fn()
            self.assertEqual(improved, "New system prompt here")
            self.assertIn("AI over-scored budget", status)
        finally:
            os.unlink(path)

    def test_llm_exception_returns_error(self):
        path = _tmpfile()
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=app.LOG_COLUMNS)
                w.writeheader()
                w.writerow({**{c: "" for c in app.LOG_COLUMNS}, "ai_gonogo": "Go", "correct_gonogo": "No-Go",
                            "ai_tier": "3", "correct_tier": "1", "deal_context": "ctx", "feedback_note": "wrong"})
            with patch.object(app, "LOG_FILE", path), \
                 patch.object(app.scoring_agent.client.messages, "create", side_effect=RuntimeError("down")):
                improved, status = app.analyze_feedback_fn()
            self.assertEqual(improved, "")
            self.assertIn("Error", status)
        finally:
            os.unlink(path)


class ApplyPromptFnTests(unittest.TestCase):
    def test_blank_prompt_shows_warning(self):
        self.assertIn("ไม่มี prompt", app.apply_prompt_fn("   "))

    def test_saves_prompt_to_file(self):
        path = _tmpfile(suffix=".txt")
        try:
            with patch.object(app, "OPTIMIZED_PROMPT_FILE", path):
                msg = app.apply_prompt_fn("new prompt text")
            with open(path, encoding="utf-8") as f:
                self.assertEqual(f.read(), "new prompt text")
            self.assertIn("success", msg.lower())
        finally:
            if os.path.exists(path):
                os.unlink(path)


class RollbackFnTests(unittest.TestCase):
    def test_removes_optimized_file_when_present(self):
        path = _tmpfile(suffix=".txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("custom")
        with patch.object(app, "OPTIMIZED_PROMPT_FILE", path):
            prompt, msg = app.rollback_fn()
        self.assertEqual(prompt, app.SYSTEM_PROMPT)
        self.assertFalse(os.path.exists(path))
        self.assertIn("Rolled back", msg)

    def test_no_op_when_no_optimized_file(self):
        path = _tmpfile(suffix=".txt")  # ลบไปแล้วโดย _tmpfile()
        with patch.object(app, "OPTIMIZED_PROMPT_FILE", path):
            prompt, msg = app.rollback_fn()
        self.assertEqual(prompt, app.SYSTEM_PROMPT)
        self.assertIn("กำลังใช้ default", msg)


if __name__ == "__main__":
    unittest.main()
