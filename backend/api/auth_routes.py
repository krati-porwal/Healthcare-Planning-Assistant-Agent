"""
Auth API Routes
===============
Endpoints:
  POST /api/auth/signup   — Register a new user, issue token, start session
  POST /api/auth/login    — Authenticate an existing user by email, issue token
  POST /api/auth/logout   — Revoke token, end session
  GET  /api/auth/me       — Return current user info from token
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.database import get_db
from backend.db.models import User, UserSession
from backend.auth.token_store import issue_token, validate_token, revoke_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    name: str
    email: str
    location: str = ""
    budget: Optional[float] = None


class LoginRequest(BaseModel):
    email: str


class AuthResponse(BaseModel):
    user_id: str
    session_id: str
    access_token: str
    email: str
    name: str
    message: str


class LogoutRequest(BaseModel):
    access_token: str


# ── Helper: get or create User record ────────────────────────────────────────

async def _get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email.lower().strip()))
    return result.scalar_one_or_none()


async def _create_session_record(db: AsyncSession, user_id: str) -> UserSession:
    session = UserSession(user_id=user_id, goal="pending", status="active")
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


# ── POST /api/auth/signup ─────────────────────────────────────────────────────

@router.post("/signup", response_model=AuthResponse)
async def signup(request: SignupRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.
    If the email already exists, returns the existing user's credentials
    (idempotent signup — academic-friendly).
    """
    email = request.email.lower().strip()
    if not email or not request.name.strip():
        raise HTTPException(status_code=422, detail="Name and email are required.")

    # Check if user already exists
    existing = await _get_user_by_email(db, email)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Email '{email}' is already registered. Please use Login instead."
        )

    # Create new User
    user = User(
        name=request.name.strip(),
        email=email,
        location=request.location.strip() if request.location else "",
        budget=request.budget,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    print(f"[Auth] New user registered: {user.user_id} ({email})")

    # Create session record
    session = await _create_session_record(db, str(user.user_id))

    # Issue token
    token = issue_token(
        user_id=str(user.user_id),
        session_id=str(session.session_id),
        email=email,
    )

    return AuthResponse(
        user_id=str(user.user_id),
        session_id=str(session.session_id),
        access_token=token,
        email=email,
        name=user.name,
        message=f"Welcome, {user.name}! Your account has been created.",
    )


# ── POST /api/auth/login ──────────────────────────────────────────────────────

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticate an existing user by email.
    Returns a fresh access token and starts a new session.
    """
    email = request.email.lower().strip()
    if not email:
        raise HTTPException(status_code=422, detail="Email is required.")

    user = await _get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"No account found for '{email}'. Please sign up first."
        )

    # Create a new session for this login
    session = await _create_session_record(db, str(user.user_id))

    # Issue a fresh token
    token = issue_token(
        user_id=str(user.user_id),
        session_id=str(session.session_id),
        email=email,
    )
    print(f"[Auth] User logged in: {user.user_id} ({email})")

    return AuthResponse(
        user_id=str(user.user_id),
        session_id=str(session.session_id),
        access_token=token,
        email=email,
        name=user.name,
        message=f"Welcome back, {user.name}!",
    )


# ── POST /api/auth/logout ─────────────────────────────────────────────────────

@router.post("/logout")
async def logout(request: LogoutRequest, db: AsyncSession = Depends(get_db)):
    """
    Revoke the access token and mark the session as ended.
    """
    payload = validate_token(request.access_token)
    if payload:
        # End the DB session record
        result = await db.execute(
            select(UserSession).where(
                UserSession.session_id == payload["session_id"]
            )
        )
        db_session = result.scalar_one_or_none()
        if db_session:
            from datetime import datetime
            db_session.end_time = datetime.utcnow()
            db_session.status = "completed"
            await db.commit()

    revoke_token(request.access_token)
    return {"message": "Logged out successfully.", "status": "ok"}


# ── GET /api/auth/me ──────────────────────────────────────────────────────────

@router.get("/me")
async def get_me(authorization: Optional[str] = Header(default=None)):
    """
    Return current user info based on the Bearer token.
    Header format:  Authorization: Bearer <token>
    """
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]

    payload = validate_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    return {
        "user_id":    payload["user_id"],
        "session_id": payload["session_id"],
        "email":      payload["email"],
        "issued_at":  payload["issued_at"],
        "expires_at": payload["expires_at"],
    }
