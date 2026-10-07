import os
import json
import urllib.request
import urllib.parse

def send_telegram_message(message: str, bot_token: str = None, chat_id: str = None) -> bool:
    """Send alert notification to Telegram via Bot API."""
    token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
    cid = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not cid:
        safe_msg = message.encode("ascii", errors="replace").decode("ascii")
        print(f"[Notifier Log] TELEGRAM_BOT_TOKEN/CHAT_ID not set. Alert message:\n{safe_msg}")
        return False
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": cid, "text": message, "parse_mode": "HTML"}).encode("utf-8")
    
    try:
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"Warning: Failed sending Telegram alert: {e}")
        return False

def notify_pending_job(company: str, job_title: str, reason: str, job_url: str = "") -> bool:
    """Notify user of a job requiring human intervention (CAPTCHA / unknown field)."""
    msg = (
        f"⚠️ <b>Action Required: PENDING Job Application</b>\n\n"
        f"<b>Company:</b> {company}\n"
        f"<b>Title:</b> {job_title}\n"
        f"<b>Reason:</b> {reason}\n"
        f"<b>URL:</b> {job_url}\n\n"
        f"👉 Check your dashboard to resolve."
    )
    return send_telegram_message(msg)

if __name__ == "__main__":
    success = notify_pending_job("GitLab", "Senior Backend Engineer", "CAPTCHA_DETECTED", "https://example.com/job")
    print("Notifier test passed: Dispatched test notification log.")
