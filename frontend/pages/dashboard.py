import streamlit as st
from utils.auth_helper import check_auth_or_redirect, clear_auth_session
from utils.styles import apply_styles

# Apply custom styles
apply_styles()

# Redirect if not logged in
check_auth_or_redirect()

def show_dashboard():
    # Sidebar Logout
    with st.sidebar:
        st.markdown(f"""
        <div class="user-pill">
            <b>👤 {st.session_state.get('user_name', 'User')}</b><br>
            <span>{st.session_state.get('user_email', '')}</span>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Logout", use_container_width=True):
            clear_auth_session()

    st.markdown(f"## Welcome back, {st.session_state.get('user_name', 'User')}! 👋")
    st.markdown("Select a feature to get started with your healthcare planning.")
    
    st.markdown("<br>", unsafe_allow_html=True)

    # Feature Cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>🧠 Healthcare Planner</h3>
            <p>Our flagship 21-step AI agent orchestrator that creates a professional treatment plan for you.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Planning →", key="btn_planner", use_container_width=True):
            if hasattr(st, "navigation"):
                st.switch_page("pages/planner.py")
            else:
                st.session_state.page = "planner"
                st.rerun()

    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>📄 Lab Report Analyzer</h3>
            <p>Upload your medical reports and let our AI summarize key findings and suggest next steps.</p>
            <span style="color: #64748b; font-size: 0.8rem;">(Coming Soon)</span>
        </div>
        """, unsafe_allow_html=True)
        st.button("Analyze Reports", key="btn_reports", disabled=True, use_container_width=True)

    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>💬 Medical Chatbot</h3>
            <p>Ask quick questions about symptoms, medications, or general health advice in real-time.</p>
            <span style="color: #64748b; font-size: 0.8rem;">(Coming Soon)</span>
        </div>
        """, unsafe_allow_html=True)
        st.button("Chat Now", key="btn_chat", disabled=True, use_container_width=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Recent Activity / Stats Placeholder
    st.markdown("### 📊 Your Health Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Active Plans", "1", "+1")
    c2.metric("Reports Scanned", "0", "0")
    c3.metric("Goal Completion", "25%", "+5%")

if __name__ == "__main__":
    show_dashboard()
