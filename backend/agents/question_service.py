"""
QuestionService Agent

Responsibilities:
- Generate relevant medical questions based on disease type / user goal
- Return a structured list of questions for the user to answer
- Ensure necessary data fields are captured
"""
import json
import re
import google.generativeai as genai
from backend.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
_model = genai.GenerativeModel("gemini-1.5-flash")


# Default questions for fallback when LLM is unavailable
DEFAULT_QUESTIONS = [
    {"field": "disease_type", "question": "What type of disease or medical condition are you dealing with?", "required": True},
    {"field": "stage", "question": "What is the current stage or severity of the condition (if known)?", "required": True},
    {"field": "age", "question": "What is the patient's age?", "required": True},
    {"field": "gender", "question": "What is the patient's gender?", "required": True},
    {"field": "medical_history", "question": "Please describe any relevant medical history (previous illnesses, surgeries, medications)?", "required": True},
    {"field": "symptoms", "question": "What symptoms is the patient currently experiencing?", "required": True},
    {"field": "surgery_allowed", "question": "Is the patient open to surgical procedures? (yes/no)", "required": True},
    {"field": "budget_limit", "question": "What is the approximate budget for treatment (in INR)? E.g., 200000 for 2 lakhs", "required": True},
    {"field": "location_type", "question": "Do you prefer a local, national, or international hospital?", "required": True},
    {"field": "hospital_preference", "question": "Do you prefer a government or private hospital?", "required": False},
]


class QuestionService:
    """
    Generates medical questions using Gemini LLM based on the user goal.
    Falls back to default questions if the LLM is unavailable.
    """

    def generate_questions(self, goal: str) -> list[dict]:
        """
        Generate a list of medical questions based on the user's healthcare goal.

        Args:
            goal: The user's stated healthcare goal (e.g., "I want treatment for breast cancer")

        Returns:
            List of dicts with keys: field, question, required
        """
        try:
            prompt = f"""
You are a healthcare data collection assistant. Based on the following patient goal:

"{goal}"

Generate a concise list of 8-10 medical questions that need to be answered to build a complete medical profile and provide treatment recommendations.

Return ONLY a valid JSON array with this exact format:
[
  {{
    "field": "field_name_snake_case",
    "question": "The question text for the patient?",
    "required": true
  }}
]

Include questions about: disease type, stage/severity, age, gender, medical history, symptoms, surgery preference, budget, and location preference.
Do not include any explanatory text, only the JSON array.
"""
            response = _model.generate_content(prompt)
            raw = response.text.strip()

            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', raw, re.DOTALL)
            if json_match:
                questions = json.loads(json_match.group())
                if isinstance(questions, list) and len(questions) > 0:
                    print(f"[QuestionService] Generated {len(questions)} questions via Gemini.")
                    return questions

        except Exception as e:
            print(f"[QuestionService] Gemini error, using defaults: {e}")

        print(f"[QuestionService] Using {len(DEFAULT_QUESTIONS)} default questions.")
        return DEFAULT_QUESTIONS

    def collect_responses(self, questions: list[dict], answers: dict) -> dict:
        """
        Match user-provided answers to the question fields.

        Args:
            questions: The list of question dicts (with 'field' key)
            answers: Dict mapping field names to user-provided answers

        Returns:
            Dict of field -> answer mappings
        """
        collected = {}
        for q in questions:
            field = q.get("field", "")
            if field and field in answers:
                collected[field] = answers[field]
        print(f"[QuestionService] Collected {len(collected)} responses.")
        return collected
