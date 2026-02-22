"""
End-to-end integration test for the Healthcare Planning Assistant Agent.

Tests the full PlannerAgent pipeline without requiring a database connection.
Run with: pytest tests/ -v
"""
import sys
import os
import pytest

# Make sure backend is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Sample Test Cases ─────────────────────────────────────────────────────────
SAMPLE_BREAST_CANCER = {
    "disease_type": "Breast Cancer",
    "cancer_type": "Breast Cancer",
    "stage": "Stage II",
    "age": "45",
    "gender": "Female",
    "medical_history": "No prior surgeries. Diagnosed 2 months ago. Family history of breast cancer.",
    "symptoms": "Lump in left breast, mild pain, occasional swelling",
    "surgery_allowed": "yes",
    "budget_limit": "500000",
    "location_type": "national",
    "hospital_preference": "private",
}

SAMPLE_DIABETES = {
    "disease_type": "Diabetes",
    "stage": "Type 2 - Early",
    "age": "55",
    "gender": "Male",
    "medical_history": "Hypertension for 5 years. No prior surgeries. Currently on Metformin.",
    "symptoms": "Frequent urination, fatigue, blurred vision",
    "surgery_allowed": "no",
    "budget_limit": "100000",
    "location_type": "local",
    "hospital_preference": "government",
}

SAMPLE_HEART_DISEASE = {
    "disease_type": "Heart Disease",
    "stage": "Stable Angina",
    "age": "62",
    "gender": "Male",
    "medical_history": "Smoker for 30 years, quit 5 years ago. High cholesterol.",
    "symptoms": "Chest pain on exertion, shortness of breath",
    "surgery_allowed": "yes",
    "budget_limit": "750000",
    "location_type": "national",
    "hospital_preference": "private",
}

INCOMPLETE_ANSWERS = {
    "disease_type": "Lung Cancer",
    # Missing: stage, age, gender, medical_history, symptoms, surgery_allowed, budget_limit
}


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestQuestionService:
    def test_default_questions_returned(self):
        """QuestionService returns default questions even if Gemini is unavailable."""
        from backend.agents.question_service import QuestionService, DEFAULT_QUESTIONS
        qs = QuestionService()
        # Test collect_responses with matched fields
        questions = DEFAULT_QUESTIONS
        responses = {"disease_type": "Breast Cancer", "age": "45"}
        collected = qs.collect_responses(questions, responses)
        assert collected.get("disease_type") == "Breast Cancer"
        assert collected.get("age") == "45"

    def test_collect_responses_ignores_unknown_fields(self):
        """collect_responses should only return known fields."""
        from backend.agents.question_service import QuestionService, DEFAULT_QUESTIONS
        qs = QuestionService()
        questions = DEFAULT_QUESTIONS
        responses = {"disease_type": "Diabetes", "unknown_field": "xyz"}
        collected = qs.collect_responses(questions, responses)
        assert "unknown_field" not in collected
        assert collected.get("disease_type") == "Diabetes"


class TestValidationEngine:
    def test_complete_profile_passes(self):
        """A fully filled profile should pass validation."""
        from backend.agents.validation_engine import ValidationEngine
        ve = ValidationEngine()
        result = ve.validate_from_responses(SAMPLE_BREAST_CANCER)
        assert result["is_valid"] is True
        assert result["missing_fields"] == []

    def test_incomplete_profile_fails(self):
        """A profile missing required fields should fail validation."""
        from backend.agents.validation_engine import ValidationEngine
        ve = ValidationEngine()
        result = ve.validate_from_responses(INCOMPLETE_ANSWERS)
        assert result["is_valid"] is False
        assert len(result["missing_fields"]) > 0
        assert "stage" in result["missing_fields"]

    def test_invalid_budget_raises_error(self):
        """A negative budget should produce a validation error."""
        from backend.agents.validation_engine import ValidationEngine
        ve = ValidationEngine()
        bad = {**SAMPLE_BREAST_CANCER, "budget_limit": "-1000"}
        result = ve.validate_from_responses(bad)
        assert len(result["errors"]) > 0


