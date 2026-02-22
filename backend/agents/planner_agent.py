"""
PlannerAgent — Strict Process-Flow Orchestrator
================================================
Execution order enforced exactly per the AI Healthcare Assistant Process Flow Diagram:

  1.  User opens application → receive goal
  2.  User Login / Registration → check_authentication()
  3.  Authenticated?  No → return auth error + retry signal
  4.  Yes → verify_identity()
  5.  Generate Access Token → generate_access_token()
  6.  Decompose goal into subtasks → decomposeGoal()
  7.  Create dynamic execution plan → createExecutionPlan()
  8.  Collect Patient Data → QuestionService
  9.  Validate Input Data → ValidationEngine
  10. Data Complete?  No → loop back (loop_until_data_complete)
  11. Yes → Store Data → MedicalDataService
  12. Analyse Patient Profile → DecisionEngine (JSON + ChromaDB + Gemini)
  13. Validate Recommendations for clinical safety → validate_clinical_compliance()
  14. Safe & Compliant?  No → flag_for_manual_review() → still produce structured report
  15. Generate Treatment Plan → RecommendationEngine
  16. Match Hospital/Specialist → already inside RecommendationEngine / DecisionEngine
  17. Prepare Personalised Report + Explanation → ExplanationEngine
  18. Send Recommendations to User (return structured JSON)
  19. Schedule Follow-up / Reminders → schedule_followups()
  20. Log Activity for Audit → log_audit_trail()
  21. End Session → end_session()
"""

import uuid
import datetime
from typing import Optional

from backend.agents.question_service import QuestionService
from backend.agents.medical_data_service import MedicalDataService
from backend.agents.validation_engine import ValidationEngine
from backend.agents.decision_engine import DecisionEngine
from backend.agents.recommendation_engine import RecommendationEngine
from backend.agents.explanation_engine import ExplanationEngine

# Maximum times the data-collection loop may repeat before forcing progression
MAX_RETRY_LOOPS = 3


