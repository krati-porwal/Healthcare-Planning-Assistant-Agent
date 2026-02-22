import streamlit as st
import time
from utils.auth_helper import api_login, set_auth_session
from utils.styles import apply_styles

# Apply custom styles
apply_styles()

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
        st.markdown('### 🔐 Sign In')
        
        with st.form("login_form"):
            email = st.text_input("Email Address", placeholder="arjun@example.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            
            st.markdown('<br>', unsafe_allow_html=True)
            submit = st.form_submit_button("Sign In →", use_container_width=True)

            if submit:
                if not email or not password:
                    st.error("Please fill in all fields.")
                else:
                    with st.spinner("Authenticating..."):
                        res = api_login(email)
                        if "error" in res:
                            st.error(res["error"])
                        else:
                            set_auth_session(res)
                            st.success("Login successful! Redirecting...")
                            time.sleep(0.5)
                            # Version-safe navigation
                            if hasattr(st, "navigation"):
                                st.switch_page("pages/dashboard.py")
                            else:
                                st.session_state.page = "dashboard"
                                st.rerun()
        
        st.markdown("---")
        st.markdown("New user? [Create an account here](register)")
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    show_login()
