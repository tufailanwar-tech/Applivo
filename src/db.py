import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "app.db"
PROFILE_PATH = BASE_DIR / "config" / "profile.json"

def init_db(db_path: Path = DB_PATH) -> None:
    """Initialize SQLite database schema for jobs, applications, and profile state."""
    with sqlite3.connect(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                company TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                description TEXT,
                location TEXT,
                posted_at TIMESTAMP,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS applications (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL REFERENCES jobs(id),
                status TEXT NOT NULL, -- FOUND, SCORED, QUEUED, APPLYING, APPLIED, PENDING, FAILED, PERMANENT_FAIL
                score INTEGER DEFAULT 0,
                pending_reason TEXT,
                cover_letter TEXT,
                screenshot_path TEXT,
                retry_count INTEGER DEFAULT 0,
                last_error TEXT,
                applied_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                data TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # Safe column migrations if db was created prior
        cols = [c[1] for c in conn.execute("PRAGMA table_info(applications)").fetchall()]
        if "retry_count" not in cols:
            conn.execute("ALTER TABLE applications ADD COLUMN retry_count INTEGER DEFAULT 0")
        if "last_error" not in cols:
            conn.execute("ALTER TABLE applications ADD COLUMN last_error TEXT")

def load_profile_json(profile_path: Path = PROFILE_PATH) -> dict:
    """Load profile configuration from JSON file."""
    if not profile_path.exists():
        fallback = BASE_DIR / "profile.json"
        if fallback.exists():
            profile_path = fallback
        else:
            raise FileNotFoundError(f"Profile file not found at {profile_path}")
    with open(profile_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_profile_to_db(profile_data: dict, db_path: Path = DB_PATH) -> None:
    """Save or update profile JSON in SQLite database."""
    profile_json = json.dumps(profile_data, ensure_ascii=False)
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            INSERT INTO profile (id, data, updated_at) 
            VALUES (1, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET data=excluded.data, updated_at=CURRENT_TIMESTAMP
        """, (profile_json,))

def get_profile_from_db(db_path: Path = DB_PATH) -> dict:
    """Fetch active profile dict from SQLite database."""
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT data FROM profile WHERE id = 1").fetchone()
        return json.loads(row[0]) if row else {}

if __name__ == "__main__":
    init_db()
    p_data = load_profile_json()
    save_profile_to_db(p_data)
    loaded = get_profile_from_db()
    assert loaded["email"] == "jane.doe@example.com", "Profile email mismatch!"
    print("Phase 1 verification passed: DB initialized & profile loaded successfully.")
