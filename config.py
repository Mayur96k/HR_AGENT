"""
config.py — Central configuration for SUEZ HR Agent
Set your paths and API keys here (or use .env)
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Folder Paths ──────────────────────────────────────────────
BASE_DIR     = os.getenv("BASE_DIR", r"C:\Users\NDC719\Desktop\HR_AGENT")
JD_FOLDER    = os.getenv("JD_FOLDER",     os.path.join(BASE_DIR, "JD"))
RESUME_FOLDER = os.getenv("RESUME_FOLDER", os.path.join(BASE_DIR, "RESUEME"))
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", os.path.join(BASE_DIR, "OUTPUT"))

# ── Groq API ──────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama3-8b-8192")   # Fast & cheap
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# ── Supabase (optional) ───────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ── Tuning ────────────────────────────────────────────────────
MAX_TEXT_CHARS = 4000   # Truncate long docs to save tokens
MIN_SCORE_THRESHOLD = 30  # Filter out candidates below this score
