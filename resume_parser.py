"""
resume_parser.py — Profile Analyser Agent
Token optimized: 4000→2500 chars (-38%), compact schema
FIX: Explicit instructions for Previous Employer / Designation capture
     Added CurrentLocation field
"""
from groq_client import groq_json, compress_text
 
SYSTEM = (
    "Parse CV and extract structured info. Return ONLY valid JSON. No markdown. "
    "Missing fields = empty string. KeySkills = comma-separated. "
    "IMPORTANT: Carefully extract PreviousEmployer, PreviousDesignation and PreviousEmploymentTenure "
    "from the work history / experience section. Look for the second-most-recent job or any prior company listed. "
    "CurrentLocation = city/state where candidate currently lives (from contact info or address). "
)
 
SCHEMA = (
    '{"Name":"","Gender":"","CurrentLocation":"","Education":"","CurrentCompany":"",'
    '"CurrentDesignation":"","CurrentEmploymentTenure":"",'
    '"PreviousEmployer":"","PreviousDesignation":"","PreviousEmploymentTenure":"",'
    '"TotalWorkingExperience":"","RelevantExperience":"",'
    '"Graduation":"","Specialisation":"","PostGraduate":"","SpecialisationPG":"","KeySkills":""}'
)
 
async def parse_resume(text: str) -> dict:
    prompt = (
        f"CV:\n{compress_text(text, 2500)}\n\n"
        "Instructions:\n"
        "- CurrentCompany / CurrentDesignation / CurrentEmploymentTenure = MOST RECENT job.\n"
        "- PreviousEmployer / PreviousDesignation / PreviousEmploymentTenure = the job BEFORE the most recent one.\n"
        "- If only one job exists, leave Previous* fields empty.\n"
        "- CurrentLocation = city/country from address or contact section.\n"
        f"\nReturn JSON exactly matching this schema:\n{SCHEMA}"
    )
    result = await groq_json(SYSTEM, prompt, max_tokens=700)
    if not result or not result.get("Name"):
        return {}
    return result
