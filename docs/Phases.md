# Implementation Phases

## Phase 1: Storage & Profile Setup (COMPLETED)
- [x] Create SQLite database schema (`jobs`, `applications`, `profile`).
- [x] Create default `profile.json` format.
- [x] Build DB initialization & atomic loader script (`db.py`).
- [x] Verification: Run `python db.py` self-check assertion test.

## Phase 2: Job Collector & Gemini AI Matcher (COMPLETED)
- [x] Implement Greenhouse & Lever public JSON API job fetching (`collector.py`).
- [x] Deduplicate new job postings against SQLite `jobs` table.
- [x] Build Gemini LLM scoring (0-10 match score) and cover letter generation (`matcher.py`).
- [x] Save qualified jobs to queue in `applications` table.
- [x] Verification: Executed `python collector.py` (210 jobs saved) and `python matcher.py` (50 jobs scored).

## Phase 3: Playwright Form Automation Engine (COMPLETED)
- [x] Implement Playwright handlers for Greenhouse and Lever forms (`applier.py`).
- [x] Implement CAPTCHA & un-handled question detection (`PENDING` state).
- [x] Add pre-submission screenshot capture functionality.
- [x] Verification: Executed `python applier.py` dry-run processing.

## Phase 4: Telegram Scheduler & Notification Service (COMPLETED)
- [x] Implement Telegram Bot API alert dispatcher (`notifier.py`).
- [x] Add automated 6-hour polling cycle and daily limit counter.
- [x] Send instant Telegram alerts on `PENDING` job states.
- [x] Verification: Executed `python notifier.py` test run.

## Phase 5: Web Dashboard & Human Review UI (COMPLETED)
- [x] Build single-file FastAPI server-rendered dashboard (`dashboard.py`).
- [x] Display application counts by status (Applied, Pending, Failed).
- [x] Add interactive manual resolution buttons for `PENDING` applications.
- [x] Verification: Executed `python dashboard.py` HTML rendering test.
