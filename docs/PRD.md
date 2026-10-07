# Project Requirements Document (PRD)
# Auto Job/Internship Applier — Updated

---

## 1. Overview

**Auto-Job Applier** is a fully automated, single-stack job application tool that:
- Fetches software engineering job postings from public APIs (Greenhouse, Lever, Ashby, Remotive)
- Matches and scores jobs against a candidate's profile using Google Gemini LLM
- Automatically fills and submits application forms using Playwright
- Answers custom application questions using Gemini AI (from profile data only)
- Alerts the user via Telegram when human intervention is required (CAPTCHA, unknown fields)
- Tracks all applications in a dashboard with screenshots and Q&A review
- Retries failed applications automatically before escalating to user

---

## 2. Target Users

- Software engineers, interns, and tech job seekers applying to high volumes of Greenhouse / Lever / Ashby / Remotive postings
- Users wanting to avoid repetitive manual form entry while retaining full control over CAPTCHAs and sensitive data
- Users who want AI-powered custom question answering without hallucination (profile-only answers)

---

## 3. Core Features

### 3.1 Job Collection
- Periodically query public JSON endpoints for:
  - **Greenhouse** — `boards-api.greenhouse.io/v1/boards/{company}/jobs`
  - **Lever** — `api.lever.co/v0/postings/{company}?mode=json`
  - **Ashby** — `api.ashbyhq.com/posting-api/job-board/{company}` *(new)*
  - **Remotive** — `remotive.com/api/remote-jobs?category={field}` *(new)*
- Target companies loaded dynamically from `profile.json` (not hardcoded)
- Deduplicate jobs by URL before adding to queue
- Filter jobs by user's preferred field and location

### 3.2 AI Job Matching & Scoring
- Score each job description against user's resume (0–10) using Gemini 1.5 Flash
- Only queue jobs scoring >= user-defined threshold (default: 6/10)
- Low-score jobs logged but skipped

### 3.3 Automated Form Filling
- Playwright engine fills standard fields:
  - First name, last name, email, phone
  - LinkedIn, GitHub, portfolio links
  - Resume PDF upload
  - Better Playwright waits for dynamic pages *(done)*
  - Deterministic screenshot filenames before every submit *(done)*
- Separate form handlers per platform:
  - `greenhouse_handler.py`
  - `lever_handler.py` *(selectors done)*
  - `ashby_handler.py` *(new)*

### 3.4 Gemini Custom Question Answering *(new)*
- Detect custom text fields not in standard field mapping
- Send question + user profile to Gemini with strict prompt:
  *"Answer only using the provided profile data. If information is not available, return UNKNOWN."*
- Temperature: 0.3, max tokens: 200
- If Gemini returns `UNKNOWN` → mark application `PENDING` with reason `UNKNOWN_FIELD`
- Log question + answer for dashboard review

### 3.5 Human Checkpoint (PENDING State)
- Automatically detect and pause on:
  - **CAPTCHA** — reCAPTCHA / hCaptcha iframe detected
  - **Unknown field** — required field not in profile, Gemini returns UNKNOWN
  - **Form error** — unexpected page structure or missing submit button
- On PENDING: save screenshot, send Telegram alert with reason
- Dashboard shows exact reason per pending item with "Open Job URL" and "Skip" buttons

### 3.6 Application Failure & Retry Handling *(new)*
- Track failed applications separately with `retry_count` field
- Auto-retry FAILED applications once after 1 hour
- Maximum 2 retry attempts per application
- After 2 failures → mark `PERMANENT_FAIL`, send Telegram notification
- All failure reasons logged to `logs/failures.log`
- Dashboard shows retry count and last error message per application

