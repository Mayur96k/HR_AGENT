"""
excel_exporter.py — Step 9: Export results to formatted Excel
"""
import logging
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

log = logging.getLogger(__name__)

COLUMNS = [
    ("source_jd",                   "JD File"),
    ("source_resume",               "Resume File"),
    ("name",                        "Name"),
    ("gender",                      "Gender"),
    ("applied_position",            "Applied Position"),
    ("overall_fit_score",           "Overall Fit %"),
    ("recommendation",              "Recommendation"),
    ("similarity_score",            "Similarity Score"),
    ("skill_similarity",            "Skill Similarity"),
    ("current_company",             "Current Company"),
    ("current_designation",         "Current Designation"),
    ("current_employment_tenure",   "Current Tenure"),
    ("previous_employer",           "Previous Employer"),
    ("previous_designation",        "Previous Designation"),
    ("previous_employment_tenure",  "Prev Tenure"),
    ("total_working_experience",    "Total Experience"),
    ("relevance_experience",        "Relevant Experience"),
    ("education",                   "Education"),
    ("graduation",                  "Graduation"),
    ("specialisation",              "Specialisation"),
    ("post_graduate",               "Post Graduate"),
    ("specialisation_pg",           "Specialisation PG"),
    ("key_skills",                  "Key Skills"),
    ("required_experience_match",   "Exp Match"),
    ("skill_match_summary",         "Skill Match Summary"),
    ("education_certifications_match", "Education Match"),
    ("soft_skills_traits",          "Soft Skills"),
    ("strengths",                   "Strengths"),
    ("concerns_or_gaps",            "Concerns/Gaps"),
    ("final_notes",                 "Final Notes"),
]

# Color bands per recommendation
REC_COLORS = {
    "highly recommended": "C6EFCE",
    "recommended":        "FFEB9C",
    "maybe":              "FFEB9C",
    "not recommended":    "FFC7CE",
    "parse error":        "D9D9D9",
}

HDR_FILL  = PatternFill("solid", fgColor="1F3864")
HDR_FONT  = Font(bold=True, color="FFFFFF", size=11)
THIN_SIDE = Side(style="thin", color="BFBFBF")
THIN_BORDER = Border(left=THIN_SIDE, right=THIN_SIDE, top=THIN_SIDE, bottom=THIN_SIDE)


def export_to_excel(results: list, output_path: str):
    wb = Workbook()
    ws = wb.active
    ws.title = "HR Evaluation"

    # Sort by overall_fit_score desc
    results = sorted(results, key=lambda x: float(x.get("overall_fit_score", 0) or 0), reverse=True)

    # Header row
    for col_idx, (_, header) in enumerate(COLUMNS, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = HDR_FILL
        cell.font = HDR_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = THIN_BORDER

    ws.row_dimensions[1].height = 30

    # Data rows
    for row_idx, r in enumerate(results, 2):
        rec = str(r.get("recommendation", "")).lower()
        row_color = REC_COLORS.get(rec, "FFFFFF")
        fill = PatternFill("solid", fgColor=row_color)

        for col_idx, (field, _) in enumerate(COLUMNS, 1):
            val = r.get(field, "")
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.fill = fill
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = THIN_BORDER

            # Bold score column
            if field == "overall_fit_score":
                cell.font = Font(bold=True, size=12)
                cell.alignment = Alignment(horizontal="center", vertical="top")

    # Column widths
    col_widths = {
        1: 18, 2: 25, 3: 22, 4: 10, 5: 22, 6: 12, 7: 20, 8: 14, 9: 14,
        10: 22, 11: 22, 12: 14, 13: 22, 14: 22, 15: 14, 16: 16, 17: 16,
        18: 18, 19: 18, 20: 18, 21: 18, 22: 18, 23: 35, 24: 18, 25: 35,
        26: 22, 27: 25, 28: 35, 29: 35, 30: 40
    }
    for col, width in col_widths.items():
        ws.column_dimensions[get_column_letter(col)].width = width

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    # Legend sheet
    ls = wb.create_sheet("Legend")
    ls.append(["Color", "Meaning"])
    for rec, color in REC_COLORS.items():
        c = ls.cell(row=ls.max_row + 1, column=1, value=rec.title())
        c.fill = PatternFill("solid", fgColor=color)
        ls.cell(row=ls.max_row, column=2, value=f"Recommendation: {rec.title()}")

    wb.save(output_path)
    log.info(f"Excel saved: {output_path} ({len(results)} rows)")
