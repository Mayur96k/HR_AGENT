"""
resume_parser.py — Step 4: Profile Analyser Agent (Groq)
Extracts structured candidate data from resume text
"""
from groq_client import groq_json
from config import MAX_TEXT_CHARS

SYSTEM = """You are an AI resume parsing assistant. Extract structured information from the CV.
Return ONLY valid JSON. No explanations. No markdown. No wrapping object.
If a field is missing return "". KeySkills must be comma-separated."""

SCHEMA = """{
"Name":"","Gender":"","Education":"","CurrentCompany":"","CurrentDesignation":"",
"CurrentEmploymentTenure":"","PreviousEmployer":"","PreviousDesignation":"",
"PreviousEmploymentTenure":"","TotalWorkingExperience":"","RelevantExperience":"",
"Graduation":"","Specialisation":"","PostGraduate":"","SpecialisationPG":"","KeySkills":""
}"""

async def parse_resume(text: str) -> dict:
    truncated = text[:MAX_TEXT_CHARS]
    prompt = f"CV:\n{truncated}\n\nReturn JSON in this exact structure:\n{SCHEMA}"
    result = await groq_json(SYSTEM, prompt, max_tokens=800)
    # Step 5: Remove bad data — filter empty results
    if not result or not result.get("Name"):
        return {}
    return result
