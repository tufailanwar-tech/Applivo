import sys
import time
import argparse
from pathlib import Path

# Add src/ to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from db import init_db, load_profile_json, save_profile_to_db
from collector import collect_and_save_jobs
from matcher import process_unscored_jobs
from applier import process_queued_applications
from notifier import notify_pending_job

def run_pipeline(dry_run: bool = True):
    """Run full job application pipeline end-to-end."""
    print("=== Step 1: Initializing Database & Loading Profile ===")
    init_db()
    profile = load_profile_json()
    save_profile_to_db(profile)
    print("-> Database initialized and profile synced.")

    print("\n=== Step 2: Collecting Jobs (Greenhouse / Lever) ===")
    collected = collect_and_save_jobs(companies=profile.get("target_companies"))
    print(f"-> Collected & saved {collected} new job postings.")

    print("\n=== Step 3: Scoring Jobs with Gemini LLM ===")
    scored = process_unscored_jobs(min_score=6)
    print(f"-> Scored {scored} job postings and updated queue.")

    print("\n=== Step 4: Executing Form Applications (Playwright) ===")
    applied = process_queued_applications(dry_run=dry_run)
    print(f"-> Processed {applied} queued applications (dry_run={dry_run}).")

    print("\n=== Pipeline Execution Complete ===")

def run_loop(interval_hours: int = 6, dry_run: bool = True):
    """Run pipeline continuously every X hours."""
    print(f"Starting pipeline scheduler loop (interval: {interval_hours}h)...")
    while True:
        try:
            run_pipeline(dry_run=dry_run)
        except Exception as e:
            print(f"Pipeline loop error: {e}")
        print(f"\nSleeping for {interval_hours} hours until next run...")
        time.sleep(interval_hours * 3600)

def start_dashboard_server(port: int = 8000):
    """Start local dashboard web server."""
    try:
        import uvicorn
        from dashboard import app
        if app:
            print(f"Launching Auto-Job Applier Dashboard at http://127.0.0.1:{port}")
            uvicorn.run(app, host="127.0.0.1", port=port)
        else:
            print("FastAPI not installed. Run: pip install fastapi uvicorn")
    except ImportError as e:
        print(f"Failed starting dashboard server: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-Job Applier Pipeline & Service Runner")
    parser.add_argument("--live", action="store_true", help="Execute live form filling instead of dry-run")
    parser.add_argument("--loop", action="store_true", help="Run pipeline continuously in background loop")
    parser.add_argument("--interval", type=int, default=6, help="Interval in hours for --loop mode (default: 6)")
    parser.add_argument("--dashboard", action="store_true", help="Launch interactive web dashboard server")
    parser.add_argument("--port", type=int, default=8000, help="Port for web dashboard (default: 8000)")
    
    args = parser.parse_args()

    if args.dashboard:
        start_dashboard_server(port=args.port)
    elif args.loop:
        run_loop(interval_hours=args.interval, dry_run=not args.live)
    else:
        run_pipeline(dry_run=not args.live)
