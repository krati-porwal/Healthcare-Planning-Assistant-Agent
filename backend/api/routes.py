"""
FastAPI API Routes for the Healthcare Planning Assistant Agent.

Endpoints:
  POST /api/session/start      - Start a new user session
  POST /api/plan/start         - Submit goal and generate questions
  POST /api/plan/respond       - Submit answers and execute the plan
  GET  /api/plan/{session_id}  - Get the final treatment plan
  GET  /health                 - Health check
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.database import get_db

router = APIRouter()
# In-memory store for PlannerAgent instances (one per session)
_planner_sessions = {}  # Store as generic dict to avoid early import
_plan_results: dict[str, dict] = {}


# ── Pydantic Request/Response Models ─────────────────────────────────────────

class SessionStartRequest(BaseModel):
    name: str
    email: str
    location: str = ""
    budget: float | None = None


class SessionStartResponse(BaseModel):
    session_id: str
    user_id: str
    message: str


class PlanStartRequest(BaseModel):
    session_id: str
    user_id: str
    goal: str


class PlanStartResponse(BaseModel):
    session_id: str
    status: str
    questions: list[dict]
    subtasks: list[str]
    execution_plan: dict


class PlanRespondRequest(BaseModel):
    session_id: str
    user_id: str
    answers: dict


class PlanRespondResponse(BaseModel):
    session_id: str
    status: str
    result: dict | None = None
    missing_fields: list[str] | None = None
    follow_up_questions: list[dict] | None = None
    message: str = ""


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/api/session/start", response_model=SessionStartResponse, tags=["Session"])
async def start_session(request: SessionStartRequest, db: AsyncSession = Depends(get_db)):
    """Create a new user and session in PostgreSQL."""
    from backend.agents.medical_data_service import MedicalDataService
    svc = MedicalDataService()
    user = await svc.get_or_create_user(
        db=db,
        name=request.name,
        email=request.email,
        location=request.location,
        budget=request.budget
    )
    session = await svc.create_session(db=db, user_id=user.user_id, goal="pending")
    return SessionStartResponse(
        session_id=session.session_id,
        user_id=user.user_id,
        message="Session started successfully."
    )


@router.post("/api/plan/start", response_model=PlanStartResponse, tags=["Planning"])
async def start_plan(request: PlanStartRequest):
    """
    Initialise the PlannerAgent for a session, decompose the goal,
    and return generated medical questions.
    """
    from backend.agents.planner_agent import PlannerAgent
    planner = PlannerAgent()

    # Phase 1-3: receive goal, decompose, create plan
    planner.receiveGoal(request.goal)
    subtasks = planner.decomposeGoal()
    execution_plan = planner.createExecutionPlan()

    # Phase 4: generate questions
    questions = planner.generateQuestions()

    # Store planner instance by session
    _planner_sessions[request.session_id] = planner

    return PlanStartResponse(
        session_id=request.session_id,
        status="questions_ready",
        questions=questions,
        subtasks=subtasks,
        execution_plan=execution_plan,
    )


@router.post("/api/plan/respond", response_model=PlanRespondResponse, tags=["Planning"])
async def respond_to_plan(request: PlanRespondRequest, db: AsyncSession = Depends(get_db)):
    """
    Submit user answers. Executes the full agent pipeline.
    If data is incomplete, returns missing fields and follow-up questions.
    """
    planner = _planner_sessions.get(request.session_id)
    if not planner:
        raise HTTPException(status_code=404, detail="Session not found. Please call /api/plan/start first.")

    # Execute full pipeline with DB persistence
    result = await planner.executePlanWithDB(
        answers=request.answers,
        db=db,
        user_id=request.user_id,
        session_id=request.session_id,
    )

    # Handle loop-back scenario
    if result.get("status") == "needs_more_data":
        follow_up_questions = planner.get_missing_questions()
        return PlanRespondResponse(
            session_id=request.session_id,
            status="needs_more_data",
            missing_fields=result.get("missing_fields", []),
            follow_up_questions=follow_up_questions,
            message=result.get("message", ""),
        )

    # Store result
    _plan_results[request.session_id] = result

    return PlanRespondResponse(
        session_id=request.session_id,
        status="completed",
        result=result,
        message="Treatment plan generated successfully.",
    )


@router.get("/api/plan/{session_id}", tags=["Planning"])
async def get_plan(session_id: str):
    """Retrieve the final treatment plan for a session."""
    result = _plan_results.get(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Plan not found for this session.")
    return {"session_id": session_id, "status": "completed", "result": result}


@router.get("/health", tags=["Health"])
async def health_check():
    """Basic health check."""
    return {"status": "healthy", "service": "Healthcare Planning Assistant Agent"}
