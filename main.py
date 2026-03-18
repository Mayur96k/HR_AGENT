"""
SUEZ AI HR Agent - Production Level
Reads JD & Resumes (PDF/DOCX), extracts structured data via Groq, scores candidates, exports Excel
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime

from file_reader import read_file_to_text
from resume_parser import parse_resume
from jd_parser import parse_jd
from hr_scorer import score_candidate
from excel_exporter import export_to_excel
from config import JD_FOLDER, RESUME_FOLDER, OUTPUT_FOLDER

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


async def process_all():
    log.info("=" * 60)
    log.info("SUEZ AI HR AGENT STARTED")
    log.info("=" * 60)

    # --- Load JDs ---
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
            log.info(f"  ✓ JD loaded: {jd_path.name} → Position: {jd_data.get('position_title','?')}")

    # --- Load Resumes ---
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

        # Step 4: Parse resume via Groq
        candidate = await parse_resume(text)
        if not candidate or not candidate.get("Name"):
            log.warning(f"  ✗ Skipping {resume_path.name} — could not extract name")
            continue

        log.info(f"  ✓ Parsed: {candidate.get('Name')} | {candidate.get('CurrentDesignation','?')}")

        # Step 6+7: Match against each JD
        for jd_stem, jd_info in jd_texts.items():
            log.info(f"    Scoring against JD: {jd_stem}")
            result = await score_candidate(candidate, jd_info["text"])
            result["source_resume"] = resume_path.name
            result["source_jd"] = jd_stem
            all_results.append(result)
            log.info(f"    ✓ Score: {result.get('overall_fit_score',0)}% | {result.get('recommendation','?')}")

    if not all_results:
        log.error("No results generated.")
        return

    # Step 9: Export to Excel
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(OUTPUT_FOLDER) / f"HR_Report_{timestamp}.xlsx"
    export_to_excel(all_results, str(output_path))
    log.info(f"\n✅ DONE! Report saved: {output_path}")
    log.info(f"   Total candidates evaluated: {len(all_results)}")


if __name__ == "__main__":
    asyncio.run(process_all())
