import os
import sys
import json
from pathlib import Path

# Add src/ to path
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
from matcher import score_job_with_llm, process_unscored_jobs

def answer_custom_question(question: str, profile: dict) -> str:
    """
    Answer custom application questions using Gemini AI strictly from candidate profile.
    Returns the answer string, or 'UNKNOWN' if profile data is insufficient.
    Strictly follows Rules: Temperature 0.3, max tokens 200, no hallucination.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                "gemini-1.5-flash",
                generation_config={"temperature": 0.3, "max_output_tokens": 200}
            )
            prompt = f"""
Answer the following job application question strictly and ONLY using the provided candidate profile data.
If the required information is not available in the profile, return exactly UNKNOWN without any extra text or elaboration.

CANDIDATE PROFILE:
{json.dumps(profile, indent=2, ensure_ascii=False)}

QUESTION:
{question}
"""
            res = model.generate_content(prompt)
            answer = res.text.strip()
            if not answer or "UNKNOWN" in answer.upper():
                return "UNKNOWN"
            return answer
        except Exception as e:
            print(f"Gemini API question answering warning: {e}")

    # Fallback heuristic checking profile directly without API key
    q_lower = question.lower()
    if "first name" in q_lower:
        return profile.get("first_name", "UNKNOWN") or "UNKNOWN"
    if "last name" in q_lower:
        return profile.get("last_name", "UNKNOWN") or "UNKNOWN"
    if "email" in q_lower:
        return profile.get("email", "UNKNOWN") or "UNKNOWN"
    if "phone" in q_lower:
        return profile.get("phone", "UNKNOWN") or "UNKNOWN"
    if "linkedin" in q_lower:
        return profile.get("linkedin_url", "UNKNOWN") or "UNKNOWN"
    if "github" in q_lower:
        return profile.get("github_url", "UNKNOWN") or "UNKNOWN"
    if "portfolio" in q_lower or "website" in q_lower:
        return profile.get("portfolio_url", "UNKNOWN") or "UNKNOWN"
    if "location" in q_lower or "city" in q_lower:
        locs = profile.get("location_preferences", [])
        return ", ".join(locs) if locs else "UNKNOWN"

    return "UNKNOWN"

if __name__ == "__main__":
    test_profile = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.com",
        "github_url": "https://github.com/janedoe"
    }
    ans1 = answer_custom_question("What is your GitHub profile link?", test_profile)
    ans2 = answer_custom_question("How many years have you lived in Tokyo?", test_profile)
    assert ans1 == "https://github.com/janedoe", f"Expected github url, got {ans1}"
    assert ans2 == "UNKNOWN", f"Expected UNKNOWN, got {ans2}"
    print("llm_service verification passed: answer_custom_question working properly.")
