import os
import sys
import sqlite3
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
from db import DB_PATH, init_db

SCREENSHOTS_DIR = Path("screenshots")
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "admin123")

DASHBOARD_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Auto-Job Applier Dashboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {{ background-color: #0f172a; color: #f8fafc; font-family: system-ui, -apple-system, sans-serif; }}
    .card {{ background-color: #1e293b; border: 1px solid #334155; }}
    .badge-applied {{ background-color: #064e3b; color: #34d399; }}
    .badge-pending {{ background-color: #78350f; color: #fbbf24; }}
    .badge-failed {{ background-color: #7f1d1d; color: #f87171; }}
    .badge-permanent_fail {{ background-color: #450a0a; color: #ef4444; border: 1px solid #991b1b; }}
    .badge-queued {{ background-color: #312e81; color: #818cf8; }}
    .tab-btn.active {{ border-bottom: 2px solid #38bdf8; color: #38bdf8; font-weight: 600; }}
  </style>
</head>
<body class="p-4 md:p-8">
  <div class="max-w-6xl mx-auto space-y-6">
    
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between border-b border-slate-700 pb-4 gap-4">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">Auto-Job Applier</h1>
        <p class="text-slate-400 text-sm mt-1">Multi-Platform Automation & Gemini AI Matching</p>
      </div>
      <div class="flex items-center space-x-3">
        <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-emerald-950 text-emerald-400 border border-emerald-800">
          ● System Active (20/day Cap)
        </span>
      </div>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div class="card p-4 rounded-xl cursor-pointer hover:border-emerald-500" onclick="filterTab('APPLIED')">
        <span class="text-slate-400 text-xs font-semibold uppercase tracking-wider">Applied</span>
        <div class="text-2xl font-bold mt-1 text-emerald-400">{applied_count}</div>
      </div>
      <div class="card p-4 rounded-xl cursor-pointer hover:border-amber-500" onclick="filterTab('PENDING')">
        <span class="text-slate-400 text-xs font-semibold uppercase tracking-wider">Pending (Action)</span>
        <div class="text-2xl font-bold mt-1 text-amber-400">{pending_count}</div>
      </div>
      <div class="card p-4 rounded-xl cursor-pointer hover:border-rose-500" onclick="filterTab('FAILED')">
        <span class="text-slate-400 text-xs font-semibold uppercase tracking-wider">Failed / Retries</span>
        <div class="text-2xl font-bold mt-1 text-rose-400">{failed_count}</div>
      </div>
      <div class="card p-4 rounded-xl cursor-pointer hover:border-indigo-500" onclick="filterTab('ALL')">
        <span class="text-slate-400 text-xs font-semibold uppercase tracking-wider">Total Scored</span>
        <div class="text-2xl font-bold mt-1 text-indigo-400">{total_count}</div>
      </div>
    </div>

    <!-- Filter Tabs -->
    <div class="flex border-b border-slate-700 space-x-6 text-sm">
      <button class="tab-btn pb-3 active text-slate-300 hover:text-white" onclick="filterTab('ALL', this)">All Applications</button>
      <button class="tab-btn pb-3 text-slate-300 hover:text-white" onclick="filterTab('PENDING', this)">Pending Review</button>
      <button class="tab-btn pb-3 text-slate-300 hover:text-white" onclick="filterTab('APPLIED', this)">Applied</button>
      <button class="tab-btn pb-3 text-slate-300 hover:text-white" onclick="filterTab('FAILED', this)">Failed</button>
    </div>

    <!-- Applications Table / Cards -->
    <div class="card rounded-xl overflow-hidden">
      <div class="px-6 py-4 border-b border-slate-700 flex justify-between items-center">
        <h2 class="text-lg font-semibold">Application History & Q&A</h2>
        <span class="text-xs text-slate-400">Real-time status</span>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-left text-sm" id="appTable">
          <thead class="bg-slate-900/50 text-slate-400 uppercase text-xs">
            <tr>
              <th class="px-6 py-3">Company & Title</th>
              <th class="px-6 py-3">Source</th>
              <th class="px-6 py-3">Score</th>
              <th class="px-6 py-3">Status</th>
              <th class="px-6 py-3">Details / Screenshot</th>
              <th class="px-6 py-3">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-800">
            {table_rows}
          </tbody>
        </table>
      </div>
    </div>

  </div>

  <script>
    function filterTab(status, btn) {{
      if (btn) {{
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      }}
      const rows = document.querySelectorAll('#appTable tbody tr');
      rows.forEach(r => {{
        const rowStatus = r.getAttribute('data-status');
        if (status === 'ALL' || rowStatus === status || (status === 'FAILED' && (rowStatus === 'FAILED' || rowStatus === 'PERMANENT_FAIL'))) {{
          r.style.display = '';
        }} else {{
          r.style.display = 'none';
        }}
      }});
    }}

    async function resolveApp(appId, newStatus) {{
      try {{
        const res = await fetch(`/api/resolve/${{appId}}?status=${{newStatus}}`, {{ method: 'POST' }});
        if (res.ok) {{
          window.location.reload();
        }} else {{
          alert('Failed to resolve application status');
        }}
      }} catch (err) {{
        console.error(err);
      }}
    }}
  </script>
</body>
</html>
"""

def render_dashboard_html(db_path: Path = DB_PATH) -> str:
    """Query database statistics and render single-file HTML dashboard."""
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        stats = dict(conn.execute("""
            SELECT status, COUNT(*) as cnt FROM applications GROUP BY status
        """).fetchall())
        
        applied_count = stats.get("APPLIED", 0)
        pending_count = stats.get("PENDING", 0)
        failed_count = stats.get("FAILED", 0) + stats.get("PERMANENT_FAIL", 0)
        total_count = sum(stats.values())
        
        rows = conn.execute("""
            SELECT a.id, a.status, a.score, a.pending_reason, a.cover_letter, a.screenshot_path, a.retry_count, a.last_error,
                   j.company, j.title, j.source, j.url
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            ORDER BY a.updated_at DESC
            LIMIT 50
        """).fetchall()
        
        table_rows = []
        for r in rows:
            badge_class = f"badge-{r['status'].lower()}"
            reason_text = r["pending_reason"] or r["last_error"] or "-"
            
            # Screenshot link
            ss_html = ""
            if r["screenshot_path"] and os.path.exists(r["screenshot_path"]):
                ss_filename = Path(r["screenshot_path"]).name
                ss_html = f"<a href='/screenshots/{ss_filename}' target='_blank' class='text-xs text-sky-400 hover:underline block'>🖼️ Screenshot</a>"
            
            # Cover letter / Q&A
            qa_html = ""
            if r["cover_letter"]:
                qa_snippet = (r["cover_letter"][:60] + "...") if len(r["cover_letter"]) > 60 else r["cover_letter"]
                qa_html = f"<span class='text-xs text-slate-400 block' title='{r['cover_letter']}'>📝 {qa_snippet}</span>"

            action_btn = f"<span class='text-xs text-slate-400'>{reason_text}</span>"
            if r["status"] == "PENDING":
                action_btn = f"""
                <div class='flex flex-wrap gap-1'>
                  <a href="{r['url']}" target="_blank" class="px-2 py-1 bg-blue-700 hover:bg-blue-600 text-white text-xs rounded font-medium">Open Form</a>
                  <button onclick="resolveApp('{r['id']}', 'APPLIED')" class="px-2 py-1 bg-emerald-700 hover:bg-emerald-600 text-white text-xs rounded font-medium">Applied</button>
                  <button onclick="resolveApp('{r['id']}', 'FAILED')" class="px-2 py-1 bg-slate-700 hover:bg-slate-600 text-slate-300 text-xs rounded font-medium">Skip</button>
                </div>
                """
            elif r["status"] in ("FAILED", "PERMANENT_FAIL"):
                action_btn = f"""
                <div class='flex flex-wrap gap-1'>
                  <button onclick="resolveApp('{r['id']}', 'QUEUED')" class="px-2 py-1 bg-indigo-700 hover:bg-indigo-600 text-white text-xs rounded font-medium">Retry</button>
                  <span class='text-xs text-rose-400 block'>{reason_text}</span>
                </div>
                """
                
            row_html = f"""
            <tr class="hover:bg-slate-800/50" data-status="{r['status']}">
              <td class="px-6 py-4 font-medium">
                <a href="{r['url']}" target="_blank" class="text-blue-400 hover:underline font-semibold">{r['company']} - {r['title']}</a>
              </td>
              <td class="px-6 py-4 text-slate-400 uppercase text-xs">{r['source']}</td>
              <td class="px-6 py-4 font-mono font-bold">{r['score']}/10</td>
              <td class="px-6 py-4">
                <span class="px-2.5 py-1 rounded-md text-xs font-semibold {badge_class}">{r['status']}</span>
              </td>
              <td class="px-6 py-4 space-y-1">
                {ss_html}
                {qa_html}
              </td>
              <td class="px-6 py-4">{action_btn}</td>
            </tr>
            """
            table_rows.append(row_html)
            
        if not table_rows:
            table_rows = ["<tr><td colspan='6' class='px-6 py-8 text-center text-slate-500'>No applications in queue yet.</td></tr>"]

    return DASHBOARD_HTML_TEMPLATE.format(
        applied_count=applied_count,
        pending_count=pending_count,
        failed_count=failed_count,
        total_count=total_count,
        table_rows="".join(table_rows)
    )

# FastAPI Integration
try:
    from fastapi import FastAPI, Depends, HTTPException, status
    from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
    from fastapi.security import HTTPBasic, HTTPBasicCredentials
    import secrets

    security = HTTPBasic()
    app = FastAPI(title="Auto-Job Applier Dashboard")

    def verify_auth(credentials: HTTPBasicCredentials = Depends(security)):
        correct_password = os.environ.get("DASHBOARD_PASSWORD", "admin123")
        is_correct_password = secrets.compare_digest(credentials.password, correct_password)
        if not is_correct_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect credentials",
                headers={"WWW-Authenticate": "Basic"},
            )
        return credentials.username

    @app.get("/", response_class=HTMLResponse)
    @app.get("/dashboard", response_class=HTMLResponse)
    def dashboard():
        return HTMLResponse(content=render_dashboard_html())

    @app.get("/screenshots/{filename}")
    def get_screenshot(filename: str):
        file_path = SCREENSHOTS_DIR / filename
        if file_path.exists():
            return FileResponse(file_path)
        raise HTTPException(status_code=404, detail="Screenshot not found")

    @app.get("/api/stats")
    def get_stats():
        init_db()
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute("SELECT status, COUNT(*) FROM applications GROUP BY status").fetchall()
            return dict(rows)

    @app.post("/api/resolve/{app_id}")
    def resolve_application(app_id: str, status: str = "APPLIED"):
        init_db()
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                UPDATE applications 
                SET status = ?, pending_reason = NULL, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (status, app_id))
        return JSONResponse(content={"status": "ok", "app_id": app_id, "new_status": status})
except ImportError:
    app = None

if __name__ == "__main__":
    init_db()
    html_output = render_dashboard_html()
    assert "Auto-Job Applier Dashboard" in html_output, "Dashboard HTML render failed!"
    print("Dashboard test passed: Rendered HTML dashboard successfully.")
