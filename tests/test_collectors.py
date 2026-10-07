import unittest
from unittest.mock import patch, MagicMock
from handlers.ashby_handler import fetch_ashby_jobs
from handlers.remotive_handler import fetch_remotive_jobs
from src.collector import fetch_greenhouse_jobs, fetch_lever_jobs, collect_and_save_jobs

class TestCollectors(unittest.TestCase):

    @patch("urllib.request.urlopen")
    def test_fetch_greenhouse_jobs(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"jobs": [{"id": 101, "title": "Dev", "absolute_url": "https://gh/101", "content": "Desc", "location": {"name": "Remote"}}]}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        jobs = fetch_greenhouse_jobs("testco")
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["id"], "gh_101")
        self.assertEqual(jobs[0]["title"], "Dev")

    @patch("urllib.request.urlopen")
    def test_fetch_lever_jobs(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'[{"id": "lev_202", "text": "Backend Eng", "hostedUrl": "https://lever/202", "descriptionPlain": "Desc", "categories": {"location": "Remote"}}]'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        jobs = fetch_lever_jobs("testco")
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["id"], "lever_lev_202")

    @patch("urllib.request.urlopen")
    def test_fetch_ashby_jobs(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"jobs": [{"id": "ash_303", "title": "Full Stack", "jobUrl": "https://ashby/303", "descriptionPlain": "Desc", "location": "Remote"}]}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        jobs = fetch_ashby_jobs("testco")
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["id"], "ashby_ash_303")

    @patch("urllib.request.urlopen")
    def test_fetch_remotive_jobs(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"jobs": [{"id": 404, "title": "Python Dev", "company_name": "Acme", "url": "https://remotive/404", "description": "Desc", "candidate_required_location": "Remote"}]}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        jobs = fetch_remotive_jobs()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["id"], "remotive_404")

if __name__ == "__main__":
    unittest.main()
