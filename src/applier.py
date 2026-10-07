import hashlib
import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
from db import DB_PATH, get_profile_from_db, init_db
from notifier import notify_pending_job

SCREENSHOTS_DIR = Path("screenshots")

def detect_custom_question(page) -> str | None:
    """Detect unhandled custom questions in inputs, textareas, and select elements."""
    standard_names = {
        "first_name", "last_name", "name", "email", "phone", "org", "company", "organization",
        "urls[linkedin]", "urls[github]", "urls[portfolio]", "urls[twitter]", "urls[other]",
        "linkedin", "github", "website", "portfolio", "resume"
    }
    
    elements = page.query_selector_all("textarea, select, input[type='text'], input:not([type])")
    for el in elements:
        try:
            if hasattr(el, "is_visible") and not el.is_visible():
                continue
        except Exception:
            pass
        name = (el.get_attribute("name") or "").lower()
        elem_id = (el.get_attribute("id") or "").lower()
        
        if name in standard_names or elem_id in standard_names:
            continue
        if any(std in name or std in elem_id for std in ["linkedin", "github", "website", "portfolio"]):
            continue
            
        # Extract label or question text
        try:
            text = el.evaluate("""e => {
                const id = e.id;
                const label = (id ? document.querySelector(`label[for='${id}']`) : null) 
                    || e.closest('label') 
                    || e.closest('div')?.querySelector('label')
                    || e.closest('.field')?.querySelector('label');
                return (label ? label.innerText : '') || e.getAttribute('aria-label') || e.getAttribute('placeholder') || e.getAttribute('name') || '';
            }""").strip()
            if text:
                return " ".join(text.split())[:100]
        except Exception:
            pass
            
        fallback = el.get_attribute("placeholder") or el.get_attribute("name") or el.get_attribute("id") or "Custom Question"
        return str(fallback)[:100]
        
    return None

def apply_to_job(job_url: str, profile: dict, dry_run: bool = False) -> tuple[str, str, str]:
    """
    Automate form submission for Greenhouse/Lever job postings.
    Returns tuple of (status, pending_reason, screenshot_path).
    """
    SCREENSHOTS_DIR.mkdir(exist_ok=True)
    url_hash = hashlib.sha256(job_url.encode("utf-8")).hexdigest()[:12]
    screenshot_path = str(SCREENSHOTS_DIR / f"app_{url_hash}.png")
    
    if dry_run:
        return "APPLIED", "", screenshot_path

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not installed.")
        return "PENDING", "PLAYWRIGHT_NOT_INSTALLED", screenshot_path

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(job_url, timeout=30000)
            
            # Rule: CAPTCHA Non-Bypass -> Trigger PENDING
            if page.query_selector("iframe[src*='recaptcha'], iframe[src*='hcaptcha']"):
                page.screenshot(path=screenshot_path)
                return "PENDING", "CAPTCHA_DETECTED", screenshot_path
                
            # Fill standard fields if present (Greenhouse & Lever)
            full_name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()
            if page.query_selector("#first_name"):
                page.fill("#first_name", profile.get("first_name", ""))
            if page.query_selector("#last_name"):
                page.fill("#last_name", profile.get("last_name", ""))
            if page.query_selector("input[name='name']") and not page.query_selector("#first_name"):
                page.fill("input[name='name']", full_name)
            elif page.query_selector("#name") and not page.query_selector("#first_name"):
                page.fill("#name", full_name)
                
            if page.query_selector("input[name='email']"):
                page.fill("input[name='email']", profile.get("email", ""))
            elif page.query_selector("#email"):
                page.fill("#email", profile.get("email", ""))
                
            if page.query_selector("input[name='phone']"):
                page.fill("input[name='phone']", profile.get("phone", ""))
            elif page.query_selector("#phone"):
                page.fill("#phone", profile.get("phone", ""))

            company = profile.get("current_company", profile.get("company", profile.get("organization", "")))
            if company:
                if page.query_selector("input[name='org']"):
                    page.fill("input[name='org']", company)
                elif page.query_selector("input[name='company']"):
                    page.fill("input[name='company']", company)
                
            # Upload resume PDF if present
            resume_path = profile.get("resume_path")
            if resume_path and os.path.exists(resume_path) and page.query_selector("input[type='file']"):
                page.set_input_files("input[type='file']", resume_path)
                
            # Detect unhandled custom questions -> Trigger PENDING
            custom_q = detect_custom_question(page)
            if custom_q:
                page.screenshot(path=screenshot_path)
                return "PENDING", f"CUSTOM_QUESTION: {custom_q}", screenshot_path

            # Pre-submission Screenshot per Rule
            page.screenshot(path=screenshot_path)
            
            # Submit form if not dry run (Greenhouse & Lever)
            submit_btn = page.query_selector("#submit_app, #btn-submit, button[data-qa='btn-submit'], button[type='submit']")
            if submit_btn:
                submit_btn.click()
                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    page.wait_for_load_state("domcontentloaded", timeout=5000)
                return "APPLIED", "", screenshot_path
            else:
                return "PENDING", "SUBMIT_BUTTON_NOT_FOUND", screenshot_path

    except Exception as e:
        return "FAILED", str(e), screenshot_path

