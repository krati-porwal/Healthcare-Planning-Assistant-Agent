"""
Main entry point — Streamlit Multi-Page App Router.
Run: streamlit run frontend/main.py
"""
import streamlit as st
import os
import sys

# Ensure the frontend and project root are in the Python path for modular imports
_frontend_root = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_frontend_root)
if _frontend_root not in sys.path:
    sys.path.insert(0, _frontend_root)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from utils.auth_helper import api_validate_token, set_auth_session

# Page configuration
st.set_page_config(
    page_title="Healthcare Planning Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Initialize Session State ────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Auto-validate token if present but not yet authenticated
if not st.session_state["authenticated"] and "token" in st.session_state:
    user_info = api_validate_token(st.session_state["token"])
    if user_info:
        set_auth_session(user_info)
        st.session_state["authenticated"] = True


# ── Navigation ──────────────────────────────────────────────────────────────
def main():
    # Define pages
    landing_page     = st.Page("pages/1_landing.py",         title="Home",               icon="🏠")
    login_page       = st.Page("pages/2_login.py",           title="Login",              icon="🔐")
    register_page    = st.Page("pages/3_register.py",        title="Register",           icon="📝")
    dashboard_page   = st.Page("pages/4_dashboard.py",       title="Dashboard",          icon="📊")
    planner_page     = st.Page("pages/5_planner.py",         title="Healthcare Planner", icon="🧠")
    public_chat_page = st.Page("pages/6_public_chatbot.py",  title="Public Chatbot",     icon="💬")
    smart_chat_page  = st.Page("pages/7_smart_chatbot.py",   title="Smart Chatbot",      icon="🤖")

    if not st.session_state["authenticated"]:
        # Unauthenticated: show public pages only, hide dashboard/planner/smart chat
        pg = st.navigation({
            "Welcome": [landing_page],
            "Account": [login_page, register_page],
            "Tools":   [public_chat_page],
        })
    else:
        # Authenticated: show protected pages, hide login/register
        pg = st.navigation({
            "Health Platform": [dashboard_page, planner_page],
            "Chat":            [smart_chat_page, public_chat_page],
        })

    pg.run()


if __name__ == "__main__":
    main()