class TestDecisionEngine:
    def test_breast_cancer_decision(self):
        """DecisionEngine should correctly identify Oncology hospital type for breast cancer."""
        from backend.agents.decision_engine import DecisionEngine
        de = DecisionEngine()
        profile = {
            "disease_type": "Breast Cancer",
            "stage": "Stage II",
            "surgery_allowed": True,
            "age": 45,
            "gender": "Female",
            "medical_history": "None",
            "symptoms": "Lump in breast",
        }
        constraint = {
            "budget_limit": 500000,
            "location_type": "national",
            "hospital_preference": "private",
        }
        decision = de.analyze(profile, constraint)
        assert decision["hospital_type"] == "Oncology"
        assert "Cancer" in decision["disease_type"] or "cancer" in decision["treatment_type"].lower()
        assert isinstance(decision["suggested_hospitals"], list)
        assert decision["timeline"] != ""

    def test_diabetes_decision(self):
        """DecisionEngine should identify Endocrinology for diabetes."""
        from backend.agents.decision_engine import DecisionEngine
        de = DecisionEngine()
        profile = {
            "disease_type": "Diabetes",
            "stage": "Type 2 - Early",
            "surgery_allowed": False,
            "age": 55,
            "gender": "Male",
            "medical_history": "Hypertension",
            "symptoms": "Fatigue",
        }
        constraint = {"budget_limit": 100000, "location_type": "local", "hospital_preference": "government"}
        decision = de.analyze(profile, constraint)
        assert decision["hospital_type"] == "Endocrinology"

    def test_no_surgery_filters_surgical_treatments(self):
        """Surgery-related treatments must be excluded when surgery_allowed=False."""
        from backend.agents.decision_engine import DecisionEngine
        de = DecisionEngine()
        profile = {
            "disease_type": "Breast Cancer",
            "stage": "Stage I",
            "surgery_allowed": False,
            "age": 50,
            "gender": "Female",
            "medical_history": "None",
            "symptoms": "Lump",
        }
        constraint = {"budget_limit": 300000, "location_type": "national", "hospital_preference": "private"}
        decision = de.analyze(profile, constraint)
        treatment = decision["treatment_type"].lower()
        assert "mastectomy" not in treatment
        assert "lumpectomy" not in treatment


class TestRecommendationEngine:
    def test_generate_plan_structure(self):
        """RecommendationEngine must return correctly structured output."""
        from backend.agents.recommendation_engine import RecommendationEngine
        re = RecommendationEngine()
        mock_decision = {
            "disease_type": "Breast Cancer",
            "treatment_type": "Chemotherapy + Surgery",
            "hospital_type": "Oncology",
            "specialist": "Oncologist",
            "timeline": "6-9 months",
            "required_reports": ["Biopsy", "MRI"],
            "notes": "Standard of care",
            "surgery_allowed": True,
            "suggested_hospitals": [
                {
                    "hospital_id": "H001",
                    "name": "Apollo Cancer Centre",
                    "type": "Oncology",
                    "location": "Mumbai",
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "rating": 4.8,
                    "budget_category": "Premium",
                    "accreditation": "NABH, JCI",
                    "accepts_insurance": True,
                    "contact": "+91-22-6789-0000",
                    "specializations": ["Breast Cancer"],
                }
            ],
            "llm_reasoning": "Stage II requires combination therapy.",
        }
        result = re.generate_plan(mock_decision)
        assert "treatment_plan" in result
        assert "ranked_hospitals" in result
        assert len(result["ranked_hospitals"]) == 1
        assert result["ranked_hospitals"][0]["priority_rank"] == "1"

    def test_hospital_ranking_order(self):
        """Hospitals should be sorted correctly by composite score."""
        from backend.agents.recommendation_engine import RecommendationEngine
        re = RecommendationEngine()
        hospitals = [
            {"hospital_id": "HA", "name": "Hospital A", "type": "Multi-specialty",
             "location": "Delhi", "city": "Delhi", "state": "Delhi", "rating": 3.5,
             "budget_category": "Standard", "accreditation": "NABH", "accepts_insurance": True,
             "contact": "", "specializations": []},
            {"hospital_id": "HB", "name": "Hospital B", "type": "Oncology",
             "location": "Mumbai", "city": "Mumbai", "state": "MH", "rating": 4.9,
             "budget_category": "Premium", "accreditation": "JCI, NABH", "accepts_insurance": True,
             "contact": "", "specializations": []},
        ]
        ranked = re._rank_hospitals(hospitals, "Oncology")
        # Hospital B should be rank 1 (type match + higher rating + JCI)
        assert ranked[0]["name"] == "Hospital B"
        assert ranked[0]["priority_rank"] == "1"


