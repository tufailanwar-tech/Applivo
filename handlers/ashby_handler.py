import json
import urllib.request
import urllib.error

def fetch_ashby_jobs(company: str) -> list[dict]:
    """Fetch public job postings from Ashby API for a company."""
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

if __name__ == "__main__":
    jobs = fetch_ashby_jobs("ramp")
    print(f"Ashby test fetched {len(jobs)} jobs.")
