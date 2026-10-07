import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.db import init_db, save_profile_to_db
from src.applier import apply_to_job, process_queued_applications
from src.matcher import process_unscored_jobs

class TestPipeline(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = Path(self.temp_dir.name) / "test_app.db"
        init_db(self.db_path)
        self.profile = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
            "phone": "+1234567890",
            "daily_apply_limit": 2,
            "field_preferences": ["Engineer"]
        }
        save_profile_to_db(self.profile, self.db_path)

    def tearDown(self):
        import gc
        gc.collect()
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_daily_apply_limit_enforced(self):
        # Insert 3 jobs
        with sqlite3.connect(self.db_path) as conn:
            for i in range(3):
                conn.execute("INSERT INTO jobs (id, source, company, title, url) VALUES (?, ?, ?, ?, ?)",
                             (f"job_{i}", "lever", "testco", f"Title {i}", f"https://job/{i}"))
                conn.execute("INSERT INTO applications (id, job_id, status, score) VALUES (?, ?, 'QUEUED', 8)",
                             (f"app_{i}", f"job_{i}"))

        # Daily limit is 2
        processed = process_queued_applications(self.db_path, dry_run=True)
        self.assertEqual(processed, 2)

        # Remaining processed on next run should be 0 because daily limit reached
        processed_next = process_queued_applications(self.db_path, dry_run=True)
        self.assertEqual(processed_next, 0)

    def test_failed_application_retries_and_permanent_fail(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO jobs (id, source, company, title, url) VALUES (?, ?, ?, ?, ?)",
                         ("job_err", "lever", "testco", "Title Err", "https://job/err"))
            conn.execute("INSERT INTO applications (id, job_id, status, retry_count) VALUES (?, ?, 'FAILED', 1)",
                         ("app_err", "job_err"))

        with patch("src.applier.apply_to_job", return_value=("FAILED", "Simulated Error", "screenshot.png")):
            process_queued_applications(self.db_path, dry_run=False)

        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT status, retry_count FROM applications WHERE id = 'app_err'").fetchone()
            self.assertEqual(row[0], "PERMANENT_FAIL")
            self.assertEqual(row[1], 2)

if __name__ == "__main__":
    unittest.main()