class TestPlannerAgent:
    def test_goal_decomposition(self):
        """PlannerAgent must decompose goal into 11 subtasks."""
        from backend.agents.planner_agent import PlannerAgent
        planner = PlannerAgent()
        planner.receiveGoal("I want treatment options for breast cancer")
        subtasks = planner.decomposeGoal()
        assert len(subtasks) == 11
        assert planner.state["status"] == "goal_decomposed"

    def test_execution_plan_structure(self):
        """createExecutionPlan must list 6 agent steps."""
        from backend.agents.planner_agent import PlannerAgent
        planner = PlannerAgent()
        planner.receiveGoal("Treatment for diabetes")
        planner.decomposeGoal()
        plan = planner.createExecutionPlan()
        assert len(plan["agents"]) == 6
        assert plan["agents"][0]["agent"] == "QuestionService"

    def test_full_pipeline_breast_cancer(self):
        """End-to-end pipeline for breast cancer must return a valid structured output."""
        from backend.agents.planner_agent import PlannerAgent
        planner = PlannerAgent()
        planner.receiveGoal("I want treatment options for breast cancer")
        planner.decomposeGoal()
        planner.createExecutionPlan()

        result = planner.executePlan(SAMPLE_BREAST_CANCER)

        assert "treatment_plan" in result
        assert "recommended_hospitals" in result
        assert "explanation" in result
        assert "disclaimer" in result

        tp = result["treatment_plan"]
        assert tp["disease_type"] != ""
        assert tp["treatment_type"] != ""
        assert tp["timeline"] != ""

        hospitals = result["recommended_hospitals"]
        assert len(hospitals) > 0
        assert "name" in hospitals[0]
        assert "priority_rank" in hospitals[0]

        assert "consult" in result["disclaimer"].lower() or "medical" in result["disclaimer"].lower()

    def test_full_pipeline_diabetes(self):
        """End-to-end pipeline for diabetes."""
        from backend.agents.planner_agent import PlannerAgent
        planner = PlannerAgent()
        planner.receiveGoal("I have Type 2 Diabetes and need a treatment plan")
        planner.decomposeGoal()
        planner.createExecutionPlan()
        result = planner.executePlan(SAMPLE_DIABETES)
        assert "treatment_plan" in result
        assert result["treatment_plan"]["disease_type"] == "Diabetes"

    def test_incomplete_data_triggers_loop_back(self):
        """PlannerAgent should return 'needs_more_data' when required fields are missing."""
        from backend.agents.planner_agent import PlannerAgent
        planner = PlannerAgent()
        planner.receiveGoal("Lung cancer treatment")
        planner.decomposeGoal()
        planner.createExecutionPlan()

        result = planner.executePlan(INCOMPLETE_ANSWERS)

        assert result.get("status") == "needs_more_data"
        assert "missing_fields" in result
        assert len(result["missing_fields"]) > 0

    def test_state_tracking(self):
        """Planner state should correctly track execution stages."""
        from backend.agents.planner_agent import PlannerAgent
        planner = PlannerAgent()
        assert planner.state["status"] == "idle"
        planner.receiveGoal("Heart disease treatment")
        assert planner.state["status"] == "goal_received"
        planner.decomposeGoal()
        assert planner.state["status"] == "goal_decomposed"
        planner.createExecutionPlan()
        assert planner.state["status"] == "plan_created"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
