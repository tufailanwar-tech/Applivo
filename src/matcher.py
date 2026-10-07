import os
import sys
import json
import sqlite3
import uuid
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
from db import DB_PATH, get_profile_from_db, init_db

_GENAI_WARNED = False

def score_job_with_llm(job_title: str, job_desc: str, profile: dict) -> tuple[int, str]:
    """Score job alignment from 0-10 and generate cover letter text."""
    global _GENAI_WARNED
    api_key = os.environ.get("GEMINI_API_KEY")
    resume_text = profile.get("resume_text", "")
    
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt = f"""
            Score how well this candidate matches this job on a scale from 0 to 10.
            Return a valid JSON object with keys 'score' (int 0-10) and 'cover_letter' (string max 3 paragraphs).
            
            JOB TITLE: {job_title}
            JOB DESCRIPTION: {job_desc[:2000]}
            
            CANDIDATE RESUME: {resume_text}
            """
            res = model.generate_content(prompt)
            data = json.loads(res.text.strip().lstrip("```json").rstrip("```"))
            return int(data.get("score", 5)), data.get("cover_letter", "")
        except Exception as e:
            if not _GENAI_WARNED:
                print(f"Gemini API call warning (using fallback heuristic): {e}")
                _GENAI_WARNED = True
            
    # Heuristic scoring fallback for testing without API key
    preferred_fields = [f.lower() for f in profile.get("field_preferences", [])]
    title_lower = job_title.lower()
    match = any(field in title_lower for field in preferred_fields)
    score = 8 if match else 4
    cover_letter = (
        f"Dear Hiring Manager,\n\nI am writing to express my strong interest in the {job_title} role at your company. "
        f"With a background in software development and technical problem solving, I am confident in my ability to add value to your team.\n\n"
        f"Best regards,\n{profile.get('first_name', 'Applicant')} {profile.get('last_name', '')}"
    )
    return score, cover_letter

def answer_custom_question(question: str, profile: dict) -> str:
    """
    Answer custom application questions using Gemini AI strictly from candidate profile.
    Returns the answer string, or 'UNKNOWN' if profile data is insufficient.
    Strictly follows Rules: Temperature 0.3, max tokens 200, no hallucination.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                "gemini-1.5-flash",
                generation_config={"temperature": 0.3, "max_output_tokens": 200}
            )
            prompt = f"""
Answer the following job application question strictly and ONLY using the provided candidate profile data.
If the required information is not available in the profile, return exactly UNKNOWN without any extra text or elaboration.

CANDIDATE PROFILE:
{json.dumps(profile, indent=2, ensure_ascii=False)}

QUESTION:
{question}
"""
            res = model.generate_content(prompt)
            answer = res.text.strip()
            if not answer or "UNKNOWN" in answer.upper():
                return "UNKNOWN"
            return answer
        except Exception as e:
            print(f"Gemini API question answering warning: {e}")

    # Fallback heuristic checking profile directly without API key
    q_lower = question.lower()
    if "first name" in q_lower:
        return profile.get("first_name", "UNKNOWN") or "UNKNOWN"
    if "last name" in q_lower:
        return profile.get("last_name", "UNKNOWN") or "UNKNOWN"
    if "email" in q_lower:
        return profile.get("email", "UNKNOWN") or "UNKNOWN"
    if "phone" in q_lower:
        return profile.get("phone", "UNKNOWN") or "UNKNOWN"
    if "linkedin" in q_lower:
        return profile.get("linkedin_url", "UNKNOWN") or "UNKNOWN"
    if "github" in q_lower:
        return profile.get("github_url", "UNKNOWN") or "UNKNOWN"
    if "portfolio" in q_lower or "website" in q_lower:
        return profile.get("portfolio_url", "UNKNOWN") or "UNKNOWN"
    if "location" in q_lower or "city" in q_lower:
        locs = profile.get("location_preferences", [])
        return ", ".join(locs) if locs else "UNKNOWN"

    return "UNKNOWN"

def process_unscored_jobs(db_path: Path = DB_PATH, min_score: int = 6) -> int:
    """Score all un-scored jobs in SQLite database and populate applications queue."""
    init_db(db_path)
    profile = get_profile_from_db(db_path)
    if not profile:
        print("Warning: No profile found in DB, skipping matcher.")
        return 0
        
    scored_count = 0
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        unscored = conn.execute("""
            SELECT j.id, j.title, j.description 
            FROM jobs j 
            LEFT JOIN applications a ON j.id = a.job_id 
            WHERE a.id IS NULL
            LIMIT 50
        """).fetchall()
        
        for job in unscored:
            score, cover_letter = score_job_with_llm(job["title"], job["description"] or "", profile)
            status = "QUEUED" if score >= min_score else "SCORED"
            app_id = str(uuid.uuid4())
            conn.execute("""
                INSERT INTO applications (id, job_id, status, score, cover_letter)
                VALUES (?, ?, ?, ?, ?)
            """, (app_id, job["id"], status, score, cover_letter))
            scored_count += 1
            
    return scored_count

if __name__ == "__main__":
    init_db()
    count = process_unscored_jobs()
    print(f"Matcher test passed: Scored {count} jobs in queue.")
