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

def api_login(email: str) -> dict:
    """Call POST /api/auth/login."""
    try:
        r = requests.post(f"{BACKEND_IP}/api/auth/login", json={"email": email.strip().lower()}, timeout=30)
        if r.status_code == 404:
            return {"error": "Account not found. Please register."}
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": f"Login failed: {str(e)}"}

def api_register(name: str, email: str, location: str = "") -> dict:
    """Call POST /api/auth/signup."""
    try:
        r = requests.post(f"{BACKEND_IP}/api/auth/signup", json={
            "name": name.strip(),
            "email": email.strip().lower(),
            "location": location.strip()
        }, timeout=30)
        if r.status_code == 409:
            return {"error": "Email already registered."}
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": f"Registration failed: {str(e)}"}

def api_logout(token: str):
    """Call POST /api/auth/logout."""
    try:
        requests.post(f"{BACKEND_IP}/api/auth/logout", json={"access_token": token}, timeout=10)
    except:
        pass

def api_validate_token(token: str):
    """Call GET /api/auth/me."""
    try:
        r = requests.get(f"{BACKEND_IP}/api/auth/me", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def set_auth_session(response: dict):
    """Store auth details in session state."""
    st.session_state["authenticated"] = True
    st.session_state["token"] = response.get("access_token")
    st.session_state["user_id"] = response.get("user_id")
    st.session_state["user_name"] = response.get("name")
    st.session_state["user_email"] = response.get("email")
    st.session_state["session_id"] = response.get("session_id")

def clear_auth_session():
    """Clear session data."""
    for key in ["authenticated", "token", "user_id", "user_name", "user_email", "session_id", "step", "goal", "answers", "result"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

def check_auth_or_redirect():
    """Redirect to login if not authenticated."""
    if not st.session_state.get("authenticated"):
        st.switch_page("pages/login.py")
