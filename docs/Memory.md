# Active Project Memory & Progress Log

## Project State Summary
- **App Name**: Auto-Job Applier
- **Architecture**: Single-stack Python 3.10+ (SQLite3, Playwright, Gemini API, FastAPI, Telegram Bot)
- **Structure**: Clean modular folder structure (`src/`, `config/`, `docs/`, `main.py`)
- **Current Phase**: All Tasks 1–21 Completed & Verified

## Completed Tasks
- [x] **Task 1: Connect Telegram notifications to PENDING application state**:
  - Imported `notify_pending_job` into `src/applier.py`.
  - Added notification trigger in `process_queued_applications` whenever an application transitions from `QUEUED` to `PENDING`.
  - Ensured single notification per transition (only runs on initial `QUEUED` -> `PENDING` database status update).
  - Ensured non-blocking error handling to prevent Telegram network/auth failures from crashing application runs.
  - Verified safe credential handling (no tokens exposed in logs).
- [x] **Task 2: Daily Application Limit**:
  - `daily_apply_limit` is now enforced from `config/profile.json` (defaults to 20 if missing or invalid).
  - Applications are counted within the 24-hour window (`datetime('now', '-24 hours')`) in SQLite.
  - `applied_at` timestamp is set when status becomes `APPLIED`.
  - `dry_run` works correctly without Playwright installed (evaluates dry-run flag prior to importing Playwright).
  - Task 2 testing passed.
- [x] **Task 3: Deterministic Screenshot Filenames**:
  - Replaced built-in `hash(job_url)` in `src/applier.py` with `hashlib.sha256(job_url.encode("utf-8")).hexdigest()[:12]`.
  - Produces stable and deterministic screenshot filenames across different Python processes.
  - Verified with focused test: identical URLs yield identical filenames, distinct URLs yield distinct filenames, and cross-process runs remain consistent.
- [x] **Task 4A: Resume PDF Upload via Playwright**:
  - Added `resume_path` to `config/profile.json`.
  - Integrated `page.set_input_files("input[type='file']", resume_path)` in `src/applier.py` to upload the PDF when file input is present.
  - Preserved existing `dry_run` behavior and CAPTCHA detection.
  - Focused test passed verifying resume file upload execution and error/captcha boundary cases.
- [x] **Task 4B: Lever-Specific Form Selectors**:
  - Added Lever selectors in `src/applier.py` for full name (`input[name='name']`, `#name`), email (`input[name='email']`), phone (`input[name='phone']`), organization/company (`input[name='org']`, `input[name='company']`), and submit buttons (`#btn-submit`, `button[data-qa='btn-submit']`, `button[type='submit']`).
  - Preserved Greenhouse selectors, resume upload, CAPTCHA triggers, and error recovery.
  - Verified with focused mock unit tests for both Lever and Greenhouse submissions.
- [x] **Task 5: Dynamic Target Companies**:
  - Added `target_companies` list to `config/profile.json`.
  - Updated `src/collector.py` to read target companies from active profile / `profile.json` instead of relying solely on a hardcoded list.
  - Preserved fallback to `DEFAULT_COMPANIES = ["gitlab", "hashicorp", "automattic"]` if config is missing or empty.
  - Focused test passed verifying dynamic configuration loading and fallback behavior.
- [x] **Task 6: Improved Playwright Waits**:
  - Replaced arbitrary `page.wait_for_timeout(3000)` in `src/applier.py` with event-driven `page.wait_for_load_state("networkidle", timeout=5000)` (with graceful `domcontentloaded` fallback).
  - Preserved selectors, resume upload, CAPTCHA handling, and submission logic.
  - Focused test passed verifying `wait_for_load_state` invocation on submission without fixed sleep overhead.
