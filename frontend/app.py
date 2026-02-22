"""
Streamlit Frontend — Healthcare Planning Assistant Agent

Multi-step UI:
  Step 1: User registration + goal input
  Step 2: Answer medical questions
  Step 3: Display structured treatment plan results
"""
import sys
import os

# Ensure the project root (Healthcare-agent/) is on sys.path so that
# `backend` is importable regardless of which directory Streamlit is launched from.
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import json
import time
import streamlit as st
import requests
from backend.config import BACKEND_URL

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Healthcare Planning Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Dark gradient background */
    .main {
        background: linear-gradient(135deg, #0f1724 0%, #1a2744 50%, #0f2235 100%);
        min-height: 100vh;
    }
    .stApp {
        background: linear-gradient(135deg, #0f1724 0%, #1a2744 50%, #0f2235 100%);
    }

    /* Header */
    .hero-header {
        text-align: center;
        padding: 2.5rem 1rem 1.5rem 1rem;
        background: linear-gradient(135deg, rgba(30,58,138,0.6), rgba(15,172,142,0.3));
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 2rem;
        backdrop-filter: blur(10px);
    }
    .hero-header h1 {
        font-size: 2.6rem;
        font-weight: 700;
        background: linear-gradient(90deg, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .hero-header p {
        color: #94a3b8;
        font-size: 1.1rem;
        margin: 0;
    }

    /* Step card */
    .step-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 14px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    .step-card:hover {
        border-color: rgba(96,165,250,0.4);
        background: rgba(255,255,255,0.07);
    }

    /* Step badge */
    .step-badge {
        display: inline-block;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }
    .step-active   { background: rgba(96,165,250,0.2); color: #60a5fa; border: 1px solid #60a5fa44; }
    .step-done     { background: rgba(52,211,153,0.2); color: #34d399; border: 1px solid #34d39944; }
    .step-inactive { background: rgba(148,163,184,0.1); color: #64748b; border: 1px solid #33415544; }

    /* Result cards */
    .result-card {
        background: rgba(15,172,142,0.08);
        border: 1px solid rgba(52,211,153,0.25);
        border-radius: 14px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .hospital-card {
        background: rgba(30,58,138,0.2);
        border: 1px solid rgba(96,165,250,0.2);
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 0.75rem;
        transition: all 0.2s;
    }
    .hospital-card:hover {
        border-color: rgba(96,165,250,0.5);
        background: rgba(30,58,138,0.3);
    }
    .rank-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 2rem;
        height: 2rem;
        border-radius: 50%;
        font-weight: 700;
        font-size: 0.9rem;
        margin-right: 0.5rem;
    }
    .rank-1 { background: #f59e0b22; color: #f59e0b; border: 2px solid #f59e0b; }
    .rank-2 { background: #94a3b822; color: #94a3b8; border: 2px solid #94a3b8; }
    .rank-3 { background: #cd7c2922; color: #cd7c29; border: 2px solid #cd7c29; }
    .rank-n { background: #60a5fa22; color: #60a5fa; border: 2px solid #60a5fa; }

    /* Disclaimer box */
    .disclaimer-box {
        background: rgba(239,68,68,0.08);
        border: 1px solid rgba(239,68,68,0.3);
        border-radius: 10px;
        padding: 1rem 1.25rem;
        margin-top: 1.5rem;
        color: #fca5a5;
        font-size: 0.9rem;
    }

    /* Progress bar */
    .progress-container {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 2rem;
    }
    .progress-step {
        flex: 1;
        height: 6px;
        border-radius: 3px;
    }
    .progress-done       { background: linear-gradient(90deg, #34d399, #059669); }
    .progress-active     { background: linear-gradient(90deg, #60a5fa, #3b82f6); }
    .progress-incomplete { background: rgba(255,255,255,0.1); }

    /* Section titles */
    .section-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 0.75rem;
        border-left: 4px solid #60a5fa;
        padding-left: 0.75rem;
    }

    /* Streamlit overrides */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: rgba(255,255,255,0.07) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 8px !important;
    }
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.6rem 2rem !important;
        transition: all 0.2s !important;
    }
    .stButton > button:first-child {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important;
        border: none !important;
        color: white !important;
    }
    .stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(59,130,246,0.4) !important;
    }
    label { color: #cbd5e1 !important; }
    h2, h3, h4 { color: #e2e8f0 !important; }
    p { color: #94a3b8; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(15,23,42,0.95) !important;
        border-right: 1px solid rgba(255,255,255,0.07);
    }
    [data-testid="stSidebar"] .stMarkdown { color: #94a3b8; }
</style>
""", unsafe_allow_html=True)

# === AUTHENTICATION SECTION START — Auth CSS ===
# Injected after the existing CSS block; uses the same design system (glassmorphism, Inter, dark theme)
st.markdown("""
<style>
    /* User info pill shown in sidebar when authenticated */
    .user-pill {
        background: rgba(52,211,153,0.12);
        border: 1px solid rgba(52,211,153,0.3);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
    }
    .user-pill .user-name { color: #34d399; font-weight: 600; font-size: 0.95rem; }
    .user-pill .user-email { color: #64748b; font-size: 0.8rem; }

    /* Inline alert banners for auth feedback */
    .auth-error {
        background: rgba(239,68,68,0.1);
        border: 1px solid rgba(239,68,68,0.35);
        border-radius: 8px;
        padding: 0.65rem 1rem;
        color: #fca5a5;
        font-size: 0.88rem;
        margin-top: 0.5rem;
    }
    .auth-success {
        background: rgba(52,211,153,0.1);
        border: 1px solid rgba(52,211,153,0.35);
        border-radius: 8px;
        padding: 0.65rem 1rem;
        color: #6ee7b7;
        font-size: 0.88rem;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)
# === AUTHENTICATION SECTION END — Auth CSS ===


# ── Session State Initialization ─────────────────────────────────────────────
def init_session_state():
    defaults = {
        "step": 1,
        "session_id": None,
        "user_id": None,
        "goal": "",
        "questions": [],
        "subtasks": [],
        "execution_plan": {},
        "answers": {},
        "result": None,
        "missing_fields": [],
        "follow_up_questions": [],
        "error": None,
        "use_direct_mode": True,  # Use direct agent call (no DB required)
        # === AUTHENTICATION SECTION START ===
        "token": None,           # JWT/UUID access token from /auth/login or /auth/signup
        "auth_user_id": None,    # Authenticated user ID (separate from planner user_id)
        "auth_email": None,      # Authenticated user email
        "auth_name": None,       # Authenticated user display name
        "authenticated": False,  # Master auth gate flag
        # === AUTHENTICATION SECTION END ===
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session_state()


# ── API Helpers ───────────────────────────────────────────────────────────────
def api_start_session(name: str, email: str, location: str, budget: float | None):
    try:
        r = requests.post(f"{BACKEND_URL}/api/session/start", json={
            "name": name, "email": email, "location": location, "budget": budget
        }, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def api_start_plan(session_id: str, user_id: str, goal: str):
    try:
        r = requests.post(f"{BACKEND_URL}/api/plan/start", json={
            "session_id": session_id, "user_id": user_id, "goal": goal
        }, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def api_respond_plan(session_id: str, user_id: str, answers: dict):
    try:
        r = requests.post(f"{BACKEND_URL}/api/plan/respond", json={
            "session_id": session_id, "user_id": user_id, "answers": answers
        }, timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


# === AUTHENTICATION SECTION START — Auth API Helpers ===

def _extract_error(r: requests.Response, fallback: str) -> str:
    """Extract the 'detail' field from a FastAPI error response, or return fallback."""
    try:
        detail = r.json().get("detail", fallback)
        # detail can be a list of validation errors
        if isinstance(detail, list):
            return "; ".join(str(d.get("msg", d)) for d in detail)
        return str(detail)
    except Exception:
        return fallback


def _check_backend_health() -> bool:
    """Ping GET /health to check if the FastAPI backend is reachable."""
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=4)
        return r.status_code == 200
    except Exception:
        return False


def api_login(email: str) -> dict:
    """
    Call POST /api/auth/login with the given email.
    Returns the AuthResponse dict or a dict with key 'error'.
    Note: The backend currently authenticates by email only (no password hashing
    is stored) — this matches the existing auth_routes.py implementation.
    """
    try:
        r = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            json={"email": email.strip().lower()},
            timeout=10,
        )
        if r.status_code == 404:
            return {"error": "No account found for that email. Please register first."}
        if r.status_code == 422:
            return {"error": _extract_error(r, "Invalid input. Please check your email address.")}
        if r.status_code >= 500:
            return {"error": f"Backend error ({r.status_code}): {_extract_error(r, 'Database may be unavailable. Try Direct Mode.')}"}
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"error": f"Cannot connect to backend at {BACKEND_URL}. Ensure FastAPI is running, or enable Direct Mode in the sidebar."}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out. Backend may be overloaded."}
    except Exception as e:
        return {"error": str(e)}


def api_register(name: str, email: str, location: str = "", budget: float | None = None) -> dict:
    """
    Call POST /api/auth/signup to create a new user account.
    Returns the AuthResponse dict or a dict with key 'error'.
    """
    try:
        r = requests.post(
            f"{BACKEND_URL}/api/auth/signup",
            json={
                "name": name.strip(),
                "email": email.strip().lower(),
                "location": location.strip(),
                "budget": budget,
            },
            timeout=10,
        )
        if r.status_code == 409:
            return {"error": "This email is already registered. Please use Login instead."}
        if r.status_code == 422:
            return {"error": _extract_error(r, "Invalid input. Name and a valid email are required.")}
        if r.status_code >= 500:
            return {"error": f"Backend error ({r.status_code}): {_extract_error(r, 'Database may be unavailable. Try Direct Mode.')}"}
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"error": f"Cannot connect to backend at {BACKEND_URL}. Ensure FastAPI is running, or enable Direct Mode in the sidebar."}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out. Backend may be overloaded."}
    except Exception as e:
        return {"error": str(e)}


def api_logout(token: str) -> dict:
    """
    Call POST /api/auth/logout to revoke the current access token.
    Returns {"status": "ok"} or a dict with key 'error'.
    """
    try:
        r = requests.post(
            f"{BACKEND_URL}/api/auth/logout",
            json={"access_token": token},
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        # Even if logout API fails, we clear local state
        return {"status": "ok", "note": "token revoked locally"}


def api_validate_token(token: str) -> dict | None:
    """
    Call GET /api/auth/me to validate a stored token on page reload.
    Returns the user payload dict or None if the token is invalid/expired.
    """
    try:
        r = requests.get(
            f"{BACKEND_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if r.status_code == 401:
            return None
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _set_auth_state(response: dict) -> None:
    """
    Persist auth data from a login/signup API response into session_state.
    Called after successful login or registration.
    """
    st.session_state["token"]        = response["access_token"]
    st.session_state["auth_user_id"] = response["user_id"]
    st.session_state["auth_email"]   = response["email"]
    st.session_state["auth_name"]    = response["name"]
    st.session_state["authenticated"] = True
    # Also pre-populate planner user_id / session_id for API mode
    st.session_state["user_id"]      = response["user_id"]
    st.session_state["session_id"]   = response["session_id"]


def _clear_auth_state() -> None:
    """
    Clear all auth-related keys from session state (used on logout / restart).
    Planner state is intentionally also cleared so the user starts fresh.
    """
    auth_keys = [
        "token", "auth_user_id", "auth_email", "auth_name", "authenticated",
        "user_id", "session_id", "step", "goal", "questions", "subtasks",
        "execution_plan", "answers", "result", "missing_fields",
        "follow_up_questions", "error", "_planner",
    ]
    for k in auth_keys:
        st.session_state.pop(k, None)

# === AUTHENTICATION SECTION END — Auth API Helpers ===


def direct_plan(goal: str, answers: dict) -> dict:
    """
    Directly call PlannerAgent without going through HTTP (no DB required).
    Used when the backend is not running or for demo mode.
    """
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from backend.agents.planner_agent import PlannerAgent
        planner = PlannerAgent()
        planner.receiveGoal(goal)
        planner.decomposeGoal()
        planner.createExecutionPlan()
        result = planner.executePlan(answers)
        return result
    except Exception as e:
        return {"error": str(e)}


# === AUTHENTICATION SECTION START — Auth Page UI ===

def login_ui() -> None:
    """
    Render the Login form.
    On success: stores token in session_state and reruns to show planner.
    """
    with st.form("login_form", clear_on_submit=False):
        st.markdown("##### 📧 Email Address")
        email = st.text_input(
            "Email", label_visibility="collapsed",
            placeholder="you@example.com", key="login_email"
        )
        # NOTE: The current backend auth_routes.py authenticates by email only.
        # A password field is shown here for UI completeness / future extension.
        st.markdown("##### 🔑 Password")
        password = st.text_input(
            "Password", label_visibility="collapsed",
            type="password", placeholder="••••••••", key="login_password"
        )
        st.caption(
            "ℹ️ This demo uses email-only authentication. "
            "Password validation will be enforced when hashing is added."
        )
        submitted = st.form_submit_button("🔐 Login", use_container_width=True)

    if submitted:
        if not email.strip():
            st.markdown('<div class="auth-error">⚠️ Please enter your email address.</div>',
                        unsafe_allow_html=True)
            return
        with st.spinner("Verifying credentials…"):
            resp = api_login(email)
        if "error" in resp:
            st.markdown(f'<div class="auth-error">❌ {resp["error"]}</div>',
                        unsafe_allow_html=True)
        else:
            _set_auth_state(resp)
            st.markdown('<div class="auth-success">✅ Login successful! Redirecting…</div>',
                        unsafe_allow_html=True)
            time.sleep(0.6)
            st.rerun()


def register_ui() -> None:
    """
    Render the Registration form.
    On success: stores token in session_state and reruns to show planner.
    """
    with st.form("register_form", clear_on_submit=False):
        st.markdown("##### 👤 Full Name")
        name = st.text_input(
            "Full Name", label_visibility="collapsed",
            placeholder="e.g. Arjun Sharma", key="reg_name"
        )
        st.markdown("##### 📧 Email Address")
        email = st.text_input(
            "Email", label_visibility="collapsed",
            placeholder="you@example.com", key="reg_email"
        )
        st.markdown("##### 🔑 Password")
        password = st.text_input(
            "Password", label_visibility="collapsed",
            type="password", placeholder="Min. 8 characters", key="reg_password"
        )
        st.markdown("##### 📍 City / Location _(optional)_")
        location = st.text_input(
            "Location", label_visibility="collapsed",
            placeholder="e.g. Mumbai", key="reg_location"
        )
        submitted = st.form_submit_button("🚀 Create Account", use_container_width=True)

    if submitted:
        if not name.strip() or not email.strip():
            st.markdown('<div class="auth-error">⚠️ Name and email are required.</div>',
                        unsafe_allow_html=True)
            return
        with st.spinner("Creating your account…"):
            resp = api_register(name, email, location)
        if "error" in resp:
            st.markdown(f'<div class="auth-error">❌ {resp["error"]}</div>',
                        unsafe_allow_html=True)
        else:
            _set_auth_state(resp)
            st.success(f"🎉 Welcome, {resp.get('name', 'User')}! Account created.")
            time.sleep(0.8)
            st.rerun()


def render_auth_page() -> None:
    """
    Full-page auth gate shown when the user is not authenticated.
    Provides Login and Register tabs side by side with a backend health banner.
    """
    # Hero banner (reuse existing CSS class)
    st.markdown("""
<div class="hero-header">
    <h1>🏥 Healthcare Planning Assistant</h1>
    <p>AI-powered treatment planning · Secure · Multi-agent architecture</p>
</div>
""", unsafe_allow_html=True)

    # ── Backend health status banner ──────────────────────────────────────────
    backend_ok = _check_backend_health()
    if backend_ok:
        st.markdown(
            f'<div style="text-align:center; margin-bottom:1rem;">'
            f'<span style="background:rgba(52,211,153,0.15);border:1px solid rgba(52,211,153,0.4);'
            f'color:#34d399;padding:0.35rem 1rem;border-radius:20px;font-size:0.85rem;">'
            f'🟢 Backend connected ({BACKEND_URL})</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div style="text-align:center; margin-bottom:0.5rem;">'
            f'<span style="background:rgba(239,68,68,0.12);border:1px solid rgba(239,68,68,0.4);'
            f'color:#fca5a5;padding:0.35rem 1rem;border-radius:20px;font-size:0.85rem;">'
            f'🔴 Backend offline ({BACKEND_URL})</span></div>',
            unsafe_allow_html=True,
        )
        st.warning(
            "⚠️ **FastAPI backend is not reachable.** "
            "To use authentication, start the backend with:\n\n"
            "```\nuvicorn backend.main:app --reload --port 8000\n```\n\n"
            "Or **enable Direct Mode** in the sidebar to skip login and use the planner locally."
        )

    # Centre the auth card using columns
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("")
        tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register"])
        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            login_ui()
            st.caption("Don't have an account? Switch to the **Register** tab above.")
        with tab_register:
            st.markdown("<br>", unsafe_allow_html=True)
            register_ui()
            st.caption("Already registered? Switch to the **Login** tab above.")

# === AUTHENTICATION SECTION END — Auth Page UI ===


# ── Progress Indicator ────────────────────────────────────────────────────────
def render_progress():
    step = st.session_state.step
    steps_labels = ["Profile & Goal", "Medical Questions", "Your Plan"]
    html = '<div class="progress-container">'
    for i, label in enumerate(steps_labels, start=1):
        if i < step:
            cls = "progress-done"
        elif i == step:
            cls = "progress-active"
        else:
            cls = "progress-incomplete"
        html += f'<div class="progress-step {cls}" title="{label}"></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    for col, label, i in zip([col1, col2, col3], steps_labels, [1, 2, 3]):
        with col:
            if i < step:
                badge = f'<span class="step-badge step-done">✓ {label}</span>'
            elif i == step:
                badge = f'<span class="step-badge step-active">● {label}</span>'
            else:
                badge = f'<span class="step-badge step-inactive">○ {label}</span>'
            st.markdown(badge, unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("## 🏥 Healthcare Agent")
        st.markdown("---")

        # === AUTHENTICATION SECTION START — Sidebar Auth Info ===
        if st.session_state.get("authenticated"):
            name  = st.session_state.get("auth_name", "User")
            email = st.session_state.get("auth_email", "")
            st.markdown(
                f'<div class="user-pill">'
                f'<div class="user-name">👤 {name}</div>'
                f'<div class="user-email">{email}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button("🚪 Logout", use_container_width=True, key="sidebar_logout"):
                token = st.session_state.get("token")
                if token:
                    api_logout(token)   # Revoke token on server
                _clear_auth_state()    # Wipe local session
                st.rerun()
            st.markdown("---")
        # === AUTHENTICATION SECTION END — Sidebar Auth Info ===

        st.markdown("**Multi-Agent Architecture**")
        st.markdown("""
- 🧠 **PlannerAgent** — Orchestrator
- ❓ **QuestionService** — Data Collection
- 🗄️ **MedicalDataService** — Storage
- ✅ **ValidationEngine** — Checks
- 🔍 **DecisionEngine** — Gemini AI
- 🏆 **RecommendationEngine** — Ranking
- 📋 **ExplanationEngine** — Output
        """)
        st.markdown("---")
        st.markdown("**Supported Conditions**")
        st.markdown("""
- 🎗️ Breast Cancer
- 🫁 Lung Cancer
- 💊 Diabetes
- ❤️ Heart Disease
- 🩺 Kidney Disease
        """)
        st.markdown("---")

        mode = st.checkbox(
            "🔗 Use Direct Mode (no DB)",
            value=st.session_state.use_direct_mode,
            help="Calls agents directly without PostgreSQL. Use this if DB is not configured."
        )
        st.session_state.use_direct_mode = mode

        if st.button("🔄 Restart", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.markdown("---")
        st.caption("⚕️ For educational purposes only. Always consult a licensed physician.")


# ── Step 1: Profile & Goal ───────────────────────────────────────────────────
def render_step1():
    st.markdown("""
<div class="hero-header">
    <h1>🏥 Healthcare Planning Assistant</h1>
    <p>AI-powered treatment planning · Multi-agent architecture · Gemini LLM</p>
</div>
""", unsafe_allow_html=True)

    render_progress()

    with st.form("step1_form"):
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">👤 Your Information</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", placeholder="e.g. Arjun Sharma", key="s1_name")
            email = st.text_input("Email Address", placeholder="arjun@example.com", key="s1_email")
        with col2:
            location = st.text_input("Your City / Location", placeholder="e.g. Mumbai", key="s1_location")
            budget = st.number_input(
                "Approximate Treatment Budget (₹)",
                min_value=0, max_value=10000000, value=0, step=10000,
                help="Enter 0 if you are unsure. This helps filter hospitals.",
                key="s1_budget"
            )

        st.markdown('<div class="section-title" style="margin-top:1.5rem;">🎯 Your Healthcare Goal</div>', unsafe_allow_html=True)
        goal = st.text_area(
            "Describe your healthcare need",
            placeholder='e.g. "I want treatment options for breast cancer Stage II"\n"I need guidance for managing Type 2 Diabetes"\n"I have heart disease and need hospital recommendations"',
            height=120,
            key="s1_goal"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        submitted = st.form_submit_button("🚀 Get My Questions →", use_container_width=True)

    if submitted:
        if not name.strip() or not email.strip() or not goal.strip():
            st.error("⚠️ Please fill in your name, email, and healthcare goal.")
            return

        with st.spinner("🤖 PlannerAgent is decomposing your goal and generating questions..."):
            time.sleep(0.5)

            if st.session_state.use_direct_mode:
                # Direct mode: skip HTTP session creation
                import uuid as _uuid
                st.session_state.session_id = str(_uuid.uuid4())
                st.session_state.user_id    = str(_uuid.uuid4())
                # Store city for hospital location ranking (Fix 4)
                st.session_state.patient_city = location.strip()

                # Generate questions via direct agent call
                import sys, os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
                from backend.agents.planner_agent import PlannerAgent
                from backend.agents.question_service import QuestionService

                planner = PlannerAgent()
                planner.receiveGoal(goal)
                subtasks = planner.decomposeGoal()
                execution_plan = planner.createExecutionPlan()
                questions = planner.generateQuestions()

                # Cache planner in session state
                st.session_state._planner = planner
                st.session_state.questions = questions
                st.session_state.subtasks = subtasks
                st.session_state.execution_plan = execution_plan
                st.session_state.goal = goal
                st.session_state.step = 2
                st.rerun()
            else:
                # API mode: go through FastAPI backend
                sess_resp = api_start_session(name, email, location, budget if budget > 0 else None)
                if "error" in sess_resp:
                    st.error(f"Backend error: {sess_resp['error']}. Try enabling Direct Mode in the sidebar.")
                    return

                st.session_state.session_id = sess_resp["session_id"]
                st.session_state.user_id = sess_resp["user_id"]

                plan_resp = api_start_plan(
                    st.session_state.session_id,
                    st.session_state.user_id,
                    goal
                )
                if "error" in plan_resp:
                    st.error(f"Backend error: {plan_resp['error']}")
                    return

                st.session_state.questions = plan_resp.get("questions", [])
                st.session_state.subtasks = plan_resp.get("subtasks", [])
                st.session_state.execution_plan = plan_resp.get("execution_plan", {})
                st.session_state.goal = goal
                st.session_state.step = 2
                st.rerun()


# ── Step 2: Medical Questions ────────────────────────────────────────────────
def render_step2():
    render_progress()

    st.markdown(f"""
<div class="step-card">
    <div class="step-badge step-active">Step 2 — Medical Questions</div>
    <b>Goal:</b> <span style="color:#60a5fa">{st.session_state.goal}</span>
</div>
""", unsafe_allow_html=True)

    # Show execution plan subtasks in expander
    with st.expander("🔍 View Agent Execution Plan", expanded=False):
        st.markdown("**PlannerAgent decomposed your goal into:**")
        for task in st.session_state.subtasks:
            st.markdown(f"  {task}")
        if st.session_state.execution_plan:
            st.markdown("**Agent Pipeline:**")
            for agent_step in st.session_state.execution_plan.get("agents", []):
                st.markdown(f"  **Step {agent_step['step']}** → `{agent_step['agent']}`: {agent_step['task']}")

    questions = st.session_state.questions
    if st.session_state.missing_fields:
        questions = [q for q in questions if q.get("field") in st.session_state.missing_fields]
        st.warning(f"⚠️ Some required fields were missing. Please fill these in: **{', '.join(st.session_state.missing_fields)}**")

    st.markdown('<div class="section-title">📋 Please answer the following medical questions</div>', unsafe_allow_html=True)

    with st.form("step2_form"):
        answers = {}
        previous_answers = st.session_state.answers

        # Group into columns for better UX
        for i, q in enumerate(questions):
            field = q.get("field", f"field_{i}")
            question_text = q.get("question", "")
            required = q.get("required", False)
            default_val = previous_answers.get(field, "")
            label = f"{'**' if required else ''}{question_text}{'**' if required else ''}" + (" _(required)_" if required else "")

            # Render appropriate input types
            if field == "surgery_allowed":
                val = st.selectbox(
                    f"{'🔴' if required else '🔵'} {question_text}",
                    options=["yes", "no"],
                    index=0 if default_val in ("yes", True) else 1,
                    key=f"q_{field}"
                )
            elif field == "patient_area_type":
                val = st.selectbox(
                    f"{'🔴' if required else '🔵'} {question_text}",
                    options=["urban", "rural", "remote"],
                    index=0,
                    key=f"q_{field}"
                )
            elif field == "location_type":
                val = st.selectbox(
                    f"{'🔴' if required else '🔵'} {question_text}",
                    options=["national", "local", "international"],
                    index=0,
                    key=f"q_{field}"
                )
            elif field == "hospital_preference":
                val = st.selectbox(
                    f"{'🔴' if required else '🔵'} {question_text}",
                    options=["private", "government", "any"],
                    index=0,
                    key=f"q_{field}"
                )
            elif field == "gender":
                val = st.selectbox(
                    f"{'🔴' if required else '🔵'} {question_text}",
                    options=["Male", "Female", "Other", "Prefer not to say"],
                    index=0,
                    key=f"q_{field}"
                )
            elif field == "budget_limit":
                val = st.number_input(
                    f"{'🔴' if required else '🔵'} {question_text}",
                    min_value=0, max_value=10000000,
                    value=int(default_val) if default_val else 300000,
                    step=10000,
                    key=f"q_{field}"
                )
                val = str(val)
            elif field == "age":
                val = st.number_input(
                    f"{'🔴' if required else '🔵'} {question_text}",
                    min_value=1, max_value=120,
                    value=int(default_val) if default_val else 45,
                    key=f"q_{field}"
                )
                val = str(val)
            elif field in ("medical_history", "symptoms"):
                val = st.text_area(
                    f"{'🔴' if required else '🔵'} {question_text}",
                    value=default_val,
                    height=100,
                    placeholder="Describe in detail...",
                    key=f"q_{field}"
                )
            else:
                val = st.text_input(
                    f"{'🔴' if required else '🔵'} {question_text}",
                    value=default_val,
                    key=f"q_{field}"
                )

            if val is not None and str(val).strip():
                answers[field] = val

        submitted = st.form_submit_button("🧠 Generate My Treatment Plan →", use_container_width=True)

    if submitted:
        # Merge with previously answered fields
        merged_answers = {**st.session_state.answers, **answers}
        st.session_state.answers = merged_answers

        with st.spinner("⚙️ Agents are processing your medical profile... (this may take 15-30 seconds)"):
            if st.session_state.use_direct_mode:
                planner = st.session_state.get("_planner")
                if not planner:
                    from backend.agents.planner_agent import PlannerAgent
                    planner = PlannerAgent()
                    planner.receiveGoal(st.session_state.goal)
                    planner.decomposeGoal()
                    planner.createExecutionPlan()

                # Inject patient city from Step 1 so hospital ranking uses it (Fix 4)
                patient_city = getattr(st.session_state, "patient_city", "") or ""
                if patient_city:
                    merged_answers["patient_city"] = patient_city

                result = planner.executePlan(merged_answers)
            else:
                result = api_respond_plan(
                    st.session_state.session_id,
                    st.session_state.user_id,
                    merged_answers
                )

        if "error" in result:
            st.error(f"❌ Error: {result['error']}")
            return

        # Handle loop-back scenario
        if result.get("status") == "needs_more_data":
            st.session_state.missing_fields = result.get("missing_fields", [])
            st.session_state.follow_up_questions = result.get("follow_up_questions", [])
            st.warning(f"⚠️ Still missing: **{', '.join(result['missing_fields'])}**. Please fill in the highlighted fields.")
            st.rerun()

        # Success
        final = result.get("result", result)  # API vs direct mode
        st.session_state.result = final
        st.session_state.missing_fields = []
        st.session_state.step = 3
        st.rerun()


# ── Step 3: Results Display ───────────────────────────────────────────────────
def render_step3():
    render_progress()
    result = st.session_state.result

    if not result:
        st.error("No result found. Please restart.")
        return

    # ── Header ──────────────────────────────────────────────────────────────
    st.markdown("""
<div style="text-align:center; padding: 1.5rem 0 2rem 0;">
    <h2 style="color:#34d399; font-size:2rem;">✅ Your Treatment Plan is Ready</h2>
    <p style="color:#94a3b8;">Generated by the Healthcare Planning Assistant Agent</p>
</div>
""", unsafe_allow_html=True)

    # ── Treatment Plan ───────────────────────────────────────────────────────
    tp = result.get("treatment_plan", {})
    st.markdown('<div class="section-title">💊 Recommended Treatment Plan</div>', unsafe_allow_html=True)
    st.markdown('<div class="result-card">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**🔬 Disease Type**  \n{tp.get('disease_type', '—')}")
        st.markdown(f"**💉 Treatment Type**  \n{tp.get('treatment_type', '—')}")
    with col2:
        st.markdown(f"**⏱️ Timeline**  \n{tp.get('timeline', '—')}")
        st.markdown(f"**👨‍⚕️ Specialist**  \n{tp.get('specialist', '—')}")

    if tp.get("required_reports"):
        st.markdown("**📋 Required Reports**")
        cols = st.columns(min(len(tp["required_reports"]), 4))
        for i, report in enumerate(tp["required_reports"]):
            with cols[i % 4]:
                st.markdown(f"<span style='background:rgba(96,165,250,0.15);color:#60a5fa;padding:4px 10px;border-radius:6px;font-size:0.85rem;display:inline-block'>{report}</span>", unsafe_allow_html=True)

    if tp.get("notes"):
        st.info(f"📝 {tp.get('notes')}")

    # ── Lab Verification ──────────────────────────────────────────────────
    lab_v = tp.get("lab_verification")
    if not lab_v:  # may also be nested in result directly
        lab_v = result.get("lab_verification")
    if lab_v:
        st.markdown('<div class="section-title">🧪 Lab Report Verification</div>', unsafe_allow_html=True)
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        note = lab_v.get("note", "")
        completed = lab_v.get("completed", [])
        pending   = lab_v.get("pending", [])
        if completed:
            st.success(f"✅ Already done ({len(completed)}): {', '.join(completed)}")
        if pending:
            st.warning(f"⏳ Still needed ({len(pending)}): {', '.join(pending)}")
        if note:
            st.info(f"📋 {note}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Hospitals ────────────────────────────────────────────────────────────
    hospitals = result.get("recommended_hospitals", [])
    if hospitals:
        st.markdown('<div class="section-title">🏥 Recommended Hospitals</div>', unsafe_allow_html=True)
        for h in hospitals:
            rank = int(h.get("priority_rank", 99))
            rank_class = {1: "rank-1", 2: "rank-2", 3: "rank-3"}.get(rank, "rank-n")
            rank_icon = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")

            st.markdown(f'<div class="hospital-card">', unsafe_allow_html=True)
            hcol1, hcol2, hcol3 = st.columns([3, 2, 1])
            with hcol1:
                st.markdown(f"**{rank_icon} {h.get('name', '')}**")
                st.caption(f"📍 {h.get('location', '')} &nbsp;|&nbsp; 🏷️ {h.get('type', '')}")
            with hcol2:
                st.markdown(f"⭐ **{h.get('rating', '—')}** &nbsp;|&nbsp; 💰 {h.get('budget_category', '—')}")
                st.caption(f"🏅 {h.get('accreditation', '—')}")
            with hcol3:
                st.markdown(f"📞 {h.get('contact', '—')}")
            st.markdown('</div>', unsafe_allow_html=True)

    # ── Explanation ──────────────────────────────────────────────────────────
    explanation = result.get("explanation", "")
    if explanation:
        st.markdown('<div class="section-title">🧠 Clinical Explanation</div>', unsafe_allow_html=True)
        st.markdown(f"""
<div class="step-card">
    <p style="color:#cbd5e1;line-height:1.8;">{explanation}</p>
</div>
""", unsafe_allow_html=True)

    # ── Disclaimer ───────────────────────────────────────────────────────────
    disclaimer = result.get("disclaimer", "This is not a medical diagnosis. Consult a licensed medical professional.")
    st.markdown(f'<div class="disclaimer-box">⚕️ <strong>Medical Disclaimer:</strong> {disclaimer}</div>', unsafe_allow_html=True)

    # ── Raw JSON Output ──────────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("📄 View Raw JSON Output (Structured Format)", expanded=False):
        st.json(result)
        st.download_button(
            label="⬇️ Download Plan as JSON",
            data=json.dumps(result, indent=2),
            file_name="healthcare_plan.json",
            mime="application/json",
        )

    # ── Action buttons ───────────────────────────────────────────────────────
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Start New Plan", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    with col2:
        if st.button("✏️ Modify Answers", use_container_width=True):
            st.session_state.step = 2
            st.rerun()


# ── Main ─────────────────────────────────────────────────────────────────────
render_sidebar()

# === AUTHENTICATION SECTION START — Auth Gate ===
# If the user has a stored token from a previous login (e.g., page reload),
# silently re-validate it against the backend before re-granting access.
# This prevents stale/expired tokens from granting access across server restarts.
if not st.session_state.get("authenticated") and st.session_state.get("token"):
    payload = api_validate_token(st.session_state["token"])
    if payload:
        # Token is still valid — restore auth state without showing login page
        st.session_state["authenticated"] = True
        st.session_state["auth_user_id"]  = payload.get("user_id")
        st.session_state["auth_email"]    = payload.get("email")
        # auth_name not returned by /me endpoint; keep whatever is stored
    else:
        # Token has expired or backend restarted — clear it and show login
        st.session_state.pop("token", None)
        st.session_state["authenticated"] = False

if not st.session_state.get("authenticated"):
    # ── NOT AUTHENTICATED: show Login / Register page ────────────────────────
    # The planner pipeline is completely hidden until the user logs in.
    # Direct-mode users who don't want auth can toggle it off via the sidebar
    # checkbox, which bypasses the gate by immediately setting authenticated=True.
    if st.session_state.get("use_direct_mode"):
        # Direct mode shortcut: skip auth gate entirely (no DB / no backend required)
        st.session_state["authenticated"] = True
        st.session_state["auth_name"]     = "Demo User"
        st.session_state["auth_email"]    = "demo@local"
        st.session_state["auth_user_id"]  = "demo"
        st.rerun()
    else:
        render_auth_page()
        st.stop()   # Prevent any planner code from rendering below
else:
    # ── AUTHENTICATED: run the normal planner UI ─────────────────────────────
    step = st.session_state.step
    if step == 1:
        render_step1()
    elif step == 2:
        render_step2()
    elif step == 3:
        render_step3()
# === AUTHENTICATION SECTION END — Auth Gate ===
