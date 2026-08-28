"""Shared helpers for the three pipeline agents (scoring / discovery / solution shaping).

API key อ่านจาก env ANTHROPIC_API_KEY เท่านั้น (ห้าม hardcode — คีย์เก่าเคยรั่วขึ้น git มาแล้ว)
"""
import json
import os

import anthropic

MODEL = "claude-sonnet-4-6"


def new_client() -> anthropic.Anthropic:
    """ตรวจ env แล้วสร้าง client — SystemExit ถ้ายังไม่ตั้งคีย์ (เรียกตอน import agent)."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ต้องตั้ง env ANTHROPIC_API_KEY ก่อนรัน (เช่น setx / export หรือไฟล์ .env)")
    return anthropic.Anthropic()


def strip_json_fences(text: str) -> str:
    """ตัด ```json ... ``` fence ที่ model อาจครอบมา — คืนเนื้อ JSON ล้วน."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.rsplit("```", 1)[0].strip()
    return text


def parse_json_response(text: str) -> dict:
    """แปลงข้อความตอบกลับจาก model เป็น dict (รองรับ code fence). โยน json.JSONDecodeError ถ้าไม่ใช่ JSON."""
    return json.loads(strip_json_fences(text))


def load_solution_master(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()