- [x] **Task 7: Detect Custom Application Questions**:
  - Added `detect_custom_question(page)` helper in `src/applier.py` to identify unhandled text inputs, textareas, and select elements.
  - Form submission is halted when an unhandled question is detected, capturing the question/label text.
  - Application transitions to `PENDING` with reason `CUSTOM_QUESTION: <question_text>`, pre-submission screenshot is taken, and Telegram notification is dispatched.
  - Preserved standard field selectors, resume upload, CAPTCHA detection, rate limits, and submission logic.
  - Created focused unit test suite [`test_task7.py`](file:///e:/Desktop/Applivo/test_task7.py) with mocked Playwright fixtures; all 4 tests passed cleanly.
- [x] **Task 13: Gemini Custom Question Answering**:
  - Implemented `answer_custom_question(question, profile)` in [`services/llm_service.py`](file:///e:/Desktop/Applivo/services/llm_service.py) and [`src/matcher.py`](file:///e:/Desktop/Applivo/src/matcher.py).
  - Strictly follows Rules: Temperature 0.3, max tokens 200, answers strictly from profile JSON, and returns `UNKNOWN` when information is missing.
- [x] **Task 14: Ashby Job Collector**:
  - Implemented [`handlers/ashby_handler.py`](file:///e:/Desktop/Applivo/handlers/ashby_handler.py) and integrated into [`src/collector.py`](file:///e:/Desktop/Applivo/src/collector.py).
- [x] **Task 15: Remotive Job Collector**:
  - Implemented [`handlers/remotive_handler.py`](file:///e:/Desktop/Applivo/handlers/remotive_handler.py) and integrated into [`src/collector.py`](file:///e:/Desktop/Applivo/src/collector.py).
- [x] **Task 16: Dashboard Enhancements**:
  - Updated [`src/dashboard.py`](file:///e:/Desktop/Applivo/src/dashboard.py) with dynamic filter tabs (All, Pending, Applied, Failed), Q&A previews, screenshot viewer (`/screenshots/{filename}`), and pending action buttons.
- [x] **Task 17: Retry Logic & Failure Logging**:
  - Added `retry_count` and `last_error` to SQLite schema in [`src/db.py`](file:///e:/Desktop/Applivo/src/db.py).
  - Added failure logging to `logs/failures.log`, 2-attempt retry cap, and Telegram alert on `PERMANENT_FAIL`.
- [x] **Task 18 & 19: Security, Auth & Environment Configuration**:
  - Created [`.gitignore`](file:///e:/Desktop/Applivo/.gitignore), [`.env.example`](file:///e:/Desktop/Applivo/.env.example), and [`.env`](file:///e:/Desktop/Applivo/.env) with token isolation. Added HTTP basic/JWT auth support to dashboard.
- [x] **Task 20: Comprehensive Test Suite**:
  - Implemented unit & integration test suites in [`tests/`](file:///e:/Desktop/Applivo/tests/) covering collectors, LLM service, and pipeline flows. All tests passed.
- [x] **Task 21: Docker & Deployment**:
  - Created [`Dockerfile`](file:///e:/Desktop/Applivo/Dockerfile), [`docker-compose.yml`](file:///e:/Desktop/Applivo/docker-compose.yml), and [`requirements.txt`](file:///e:/Desktop/Applivo/requirements.txt).

## Current Phase: Complete (All Tasks 1–21 Complete & Verified)

## Modular File Structure & CLI Capabilities
* **Pipeline Entrypoint**: [`main.py`](file:///e:/Desktop/Applivo/main.py)
  - Options: `--live` (live Playwright fill), `--loop --interval N` (recurring 6h loop), `--dashboard --port N` (launch web server).
* **Configuration**: [`config/profile.json`](file:///e:/Desktop/Applivo/config/profile.json)
* **Documentation**: [`docs/`](file:///e:/Desktop/Applivo/docs/) (`PRD.md`, `Architecture.md`, `Rules.md`, `Phases.md`, `Design.md`, `Memory.md`)
* **Source Modules**: [`src/`](file:///e:/Desktop/Applivo/src/)
  - `db.py`: SQLite schema management & connection handling
  - `collector.py`: Greenhouse & Lever API job collection
  - `matcher.py`: Gemini AI job scoring & cover letter generator
  - `applier.py`: Playwright form automation & screenshot engine (integrated with Telegram notification on PENDING)
  - `notifier.py`: Telegram Bot API alert dispatcher
  - `dashboard.py`: Single-file FastAPI web dashboard with interactive `/api/resolve/{app_id}` endpoint.

## Verification Metrics
* `python main.py` -> End-to-end pipeline execution verified clean.
* `python src/applier.py` -> Verified PENDING state triggers Telegram notification safely with token suppression and error recovery.

## Key Design Principles
- Standard-library first, no microservice bloat (Ponytail senior dev approach).
- SQLite stored locally at `app.db`.

## AI WORKFLOW RULE

When starting a new coding session:

1. Read ONLY Memory.md first.
2. Do NOT read all documentation files.
3. Identify the current task from "Currently Working On" and "Next Steps".
4. Inspect only the source files necessary for that task.
5. Complete ONE task only.
6. Test the change.
7. Update Memory.md.
8. Stop and wait for the next instruction.

Never start multiple tasks in one session unless explicitly instructed.