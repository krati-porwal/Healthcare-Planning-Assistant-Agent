"""
Register Page — Visible only before authentication.
Redirects to Dashboard if already logged in.
"""
import streamlit as st
import time
from utils.auth_helper import api_register, set_auth_session, redirect_if_authenticated
from utils.styles import apply_styles

apply_styles()

# Guard: if already logged in, go to dashboard
redirect_if_authenticated()


def show_register():
    st.markdown("""
    <div class="hero-header">
        <h1>🏥 Create Account</h1>
        <p>Join our platform for smarter healthcare planning</p>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.5, 1])

    with col:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.markdown("### 📝 Register")

        with st.form("register_form"):
            name = st.text_input("Full Name", placeholder="Arjun Sharma")
            email = st.text_input("Email Address", placeholder="arjun@example.com")
            password = st.text_input("Password", type="password", placeholder="Min. 6 characters")
            location = st.text_input("Location (Optional)", placeholder="Mumbai, India")

            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("Create Account →", use_container_width=True)

            if submit:
                if not name or not email or not password:
                    st.error("Please fill in required fields (Name, Email, Password).")
                elif len(password.strip()) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    with st.spinner("Creating account..."):
                        res = api_register(name, email, password, location)
                        if "error" in res:
                            st.error(res["error"])
                        else:
                            set_auth_session(res)
                            st.success(f"🎉 Welcome, {res.get('name', 'User')}! Account created.")
                            time.sleep(0.5)
                            st.switch_page("pages/4_dashboard.py")

        st.markdown("---")
        st.markdown("Already have an account? Switch to the **Login** page in the sidebar.")
        st.markdown('</div>', unsafe_allow_html=True)


show_register()
