"""
main.py — SUEZ AI HR Agent CLI
Reads JD & Resumes from local folders, scores via Groq, saves to Supabase
"""
import asyncio
import logging
from pathlib import Path
from datetime import datetime

from file_reader import read_file_to_text
from resume_parser import parse_resume
from jd_parser import parse_jd
from hr_scorer import score_candidate
from supabase_sync import push_results
from config import JD_FOLDER, RESUME_FOLDER, SUPABASE_URL, SUPABASE_KEY

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


async def process_all():
    log.info("=" * 60)
    log.info("SUEZ AI HR AGENT STARTED")
    log.info("=" * 60)

    # ── Load JDs ──────────────────────────────────────────────
    jd_files = list(Path(JD_FOLDER).glob("*.pdf")) + list(Path(JD_FOLDER).glob("*.docx"))
    if not jd_files:
        log.error(f"No JD files found in: {JD_FOLDER}")
        return

    log.info(f"Found {len(jd_files)} JD file(s)")
    jd_texts = {}
    for jd_path in jd_files:
        text = read_file_to_text(jd_path)
        if text:
            jd_data = await parse_jd(text, jd_path.stem)
            jd_texts[jd_path.stem] = {"text": text, "data": jd_data}
            log.info(f"  ✓ JD loaded: {jd_path.name} → {jd_data.get('position_title','?')}")

    # ── Load Resumes ──────────────────────────────────────────
    resume_files = list(Path(RESUME_FOLDER).glob("*.pdf")) + list(Path(RESUME_FOLDER).glob("*.docx"))
    if not resume_files:
        log.error(f"No resume files found in: {RESUME_FOLDER}")
        return

    log.info(f"Found {len(resume_files)} resume(s)")
    all_results = []

    for resume_path in resume_files:
        log.info(f"\n  Processing: {resume_path.name}")
        text = read_file_to_text(resume_path)
        if not text or len(text.strip()) < 50:
            log.warning(f"  ✗ Skipping {resume_path.name} — insufficient content")
            continue

        candidate = await parse_resume(text)
        if not candidate or not candidate.get("Name"):
            log.warning(f"  ✗ Skipping {resume_path.name} — could not extract name")
            continue

        log.info(f"  ✓ Parsed: {candidate.get('Name')} | {candidate.get('CurrentDesignation','?')}")

        for jd_stem, jd_info in jd_texts.items():
            log.info(f"    Scoring against JD: {jd_stem}")
            result = await score_candidate(candidate, jd_info["text"])
            result["source_resume"] = resume_path.name
            result["source_jd"]     = jd_stem
            all_results.append(result)
            log.info(f"    ✓ Score: {result.get('overall_fit_score',0)}% | {result.get('recommendation','?')}")

    if not all_results:
        log.error("No results generated.")
        return

    # ── Save to Supabase ──────────────────────────────────────
    session_id = f"sess_{int(datetime.now().timestamp() * 1000)}"
    await push_results(all_results, SUPABASE_URL, SUPABASE_KEY, session_id)
    log.info(f"\n✅ DONE! {len(all_results)} candidates saved to Supabase hr_results table.")


if __name__ == "__main__":
    asyncio.run(process_all())
