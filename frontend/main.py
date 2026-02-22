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

# Check if modern navigation is supported in this Streamlit version
HAS_MODERN_NAV = hasattr(st, "Page") and hasattr(st, "navigation")

def switch_to(page_path, page_key=None):
    """Helper to switch pages across different Streamlit versions."""
    if HAS_MODERN_NAV:
        st.switch_page(page_path)
    else:
        st.session_state.page = page_key or page_path.split("/")[-1].replace(".py", "")
        st.rerun()

from utils.auth_helper import api_validate_token, set_auth_session
from utils.styles import apply_styles

# Page configuration
st.set_page_config(page_title="Healthcare Platform", page_icon="🏥", layout="wide", initial_sidebar_state="expanded")

# Initialize Session State
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Auto-validate token if present
if not st.session_state["authenticated"] and "token" in st.session_state:
    user_info = api_validate_token(st.session_state["token"])
    if user_info:
        set_auth_session(user_info)
        st.session_state["authenticated"] = True

# Define Navigation
def main():
    if HAS_MODERN_NAV:
        # --- MODERN NAVIGATION (Streamlit 1.35.0+) ---
        login_page = st.Page("pages/login.py", title="Login", icon="🔐")
        register_page = st.Page("pages/register.py", title="Register", icon="📝")
        dashboard_page = st.Page("pages/dashboard.py", title="Dashboard", icon="📊")
        planner_page = st.Page("pages/planner.py", title="Healthcare Planner", icon="🧠")

        if not st.session_state["authenticated"]:
            pg = st.navigation({"Authentication": [login_page, register_page]})
        else:
            pg = st.navigation({"Health Platform": [dashboard_page, planner_page]})
        pg.run()
    else:
        # --- LEGACY NAVIGATION FALLBACK ---
        apply_styles()
        if not st.session_state["authenticated"]:
            # Simple state switcher for old versions
            if "page" not in st.session_state: st.session_state.page = "login"
            
            if st.session_state.page == "register":
                from pages.register import show_register
                show_register()
            else:
                from pages.login import show_login
                show_login()
        else:
            # Simple menu for old versions
            with st.sidebar:
                st.title("🏥 Navigation")
                choice = st.radio("Go to", ["Dashboard", "Healthcare Planner"])
                if st.button("🚪 Logout"):
                    from utils.auth_helper import clear_auth_session
                    clear_auth_session()
            
            if choice == "Dashboard":
                from pages.dashboard import show_dashboard
                show_dashboard()
            else:
                from pages.planner import show_planner
                show_planner()

if __name__ == "__main__":
    main()

