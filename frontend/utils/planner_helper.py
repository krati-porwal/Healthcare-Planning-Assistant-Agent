import streamlit as st
import requests
import json
import time
import os
import sys

# Ensure backend imports are valid
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Force 127.0.0.1 to avoid Windows DNS resolution issues with 'localhost'
BACKEND_IP = "http://127.0.0.1:8000"

def api_start_session(name: str, email: str, location: str, budget: float | None):
    try:
        r = requests.post(f"{BACKEND_IP}/api/session/start", json={
            "name": name, "email": email, "location": location, "budget": budget
        }, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def api_start_plan(session_id: str, user_id: str, goal: str):
    try:
        r = requests.post(f"{BACKEND_IP}/api/plan/start", json={
            "session_id": session_id, "user_id": user_id, "goal": goal
        }, timeout=45)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def api_respond_plan(session_id: str, user_id: str, answers: dict):
    try:
        r = requests.post(f"{BACKEND_IP}/api/plan/respond", json={
            "session_id": session_id, "user_id": user_id, "answers": answers
        }, timeout=90) # Higher timeout for agent logic
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def direct_plan(goal: str, answers: dict) -> dict:
    """Directly call PlannerAgent logic for local mode."""
    try:
        from backend.agents.planner_agent import PlannerAgent
        planner = PlannerAgent()
        planner.receiveGoal(goal)
        planner.decomposeGoal()
        planner.createExecutionPlan()
        result = planner.executePlan(answers)
        return result
    except Exception as e:
        return {"error": str(e)}
