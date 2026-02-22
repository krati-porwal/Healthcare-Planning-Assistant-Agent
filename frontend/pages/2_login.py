"""
Login Page — Visible only before authentication.
Redirects to Dashboard if already logged in.
"""
import streamlit as st
import time
from utils.auth_helper import api_login, set_auth_session, redirect_if_authenticated
from utils.styles import apply_styles

apply_styles()

# Guard: if already logged in, go to dashboard
redirect_if_authenticated()


def show_login():
    st.markdown("""
    <div class="hero-header">
        <h1>🏥 Healthcare Platform</h1>
        <p>Login to access your AI-powered healthcare assistant</p>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.5, 1])

    with col:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.markdown("### 🔐 Sign In")

        with st.form("login_form"):
            email = st.text_input("Email Address", placeholder="arjun@example.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")

            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("Sign In →", use_container_width=True)

            if submit:
                if not email or not password:
                    st.error("Please fill in all fields.")
                else:
                    with st.spinner("Authenticating..."):
                        res = api_login(email, password)
                        if "error" in res:
                            st.error(res["error"])
                        else:
                            set_auth_session(res)
                            st.success("Login successful! Redirecting...")
                            time.sleep(0.5)
                            st.switch_page("pages/4_dashboard.py")

        st.markdown("---")
        st.markdown("New user? Switch to the **Register** page in the sidebar.")
        st.markdown('</div>', unsafe_allow_html=True)


show_login()
