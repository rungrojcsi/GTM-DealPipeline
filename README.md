# GTM Deal Pipeline (POC)

[![CI](https://github.com/rungrojcsi/GTM-DealPipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/rungrojcsi/GTM-DealPipeline/actions/workflows/ci.yml)

ท่อคัดกรองดีลขาย (deal qualification pipeline) 3 ขั้นด้วย Claude ผ่านหน้าจอ Gradio — เครื่องมือสนับสนุนกระบวนการ GTM (Pillar 2 Deal Qualification + Pillar 4 Processes & Tiering)

> **สถานะ: POC Phase** — ยังเป็นต้นแบบเพื่อพิสูจน์แนวทาง ยังไม่ใช่ระบบ production: เก็บข้อมูลเป็น CSV ในเครื่อง, ใช้งานคนเดียว, ยังไม่ครอบคลุมขั้น Estimation & Proposal
>
> **Internal use only — CSI GROUPS.** ผลลัพธ์การรัน (deals_log.csv, feedback CSV, optimized prompt) มีข้อมูลดีลจริง — ถูกกันไว้ใน `.gitignore` ห้าม commit

## GTM Foundation

เครื่องมือนี้เป็นส่วนหนึ่งของ GTM 8 Pillars (New Optimized Flow: Sales → Go-To-Market → Engineering) — รองรับ **Pillar 2 Deal Qualification** และ **Pillar 4 Process & Tiering**:

![GTM Foundation — 8 Pillars](docs/images/gtm-foundation.png)

## Business workflow (GTM Pillar 4 : Processes and Tiering)

กระบวนการขายจริงตามสไลด์ทางการ (stages + SLA + gates + Prospects Tiering):

![Pillar 4 — Processes and Tiering](docs/images/pillar4-process-tiering.png)

ตำแหน่งของเครื่องมือนี้ในกระบวนการข้างบน — กรอบทึบคือขั้นที่ POC ครอบคลุมแล้ว กรอบประคือขั้นที่ยังไม่อยู่ใน POC:

```mermaid
flowchart LR
    subgraph LS["Leads Stage — SLA 3 วัน"]
        LQ["Lead Qualification<br/>Warm call · BANTI<br/>Go/No-Go (Possibility)"]
    end
    subgraph DS["Discover Stage — SLA 14 วัน"]
        DC["Discovery<br/>Pains · Requirements<br/>High-level Scope"]
        SS["Solution Shaping & Validation<br/>Solution Mapping · Risks · F³ & Tiering<br/>Go/No-Go (Solution Fit: PPS)"]
    end
    subgraph PS["Propose Stage"]
        EP["Estimation & Proposal<br/>Confirm resource · Confirm Tiering<br/>Go/No-Go (Competitiveness)"]
    end
    subgraph CS["Closing Stage — SLA 90 วัน"]
        DSC["Deal Support & Close<br/>Negotiation · Customer Decision"]
    end
    LQ -->|Open Case| DC --> SS --> EP --> DSC -->|Closed Ticket| OP([Open Project])

    style LQ fill:#1e5a7a,color:#fff
    style DC fill:#1e5a7a,color:#fff
    style SS fill:#1e5a7a,color:#fff
    style EP stroke-dasharray: 5 5
    style DSC stroke-dasharray: 5 5
```

| ขั้นใน workflow | สถานะใน POC | แท็บในแอป |
|-----------------|-------------|-----------|
| Lead Qualification (BANTI, Go/No-Go) | ✅ ครอบคลุม | 1. Scoring |
| Discovery (pains / requirements / scope) | ✅ ครอบคลุม | 2. Discovery |
| Solution Shaping & Validation (F³, Tiering, PPS gate) | ✅ ครอบคลุม | 3. Solution Shaping |
| Estimation & Proposal | ⏳ ยังไม่ทำ (มีปุ่ม Proceed to Estimation รอไว้) | — |
| Deal Support & Close | ⏳ นอกขอบเขต POC | — |

### Prospects Tiering

ผล F³ จากขั้น Scoring/Shaping ชี้ Tier ของการเสนอ (MB = ล้านบาท):

| Tier | แนวทางเสนอ | ลักษณะดีล | มูลค่า | ผู้รับผิดชอบ (PC) |
|------|-----------|-----------|--------|--------------------|
| 1 | Template Propose | Solution fit, customization ต่ำ, ความเสี่ยงต่ำ | >1 MB | BizDomain |
| 2 | Proposal Propose (Story-Driven) | มี customization, มีการแข่งขัน | 1–3 MB | BizDomain, SolDomain |
| 3 | Consulting Propose (Strategic-Driven) | ซับซ้อน, ระดับ C-Level | >5 MB | GTM, SolDomain |

## Pipeline ในแอป (3 agents)

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
