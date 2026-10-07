# System Architecture & Flow

## 1. Technical Stack
* **Language & Runtime**: Python 3.10+
* **Database**: SQLite3 (`sqlite3` stdlib)
* **Browser Automation**: Playwright (`playwright` sync API)
* **AI Engine**: Google Gemini API (`google-genai`)
* **Web Framework**: FastAPI + Uvicorn (Single-file server-rendered UI)
* **Alerting**: Telegram Bot Webhook / Bot API (`urllib.request` / `requests`)

## 2. File & Folder Structure
```text
e:\Desktop\Applivo/
├── main.py             # Main entry point & pipeline orchestrator
├── app.db              # Local SQLite database
├── config/             # User configuration files
│   └── profile.json    # Candidate profile, skills & resume data
├── docs/               # Technical documentation & project blueprints
│   ├── PRD.md          # Project Requirements Document
│   ├── Architecture.md # Technical Architecture & Data Flow
│   ├── Rules.md        # AI & Development Guidelines
│   ├── Phases.md       # Implementation Phase Roadmap
│   ├── Design.md       # Visual Theme & UI Specifications
│   └── Memory.md       # Live Project State & Progress Log
└── src/                # Modular Python source package
    ├── __init__.py     # Package marker
    ├── db.py           # SQLite schema & database connection management
    ├── collector.py    # Greenhouse / Lever job collection logic
    ├── matcher.py      # Gemini AI job scoring & cover letter generator
    ├── applier.py      # Playwright form automation & screenshot engine
    ├── notifier.py     # Telegram notification dispatcher
    └── dashboard.py    # Single-file FastAPI web dashboard
```

## 3. Data Flow & Application Lifecycle
```text
[Public APIs] ---> src/collector.py ---> [jobs table (FOUND)]
                                                |
                                          src/matcher.py (Gemini 1.5)
                                                |
                                       [applications (SCORED)]
                                                |
                                          src/applier.py (Playwright)
                                                |
                         +----------------------+----------------------+
                         |                      |                      |
                    (Success)               (CAPTCHA)               (Error)
                         v                      v                      v
                    [APPLIED]               [PENDING]               [FAILED]
                                                |
                                          src/notifier.py
                                                |
                                         (Telegram Alert)
```
