"""
hr_scorer.py — HR Expert Agent
Token optimized: compact schema, strip empty fields, JD 2000→1200 chars (-40%)
"""
import json
from groq_client import groq_json, compress_text

SYSTEM = "You are an HR evaluator. Return ONLY valid JSON. No markdown."
SCHEMA = '{"name":"","gender":"","education":"","current_company":"","current_designation":"","current_employment_tenure":"","previous_employer":"","previous_designation":"","previous_employment_tenure":"","total_working_experience":"","relevance_experience":"","graduation":"","specialisation":"","post_graduate":"","specialisation_pg":"","key_skills":"","similarity_score":0,"skill_similarity":0,"applied_position":"","overall_fit_score":0,"recommendation":"","required_experience_match":"","skill_match_summary":"","education_certifications_match":"","soft_skills_traits":"","strengths":"","concerns_or_gaps":"","final_notes":""}'

async def score_candidate(candidate: dict, jd_text: str) -> dict:
    # Strip empty fields from candidate to save tokens
    compact = {k: v for k, v in candidate.items() if v}
    prompt = (
        f"Candidate:\n{json.dumps(compact, ensure_ascii=False)}\n\n"
        f"JD:\n{compress_text(jd_text, 1200)}\n\n"
        f"Return JSON:\n{SCHEMA}\n\n"
        "Rules: all scores 0-100. recommendation: 'Highly Recommended'|'Recommended'|'Maybe'|'Not Recommended'"
    )
    result = await groq_json(SYSTEM, prompt, max_tokens=800)
    if not result:
        return {
            "name": candidate.get("Name", ""), "overall_fit_score": 0,
            "recommendation": "Parse Error", "similarity_score": 0, "skill_similarity": 0,
            **{k: "" for k in ["gender","education","current_company","current_designation",
               "current_employment_tenure","previous_employer","previous_designation",
               "previous_employment_tenure","total_working_experience","relevance_experience",
               "graduation","specialisation","post_graduate","specialisation_pg","key_skills",
               "applied_position","required_experience_match","skill_match_summary",
               "education_certifications_match","soft_skills_traits","strengths","concerns_or_gaps","final_notes"]}
        }
    return result
