"""
hr_scorer.py — Step 8: HR Expert Agent
Scores candidate against JD and returns full evaluation JSON
"""
import json
from groq_client import groq_json
from config import MAX_TEXT_CHARS

SYSTEM = """You are an expert HR talent evaluator. 
Given a candidate profile and job description, evaluate fit and return ONLY valid JSON.
No markdown. No explanation. No wrapping."""

SCHEMA = """{
  "name":"","gender":"","education":"","current_company":"","current_designation":"",
  "current_employment_tenure":"","previous_employer":"","previous_designation":"",
  "previous_employment_tenure":"","total_working_experience":"","relevance_experience":"",
  "graduation":"","specialisation":"","post_graduate":"","specialisation_pg":"","key_skills":"",
  "similarity_score":0,"skill_similarity":0,"applied_position":"","overall_fit_score":0,
  "recommendation":"","required_experience_match":"","skill_match_summary":"",
  "education_certifications_match":"","soft_skills_traits":"","strengths":"",
  "concerns_or_gaps":"","final_notes":""
}"""

async def score_candidate(candidate: dict, jd_text: str) -> dict:
    candidate_str = json.dumps(candidate, ensure_ascii=False)
    jd_truncated  = jd_text[:2000]

    prompt = (
        f"Candidate Profile:\n{candidate_str}\n\n"
        f"Job Description:\n{jd_truncated}\n\n"
        f"Return evaluation JSON:\n{SCHEMA}\n\n"
        "Rules:\n"
        "- similarity_score: 0-100 (skills overlap)\n"
        "- skill_similarity: 0-100 (technical skills match)\n"
        "- overall_fit_score: 0-100 (holistic fit)\n"
        "- recommendation: 'Highly Recommended' | 'Recommended' | 'Maybe' | 'Not Recommended'"
    )

    result = await groq_json(SYSTEM, prompt, max_tokens=900)
    if not result:
        # Return skeleton with candidate basics
        return {
            "name": candidate.get("Name", ""),
            "overall_fit_score": 0,
            "recommendation": "Parse Error",
            **{k: "" for k in ["gender","education","current_company","current_designation",
               "current_employment_tenure","previous_employer","previous_designation",
               "previous_employment_tenure","total_working_experience","relevance_experience",
               "graduation","specialisation","post_graduate","specialisation_pg","key_skills",
               "applied_position","required_experience_match","skill_match_summary",
               "education_certifications_match","soft_skills_traits","strengths",
               "concerns_or_gaps","final_notes"]},
            "similarity_score": 0,
            "skill_similarity": 0
        }
    return result