LOGS_DIR = Path("logs")

def log_failure(app_id: str, job_title: str, company: str, error: str) -> None:
    """Log application failure to logs/failures.log."""
    try:
        LOGS_DIR.mkdir(exist_ok=True)
        with open(LOGS_DIR / "failures.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] ID={app_id} | {company} - {job_title} | Error: {error}\n")
    except Exception as e:
        print(f"Warning: Failed logging failure: {e}")

def process_queued_applications(db_path: Path = DB_PATH, dry_run: bool = True) -> int:
    """Process all QUEUED applications in SQLite database, respecting daily limit."""
    init_db(db_path)
    profile = get_profile_from_db(db_path)
    daily_limit = profile.get("daily_apply_limit", 20)
    processed = 0
    
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        
        # Count applications already applied in the last 24 hours
        applied_today = conn.execute("""
            SELECT COUNT(*) FROM applications
            WHERE status = 'APPLIED' AND applied_at >= datetime('now', '-1 day')
        """).fetchone()[0]
        
        remaining = max(0, daily_limit - applied_today)
        if remaining == 0:
            print(f"Daily limit reached ({daily_limit} applications in last 24h). Skipping.")
            return 0
        
        queued = conn.execute("""
            SELECT a.id, a.job_id, a.retry_count, j.url, j.company, j.title
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE a.status IN ('QUEUED', 'FAILED') AND (a.retry_count < 2 OR a.retry_count IS NULL)
            LIMIT ?
        """, (remaining,)).fetchall()
        
        for app in queued:
            status, reason, ss_path = apply_to_job(app["url"], profile, dry_run=dry_run)
            current_retry = (app["retry_count"] or 0)
            
            if status == "FAILED":
                current_retry += 1
                log_failure(app["id"], app["title"], app["company"], reason)
                if current_retry >= 2:
                    status = "PERMANENT_FAIL"
                    try:
                        notify_pending_job(
                            company=app["company"],
                            job_title=app["title"],
                            reason=f"PERMANENT_FAIL: Max retries exceeded ({reason})",
                            job_url=app["url"]
                        )
                    except Exception as e:
                        print(f"Warning: Failed sending permanent fail Telegram notification: {e}")

            applied_at_val = "CURRENT_TIMESTAMP" if status == "APPLIED" else "NULL"
            conn.execute(f"""
                UPDATE applications 
                SET status = ?, pending_reason = ?, screenshot_path = ?,
                    retry_count = ?, last_error = ?,
                    applied_at = {applied_at_val}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, reason, ss_path, current_retry, reason if status in ("FAILED", "PERMANENT_FAIL") else None, app["id"]))
            processed += 1
            
            if status == "PENDING":
                try:
                    notify_pending_job(
                        company=app["company"],
                        job_title=app["title"],
                        reason=reason,
                        job_url=app["url"]
                    )
                except Exception as e:
                    print(f"Warning: Failed to send Telegram notification: {e}")
            
    return processed

def retry_failed_applications(db_path: Path = DB_PATH, dry_run: bool = True) -> int:
    """Explicitly retry applications in FAILED state that have not exceeded max retries."""
    return process_queued_applications(db_path=db_path, dry_run=dry_run)

if __name__ == "__main__":
    init_db()
    count = process_queued_applications(dry_run=True)
    print(f"Applier test passed: Processed {count} queued applications (dry-run).")
