# Auto-Job Applier

A single-stack Python automation tool that collects Greenhouse/Lever job postings, matches and scores jobs using Google Gemini AI, fills application forms automatically via Playwright, and alerts the candidate via Telegram when human intervention is required.

## Directory Layout
```text
e:\Desktop\Applivo/
├── main.py             # Pipeline entry point
├── app.db              # SQLite database
├── config/
│   └── profile.json    # Candidate profile & preferences
├── docs/
│   ├── PRD.md          # Product Requirements Document
│   ├── Architecture.md # Technical Architecture
│   ├── Rules.md        # Development Rules
│   ├── Phases.md       # Implementation Roadmap
│   ├── Design.md       # UI Design System
│   └── Memory.md       # Progress Log
└── src/
    ├── db.py           # Database & profile operations
    ├── collector.py    # Greenhouse/Lever job scraper
    ├── matcher.py      # Gemini AI scoring engine
    ├── applier.py      # Playwright form automation
    ├── notifier.py     # Telegram notification dispatcher
    └── dashboard.py    # Single-file FastAPI dashboard
```

## Quick Start

### 1. Run Pipeline
```bash
python main.py
```

### 2. Launch Dashboard
```bash
python src/dashboard.py
```
