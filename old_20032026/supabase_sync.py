"""
supabase_sync.py — Push results to Supabase hr_results table
"""
import logging
import httpx

log = logging.getLogger(__name__)


async def push_results(results: list, supabase_url: str, supabase_key: str, session_id: str = ""):
    """Push scored results to Supabase hr_results table."""
    if not supabase_url or not supabase_key:
        log.warning("Supabase not configured — set SUPABASE_URL and SUPABASE_KEY in .env")
        return

    headers = {
        "apikey":        supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type":  "application/json",
        "Prefer":        "return=minimal"
    }

    records = []
    for c in results:
        score = float(c.get("overall_fit_score", 0) or 0)
        ats = "Strong" if score >= 80 else ("Moderate" if score >= 60 else "Weak")
        records.append({
            "session_id":     session_id,
            "job_title":      c.get("source_jd", ""),
            "candidate_name": c.get("name", c.get("Name", "")),
            "score":          round(score),
            "ats_rating":     ats,
            "result_json":    c,
            "created_by":     "main_cli"
        })

    url = f"{supabase_url.rstrip('/')}/rest/v1/hr_results"
    async with httpx.AsyncClient(timeout=30, verify=False) as client:
        resp = await client.post(url, headers=headers, json=records)
        if resp.status_code in (200, 201):
            log.info(f"Supabase: {len(records)} results saved to hr_results ✓")
        else:
            log.warning(f"Supabase push failed: {resp.status_code} — {resp.text[:200]}")
