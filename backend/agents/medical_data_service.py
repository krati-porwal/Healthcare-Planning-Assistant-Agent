"""
MedicalDataService Agent

Responsibilities:
- Map collected user responses to a structured MedicalProfile entity
- Store the medical profile in PostgreSQL
- Fetch existing profiles by user_id or profile_id
"""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.models import MedicalProfile, Constraint, User, UserSession


class MedicalDataService:
    """
    Manages medical profile data: mapping, storing, and fetching from PostgreSQL.
    """

    def map_responses_to_profile(self, user_id: str, responses: dict) -> dict:
        """
        Map raw user question responses to MedicalProfile fields.

        Args:
            user_id: The user's UUID
            responses: Dict of field -> answer from QuestionService

        Returns:
            Dict suitable for creating a MedicalProfile ORM object
        """
        # Parse surgery_allowed from text to bool
        surgery_raw = responses.get("surgery_allowed", "yes")
        if isinstance(surgery_raw, bool):
            surgery_allowed = surgery_raw
        else:
            surgery_allowed = str(surgery_raw).lower() in ("yes", "true", "1", "y")

        # Parse age to int
        try:
            age = int(responses.get("age", 0))
        except (ValueError, TypeError):
            age = None

        profile_data = {
            "user_id": user_id,
            "disease_type": responses.get("disease_type", ""),
            "cancer_type": responses.get("cancer_type", responses.get("disease_type", "")),
            "stage": responses.get("stage", ""),
            "medical_history": responses.get("medical_history", ""),
            "surgery_allowed": surgery_allowed,
            "age": age,
            "gender": responses.get("gender", ""),
            "symptoms": responses.get("symptoms", ""),
        }

        constraint_data = {
            "budget_limit": self._parse_budget(responses.get("budget_limit")),
            "location_type": responses.get("location_type", "national"),
            "hospital_preference": responses.get("hospital_preference", "private"),
        }

        print(f"[MedicalDataService] Mapped profile for user {user_id}.")
        return {"profile": profile_data, "constraint": constraint_data}

    def _parse_budget(self, value) -> float | None:
        """Parse budget value to float."""
        if value is None:
            return None
        try:
            cleaned = str(value).replace(",", "").replace("INR", "").strip()
            return float(cleaned)
        except (ValueError, TypeError):
            return None

    async def store_profile(self, db: AsyncSession, user_id: str, responses: dict) -> MedicalProfile:
        """
        Create and persist a MedicalProfile (and its Constraint) from user responses.

        Args:
            db: Async SQLAlchemy session
            user_id: The user's UUID
            responses: Dict of question field -> answer

        Returns:
            The newly created MedicalProfile ORM instance
        """
        mapped = self.map_responses_to_profile(user_id, responses)
        profile_data = mapped["profile"]
        constraint_data = mapped["constraint"]

        # Create MedicalProfile
        profile = MedicalProfile(**profile_data)
        db.add(profile)
        await db.flush()  # get profile_id before commit

        # Create associated Constraint
        constraint = Constraint(profile_id=profile.profile_id, **constraint_data)
        db.add(constraint)

        await db.commit()
        await db.refresh(profile)
        print(f"[MedicalDataService] Profile {profile.profile_id} stored in DB.")
        return profile

    async def fetch_profile(self, db: AsyncSession, profile_id: str) -> MedicalProfile | None:
        """Fetch a MedicalProfile by profile_id."""
        result = await db.execute(
            select(MedicalProfile).where(MedicalProfile.profile_id == profile_id)
        )
        return result.scalar_one_or_none()

    async def fetch_user_profiles(self, db: AsyncSession, user_id: str) -> list[MedicalProfile]:
        """Fetch all MedicalProfiles for a given user."""
        result = await db.execute(
            select(MedicalProfile).where(MedicalProfile.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_or_create_user(self, db: AsyncSession, name: str, email: str,
                                  location: str = "", budget: float = None) -> User:
        """Get an existing user by email or create a new one."""
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            user = User(name=name, email=email, location=location, budget=budget)
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print(f"[MedicalDataService] Created new user {user.user_id}.")
        return user

    async def create_session(self, db: AsyncSession, user_id: str, goal: str) -> UserSession:
        """Create a new UserSession."""
        session = UserSession(user_id=user_id, goal=goal)
        db.add(session)
        await db.commit()
        await db.refresh(session)
        print(f"[MedicalDataService] Session {session.session_id} created.")
        return session

    async def end_session(self, db: AsyncSession, session_id: str) -> None:
        """Mark a session as completed."""
        result = await db.execute(
            select(UserSession).where(UserSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            session.end_time = datetime.utcnow()
            session.status = "completed"
            await db.commit()
