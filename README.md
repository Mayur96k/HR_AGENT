# SUEZ AI HR Agent — VS Code Setup Guide

## Project Structure
```
HR_AGENT/
├── JD/                  ← Put your JD files here (.pdf / .docx)
├── RESUEME/             ← Put resume files here (.pdf / .docx)
├── OUTPUT/              ← Excel reports generated here (auto-created)
├── main.py              ← Entry point
├── config.py            ← Paths & settings
├── file_reader.py       ← Step 1-2: Read PDF/DOCX
├── resume_parser.py     ← Step 4: Profile Analyser Agent
├── jd_parser.py         ← JD extraction
├── hr_scorer.py         ← Step 8: HR Expert Agent
├── excel_exporter.py    ← Step 9: Excel report
├── groq_client.py       ← Groq API wrapper
├── supabase_sync.py     ← Optional DB sync
├── .env.example         ← Copy to .env
└── requirements.txt
```

---

## Step-by-Step Setup in VS Code

### 1. Create Project Folder
```
mkdir C:\Users\NDC719\Desktop\HR_AGENT
cd C:\Users\NDC719\Desktop\HR_AGENT
mkdir JD RESUEME OUTPUT
```

### 2. Copy all .py files into HR_AGENT folder

### 3. Open in VS Code
```
code C:\Users\NDC719\Desktop\HR_AGENT
```

### 4. Create Virtual Environment (in VS Code Terminal)
```bash
python -m venv venv
venv\Scripts\activate
```

### 5. Install Dependencies
```bash
pip install -r requirements.txt
```

### 6. Create .env file
```bash
copy .env.example .env
```
Then open `.env` and set your **GROQ_API_KEY**:
- Go to: https://console.groq.com/keys
- Create a free API key
- Paste it: `GROQ_API_KEY=gsk_xxxxxxxxxxxx`

### 7. Add Your Files
- Drop JD files (PDF or DOCX) into: `C:\Users\NDC719\Desktop\HR_AGENT\JD\`
- Drop Resume files (PDF or DOCX) into: `C:\Users\NDC719\Desktop\HR_AGENT\RESUEME\`

### 8. Run the Agent
```bash
python main.py
```

### 9. View Report
- Open `C:\Users\NDC719\Desktop\HR_AGENT\OUTPUT\HR_Report_YYYYMMDD_HHMMSS.xlsx`

---

## Optional: Supabase Sync (for HTML Dashboard)

1. Go to https://supabase.com → Create project
2. Run this SQL in Supabase SQL Editor:
```sql
CREATE TABLE candidates (
  id SERIAL PRIMARY KEY,
  name TEXT, gender TEXT, education TEXT,
  current_company TEXT, current_designation TEXT,
  current_employment_tenure TEXT, previous_employer TEXT,
  previous_designation TEXT, previous_employment_tenure TEXT,
  total_working_experience TEXT, relevance_experience TEXT,
  graduation TEXT, specialisation TEXT, post_graduate TEXT,
  specialisation_pg TEXT, key_skills TEXT,
  similarity_score NUMERIC, skill_similarity NUMERIC,
  applied_position TEXT, overall_fit_score NUMERIC,
  recommendation TEXT, required_experience_match TEXT,
  skill_match_summary TEXT, education_certifications_match TEXT,
  soft_skills_traits TEXT, strengths TEXT,
  concerns_or_gaps TEXT, final_notes TEXT,
  source_resume TEXT, source_jd TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```
3. Add to `.env`:
```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=your_anon_key
```
4. In `main.py`, uncomment the supabase_sync section (see below)

---

## Enable Supabase Sync in main.py
Add this at the bottom of `process_all()` before the final log:
```python
from supabase_sync import push_results
from config import SUPABASE_URL, SUPABASE_KEY
await push_results(all_results, SUPABASE_URL, SUPABASE_KEY)
```

---

## Groq Models (Speed vs Quality)
| Model              | Speed  | Quality | Use When         |
|--------------------|--------|---------|------------------|
| llama3-8b-8192     | Fast ⚡ | Good    | Default (recommended) |
| llama3-70b-8192    | Medium | Better  | More accuracy needed  |
| mixtral-8x7b-32768 | Medium | Best    | Complex JDs           |

Change in `.env`: `GROQ_MODEL=llama3-70b-8192`

---

## Troubleshooting

**"No JD files found"** → Check path in config.py or .env  
**"JSON parse error"** → Switch to llama3-70b-8192 model  
**PDF extraction empty** → PDF may be scanned image, try converting to DOCX first  
**Rate limit error** → Add `await asyncio.sleep(1)` between calls in main.py
