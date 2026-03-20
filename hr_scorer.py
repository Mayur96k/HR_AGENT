"""
hr_scorer.py — HR Expert Agent
Token optimized: compact schema, strip empty fields, JD 2000→1200 chars (-40%)
FIX: Includes previous_employer / previous_designation / current_location in schema
     Rank field added (1-based ranking handled in api_server after sort)
"""
import json
from groq_client import groq_json, compress_text

SYSTEM = "You are an HR evaluator. Return ONLY valid JSON. No markdown."

SCHEMA = (
    '{"name":"","gender":"","current_location":"","education":"",'
    '"current_company":"","current_designation":"","current_employment_tenure":"",'
    '"previous_employer":"","previous_designation":"","previous_employment_tenure":"",'
    '"total_working_experience":"","relevance_experience":"",'
    '"graduation":"","specialisation":"","post_graduate":"","specialisation_pg":"",'
    '"key_skills":"","similarity_score":0,"skill_similarity":0,'
    '"applied_position":"","overall_fit_score":0,"recommendation":"",'
    '"required_experience_match":"","skill_match_summary":"",'
    '"education_certifications_match":"","soft_skills_traits":"",'
    '"strengths":"","concerns_or_gaps":"","final_notes":""}'
)


async def score_candidate(candidate: dict, jd_text: str) -> dict:
    # Strip empty fields from candidate to save tokens
    compact = {k: v for k, v in candidate.items() if v}
    prompt = (
        f"Candidate:\n{json.dumps(compact, ensure_ascii=False)}\n\n"
        f"JD:\n{compress_text(jd_text, 1200)}\n\n"
        f"Return JSON:\n{SCHEMA}\n\n"
        "Rules:\n"
        "- All scores 0-100 integers.\n"
        "- recommendation: 'Highly Recommended' | 'Recommended' | 'Maybe' | 'Not Recommended'\n"
        "- Copy previous_employer, previous_designation, previous_employment_tenure directly from candidate data if present.\n"
        "- Copy current_location from candidate data if present.\n"
        "- applied_position = the job title from the JD.\n"
    )
    result = await groq_json(SYSTEM, prompt, max_tokens=900)
    if not result:
        return {
            "name": candidate.get("Name", ""),
            "overall_fit_score": 0,
            "recommendation": "Parse Error",
            "similarity_score": 0,
            "skill_similarity": 0,
            **{k: "" for k in [
                "gender", "current_location", "education",
                "current_company", "current_designation", "current_employment_tenure",
                "previous_employer", "previous_designation", "previous_employment_tenure",
                "total_working_experience", "relevance_experience",
                "graduation", "specialisation", "post_graduate", "specialisation_pg",
                "key_skills", "applied_position", "required_experience_match",
                "skill_match_summary", "education_certifications_match",
                "soft_skills_traits", "strengths", "concerns_or_gaps", "final_notes"
            ]}
        }
    return result
