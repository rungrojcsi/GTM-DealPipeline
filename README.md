# GTM Deal Pipeline

[![CI](https://github.com/rungrojcsi/GTM-DealPipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/rungrojcsi/GTM-DealPipeline/actions/workflows/ci.yml)

Internal prototype — ท่อคัดกรองดีลขาย (deal qualification pipeline) 3 ขั้นด้วย Claude ผ่านหน้าจอ Gradio

> **Internal use only — CSI GROUPS.** ผลลัพธ์การรัน (deals_log.csv, feedback CSV, optimized prompt) มีข้อมูลดีลจริง — ถูกกันไว้ใน `.gitignore` ห้าม commit

## Pipeline

```mermaid
flowchart LR
    A[Deal Info] --> B["1 Scoring<br/>BANTi 0-100 + F³ 0-15"]
    B -->|Go| C["2 Discovery<br/>map vs Solution Master"]
    B -->|No-Go| X([stop])
    C -->|"Full/Partial Fit"| D["3 Solution Shaping<br/>modules + risks"]
    C -->|No Fit| X
    D --> E([Go / No-Go + Tier])
```

| ขั้น | ไฟล์ | หน้าที่ |
|------|------|---------|
| 1. Scoring | `scoring_agent.py` | ให้คะแนน BANTi (0-100) + F³ (0-15) → Go/No-Go + Tier 1-3 |
| 2. Discovery | `discovery_agent.py` | จับคู่ pain/requirement กับ `solution_master.md` → Full Fit / Partial Fit / Full Custom |
| 3. Solution Shaping | `solution_shaping_agent.py` | ออกแบบ module + function list + ประเมินความเสี่ยง → Go/No-Go รอบสอง |

## Project layout

```
app.py                     Gradio UI — 5 แท็บ (Scoring / Discovery / Shaping / History / Prompt Optimizer)
render.py                  HTML render helpers + สี/label (ไม่ผูกกับ Gradio)
llm_utils.py               ส่วนกลาง: client, model, JSON parsing, solution master loader
scoring_agent.py           ขั้น 1 — BANTi-F³ qualification
discovery_agent.py         ขั้น 2 — solution fit mapping
solution_shaping_agent.py  ขั้น 3 — solution design + risk
solution_master.md         คลังความรู้ solution ของบริษัท (agent 2-3 ใช้)
examples/example-deal.txt  ตัวอย่างข้อมูลป้อน (สมมติทั้งหมด)
tests/                     unit tests — mock ทุก external call ไม่เรียก API จริง
```

หน้าจอมีระบบเก็บ feedback จากผู้ใช้ลง CSV และแท็บ **Prompt Optimizer** ที่นำเคสที่ AI ตอบผิดไปให้ LLM เสนอ prompt ปรับปรุง (apply/rollback ได้)

## Run

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python app.py
```

## Tests & lint

```bash
pip install pytest ruff
pytest tests/
ruff check .
```

ชุดทดสอบ 77 เคสใช้ fake client (`tests/_fakes.py`) — ไม่เรียก API จริง ไม่ต้องมีคีย์ · CI รันทั้ง lint + tests ทุก push/PR

## หมายเหตุ

- คีย์อ่านจาก env `ANTHROPIC_API_KEY` เท่านั้น — ห้าม hardcode ลงไฟล์
- ระบบตรวจข้อเสนอ (proposal evaluator) แยกอยู่คนละ repo: [Proposal-Evaluator](https://github.com/rungrojcsi/Proposal-Evaluator)
