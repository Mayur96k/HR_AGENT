"""
groq_client.py — Lightweight Groq API wrapper
"""
import json
import logging
import httpx
from config import GROQ_API_KEY, GROQ_MODEL, GROQ_BASE_URL

log = logging.getLogger(__name__)


async def groq_json(system_prompt: str, user_content: str, max_tokens: int = 1000) -> dict:
    """Call Groq and return parsed JSON. Returns {} on failure."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set in .env")

    payload = {
        "model": GROQ_MODEL,
        "max_tokens": max_tokens,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_content}
        ]
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{GROQ_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json=payload
        )
        r.raise_for_status()
        raw = r.json()["choices"][0]["message"]["content"].strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        log.error(f"JSON parse error. Raw response:\n{raw[:300]}")
        return {}
