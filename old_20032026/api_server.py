"""
api_server.py — SUEZ AI HR Agent  ·  Web Portal Bridge
Fixed for:
  1. Windows Python 3.8 asyncio threading issue
  2. Field name mismatch (snake_case → Title Case for frontend)
  3. Results pushed directly to Supabase hr_results (no local OUTPUT folder)
"""

import asyncio
import logging
import tempfile
import json
import threading
import httpx
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from typing import List, Dict

from file_reader import read_file_to_text
from resume_parser import parse_resume
from jd_parser import parse_jd
from hr_scorer import score_candidate
from config import SUPABASE_URL, SUPABASE_KEY

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc'}


def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


# ── Supabase direct push ──────────────────────────────────────────────────────

async def push_to_supabase(rows: list, session_id: str, job_title: str):
    """Push scored results directly to Supabase hr_results table."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        log.warning("Supabase not configured — skipping DB push (set SUPABASE_URL and SUPABASE_KEY in .env)")
        return

    headers = {
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "return=minimal"
    }

    records = []
    for c in rows:
        score = float(c.get("Overall Fit Score", 0) or 0)
        ats = "Strong" if score >= 80 else ("Moderate" if score >= 60 else "Weak")
        records.append({
            "session_id":     session_id,
            "job_title":      job_title,
            "candidate_name": c.get("Name", ""),
            "score":          round(score),
            "ats_rating":     ats,
            "result_json":    c,
            "created_by":     "api_server"
        })

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/hr_results"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, headers=headers, json=records)
        if resp.status_code in (200, 201):
            log.info(f"Supabase: {len(records)} results saved to hr_results ✓")
        else:
            log.warning(f"Supabase push failed: {resp.status_code} — {resp.text[:200]}")


# ── Key remapping: snake_case → Title Case (what the HTML table expects) ──────

FIELD_MAP = {
    "name":                         "Name",
    "gender":                       "Gender",
    "education":                    "Education",
    "current_company":              "Current Company",
    "current_designation":          "Current Designation",
    "current_employment_tenure":    "Current Employement Tenure",
    "previous_employer":            "Previous Employer",
    "previous_designation":         "Previous Designation",
    "previous_employment_tenure":   "Employement Tenure",
    "total_working_experience":     "Total Working Experience",
    "relevance_experience":         "Relevance Experience",
    "graduation":                   "Graduation",
    "specialisation":               "Specialisation",
    "post_graduate":                "Post Graduate",
    "specialisation_pg":            "Specialisation PG",
    "key_skills":                   "Key Skills",
    "overall_fit_score":            "Overall Fit Score",
    "similarity_score":             "similarity_score",
    "skill_similarity":             "skill_similarity",
    "applied_position":             "applied_position",
    "recommendation":               "recommendation",
    "required_experience_match":    "required_experience_match",
    "skill_match_summary":          "skill_match_summary",
    "education_certifications_match": "education_certifications_match",
    "soft_skills_traits":           "soft_skills_traits",
    "strengths":                    "Strengths",
    "concerns_or_gaps":             "Concerns/Gaps",
    "final_notes":                  "Final Notes",
    "CurrentCompany":               "Current Company",
    "CurrentDesignation":           "Current Designation",
    "CurrentEmploymentTenure":      "Current Employement Tenure",
    "PreviousEmployer":             "Previous Employer",
    "PreviousDesignation":          "Previous Designation",
    "PreviousEmploymentTenure":     "Employement Tenure",
    "TotalWorkingExperience":       "Total Working Experience",
    "RelevantExperience":           "Relevance Experience",
    "PostGraduate":                 "Post Graduate",
    "SpecialisationPG":             "Specialisation PG",
    "KeySkills":                    "Key Skills",
}


def normalize_candidate(raw: dict) -> dict:
    """Remap all field names to what the HTML frontend expects."""
    out = {}
    for key, value in raw.items():
        mapped = FIELD_MAP.get(key, key)
        if mapped not in out:
            out[mapped] = value
    return out


# ── Fix for Windows Python 3.8 ───────────────────────────────────────────────

def run_async(coro):
    """
    Safely run async coroutine from a Flask (sync) route on Windows Python 3.8.
    Uses SelectorEventLoop to avoid ProactorEventLoop set_wakeup_fd crash.
    """
    import sys
    result = {}

    def thread_target():
        if sys.platform == 'win32':
            loop = asyncio.SelectorEventLoop()
        else:
            loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result['value'] = loop.run_until_complete(coro)
        except Exception as e:
            result['error'] = e
        finally:
            try:
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            loop.close()

    t = threading.Thread(target=thread_target)
    t.start()
    t.join()

    if 'error' in result:
        raise result['error']
    return result.get('value')


# ── Health Check ──────────────────────────────────────────────────────────────

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'SUEZ AI HR Agent',
        'supabase': 'configured' if (SUPABASE_URL and SUPABASE_KEY) else 'not configured',
        'time': datetime.now().isoformat()
    })


# ── Main Analysis Endpoint ────────────────────────────────────────────────────

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'job_description' not in request.files:
        return jsonify({'error': 'No job_description file uploaded'}), 400

    resume_files = request.files.getlist('resume')
    if not resume_files or all(f.filename == '' for f in resume_files):
        return jsonify({'error': 'No resume files uploaded'}), 400

    jd_file = request.files['job_description']
    if not allowed_file(jd_file.filename):
        return jsonify({'error': f'Unsupported JD file type: {jd_file.filename}'}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        jd_filename = secure_filename(jd_file.filename)
        jd_path = tmpdir / jd_filename
        jd_file.save(jd_path)

        resume_paths = []
        for rf in resume_files:
            if rf.filename and allowed_file(rf.filename):
                fname = secure_filename(rf.filename)
                rpath = tmpdir / fname
                rf.save(rpath)
                resume_paths.append(rpath)

        if not resume_paths:
            return jsonify({'error': 'No valid resume files (.pdf or .docx)'}), 400

        try:
            results = run_async(_run_pipeline(jd_path, resume_paths))
        except Exception as e:
            log.error(f"Pipeline error: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500

    # Normalize all field names to Title Case for frontend
    normalized = [normalize_candidate(r) for r in results]

    # Sort by Overall Fit Score descending
    normalized.sort(
        key=lambda x: float(x.get('Overall Fit Score', x.get('overall_fit_score', 0)) or 0),
        reverse=True
    )

    # Ensure score is always 0-100 integer
    for c in normalized:
        raw = float(c.get('Overall Fit Score', 0) or 0)
        c['Overall Fit Score'] = round(raw if raw > 1 else raw * 100)

    # Push results directly to Supabase hr_results table
    session_id = f"sess_{int(datetime.now().timestamp() * 1000)}"
    job_title  = jd_file.filename
    try:
        run_async(push_to_supabase(normalized, session_id, job_title))
    except Exception as e:
        log.warning(f"Supabase push failed (non-fatal): {e}")

    log.info(f"Analysis complete: {len(normalized)} candidates processed")
    return jsonify(normalized)


# ── Async pipeline ────────────────────────────────────────────────────────────

async def _run_pipeline(jd_path: Path, resume_paths: List[Path]) -> List[Dict]:
    jd_text = read_file_to_text(jd_path)
    if not jd_text or len(jd_text.strip()) < 20:
        raise ValueError(f"Could not extract text from JD: {jd_path.name}")

    jd_data = await parse_jd(jd_text, jd_path.stem)
    log.info(f"JD parsed: {jd_data.get('position_title', '?')}")

    results = []
    for rpath in resume_paths:
        log.info(f"Processing: {rpath.name}")
        text = read_file_to_text(rpath)
        if not text or len(text.strip()) < 50:
            log.warning(f"Skipping {rpath.name} — insufficient content")
            continue

        try:
            candidate = await parse_resume(text)
        except Exception as e:
            log.warning(f"Parse failed for {rpath.name}: {e}")
            continue

        if not candidate or not candidate.get('Name'):
            log.warning(f"No name extracted from {rpath.name}")
            continue

        try:
            result = await score_candidate(candidate, jd_text)
            result['source_resume'] = rpath.name
            result['source_jd']     = jd_path.stem
            results.append(result)
            log.info(f"Scored: {candidate.get('Name')} → {result.get('overall_fit_score', 0)}%")
        except Exception as e:
            log.warning(f"Scoring failed for {rpath.name}: {e}")

    return results


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 55)
    print("  SUEZ AI HR Agent  —  Web Portal API Server")
    print("=" * 55)
    print("  Starting on http://localhost:5000")
    print("  Open index.html via Live Server")
    print(f"  Supabase: {'✓ configured' if (SUPABASE_URL and SUPABASE_KEY) else '✗ not set — add to .env'}")
    print("=" * 55)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)