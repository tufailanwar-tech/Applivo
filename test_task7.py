import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add src/ to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from applier import detect_custom_question, apply_to_job

class TestCustomQuestions(unittest.TestCase):

    def test_detect_custom_question_standard_fields_only(self):
        """Page with only standard fields should return None."""
        page = MagicMock()
        first_name_el = MagicMock()
        first_name_el.is_visible.return_value = True
        first_name_el.get_attribute.side_effect = lambda attr: "first_name" if attr in ("id", "name") else None

        email_el = MagicMock()
        email_el.is_visible.return_value = True
        email_el.get_attribute.side_effect = lambda attr: "email" if attr in ("id", "name") else None

        page.query_selector_all.return_value = [first_name_el, email_el]
        
        result = detect_custom_question(page)
        self.assertIsNone(result)

    def test_detect_custom_question_with_custom_textarea(self):
        """Page with custom textarea should detect question and return label."""
        page = MagicMock()
        first_name_el = MagicMock()
        first_name_el.is_visible.return_value = True
        first_name_el.get_attribute.side_effect = lambda attr: "first_name" if attr in ("id", "name") else None

        custom_el = MagicMock()
        custom_el.is_visible.return_value = True
        custom_el.get_attribute.side_effect = lambda attr: "custom_q_1" if attr in ("id", "name") else None
        custom_el.evaluate.return_value = "Why do you want to work here?"

        page.query_selector_all.return_value = [first_name_el, custom_el]
        
        result = detect_custom_question(page)
        self.assertEqual(result, "Why do you want to work here?")

    def test_detect_custom_question_with_custom_select(self):
        """Page with custom select dropdown should detect question."""
        page = MagicMock()
        custom_select = MagicMock()
        custom_select.is_visible.return_value = True
        custom_select.get_attribute.side_effect = lambda attr: "sponsorship_status" if attr in ("id", "name") else None
        custom_select.evaluate.return_value = "Will you now or in the future require visa sponsorship?"

        page.query_selector_all.return_value = [custom_select]
        
        result = detect_custom_question(page)
        self.assertEqual(result, "Will you now or in the future require visa sponsorship?")

    def test_apply_to_job_transitions_to_pending_on_custom_question(self):
        """apply_to_job should transition to PENDING status and not submit when custom question found."""
        mock_playwright_mod = MagicMock()
        mock_p_instance = MagicMock()
        mock_playwright_mod.sync_playwright.return_value.__enter__.return_value = mock_p_instance
        mock_browser = MagicMock()
        mock_p_instance.chromium.launch.return_value = mock_browser
        mock_page = MagicMock()
        mock_browser.new_page.return_value = mock_page

        # No CAPTCHA
        mock_page.query_selector.side_effect = lambda sel: None

        # Return a custom question input
        custom_el = MagicMock()
        custom_el.is_visible.return_value = True
        custom_el.get_attribute.side_effect = lambda attr: "custom_notes" if attr in ("id", "name") else None
        custom_el.evaluate.return_value = "Describe your experience with distributed systems."

        mock_page.query_selector_all.return_value = [custom_el]

        profile = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com"
        }

        with patch.dict("sys.modules", {"playwright.sync_api": mock_playwright_mod}):
            status, reason, ss_path = apply_to_job("https://boards.greenhouse.io/job/123", profile, dry_run=False)

        self.assertEqual(status, "PENDING")
        self.assertIn("CUSTOM_QUESTION", reason)
        self.assertIn("Describe your experience with distributed systems", reason)
        mock_page.screenshot.assert_called()

if __name__ == "__main__":
    unittest.main()
