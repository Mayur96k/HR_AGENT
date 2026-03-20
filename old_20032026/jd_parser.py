"""
jd_parser.py — Parse Job Description
Token optimized: 4000→1500 chars (-63%)
"""
from groq_client import groq_json, compress_text

SYSTEM = "Extract fields from job description. Return ONLY valid JSON. No markdown."
SCHEMA = '{"position_title":"","required_experience":"","required_skills":"","education_required":"","key_responsibilities":""}'

async def parse_jd(text: str, filename: str) -> dict:
    prompt = f"JD:\n{compress_text(text, 1500)}\n\nReturn JSON:\n{SCHEMA}"
    result = await groq_json(SYSTEM, prompt, max_tokens=250)
    return result or {"position_title": filename, "required_experience": "", "required_skills": ""}
