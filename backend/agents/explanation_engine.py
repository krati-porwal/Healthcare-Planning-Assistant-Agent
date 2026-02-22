"""
ExplanationEngine Agent

Responsibilities:
- Generate a human-readable explanation of the treatment plan
- Add a medical disclaimer
- Prepare the final structured JSON output
"""
import google.generativeai as genai
from backend.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
_model = genai.GenerativeModel("gemini-1.5-flash")

DISCLAIMER = (
    "This is not a medical diagnosis. "
    "Consult a licensed medical professional before making any healthcare decisions."
)


class ExplanationEngine:
    """
    Generates the final structured JSON output with explanations and disclaimer.
    """

    def generate(self, profile: dict, plan_data: dict, ranked_hospitals: list[dict],
                 llm_reasoning: str) -> dict:
        """
        Combine all agent outputs into a final structured JSON response.

        Args:
            profile: MedicalProfile dict
            plan_data: Treatment plan dict from RecommendationEngine
            ranked_hospitals: Ranked hospital list
            llm_reasoning: Clinical reasoning from DecisionEngine

        Returns:
            Final structured output dict matching the required JSON schema
        """
        explanation = self._generate_explanation(profile, plan_data, llm_reasoning)

        # Format hospitals to required schema
        formatted_hospitals = []
        for h in ranked_hospitals[:5]:
            formatted_hospitals.append({
                "name": h.get("name", ""),
                "location": f"{h.get('city', h.get('location', ''))}, {h.get('state', '')}".strip(", "),
                "type": h.get("type", ""),
                "contact": h.get("contact", ""),
                "accreditation": h.get("accreditation", ""),
                "rating": str(h.get("rating", "")),
                "budget_category": h.get("budget_category", ""),
                "priority_rank": str(h.get("priority_rank", "")),
            })

        output = {
            "treatment_plan": {
                "disease_type": plan_data.get("disease_type", ""),
                "treatment_type": plan_data.get("treatment_type", ""),
                "timeline": plan_data.get("timeline", ""),
                "specialist": plan_data.get("specialist", ""),
                "required_reports": plan_data.get("required_reports", []),
                "notes": plan_data.get("notes", ""),
            },
            "recommended_hospitals": formatted_hospitals,
            "explanation": explanation,
            "disclaimer": DISCLAIMER,
        }

        print("[ExplanationEngine] Final output prepared.")
        return output

    def _generate_explanation(self, profile: dict, plan_data: dict, llm_reasoning: str) -> str:
        """Generate a clear, patient-friendly explanation using Gemini."""
        try:
            prompt = f"""
You are a compassionate healthcare advisor explaining a treatment recommendation to a patient.

Patient Details:
- Disease: {profile.get('disease_type', 'Unknown')}
- Stage: {profile.get('stage', 'Unknown')}
- Age: {profile.get('age', 'Unknown')}
- Gender: {profile.get('gender', 'Unknown')}
- Surgery Allowed: {profile.get('surgery_allowed', True)}

Recommended Treatment: {plan_data.get('treatment_type', '')}
Timeline: {plan_data.get('timeline', '')}
Clinical Reasoning: {llm_reasoning}

Write a clear, empathetic 3-5 sentence explanation for the patient about:
1. What treatment is recommended and why
2. What they can expect in terms of timeline
3. The importance of visiting a specialist

Use simple language. Do not include any markdown or headers. Write as a single paragraph.
"""
            response = _model.generate_content(prompt)
            explanation = response.text.strip()
            print("[ExplanationEngine] Gemini explanation generated.")
            return explanation

        except Exception as e:
            print(f"[ExplanationEngine] Gemini failed, using default explanation: {e}")
            return (
                f"Based on your {profile.get('stage', '')} {profile.get('disease_type', 'condition')}, "
                f"the recommended treatment approach is {plan_data.get('treatment_type', 'medical management')}. "
                f"The expected treatment timeline is {plan_data.get('timeline', 'to be determined by your specialist')}. "
                f"{llm_reasoning} "
                f"Please consult with a {plan_data.get('specialist', 'licensed medical professional')} "
                f"for personalized guidance and to discuss your treatment options in detail."
            )
