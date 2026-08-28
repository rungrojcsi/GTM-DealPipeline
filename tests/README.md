# Unit tests — Discovery RAG pipeline (ส่วน A)

ทดสอบ `discovery_agent.py`, `scoring_agent.py`, `solution_shaping_agent.py` โดย mock
`anthropic.Anthropic` client ทั้งหมด — **ไม่เรียก API จริง ไม่ต้องมี ANTHROPIC_API_KEY จริง**
(ตั้งค่า dummy ให้อัตโนมัติใน `_fakes.py`)

## รัน

```bash
cd GTM
python -m unittest discover -s tests -p "test_*.py" -v
```

## ครอบคลุม

| ไฟล์ | ทดสอบ |
|---|---|
| `test_scoring_agent.py` | `score_deal()` parse JSON/code-fence, error handling (invalid JSON, auth error), `get_active_prompt()` fallback/override |
| `test_discovery_agent.py` | `discover_deal()` substitution ของ scoring summary เข้า prompt, ค่า default N/A, อ่าน solution_master file, error handling |
| `test_solution_shaping_agent.py` | `shape_solution()` matched_solutions/out_of_scope formatting, error handling ครบ 3 แบบ (JSON/auth/generic exception) |
| `test_app.py` | ทุก tab callback ของ `app.py` (Gradio UI): `submit`/`proceed_to_discovery`/`submit_feedback` (Scoring), `run_discovery`/`submit_discovery_feedback`, `run_shaping`/`submit_shaping_feedback`, `load_history`, `analyze_feedback_fn`/`apply_prompt_fn`/`rollback_fn` — CSV logging helpers (`_ensure_log`/`_generate_deal_id`/`_log_scoring`/`_update_discovery_log`) + ทุก HTML render helper (`_render_shaping_design`/`_render_function_summary`/`_render_f3`/`_render_risks`/`_render_gonogo`) + pure helpers (`_score_bar`/`_badge`/`build_deal_context`/`get_current_prompt`) |

## ขอบเขตที่ไม่ครอบคลุม

- การสร้าง `gr.Blocks()`/`Tabs()`/event wiring เอง (บรรทัด 776+ ของ `app.py`) — ทดสอบได้แค่ผ่าน browser/Gradio server จริง ไม่ใช่ unit test (แต่ทุก callback function ที่ event เหล่านั้นเรียก ถูก test แล้วทั้งหมดใน `test_app.py`)
- ยังไม่ทดสอบกับ Anthropic API จริง (integration) — เฉพาะ mock response
