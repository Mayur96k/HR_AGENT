"""
resume_parser.py — Profile Analyser Agent
Token optimized: 4000→2500 chars (-38%), compact schema
"""
from groq_client import groq_json, compress_text

SYSTEM = "Parse CV and extract structured info. Return ONLY valid JSON. No markdown. Missing fields = empty string. KeySkills = comma-separated."
SCHEMA = '{"Name":"","Gender":"","Education":"","CurrentCompany":"","CurrentDesignation":"","CurrentEmploymentTenure":"","PreviousEmployer":"","PreviousDesignation":"","PreviousEmploymentTenure":"","TotalWorkingExperience":"","RelevantExperience":"","Graduation":"","Specialisation":"","PostGraduate":"","SpecialisationPG":"","KeySkills":""}'

async def parse_resume(text: str) -> dict:
    prompt = f"CV:\n{compress_text(text, 2500)}\n\nReturn JSON:\n{SCHEMA}"
    result = await groq_json(SYSTEM, prompt, max_tokens=600)
    if not result or not result.get("Name"):
        return {}
    return result
