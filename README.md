# GTM Deal Pipeline

Internal prototype — ท่อคัดกรองดีลขาย (deal qualification pipeline) 3 ขั้นด้วย Claude ผ่านหน้าจอ Gradio

> **Internal use only.** ผลลัพธ์การรัน (deals_log.csv, feedback CSV, optimized prompt) มีข้อมูลดีลจริง — ถูกกันไว้ใน `.gitignore` ห้าม commit

## Pipeline

| ขั้น | ไฟล์ | หน้าที่ |
|------|------|---------|
| 1. Scoring | `scoring_agent.py` | ให้คะแนน BANTi (0-100) + F³ (0-15) → Go/No-Go + Tier 1-3 |
| 2. Discovery | `discovery_agent.py` | จับคู่ pain/requirement กับ `solution_master.md` → Full Fit / Partial Fit / Full Custom |
| 3. Solution Shaping | `solution_shaping_agent.py` | ออกแบบ module + function list + ประเมินความเสี่ยง → Go/No-Go รอบสอง |

`app.py` = หน้าจอ Gradio รวมทั้ง 3 ขั้น + History Log + Prompt Optimizer (เอาเคสที่ AI ตอบผิดจาก feedback ไปให้ LLM ปรับ prompt เอง)

## Run

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python app.py
```

ตัวอย่างข้อมูลป้อน (สมมติทั้งหมด): `Example Deal.txt`

## Tests

```bash
pip install pytest
pytest tests/
```

ชุดทดสอบใช้ fake client (`tests/_fakes.py`) — ไม่เรียก API จริง ไม่ต้องมีคีย์

## หมายเหตุ

- คีย์อ่านจาก env `ANTHROPIC_API_KEY` เท่านั้น — ห้าม hardcode ลงไฟล์
- ระบบตรวจข้อเสนอ (proposal evaluator) แยกอยู่คนละ repo: `proposal-evaluator`
