import streamlit as st
import requests
import os
import sys
import time

# Ensure imports from backend are possible
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Force 127.0.0.1 to avoid Windows DNS resolution issues with 'localhost'
BACKEND_IP = "http://127.0.0.1:8000"


# ── API Functions ────────────────────────────────────────────────────────────

def api_login(email: str, password: str = "") -> dict:
    """Call POST /api/auth/login with email + password (bcrypt verified)."""
    try:
        r = requests.post(
            f"{BACKEND_IP}/api/auth/login",
            json={"email": email.strip().lower(), "password": password},
            timeout=30,
        )
        if r.status_code == 404:
            return {"error": "Account not found. Please register."}
        if r.status_code == 401:
            detail = r.json().get("detail", "Incorrect password.")
            return {"error": str(detail)}
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"error": f"Cannot connect to backend at {BACKEND_IP}. Is FastAPI running?"}
    except Exception as e:
        return {"error": f"Login failed: {str(e)}"}


def api_register(name: str, email: str, password: str = "", location: str = "") -> dict:
    """Call POST /api/auth/signup with password (hashed server-side)."""
    try:
        r = requests.post(
            f"{BACKEND_IP}/api/auth/signup",
            json={
                "name": name.strip(),
                "email": email.strip().lower(),
                "password": password,
                "location": location.strip(),
            },
            timeout=30,
        )
        if r.status_code == 409:
            return {"error": "Email already registered."}
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"error": f"Cannot connect to backend at {BACKEND_IP}. Is FastAPI running?"}
    except Exception as e:
        return {"error": f"Registration failed: {str(e)}"}


def api_logout(token: str):
    """Call POST /api/auth/logout."""
    try:
        requests.post(f"{BACKEND_IP}/api/auth/logout", json={"access_token": token}, timeout=10)
    except Exception:
        pass


def api_validate_token(token: str):
    """Call GET /api/auth/me."""
    try:
        r = requests.get(
            f"{BACKEND_IP}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


# ── Session Helpers ──────────────────────────────────────────────────────────

def set_auth_session(response: dict):
    """Store auth details in session state after successful login/register."""
    st.session_state["authenticated"] = True
    st.session_state["token"] = response.get("access_token")
    st.session_state["user_id"] = response.get("user_id")
    st.session_state["user_name"] = response.get("name")
    st.session_state["user_email"] = response.get("email")
    st.session_state["session_id"] = response.get("session_id")


def clear_auth_session():
    """Clear all auth & planner state and rerun."""
    keys = [
        "authenticated", "token", "user_id", "user_name", "user_email",
        "session_id", "step", "goal", "answers", "result",
        "chat_history", "smart_chat_history",
    ]
    for key in keys:
        st.session_state.pop(key, None)
    st.rerun()


# ── Navigation Guards ────────────────────────────────────────────────────────

def check_auth_or_redirect():
    """Redirect unauthenticated users to Login page. Use at top of protected pages."""
    if not st.session_state.get("authenticated"):
        st.switch_page("pages/2_login.py")


def redirect_if_authenticated():
    """Redirect already-authenticated users to Dashboard. Use at top of auth pages."""
    if st.session_state.get("authenticated"):
        st.switch_page("pages/4_dashboard.py")