### 3.7 Dashboard (Web UI)
- Single-file dashboard showing all application statuses
- **Status summary** at top: Applied 🟢 / Pending 🟡 / Failed 🔴 / Total counts
- **Filter tabs**: All / Applied / Pending / Failed
- **Screenshots tab**: view screenshot per application *(new)*
- **Custom Q&A review**: see question asked + Gemini answer given *(new)*
- **Pending cards**: exact reason + "Open Job URL" + "Skip" + "Retry" buttons *(new)*
- **Authentication**: login required to access dashboard *(new)*

### 3.8 Notifications (Telegram)
- Immediate alert when application goes PENDING (with reason)
- Daily summary at 8 PM: Applied / Pending / Failed counts *(done)*
- Alert on PERMANENT_FAIL after 2 retries *(new)*

### 3.9 Rate Limiting & Safety
- Daily application cap: default 20 applications/24h *(done)*
- Per-user configurable limit
- App stops queuing once daily limit reached
- 3–5 second delay between form field fills
- Never bypass or solve CAPTCHAs programmatically

---

## 4. Security Requirements *(new)*

- All secrets (API keys, Telegram token, email credentials) stored in `.env` only — never in `profile.json`
- `.env` added to `.gitignore`; `.env.example` committed with empty values
- Resume PDF encrypted at rest (AES or S3 server-side encryption)
- Dashboard and all API routes protected with JWT authentication
- Profile data and resume content never logged to console or log files
- Passwords hashed with BCrypt

---

## 5. Non-Functional Requirements

| Requirement | Detail |
|---|---|
| **Reliability** | Failed jobs auto-retried once after 1 hour |
| **Safety** | Max 20–30 applications per day, screenshots before every submit |
| **Privacy** | Profile data used only for applying, never shared or logged |
| **Legal** | Only Greenhouse / Lever / Ashby / Remotive public APIs — no LinkedIn/Indeed scraping |
| **LLM Honesty** | Gemini answers only from profile; returns UNKNOWN rather than hallucinating |
| **Scalability** | Designed for single user now, multi-user later |

---

## 6. Testing Requirements *(new)*

- Unit tests for `llm_service.py` (mock Gemini, test score + answer functions)
- Unit tests for each collector (mock API response, verify job parsing)
- Integration test: full collect → score → apply dry-run flow
- CAPTCHA detection test: verify PENDING returned on reCAPTCHA page
- UNKNOWN_FIELD test: field not in profile → verify PENDING returned
- Daily limit test: verify app stops after 20 applications
- Retry logic test: force failure → verify retry fires after 1 hour
- All tests in `/tests` folder using `pytest`

---

## 7. Deployment Plan *(new)*

| Service | Platform | Cost |
|---|---|---|
| Python FastAPI + Playwright | Railway | Free tier |
| React Dashboard | Vercel | Free |
| PostgreSQL | Supabase | Free tier |
| Domain (optional) | Any registrar | ~$10/year |

- Dockerized with `Dockerfile` per service and `docker-compose.yml`
- All secrets managed via platform environment variables
- First live test: daily limit set to 5 for monitoring

---

## 8. Out of Scope (v1)

- Mobile app
- Browser extension
- LinkedIn / Indeed / Naukri automation (ToS violation)
- Interview scheduling
- Application response / email tracking
- Payment / subscription system
- Multi-user support

---

## 9. Current Status

| Phase | Tasks | Status |
|---|---|---|
| Core automation | 1–12 | ✅ Done |
| Gemini Q&A + new collectors | 13–15 | ⏳ Remaining |
| Dashboard improvements | 16–17 | ⏳ Remaining |
| Security + auth | 18–19 | ⏳ Remaining |
| Tests | 20 | ⏳ Remaining |
| Deployment | 21 | ⏳ Remaining |

**Overall: 12/21 tasks complete (~57%)**

---

## 10. Success Metrics

- User applies to 20+ jobs per day with zero manual effort
- Less than 5% failure rate on Greenhouse / Lever / Ashby forms
- Pending rate under 15% of total applications
- Custom questions answered correctly from profile > 80% of the time
- User spends less than 5 minutes/day resolving pending items