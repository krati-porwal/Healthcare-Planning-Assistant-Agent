"""
ValidationEngine Agent

Responsibilities:
- Validate completeness of the MedicalProfile
- Validate constraint logic (budget, location)
- Verify required reports are mentioned
- Signal if data is incomplete (so PlannerAgent can loop back to QuestionService)
"""

# Required fields for a valid MedicalProfile
REQUIRED_FIELDS = [
    "disease_type",
    "stage",
    "age",
    "gender",
    "medical_history",
    "symptoms",
    "surgery_allowed",
]

# Required constraint fields
REQUIRED_CONSTRAINT_FIELDS = [
    "budget_limit",
    "location_type",
]

VALID_LOCATION_TYPES = {"local", "national", "international"}
VALID_HOSPITAL_PREFERENCES = {"government", "private", "any"}


class ValidationEngine:
    """
    Validates MedicalProfile data completeness and constraint logic.
    Returns validation status and a list of missing/invalid fields.
    """

    def validate(self, profile: dict, constraint: dict) -> dict:
        """
        Perform full validation of a medical profile and its constraints.

        Args:
            profile: Dict with MedicalProfile fields
            constraint: Dict with Constraint fields

        Returns:
            Dict with keys:
              - is_valid (bool)
              - missing_fields (list of str)
              - warnings (list of str)
              - errors (list of str)
        """
        missing_fields = []
        warnings = []
        errors = []

        # ── Profile completeness check ────────────────────────────────────────
        for field in REQUIRED_FIELDS:
            value = profile.get(field)
            if value is None or str(value).strip() == "":
                missing_fields.append(field)

        # ── Constraint completeness check ─────────────────────────────────────
        for field in REQUIRED_CONSTRAINT_FIELDS:
            value = constraint.get(field)
            if value is None or str(value).strip() == "":
                missing_fields.append(field)

        # ── Constraint logic validation ───────────────────────────────────────
        location_type = str(constraint.get("location_type", "")).lower()
        if location_type and location_type not in VALID_LOCATION_TYPES:
            warnings.append(
                f"Invalid location_type '{location_type}'. Expected: {VALID_LOCATION_TYPES}. Defaulting to 'national'."
            )

        hospital_pref = str(constraint.get("hospital_preference", "")).lower()
        if hospital_pref and hospital_pref not in VALID_HOSPITAL_PREFERENCES:
            warnings.append(
                f"Invalid hospital_preference '{hospital_pref}'. Expected: {VALID_HOSPITAL_PREFERENCES}. Defaulting to 'private'."
            )

        budget = constraint.get("budget_limit")
        if budget is not None:
            try:
                budget_val = float(budget)
                if budget_val <= 0:
                    errors.append("budget_limit must be a positive number.")
            except (ValueError, TypeError):
                errors.append(f"budget_limit '{budget}' is not a valid number.")

        # ── Surgery logic check ───────────────────────────────────────────────
        surgery_allowed = profile.get("surgery_allowed")
        disease_stage = str(profile.get("stage", "")).lower()
        if surgery_allowed is False and "stage iv" in disease_stage:
            warnings.append(
                "Surgery is not allowed, but Stage IV may require urgent intervention. "
                "Please confirm constraint with a medical professional."
            )

        is_valid = len(missing_fields) == 0 and len(errors) == 0

        result = {
            "is_valid": is_valid,
            "missing_fields": missing_fields,
            "warnings": warnings,
            "errors": errors,
        }

        if is_valid:
            print("[ValidationEngine] Profile is valid.")
        else:
            print(f"[ValidationEngine] Validation failed. Missing: {missing_fields}, Errors: {errors}")

        return result

    def validate_from_responses(self, responses: dict) -> dict:
        """
        Convenience method: validate directly from the raw responses dict.
        Maps responses to profile/constraint format before validating.
        """
        profile = {
            "disease_type": responses.get("disease_type"),
            "stage": responses.get("stage"),
            "age": responses.get("age"),
            "gender": responses.get("gender"),
            "medical_history": responses.get("medical_history"),
            "symptoms": responses.get("symptoms"),
            "surgery_allowed": responses.get("surgery_allowed"),
        }
        constraint = {
            "budget_limit": responses.get("budget_limit"),
            "location_type": responses.get("location_type"),
            "hospital_preference": responses.get("hospital_preference"),
        }
        return self.validate(profile, constraint)
