# Development Rules & Boundaries

## 1. Architectural & Library Rules
- **Standard Library First**: Use `sqlite3`, `json`, `pathlib`, and native features before adding external dependencies.
- **No Microservices**: Keep all components in a single Python runtime. Do not introduce Spring Boot, PostgreSQL servers, or Redis.
- **Single DB Source of Truth**: All job and application state transitions must be committed atomically to `app.db`.

## 2. Automation & Safety Boundaries
- **CAPTCHA Non-Bypass Rule**: Never attempt to solve or bypass CAPTCHAs programmatically. Mark job as `PENDING` and notify user immediately.
- **Pre-Submission Screenshot**: Always capture and save a full-page screenshot before clicking application submit buttons.
- **Strict Rate Limits**: Enforce a maximum of 20 automated submissions per 24 hours per user.
- **Truthful Answers**: Never hallucinate experience or profile data in AI-generated cover letters or custom questions.

## 3. Code Style & Testing
- **Ponytail Discipline**: Prefer standard library, write short working diffs, and eliminate unrequested abstractions (interfaces for single implementations, unnecessary wrappers).
- **Self-Checking Execution**: Every core script must include a runnable `if __name__ == "__main__":` block with lightweight `assert` statements.
