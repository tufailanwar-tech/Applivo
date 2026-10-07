import json
import urllib.request
import urllib.error

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

if __name__ == "__main__":
    jobs = fetch_remotive_jobs("software-dev")
    print(f"Remotive test fetched {len(jobs)} jobs.")