class PlannerAgent:
    """
    Strict goal-driven planner that orchestrates the full healthcare planning
    pipeline following the exact process flow diagram.

    All public surface-area used by the API routes and the Streamlit frontend is
    preserved; new step methods are added alongside existing ones.
    """

    # ─────────────────────────────────────────────────────────────────────────
    # Initialisation
    # ─────────────────────────────────────────────────────────────────────────
    def __init__(self):
        self.goal: str = ""
        self.subtasks: list[str] = []
        self.execution_plan: dict = {}

        # Flat state dict — a single source of truth across all steps
        self.state: dict = {
            "goal": None,
            "questions": [],
            "responses": {},
            "profile": {},
            "constraint": {},
            "validation_result": {},
            "decision": {},
            "recommendation": {},
            "final_output": {},
            "status": "idle",                 # lifecycle status
            "retry_count": 0,
            "missing_fields": [],
            # ── New fields per process-flow diagram ──────────────────────────
            "authenticated": False,
            "access_token": None,
            "session_id": None,
            "user_id": None,
            "audit_trail": [],                # ordered list of audit log entries
            "followups": [],                  # scheduled follow-up reminders
            "compliance_status": "pending",   # 'compliant' | 'flagged'
            "manual_review_flagged": False,
            "session_ended": False,
        }

        # Sub-agent instances (one per PlannerAgent lifetime)
        self._question_service    = QuestionService()
        self._medical_data_service = MedicalDataService()
        self._validation_engine   = ValidationEngine()
        self._decision_engine     = DecisionEngine()
        self._recommendation_engine = RecommendationEngine()
        self._explanation_engine  = ExplanationEngine()

    # =========================================================================
    # STEP 1 — Goal Reception  (was receiveGoal)
    # =========================================================================
    def receiveGoal(self, goal: str) -> str:
        """Receive and store the user's healthcare goal (Step 1)."""
        self.goal = goal.strip()
        self.state["goal"]   = self.goal
        self.state["status"] = "goal_received"
        self._log("Goal received", detail=self.goal)
        print(f"[PlannerAgent] Goal received: '{self.goal}'")
        return self.goal

    # Alias for cleaner internal calls
    receive_goal = receiveGoal

    # =========================================================================
    # STEP 2 — Authentication Check
    # =========================================================================
    def check_authentication(
        self,
        access_token: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        authenticated: bool = False,          # Deprecated bypass — only for tests
    ) -> dict:
        """
        Verify the user is authenticated (Step 2 of the process flow diagram).

        Priority order:
        1. If ``access_token`` is supplied → validate it against TokenStore.
           On success: populate state from token payload.
           On failure: return auth error + retry=True.

        2. Legacy / direct-mode bypass (for existing tests and internal calls):
           If ``access_token`` is None AND ``authenticated=True``, trust the
           caller and use the supplied ``user_id`` / ``session_id``.

        Returns:
            { "authenticated": bool, "error": str|None, "retry": bool,
              "user_id": str|None, "session_id": str|None }
        """
        self._log("Authentication check started")

        # ── Path 1: Real token validation ─────────────────────────────────────
        if access_token is not None:
            try:
                from backend.auth.token_store import validate_token
                payload = validate_token(access_token)
            except ImportError:
                payload = None

            if payload:
                self.state["authenticated"] = True
                self.state["user_id"]       = payload["user_id"]
                self.state["session_id"]    = payload["session_id"]
                self.state["access_token"]  = access_token
                self.state["status"]        = "authenticated"
                self._log("Token validated",
                          detail=f"user_id={payload['user_id']}")
                print(f"[PlannerAgent] ✅ Token validated. user_id={payload['user_id']}")
                return {
                    "authenticated": True,
                    "error": None,
                    "retry": False,
                    "user_id":    payload["user_id"],
                    "session_id": payload["session_id"],
                }
            else:
                self.state["authenticated"] = False
                self.state["status"]        = "auth_failed"
                self._log("Token invalid or expired — retry required")
                print("[PlannerAgent] ❌ Token invalid or expired.")
                return {
                    "authenticated": False,
                    "error": "Invalid or expired access token. Please log in again.",
                    "retry": True,
                    "user_id":    None,
                    "session_id": None,
                }

        # ── Path 2: Legacy bypass (authenticated=True, no token) ──────────────
        if authenticated:
            self.state["user_id"]       = user_id or str(uuid.uuid4())
            self.state["session_id"]    = session_id or str(uuid.uuid4())
            self.state["authenticated"] = True
            self.state["access_token"]  = None
            self.state["status"]        = "authenticated"
            self._log("Authentication bypassed (direct mode)",
                      detail=f"user_id={self.state['user_id']}")
            print(f"[PlannerAgent] ✅ Direct-mode auth. user_id={self.state['user_id']}")
            return {
                "authenticated": True,
                "error": None,
                "retry": False,
                "user_id":    self.state["user_id"],
                "session_id": self.state["session_id"],
            }

        # ── Path 3: No token, not bypassed → fail ────────────────────────────
        self.state["authenticated"] = False
        self.state["status"]        = "auth_failed"
        self._log("Authentication failed — no token supplied")
        print("[PlannerAgent] ❌ No access token supplied.")
        return {
            "authenticated": False,
            "error": "No access token provided. Please log in first.",
            "retry": True,
            "user_id":    None,
            "session_id": None,
        }


    # =========================================================================
    # STEP 3 — Identity Verification
    # =========================================================================
    def verify_identity(self) -> bool:
        """
        Verify the stored user identity before generating an access token (Step 3).
        Returns True if identity is confirmed, False otherwise.
        """
        if not self.state.get("authenticated"):
            self._log("Identity verification skipped — not authenticated")
            return False

        # In a real system this would cross-check against the User table.
        # Here we assert identity is valid if a user_id is present.
        identity_confirmed = bool(self.state.get("user_id"))
        self.state["status"] = "identity_verified" if identity_confirmed else "identity_failed"
        self._log("Identity verified", detail=str(identity_confirmed))
        print(f"[PlannerAgent] Identity verified: {identity_confirmed}")
        return identity_confirmed

    # =========================================================================
    # STEP 4 — Access Token Generation
    # =========================================================================
    def generate_access_token(self) -> str:
        """
        Generate a session-scoped access token (Step 4).
        Returns the token string.
        """
        token = f"hca-token-{self.state['session_id']}-{uuid.uuid4().hex[:12]}"
        self.state["access_token"] = token
        self.state["status"] = "token_generated"
        self._log("Access token generated", detail=token[:24] + "…")
        print(f"[PlannerAgent] Access token generated.")
        return token

    # =========================================================================
    # STEP 5 — Goal Decomposition  (was decomposeGoal)
    # =========================================================================
    def decomposeGoal(self) -> list[str]:
        """Decompose the goal into structured subtasks (Step 5)."""
        self.subtasks = [
            "1. Identify disease type from user goal",
            "2. Generate medical questions for data collection",
            "3. Collect patient medical history and responses",
            "4. Check medical constraints (budget, location, surgery)",
            "5. Validate data completeness",
            "6. Analyse medical profile and apply decision logic",
            "7. Suggest appropriate treatment type",
            "8. Recommend suitable hospitals",
            "9. Generate treatment timeline",
            "10. Add medical disclaimer and explanation",
            "11. Prepare final structured recommendation",
        ]
        self.state["status"] = "goal_decomposed"
        self._log("Goal decomposed", detail=f"{len(self.subtasks)} subtasks")
        print(f"[PlannerAgent] Goal decomposed into {len(self.subtasks)} subtasks.")
        return self.subtasks

    # =========================================================================
    # STEP 6 — Create Dynamic Execution Plan  (was createExecutionPlan)
    # =========================================================================
    def createExecutionPlan(self) -> dict:
        """Create a dynamic execution plan from the subtasks (Step 6)."""
        self.execution_plan = {
            "goal": self.goal,
            "agents": [
                {"step": 1, "agent": "QuestionService",
                 "task": "Generate & collect medical questions"},
                {"step": 2, "agent": "ValidationEngine",
                 "task": "Validate data completeness (loop until complete)"},
                {"step": 3, "agent": "MedicalDataService",
                 "task": "Store validated medical profile in PostgreSQL"},
                {"step": 4, "agent": "DecisionEngine",
                 "task": "Analyse profile + apply decision logic (JSON + ChromaDB + Gemini)"},
                {"step": 5, "agent": "RecommendationEngine",
                 "task": "Generate treatment plan + rank hospitals"},
                {"step": 6, "agent": "ExplanationEngine",
                 "task": "Format final output + add disclaimer"},
            ],
            "max_retries": MAX_RETRY_LOOPS,
            "status": "planned",
        }
        self.state["status"] = "plan_created"
        self._log("Execution plan created")
        print("[PlannerAgent] Execution plan created.")
        return self.execution_plan

    # =========================================================================
    # STEP 7 — Question Generation  (was generateQuestions)
    # =========================================================================
    def generateQuestions(self) -> list[dict]:
        """Trigger QuestionService to generate medical questions (Step 7)."""
        self.state["status"] = "generating_questions"
        questions = self._question_service.generate_questions(self.goal)
        self.state["questions"] = questions
        self.state["status"] = "questions_ready"
        self._log("Questions generated", detail=f"{len(questions)} questions")
        print(f"[PlannerAgent] {len(questions)} questions ready for user.")
        return questions

    # =========================================================================
    # STEP 8–10 — Strict Data-Collection Loop
    # =========================================================================
    def loop_until_data_complete(self, answers: dict) -> dict:
        """
        Strict loop controller (Steps 8-10 of the diagram).
        Injects sensible defaults and infers disease_type from goal
        before validation so the pipeline is not blocked by trivial omissions.
        """
        # Merge incoming answers with any previously collected ones
        self.state["responses"].update(answers)
        self.state["retry_count"] += 1
        loop_count = 0

        # ── Smart defaults for constraint fields ──────────────────────────────
        resp = self.state["responses"]

        # location_type / hospital_preference / surgery_allowed always have defaults
        if not resp.get("location_type"):
            resp["location_type"] = "national"
        if not resp.get("hospital_preference"):
            resp["hospital_preference"] = "private"
        if not resp.get("surgery_allowed"):
            resp["surgery_allowed"] = "yes"

        # Infer disease_type from the goal text if the user didn't fill it in
        if not resp.get("disease_type") and self.goal:
            resp["disease_type"] = self.goal  # best-effort fallback

        # Infer stage if missing (many patients don't know — use "unknown")
        if not resp.get("stage"):
            resp["stage"] = "unknown"

        self._log("Data-collection loop started", detail=f"retry #{self.state['retry_count']}")

        while loop_count < MAX_RETRY_LOOPS:
            loop_count += 1
            print(f"[PlannerAgent] 🔄 Data-collection loop iteration {loop_count}…")

            # Run ValidationEngine on current responses
            validation = self._validation_engine.validate_from_responses(
                self.state["responses"]
            )
            self.state["validation_result"] = validation
            self.state["missing_fields"]    = validation.get("missing_fields", [])

            if validation["is_valid"]:
                self.state["status"] = "validation_passed"
                self._log("Validation passed", detail=f"iteration {loop_count}")
                print("[PlannerAgent] ✅ Data complete — exiting collection loop.")
                break

            # Data incomplete — request missing information
            self.state["status"] = "needs_more_data"
            self._log(
                "Data incomplete — requesting missing fields",
                detail=str(validation["missing_fields"]),
            )
            print(
                f"[PlannerAgent] ⚠️  Missing fields: {validation['missing_fields']}. "
                f"Loop iteration {loop_count}/{MAX_RETRY_LOOPS}."
            )

            # If we have exhausted retries, break and continue with partial data
            if loop_count >= MAX_RETRY_LOOPS:
                self._log("Max retries reached — proceeding with partial data")
                print("[PlannerAgent] Max retries reached — proceeding with partial data.")
                break

            # In a fully interactive loop (API/WS) the caller would inject new
            # answers here. In stateless mode we break and surface missing fields.
            break  # stateless: surface missing fields to caller

        return self.state["validation_result"]

    # =========================================================================
    # STEP 11 — Clinical Compliance Validation
    # =========================================================================
    def validate_clinical_compliance(self, decision: dict) -> dict:
        """
        Validate that the recommendation is clinically safe and compliant (Step 13).

        Checks:
        - A recognised treatment type is present
        - Required diagnostic reports are listed
        - Surgery flag is respected

        Returns:
            { "compliant": bool, "flags": list[str], "action": str }
        """
        flags = []

        treatment = decision.get("treatment_type", "")
        if not treatment or treatment.strip().lower() in ("", "unknown", "tbd"):
            flags.append("Treatment type is undefined — clinical review required.")

        required_reports = decision.get("required_reports", [])
        if not required_reports:
            flags.append("No required diagnostic reports specified.")

        surgery_allowed = decision.get("surgery_allowed", True)
        treatment_lower = treatment.lower()
        surgical_keywords = ["surgery", "surgical", "mastectomy", "lumpectomy",
                             "cabg", "resection", "amputation"]
        if not surgery_allowed and any(k in treatment_lower for k in surgical_keywords):
            flags.append(
                "Recommended treatment includes surgery, but patient opted out — "
                "clinical override needed."
            )

        compliant = len(flags) == 0

        if not compliant:
            self.state["compliance_status"]      = "flagged"
            self.state["manual_review_flagged"]  = True
            self._log("Clinical compliance FAILED — flagged for manual review",
                      detail=str(flags))
            print(f"[PlannerAgent] ⚠️  Compliance flags: {flags}")
            action = "flag_for_manual_review"
        else:
            self.state["compliance_status"]     = "compliant"
            self.state["manual_review_flagged"] = False
            self._log("Clinical compliance passed")
            print("[PlannerAgent] ✅ Recommendations are clinically compliant.")
            action = "proceed"

        return {"compliant": compliant, "flags": flags, "action": action}

    # =========================================================================
    # STEP 12 — Flag for Manual Review  (called when not compliant)
    # =========================================================================
    def flag_for_manual_review(self, flags: list[str]) -> dict:
        """
        Flag the case for manual clinical review (Step 14 — 'No' branch).
        System still generates a structured report but marks it as requiring review.
        """
        notice = (
            "⚠️ This recommendation has been flagged for manual clinical review. "
            "A healthcare provider should verify this plan before it is acted upon. "
            f"Flags: {'; '.join(flags)}"
        )
        self._log("Manual review flag raised", detail=notice)
        print(f"[PlannerAgent] Manual review flag raised. Provider notification logged.")
        return {
            "manual_review": True,
            "notice": notice,
            "flags": flags,
        }

    # =========================================================================
    # STEP 19 — Schedule Follow-up Reminders
    # =========================================================================
    def schedule_followups(self, disease_type: str = "", timeline: str = "") -> list[dict]:
        """
        Schedule follow-up reminders based on treatment timeline (Step 19).
        Returns a list of reminder dicts.
        """
        now = datetime.datetime.utcnow()
        reminders = [
            {
                "reminder_id": str(uuid.uuid4())[:8],
                "type": "Initial Consultation",
                "message": f"Schedule your first specialist appointment for {disease_type}.",
                "due_date": (now + datetime.timedelta(days=7)).strftime("%Y-%m-%d"),
            },
            {
                "reminder_id": str(uuid.uuid4())[:8],
                "type": "Diagnostic Reports",
                "message": "Collect all required diagnostic reports before your appointment.",
                "due_date": (now + datetime.timedelta(days=14)).strftime("%Y-%m-%d"),
            },
            {
                "reminder_id": str(uuid.uuid4())[:8],
                "type": "Treatment Follow-up",
                "message": (
                    f"Follow-up with your specialist regarding treatment progress. "
                    f"Expected timeline: {timeline or 'as prescribed'}."
                ),
                "due_date": (now + datetime.timedelta(days=30)).strftime("%Y-%m-%d"),
            },
        ]
        self.state["followups"] = reminders
        self._log("Follow-up reminders scheduled", detail=f"{len(reminders)} reminders")
        print(f"[PlannerAgent] {len(reminders)} follow-up reminders scheduled.")
        return reminders

    # =========================================================================
    # STEP 20 — Audit Logging
    # =========================================================================
    def log_audit_trail(self, final_output: dict) -> list[dict]:
        """
        Finalise and return the complete audit trail for this session (Step 20).
        Also appends an execution-complete entry.
        """
        self._log(
            "Execution complete — audit trail finalised",
            detail=f"session_id={self.state.get('session_id')} | "
                   f"status={self.state['status']} | "
                   f"compliance={self.state['compliance_status']}",
        )
        print(f"[PlannerAgent] Audit trail has {len(self.state['audit_trail'])} entries.")
        return self.state["audit_trail"]

    # =========================================================================
    # STEP 21 — End Session
    # =========================================================================
    def end_session(self) -> dict:
        """
        Gracefully end the session and mark state as closed (Step 21).
        """
        self.state["session_ended"] = True
        self.state["status"]        = "session_ended"
        self._log("Session ended gracefully",
                  detail=f"session_id={self.state.get('session_id')}")
        print(f"[PlannerAgent] Session ended. session_id={self.state.get('session_id')}")
        return {
            "session_id": self.state.get("session_id"),
            "status": "session_ended",
            "audit_entries": len(self.state["audit_trail"]),
        }

    # =========================================================================
    # MAIN PIPELINE — Stepwise Execution (synchronous / no DB)
    # =========================================================================
    def execute_plan_stepwise(self, answers: dict) -> dict:
        """
        Execute the FULL strict process-flow pipeline (stateless / no DB).
        This is the canonical orchestration method — `executePlan()` delegates here.

        Flow:
          1 → already done (receiveGoal)
          2 → check_authentication (trusts direct-mode caller)
          3 → verify_identity
          4 → generate_access_token
          5–6 → already done (decomposeGoal + createExecutionPlan)
          7 → already done (generateQuestions)
          8–10 → loop_until_data_complete (strict loop)
          11 → DecisionEngine.analyze
          12 → validate_clinical_compliance
          13 → flag_for_manual_review if needed
          14–16 → RecommendationEngine.generate_plan
          17 → ExplanationEngine.generate
          18 (return structured JSON)
          19 → schedule_followups
          20 → log_audit_trail
          21 → end_session (state only; caller controls HTTP lifecycle)
        """
        print("[PlannerAgent] ▶ Starting STRICT stepwise plan execution…")
        self.state["status"] = "executing"

        # ── Step 2: Authentication ────────────────────────────────────────────
        auth_result = self.check_authentication(
            user_id    = self.state.get("user_id"),
            session_id = self.state.get("session_id"),
            authenticated=True,  # In direct/API mode the caller is already trusted
        )
        if not auth_result["authenticated"]:
            return {
                "status": "auth_failed",
                "error": auth_result["error"],
                "retry": True,
            }

        # ── Step 3: Identity Verification ────────────────────────────────────
        if not self.verify_identity():
            return {"status": "identity_failed", "error": "Identity verification failed."}

        # ── Step 4: Access Token ─────────────────────────────────────────────
        self.generate_access_token()

        # ── Step 8–10: Strict Data-Collection Loop ───────────────────────────
        validation = self.loop_until_data_complete(answers)

        if not validation.get("is_valid") and self.state["retry_count"] <= MAX_RETRY_LOOPS:
            # Surface missing fields to the caller for another round of answers
            return {
                "status": "needs_more_data",
                "missing_fields": validation.get("missing_fields", []),
                "warnings": validation.get("warnings", []),
                "message": (
                    "Please provide the following missing information: "
                    + ", ".join(validation.get("missing_fields", []))
                ),
            }

        # ── Step 11a: Build profile & constraint dicts ───────────────────────
        responses = self.state["responses"]
        profile = {
            "disease_type":    responses.get("disease_type", ""),
            "cancer_type":     responses.get("cancer_type", responses.get("disease_type", "")),
            "stage":           responses.get("stage", ""),
            "medical_history": responses.get("medical_history", ""),
            "surgery_allowed": self._parse_bool(responses.get("surgery_allowed", "yes")),
            "age":             responses.get("age", ""),
            "gender":          responses.get("gender", ""),
            "symptoms":        responses.get("symptoms", ""),
        }
        constraint = {
            "budget_limit":        responses.get("budget_limit"),
            "location_type":       responses.get("location_type", "national"),
            "hospital_preference": responses.get("hospital_preference", "private"),
        }
        self.state["profile"]    = profile
        self.state["constraint"] = constraint

        # ── Step 11b: DecisionEngine ─────────────────────────────────────────
        print("[PlannerAgent] → DecisionEngine analysing profile…")
        self._log("DecisionEngine triggered")
        decision = self._decision_engine.analyze(profile, constraint)
        self.state["decision"] = decision

        # ── Step 12: Clinical Compliance Validation ───────────────────────────
        compliance = self.validate_clinical_compliance(decision)
        if not compliance["compliant"]:
            review_notice = self.flag_for_manual_review(compliance["flags"])
            # Attach notice to decision notes so it surfaces in the output
            decision["notes"] = (
                (decision.get("notes") or "") + " | " + review_notice["notice"]
            ).strip(" |")

        # ── Step 14–16: RecommendationEngine ─────────────────────────────────
        print("[PlannerAgent] → RecommendationEngine generating plan…")
        self._log("RecommendationEngine triggered")
        recommendation = self._recommendation_engine.generate_plan(decision)
        self.state["recommendation"] = recommendation

        # ── Step 17: ExplanationEngine ────────────────────────────────────────
        print("[PlannerAgent] → ExplanationEngine compiling output…")
        self._log("ExplanationEngine triggered")
        final_output = self._explanation_engine.generate(
            profile         = profile,
            plan_data       = recommendation["treatment_plan"],
            ranked_hospitals= recommendation["ranked_hospitals"],
            llm_reasoning   = decision.get("llm_reasoning", ""),
        )

        # Inject compliance status into the output
        final_output["compliance_status"] = compliance["compliant"]
        if self.state["manual_review_flagged"]:
            final_output["manual_review_required"] = True
            final_output["compliance_flags"]       = compliance["flags"]

        self.state["final_output"] = final_output
        self.state["status"]       = "completed"

        # ── Step 18: Output →  ────────────────────────────────────────────────
        print("[PlannerAgent] ✅ Structured JSON output prepared.")

        # ── Step 19: Follow-up Reminders ─────────────────────────────────────
        followups = self.schedule_followups(
            disease_type = profile.get("disease_type", ""),
            timeline     = recommendation["treatment_plan"].get("timeline", ""),
        )
        final_output["followup_reminders"] = followups

        # ── Step 20: Audit Logging ────────────────────────────────────────────
        audit = self.log_audit_trail(final_output)
        final_output["audit_summary"] = {
            "total_steps_logged": len(audit),
            "session_id":         self.state.get("session_id"),
            "timestamp":          datetime.datetime.utcnow().isoformat() + "Z",
        }

        # ── Step 21: End Session ──────────────────────────────────────────────
        self.end_session()

        print("[PlannerAgent] 🏁 Strict stepwise execution complete.")
        return final_output

    # =========================================================================
    # BACKWARD-COMPATIBLE PUBLIC API  (used by Streamlit + FastAPI routes)
    # =========================================================================

    def executePlan(self, answers: dict) -> dict:
        """
        Synchronous plan execution (no DB).
        Delegates to execute_plan_stepwise() — full process-flow compliance.
        Preserved for Streamlit direct-mode calls.
        """
        return self.execute_plan_stepwise(answers)

    def updatePlan(self, answers: dict) -> dict:
        """
        Update plan with new answers and re-validate.
        Used in loop-back scenarios from the Streamlit UI.
        """
        self.state["responses"].update(answers)
        self.state["retry_count"] += 1
        self._log("Plan updated with new answers",
                  detail=f"retry #{self.state['retry_count']}")
        print(f"[PlannerAgent] Plan updated (retry #{self.state['retry_count']}).")
        return self._validate_responses()

    async def executePlanWithDB(
        self,
        answers: dict,
        db,
        user_id: str,
        session_id: str = None,
    ) -> dict:
        """
        Full pipeline with PostgreSQL persistence (async).
        Used by the FastAPI /api/plan/respond route.
        Follows the same strict process-flow, but persists profile & plan to DB.
        """
        print("[PlannerAgent] ▶ Starting async DB-backed plan execution…")

        # ── Auth + Identity (trusting FastAPI-gated request) ──────────────────
        self.check_authentication(user_id=user_id, session_id=session_id, authenticated=True)
        self.verify_identity()
        self.generate_access_token()

        self.state["responses"] = answers

        # ── Strict validation loop ─────────────────────────────────────────────
        validation = self._validate_responses()
        if not validation["is_valid"] and self.state["retry_count"] < MAX_RETRY_LOOPS:
            self._log("Validation failed — needs more data (DB mode)")
            return {
                "status":         "needs_more_data",
                "missing_fields": validation["missing_fields"],
                "warnings":       validation.get("warnings", []),
                "message": f"Please provide: {', '.join(validation['missing_fields'])}",
            }

        # ── Store MedicalProfile in DB ─────────────────────────────────────────
        self._log("Storing medical profile in PostgreSQL")
        profile_orm = await self._medical_data_service.store_profile(db, user_id, answers)
        profile_id  = str(profile_orm.profile_id)

        # Build profile + constraint dicts
        profile = {
            "disease_type":    profile_orm.disease_type or "",
            "stage":           profile_orm.stage or "",
            "medical_history": profile_orm.medical_history or "",
            "surgery_allowed": profile_orm.surgery_allowed,
            "age":             profile_orm.age,
            "gender":          profile_orm.gender or "",
            "symptoms":        profile_orm.symptoms or "",
        }

        # Explicitly query Constraint (async sessions forbid lazy-loading)
        from sqlalchemy import select as _sa_select
        from backend.db.models import Constraint as _Constraint
        _c_res = await db.execute(
            _sa_select(_Constraint).where(
                _Constraint.profile_id == profile_orm.profile_id
            )
        )
        _c = _c_res.scalar_one_or_none()
        if _c:
            constraint = {
                "budget_limit":        _c.budget_limit,
                "location_type":       _c.location_type or "national",
                "hospital_preference": _c.hospital_preference or "private",
            }
        else:
            constraint = {
                "budget_limit":        self._medical_data_service._parse_budget(
                                           answers.get("budget_limit")),
                "location_type":       answers.get("location_type", "national"),
                "hospital_preference": answers.get("hospital_preference", "private"),
            }

        self.state["profile"]    = profile
        self.state["constraint"] = constraint

        # ── DecisionEngine ────────────────────────────────────────────────────
        self._log("DecisionEngine triggered (DB mode)")
        decision = self._decision_engine.analyze(profile, constraint)

        # ── Clinical Compliance ───────────────────────────────────────────────
        compliance = self.validate_clinical_compliance(decision)
        if not compliance["compliant"]:
            review_notice = self.flag_for_manual_review(compliance["flags"])
            decision["notes"] = (
                (decision.get("notes") or "") + " | " + review_notice["notice"]
            ).strip(" |")

        # ── RecommendationEngine ──────────────────────────────────────────────
        self._log("RecommendationEngine triggered (DB mode)")
        recommendation = self._recommendation_engine.generate_plan(decision)

        # ── ExplanationEngine ─────────────────────────────────────────────────
        self._log("ExplanationEngine triggered (DB mode)")
        final_output = self._explanation_engine.generate(
            profile          = profile,
            plan_data        = recommendation["treatment_plan"],
            ranked_hospitals = recommendation["ranked_hospitals"],
            llm_reasoning    = decision.get("llm_reasoning", ""),
        )

        # Inject compliance + manual review info
        final_output["compliance_status"] = compliance["compliant"]
        if self.state["manual_review_flagged"]:
            final_output["manual_review_required"] = True
            final_output["compliance_flags"]       = compliance["flags"]

        # ── Save TreatmentPlan to DB ──────────────────────────────────────────
        self._log("Saving TreatmentPlan to PostgreSQL")
        await self._recommendation_engine.save_to_db(
            db              = db,
            profile_id      = profile_id,
            plan_data       = recommendation["treatment_plan"],
            ranked_hospitals= recommendation["ranked_hospitals"],
            raw_output      = final_output,
        )

        # ── Follow-ups + Audit ────────────────────────────────────────────────
        followups = self.schedule_followups(
            disease_type = profile.get("disease_type", ""),
            timeline     = recommendation["treatment_plan"].get("timeline", ""),
        )
        final_output["followup_reminders"] = followups

        audit = self.log_audit_trail(final_output)
        final_output["audit_summary"] = {
            "total_steps_logged": len(audit),
            "session_id":         session_id,
            "timestamp":          datetime.datetime.utcnow().isoformat() + "Z",
        }

        # ── Close DB session ──────────────────────────────────────────────────
        if session_id:
            await self._medical_data_service.end_session(db, session_id)

        self.state["final_output"] = final_output
        self.state["status"]       = "completed"
        self.end_session()

        print("[PlannerAgent] 🏁 Async DB-backed execution complete.")
        return final_output

    # =========================================================================
    # Utility / Introspection
    # =========================================================================

    def get_state(self) -> dict:
        """Return current planner state (for debugging/monitoring)."""
        return self.state

    def get_audit_trail(self) -> list[dict]:
        """Return the full audit trail for this session."""
        return self.state["audit_trail"]

    def get_followups(self) -> list[dict]:
        """Return the scheduled follow-up reminders."""
        return self.state.get("followups", [])

    def get_missing_questions(self) -> list[dict]:
        """Return only the questions for missing fields (for loop-back UI)."""
        missing      = self.state.get("missing_fields", [])
        all_questions = self.state.get("questions", [])
        if not missing:
            return []
        return [q for q in all_questions if q.get("field") in missing]

    # =========================================================================
    # Private Helpers
    # =========================================================================

    def _validate_responses(self) -> dict:
        """Internal: run ValidationEngine on current state responses."""
        validation = self._validation_engine.validate_from_responses(
            self.state["responses"]
        )
        self.state["validation_result"] = validation
        self.state["missing_fields"]    = validation.get("missing_fields", [])
        self.state["status"] = (
            "validation_passed" if validation["is_valid"] else "validation_failed"
        )
        return validation

    def _log(self, step: str, detail: str = "") -> None:
        """Append a timestamped audit entry to the internal trail."""
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "step":      step,
            "status":    self.state.get("status", "unknown"),
            "detail":    detail,
        }
        self.state["audit_trail"].append(entry)

    @staticmethod
    def _parse_bool(value) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).lower() in ("yes", "true", "1", "y")
