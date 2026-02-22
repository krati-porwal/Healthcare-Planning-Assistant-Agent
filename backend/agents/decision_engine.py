"""
DecisionEngine Agent

Responsibilities:
- Analyze medical profile using disease guidelines (JSON + ChromaDB)
- Apply decision rules to select treatment type
- Filter hospital type based on disease
- Use Gemini LLM for nuanced reasoning
- Return structured decision dict
"""
import json
import os
import re
import google.generativeai as genai
from backend.config import GEMINI_API_KEY
from backend.chroma.chroma_setup import query_disease_guidelines, query_hospital_summaries

genai.configure(api_key=GEMINI_API_KEY)
_model = genai.GenerativeModel("gemini-1.5-flash")

# Load disease guidelines from JSON for deterministic rule-based filtering
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_DIR = os.path.join(BASE_DIR, "..", "knowledge")
DISEASE_FILE = os.path.join(KNOWLEDGE_DIR, "disease_guidelines.json")
HOSPITAL_FILE = os.path.join(KNOWLEDGE_DIR, "hospital_data.json")


def _load_json(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


class DecisionEngine:
    """
    Applies decision logic to select treatment type and hospital type,
    augmented by Gemini LLM reasoning.
    """

    def __init__(self):
        self._disease_data = _load_json(DISEASE_FILE)
        self._hospital_data = _load_json(HOSPITAL_FILE)

    def _find_disease_guideline(self, disease_type: str, stage: str) -> dict | None:
        """Find the best matching disease guideline from JSON."""
        disease_type_lower = disease_type.lower()
        for disease in self._disease_data["diseases"]:
            if disease["disease_type"].lower() in disease_type_lower or \
               disease_type_lower in disease["disease_type"].lower():
                # Find matching stage
                for s in disease["stages"]:
                    if s["stage"].lower() in stage.lower() or stage.lower() in s["stage"].lower():
                        return {
                            "disease_type": disease["disease_type"],
                            "hospital_type": disease["hospital_type"],
                            "specialist": disease["specialist"],
                            "stage_info": s,
                        }
                # Return first stage if no exact match
                if disease["stages"]:
                    return {
                        "disease_type": disease["disease_type"],
                        "hospital_type": disease["hospital_type"],
                        "specialist": disease["specialist"],
                        "stage_info": disease["stages"][0],
                    }
        return None

    def _filter_hospitals(self, hospital_type: str, constraint: dict,
                          patient_city: str = "",
                          patient_area_type: str = "urban") -> list[dict]:
        """
        Filter and rank hospitals by type, budget, location match, and area type.
        Rural/remote patients get government hospital preference.
        Patient city matching gives a strong score boost so nearby hospitals
        appear first — fixing the previously broken location filtering.
        """
        budget_limit = constraint.get("budget_limit")
        hospital_pref = constraint.get("hospital_preference", "any")
        area = (patient_area_type or "urban").lower()

        # Rural / remote patients should prefer affordable government hospitals
        if area in ("rural", "remote") and hospital_pref == "any":
            hospital_pref = "government"

        # Determine budget category filter
        try:
            budget = float(budget_limit) if budget_limit else 0
        except (ValueError, TypeError):
            budget = 0

        if hospital_pref == "government":
            allowed_budgets = {"Government"}
        elif hospital_pref == "private":
            allowed_budgets = {"Standard", "Premium"}
        elif budget < 100000:
            allowed_budgets = {"Government", "Standard"}
        elif budget < 500000:
            allowed_budgets = {"Government", "Standard", "Premium"}
        else:
            allowed_budgets = {"Government", "Standard", "Premium"}

        city_lower = (patient_city or "").lower().strip()
        location_type = constraint.get("location_type", "national")

        scored = []
        for h in self._hospital_data["hospitals"]:
            # Type match (exact or multi-specialty)
            if h["type"] != hospital_type and h["type"] != "Multi-specialty":
                continue
            # Budget match
            if h["budget_category"] not in allowed_budgets:
                continue

            # ── Location score boost (FIX: was a no-op 'pass') ──────────────
            location_score = 0.0
            if city_lower:
                h_city = h.get("city", "").lower()
                h_state = h.get("state", "").lower()
                if city_lower in h_city or h_city in city_lower:
                    # Strong boost for same-city hospital
                    location_score = 4.0 if location_type == "local" else 2.0
                elif city_lower in h_state or h_state in city_lower:
                    # Mild boost for same-state
                    location_score = 1.0

            scored.append((h, location_score))

        # Sort by (location_score + rating) descending
        scored.sort(key=lambda x: x[1] + float(x[0].get("rating", 0)), reverse=True)
        return [h for h, _ in scored[:5]]  # Return top 5

    def analyze(self, profile: dict, constraint: dict) -> dict:
        """
        Analyze medical profile and return a structured decision.

        Args:
            profile: Dict with disease_type, stage, surgery_allowed, patient_city,
                     patient_area_type, existing_lab_reports, etc.
            constraint: Dict with budget_limit, location_type, hospital_preference

        Returns:
            Structured decision dict including treatment_type, hospital recommendations,
            required reports, lab report verification, and LLM reasoning.
        """
        disease_type = profile.get("disease_type", "Unknown")
        stage = profile.get("stage", "")
        surgery_allowed = profile.get("surgery_allowed", True)
        age = profile.get("age", "unknown")
        medical_history = profile.get("medical_history", "")
        symptoms = profile.get("symptoms", "")
        patient_city = profile.get("patient_city", "")  # from Step 1 location
        patient_area_type = profile.get("patient_area_type", "urban")  # urban/rural/remote
        existing_lab_reports = profile.get("existing_lab_reports", "none")

        print(f"[DecisionEngine] Analyzing: disease={disease_type}, stage={stage}, city={patient_city}, area={patient_area_type}")

        # ── Step 1: Retrieve from JSON knowledge ─────────────────────────────
        guideline = self._find_disease_guideline(disease_type, stage)
        if guideline:
            stage_info = guideline["stage_info"]
            hospital_type = guideline["hospital_type"]
            specialist = guideline["specialist"]
            treatments = stage_info["recommended_treatments"]
            # Filter out surgical treatments if surgery not allowed
            if not surgery_allowed:
                treatments = [t for t in treatments if "surgery" not in t.lower()
                              and "surgical" not in t.lower()
                              and "lumpectomy" not in t.lower()
                              and "mastectomy" not in t.lower()
                              and "cabg" not in t.lower()]
            treatment_type = ", ".join(treatments[:3]) if treatments else "Medical Management"
            timeline = stage_info.get("timeline", "To be determined")
            required_reports = stage_info.get("required_reports", [])
            notes = stage_info.get("notes", "")
            guideline_source = "JSON + ChromaDB"
        else:
            hospital_type = "Multi-specialty"
            specialist = "General Physician"
            treatment_type = "Medical Management"
            timeline = "To be determined based on further evaluation"
            required_reports = ["Blood Test", "Clinical Examination"]
            notes = "Specific guidelines not found; general management recommended."
            guideline_source = "Default"

        # ── Step 2: Verify existing lab reports vs required reports ──────────
        lab_verification = self._verify_lab_reports(existing_lab_reports, required_reports)

        # ── Step 3: ChromaDB semantic search for additional context ──────────
        try:
            chroma_results = query_disease_guidelines(
                f"{disease_type} {stage} treatment", n_results=2
            )
            chroma_context = " | ".join(
                [r["document"][:200] for r in chroma_results]
            )
        except Exception as e:
            print(f"[DecisionEngine] ChromaDB query failed: {e}")
            chroma_context = ""

        # ── Step 4: Filter & rank hospitals using patient location ───────────
        suggested_hospitals = self._filter_hospitals(
            hospital_type, constraint,
            patient_city=patient_city,
            patient_area_type=patient_area_type,
        )

        # ── Step 5: Add rural/remote advisory note ────────────────────────────
        area = (patient_area_type or "urban").lower()
        if area in ("rural", "remote"):
            notes += (
                " NOTE: As you are in a rural/remote area, government hospitals and "
                "telemedicine consultations are strongly recommended for initial assessment "
                "before travelling to a major centre."
            )

        # ── Step 6: Gemini LLM reasoning ─────────────────────────────────────
        llm_reasoning = self._gemini_reason(
            profile=profile,
            treatment_type=treatment_type,
            guideline_context=chroma_context,
            notes=notes
        )

        decision = {
            "disease_type": disease_type,
            "stage": stage,
            "treatment_type": treatment_type,
            "hospital_type": hospital_type,
            "specialist": specialist,
            "timeline": timeline,
            "required_reports": required_reports,
            "lab_verification": lab_verification,
            "notes": notes,
            "suggested_hospitals": suggested_hospitals,
            "guideline_source": guideline_source,
            "llm_reasoning": llm_reasoning,
            "surgery_allowed": surgery_allowed,
            "patient_area_type": patient_area_type,
        }

        print(f"[DecisionEngine] Decision: {treatment_type} at {hospital_type} | City: {patient_city}")
        return decision

    def _verify_lab_reports(self, existing_reports: str, required_reports: list) -> dict:
        """
        Cross-reference existing lab reports the patient has already done
        against those required for the disease/stage.
        Returns a summary dict for display in the treatment plan.
        """
        existing_lower = (existing_reports or "none").lower()
        if existing_lower in ("none", "no", "not done", "", "n/a", "na"):
            return {
                "existing": "None provided",
                "completed": [],
                "pending": required_reports,
                "note": "No prior lab results provided. All required investigations listed below should be done before starting treatment."
            }

        completed = [r for r in required_reports if r.lower() in existing_lower]
        pending   = [r for r in required_reports if r.lower() not in existing_lower]

        return {
            "existing": existing_reports,
            "completed": completed,
            "pending": pending,
            "note": (
                f"{len(completed)} of {len(required_reports)} required investigations already done. "
                f"{len(pending)} still pending: {', '.join(pending) if pending else 'None — all clear!'}"
            )
        }

    def _gemini_reason(self, profile: dict, treatment_type: str,
                       guideline_context: str, notes: str) -> str:
        """Use Gemini to generate nuanced clinical reasoning."""
        try:
            prompt = f"""
You are a senior medical decision support assistant. Given the following patient profile and recommended treatment, provide a brief clinical reasoning (3-4 sentences) explaining why this treatment is appropriate.

Patient Profile:
- Disease: {profile.get('disease_type', 'Unknown')}
- Stage: {profile.get('stage', 'Unknown')}
- Age: {profile.get('age', 'Unknown')}
- Gender: {profile.get('gender', 'Unknown')}
- Medical History: {profile.get('medical_history', 'None stated')}
- Surgery Allowed: {profile.get('surgery_allowed', True)}

Recommended Treatment: {treatment_type}
Guidelines Context: {guideline_context[:300] if guideline_context else 'Standard guidelines'}
Notes: {notes}

Provide ONLY the clinical reasoning paragraph, no headers or markdown.
"""
            response = _model.generate_content(prompt)
            reasoning = response.text.strip()
            print("[DecisionEngine] Gemini reasoning generated.")
            return reasoning
        except Exception as e:
            print(f"[DecisionEngine] Gemini reasoning failed: {e}")
            return (
                f"Based on the {profile.get('stage', 'reported')} stage of "
                f"{profile.get('disease_type', 'the condition')}, "
                f"{treatment_type} is the recommended approach per established clinical guidelines."
            )
