import unittest
from unittest.mock import patch, MagicMock
from services.llm_service import answer_custom_question, score_job_with_llm

class TestLLMService(unittest.TestCase):

    def setUp(self):
        self.profile = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
            "phone": "+1234567890",
            "linkedin_url": "https://linkedin.com/in/janedoe",
            "github_url": "https://github.com/janedoe",
            "location_preferences": ["Remote", "New York"],
            "field_preferences": ["Software Engineer", "Backend Developer"],
            "resume_text": "Experienced Software Engineer with Python and Playwright."
        }

    def test_answer_custom_question_known_profile_field(self):
        ans = answer_custom_question("What is your LinkedIn profile URL?", self.profile)
        self.assertEqual(ans, "https://linkedin.com/in/janedoe")

    def test_answer_custom_question_unknown_field_returns_unknown(self):
        ans = answer_custom_question("What is your driver's license number?", self.profile)
        self.assertEqual(ans, "UNKNOWN")

    def test_score_job_with_llm_heuristic_fallback(self):
        score, cover_letter = score_job_with_llm("Senior Software Engineer", "Build backend Python microservices", self.profile)
        self.assertGreaterEqual(score, 6)
        self.assertIn("Jane Doe", cover_letter)

if __name__ == "__main__":
    unittest.main()
