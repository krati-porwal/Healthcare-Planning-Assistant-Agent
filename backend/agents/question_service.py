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
        Generate medical questions based on the user's healthcare goal.

        IMPORTANT: Field names are ALWAYS pinned to DEFAULT_QUESTIONS keys so
        they match exactly what ValidationEngine requires.  Gemini is only used
        to personalise the question *text*, never the *field* keys.

        Args:
            goal: The user's stated healthcare goal (e.g., "I want treatment for breast cancer")

        Returns:
            List of dicts with keys: field, question, required
        """
        try:
            # Build a field→question mapping from Gemini-personalised text
            prompt = f"""
You are a healthcare data collection assistant helping a patient with this goal:

"{goal}"

Rephrase each of the following question fields into a clear, context-aware question for the patient.
Return ONLY a valid JSON object mapping field name → question text, like:
{{
  "disease_type": "...",
  "stage": "...",
  "age": "...",
  "gender": "...",
  "medical_history": "...",
  "symptoms": "...",
  "surgery_allowed": "...",
  "budget_limit": "...",
  "location_type": "...",
  "hospital_preference": "..."
}}

Fields to rephrase: disease_type, stage, age, gender, medical_history, symptoms,
surgery_allowed, budget_limit, location_type, hospital_preference.
Do not add or remove fields. Return only the JSON object, no extra text.
"""
            response = _model.generate_content(prompt)
            raw = response.text.strip()
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                text_map = json.loads(json_match.group())
                if isinstance(text_map, dict):
                    # Apply personalised text but keep field names from DEFAULT_QUESTIONS
                    personalised = []
                    for q in DEFAULT_QUESTIONS:
                        field = q["field"]
                        personalised.append({
                            "field": field,
                            "question": text_map.get(field, q["question"]),
                            "required": q["required"],
                        })
                    print(f"[QuestionService] Personalised {len(personalised)} questions via Gemini.")
                    return personalised

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
