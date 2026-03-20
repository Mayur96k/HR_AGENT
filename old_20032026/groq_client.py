"""
groq_client.py — Groq API wrapper
Optimized: retry on 429, SSL fix, token-saving compress_text utility
"""
import re
import json
import asyncio
import logging
import httpx
from config import GROQ_API_KEY, GROQ_MODEL, GROQ_BASE_URL

log = logging.getLogger(__name__)

MAX_RETRIES = 6
BASE_WAIT   = 10  # doubles: 10→20→40→80→160→320s


def compress_text(text: str, max_chars: int) -> str:
    """Reduce token count: collapse blank lines, trim spaces, truncate."""
    text = re.sub(r'\n{3,}', '\n\n', text)          # max 1 blank line
    text = re.sub(r'[ \t]{2,}', ' ', text)           # collapse spaces
    text = '\n'.join(l.rstrip() for l in text.splitlines())
    return text[:max_chars].strip()


async def groq_json(system_prompt: str, user_content: str, max_tokens: int = 800) -> dict:
    """Call Groq, retry on 429, return parsed JSON or {}."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set in .env")

    payload = {
        "model": GROQ_MODEL, "max_tokens": max_tokens, "temperature": 0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_content}
        ]
    }

    raw = ""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=60, verify=False) as client:
                r = await client.post(
                    f"{GROQ_BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                    json=payload
                )
                if r.status_code == 429:
                    wait = max(int(r.headers.get("retry-after", 0)), BASE_WAIT * (2 ** (attempt-1)))
                    log.warning(f"Rate limit (attempt {attempt}/{MAX_RETRIES}) — waiting {wait}s...")
                    await asyncio.sleep(wait)
                    continue
                r.raise_for_status()
                raw = r.json()["choices"][0]["message"]["content"].strip()
                break
        except httpx.HTTPStatusError as e:
            if attempt == MAX_RETRIES:
                log.error(f"Groq failed after {MAX_RETRIES} retries: {e}")
                return {}
            wait = BASE_WAIT * (2 ** (attempt-1))
            log.warning(f"Groq error attempt {attempt}/{MAX_RETRIES} — retry in {wait}s")
            await asyncio.sleep(wait)
    else:
        log.error("Groq max retries exceeded")
        return {}

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"): raw = raw[4:]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        log.error(f"JSON parse error:\n{raw[:300]}")
        return {}
