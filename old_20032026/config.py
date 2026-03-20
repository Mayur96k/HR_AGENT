"""
config.py — Central configuration for SUEZ HR Agent
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(r"C:\Users\NDC719\Desktop\HR_AGENT\.env"), override=True)

# ── Folder Paths (CLI only) ───────────────────────────────────
BASE_DIR      = os.getenv("BASE_DIR",      r"C:\Users\NDC719\Desktop\HR_AGENT")
JD_FOLDER     = os.getenv("JD_FOLDER",     os.path.join(BASE_DIR, "JD"))
RESUME_FOLDER = os.getenv("RESUME_FOLDER", os.path.join(BASE_DIR, "RESUEME"))

# ── Groq API ──────────────────────────────────────────────────
GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL    = os.getenv("GROQ_MODEL",   "llama-3.3-70b-versatile")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# ── Supabase — all results stored here ───────────────────────
SUPABASE_URL  = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY  = os.getenv("SUPABASE_KEY", "")

# ── Tuning ────────────────────────────────────────────────────
MAX_TEXT_CHARS      = 4000
MIN_SCORE_THRESHOLD = 30
