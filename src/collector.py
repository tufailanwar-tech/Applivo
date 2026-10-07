import sys
import json
import sqlite3
import urllib.request
import urllib.error
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
from db import DB_PATH, init_db, get_profile_from_db, load_profile_json

DEFAULT_COMPANIES = ["gitlab", "hashicorp", "automattic"]

def fetch_greenhouse_jobs(company: str) -> list[dict]:
    """Fetch public job listings from Greenhouse API for a given company."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                jobs = []
                for j in data.get("jobs", []):
                    jobs.append({
                        "id": f"gh_{j['id']}",
                        "source": "greenhouse",
                        "company": company,
                        "title": j.get("title", ""),
                        "url": j.get("absolute_url", ""),
                        "description": j.get("content", ""),
                        "location": j.get("location", {}).get("name", "Remote")
                    })
                return jobs
    except Exception as e:
        print(f"Warning: Failed fetching Greenhouse jobs for {company}: {e}")
    return []

def fetch_lever_jobs(company: str) -> list[dict]:
    """Fetch public job listings from Lever API for a given company."""
    url = f"https://api.lever.co/v0/postings/{company}?mode=json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                jobs = []
                for j in data:
                    jobs.append({
                        "id": f"lever_{j['id']}",
                        "source": "lever",
                        "company": company,
                        "title": j.get("text", ""),
                        "url": j.get("hostedUrl", ""),
                        "description": j.get("descriptionPlain", ""),
                        "location": j.get("categories", {}).get("location", "Remote")
                    })
                return jobs
    except Exception as e:
        print(f"Warning: Failed fetching Lever jobs for {company}: {e}")
    return []

def fetch_ashby_jobs(company: str) -> list[dict]:
    """Fetch public job listings from Ashby API for a given company."""
    url = f"https://api.ashbyhq.com/posting-api/job-board/{company}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                jobs = []
                for j in data.get("jobs", []):
                    jobs.append({
                        "id": f"ashby_{j.get('id', '')}",
                        "source": "ashby",
                        "company": company,
                        "title": j.get("title", ""),
                        "url": j.get("jobUrl", f"https://jobs.ashbyhq.com/{company}/{j.get('id', '')}"),
                        "description": j.get("descriptionHtml", j.get("descriptionPlain", "")),
                        "location": j.get("location", "Remote")
                    })
                return jobs
    except Exception as e:
        print(f"Warning: Failed fetching Ashby jobs for {company}: {e}")
    return []

def fetch_remotive_jobs(category: str = "software-dev") -> list[dict]:
    """Fetch remote job postings from Remotive public API."""
    url = f"https://remotive.com/api/remote-jobs?category={category}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                jobs = []
                for j in data.get("jobs", []):
                    jobs.append({
                        "id": f"remotive_{j.get('id', '')}",
                        "source": "remotive",
                        "company": j.get("company_name", "Unknown"),
                        "title": j.get("title", ""),
                        "url": j.get("url", ""),
                        "description": j.get("description", ""),
                        "location": j.get("candidate_required_location", "Remote")
                    })
                return jobs
    except Exception as e:
        print(f"Warning: Failed fetching Remotive jobs: {e}")
    return []

def collect_and_save_jobs(companies: list[str] | None = None, include_remotive: bool = True, db_path: Path = DB_PATH) -> int:
    """Collect jobs from Greenhouse, Lever, Ashby, and Remotive, saving new jobs to SQLite."""
    init_db(db_path)
    if not companies:
        try:
            profile = get_profile_from_db(db_path)
            if not profile:
                profile = load_profile_json()
            companies = profile.get("target_companies")
        except Exception:
            companies = None
    if not companies:
        companies = DEFAULT_COMPANIES

    total_saved = 0
    all_jobs = []
    
    # 1. Collect from company boards (Greenhouse, Lever, Ashby)
    for company in companies:
        all_jobs.extend(fetch_greenhouse_jobs(company))
        all_jobs.extend(fetch_lever_jobs(company))
        all_jobs.extend(fetch_ashby_jobs(company))

    # 2. Collect from Remotive category if enabled
    if include_remotive:
        all_jobs.extend(fetch_remotive_jobs("software-dev"))

    with sqlite3.connect(db_path) as conn:
        for job in all_jobs:
            if not job.get("url"):
                continue
            cursor = conn.execute("""
                INSERT INTO jobs (id, source, company, title, url, description, location)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO NOTHING
            """, (job["id"], job["source"], job["company"], job["title"], job["url"], job["description"], job["location"]))
            if cursor.rowcount > 0:
                total_saved += 1
    return total_saved

if __name__ == "__main__":
    init_db()
    count = collect_and_save_jobs(["gitlab"])
    print(f"Collector test passed: Saved {count} jobs into database.")
