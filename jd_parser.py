"""
jd_parser.py — Parse Job Description to extract key fields
"""
from groq_client import groq_json
from config import MAX_TEXT_CHARS

SYSTEM = """Extract key fields from this job description. Return ONLY valid JSON. No markdown."""

SCHEMA = """{
"position_title":"","required_experience":"","required_skills":"",
"education_required":"","key_responsibilities":""
}"""

async def parse_jd(text: str, filename: str) -> dict:
    truncated = text[:MAX_TEXT_CHARS]
    prompt = f"JD:\n{truncated}\n\nReturn JSON:\n{SCHEMA}"
    result = await groq_json(SYSTEM, prompt, max_tokens=400)
    if not result:
        return {"position_title": filename, "required_experience": "", "required_skills": ""}
    return result
