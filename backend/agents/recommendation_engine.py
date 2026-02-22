"""
RecommendationEngine Agent

Responsibilities:
- Generate a structured TreatmentPlan from the DecisionEngine output
- Rank hospitals by priority (rating, budget match, type match)
- Create prioritized hospital recommendation list
- Persist TreatmentPlan and Recommendations to PostgreSQL
"""
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.models import TreatmentPlan, Recommendation, Hospital
from sqlalchemy import select


class RecommendationEngine:
    """
    Generates and ranks treatment plan recommendations from DecisionEngine output.
    """

    def generate_plan(self, decision: dict) -> dict:
        """
        Convert DecisionEngine output into a structured TreatmentPlan dict.

        Args:
            decision: Output from DecisionEngine.analyze()

        Returns:
            Structured treatment plan dict
        """
        treatment_plan = {
            "disease_type": decision.get("disease_type", ""),
            "treatment_type": decision.get("treatment_type", ""),
            "timeline": decision.get("timeline", ""),
            "specialist": decision.get("specialist", ""),
            "required_reports": decision.get("required_reports", []),
            "lab_verification": decision.get("lab_verification", {}),  # Fix 2: lab report cross-reference
            "notes": decision.get("notes", ""),
            "surgery_allowed": decision.get("surgery_allowed", True),
            "patient_area_type": decision.get("patient_area_type", "urban"),
        }

        # Rank hospitals by composite score
        ranked_hospitals = self._rank_hospitals(
            decision.get("suggested_hospitals", []),
            decision.get("hospital_type", "Multi-specialty")
        )

        print(f"[RecommendationEngine] Ranked {len(ranked_hospitals)} hospitals.")
        return {
            "treatment_plan": treatment_plan,
            "ranked_hospitals": ranked_hospitals,
        }

    def _rank_hospitals(self, hospitals: list[dict], required_type: str) -> list[dict]:
        """
        Rank hospitals by a composite score considering type match, rating, and accreditation.

        Args:
            hospitals: List of hospital dicts from DecisionEngine
            required_type: The recommended hospital type (e.g., "Oncology")

        Returns:
            List of ranked hospital dicts with priority_rank added
        """
        scored = []
        for h in hospitals:
            score = 0.0
            # Type match bonus
            if h.get("type") == required_type:
                score += 3.0
            elif h.get("type") == "Multi-specialty":
                score += 1.5

            # Rating score (0-5 scale)
            score += float(h.get("rating", 3.0))

            # Accreditation bonus
            accreditation = h.get("accreditation", "")
            if "JCI" in accreditation:
                score += 1.0
            if "NABH" in accreditation:
                score += 0.5

            scored.append((score, h))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        ranked = []
        for rank, (score, h) in enumerate(scored, start=1):
            ranked.append({
                "name": h.get("name", ""),
                "location": h.get("location", ""),
                "city": h.get("city", ""),
                "state": h.get("state", ""),
                "type": h.get("type", ""),
                "contact": h.get("contact", ""),
                "accreditation": h.get("accreditation", ""),
                "rating": h.get("rating", ""),
                "budget_category": h.get("budget_category", ""),
                "accepts_insurance": h.get("accepts_insurance", True),
                "specializations": h.get("specializations", []),
                "hospital_id": h.get("hospital_id", ""),
                "priority_rank": str(rank),
                "score": round(score, 2),
            })

        return ranked

    async def save_to_db(self, db: AsyncSession, profile_id: str,
                         plan_data: dict, ranked_hospitals: list[dict],
                         raw_output: dict) -> TreatmentPlan:
        """
        Persist the TreatmentPlan and Recommendations to PostgreSQL.

        Args:
            db: Async SQLAlchemy session
            profile_id: The medical profile UUID
            plan_data: The treatment_plan dict
            ranked_hospitals: The ranked hospital list
            raw_output: Full structured JSON output

        Returns:
            The created TreatmentPlan ORM object
        """
        disclaimer = (
            "This is not a medical diagnosis. "
            "Consult a licensed medical professional before making any healthcare decisions."
        )

        plan = TreatmentPlan(
            profile_id=profile_id,
            treatment_type=plan_data.get("treatment_type", ""),
            timeline=plan_data.get("timeline", ""),
            disclaimer=disclaimer,
            notes=plan_data.get("notes", ""),
            raw_output=raw_output,
        )
        db.add(plan)
        await db.flush()

        # Save hospital records (upsert-style: only if not existing)
        for h in ranked_hospitals:
            h_id = h.get("hospital_id")
            if h_id:
                result = await db.execute(
                    select(Hospital).where(Hospital.hospital_id == h_id)
                )
                existing = result.scalar_one_or_none()
                if not existing:
                    hospital_record = Hospital(
                        hospital_id=h_id,
                        name=h.get("name", ""),
                        type=h.get("type", ""),
                        location=h.get("location", ""),
                        city=h.get("city", ""),
                        state=h.get("state", ""),
                        contact=h.get("contact", ""),
                        accreditation=h.get("accreditation", ""),
                        rating=h.get("rating"),
                        budget_category=h.get("budget_category", ""),
                        accepts_insurance=h.get("accepts_insurance", True),
                        specializations=h.get("specializations", []),
                    )
                    db.add(hospital_record)

                rec = Recommendation(
                    plan_id=plan.plan_id,
                    hospital_id=h_id,
                    priority_rank=int(h.get("priority_rank", 1)),
                    reasoning=f"Ranked #{h.get('priority_rank')} based on type match and rating.",
                )
                db.add(rec)

        await db.commit()
        await db.refresh(plan)
        print(f"[RecommendationEngine] Plan {plan.plan_id} saved to DB.")
        return plan
