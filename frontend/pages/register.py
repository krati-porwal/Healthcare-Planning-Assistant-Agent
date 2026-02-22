import streamlit as st
import time
from utils.auth_helper import api_register, set_auth_session
from utils.styles import apply_styles

# Apply custom styles
apply_styles()

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
        st.markdown('### 📝 Register')
        
        with st.form("register_form"):
            name = st.text_input("Full Name", placeholder="Arjun Sharma")
            email = st.text_input("Email Address", placeholder="arjun@example.com")
            password = st.text_input("Password", type="password", placeholder="Create a strong password")
            location = st.text_input("Location (Optional)", placeholder="Mumbai, India")
            
            st.markdown('<br>', unsafe_allow_html=True)
            submit = st.form_submit_button("Create Account →", use_container_width=True)

            if submit:
                if not name or not email or not password:
                    st.error("Please fill in required fields (Name, Email, Password).")
                else:
                    with st.spinner("Creating account..."):
                        res = api_register(name, email, location)
                        if "error" in res:
                            st.error(res["error"])
                        else:
                            set_auth_session(res)
                            st.success("Registration successful! Welcome aboard.")
                            time.sleep(0.5)
                            # Version-safe navigation
                            if hasattr(st, "navigation"):
                                st.switch_page("pages/dashboard.py")
                            else:
                                st.session_state.page = "dashboard"
                                st.rerun()
        
        st.markdown("---")
        st.markdown("Already have an account? [Login here](login)")
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    show_register()
