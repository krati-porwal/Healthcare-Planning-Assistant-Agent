"""
Landing Page — Public (no login required)
Accessible to everyone. Shows platform features and CTAs.
"""
import streamlit as st
from utils.styles import apply_styles

apply_styles()


def show_landing():
    # Hero Section
    st.markdown("""
    <div class="landing-hero">
        <h1>🏥 Healthcare Planning Assistant</h1>
        <p>AI-powered treatment planning with a 21-step multi-agent architecture.
        Get personalized care recommendations, hospital rankings, and expert explanations — all in one place.</p>
        <p class="subtitle">Built with Gemini AI · LangChain · FastAPI · PostgreSQL</p>
    </div>
    """, unsafe_allow_html=True)

    # CTA Buttons — vary based on auth state
    if st.session_state.get("authenticated"):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📊 Go to Dashboard →", use_container_width=True, key="landing_dash"):
                st.switch_page("pages/4_dashboard.py")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔐 Login", use_container_width=True, key="landing_login"):
                st.switch_page("pages/2_login.py")
        with col2:
            if st.button("📝 Create Account", use_container_width=True, key="landing_register"):
                st.switch_page("pages/3_register.py")
        with col3:
            if st.button("💬 Try Public Chatbot", use_container_width=True, key="landing_chat"):
                st.switch_page("pages/6_public_chatbot.py")

    st.markdown("<br>", unsafe_allow_html=True)

    # Feature Cards
    st.markdown("### ✨ Platform Features")
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("""
        <div class="feature-card">
            <h3>🧠 AI Healthcare Planner</h3>
            <p>Our flagship 21-step agentic workflow decomposes your health goal, collects medical data,
            runs clinical compliance checks, and generates a full treatment plan with hospital recommendations.</p>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="feature-card">
            <h3>💬 Medical Chatbot</h3>
            <p>Ask health questions in real-time. Use the <b>public chatbot</b> without signing up,
            or log in for a <b>smart chatbot</b> with conversation memory powered by LangChain.</p>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div class="feature-card">
            <h3>📄 PDF Reports & Audit Trail</h3>
            <p>Download your treatment plan as a formatted PDF. Every step of the pipeline
            is logged in our persistent audit trail for full transparency.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # How It Works
    st.markdown("### 🔄 How It Works")
    s1, s2, s3, s4 = st.columns(4)
    steps = [
        ("1️⃣", "Describe Goal", "Tell us your health concern"),
        ("2️⃣", "Answer Questions", "Our agents collect medical data"),
        ("3️⃣", "AI Analysis", "Gemini analyzes and validates"),
        ("4️⃣", "Get Your Plan", "Treatment plan + hospitals + PDF"),
    ]
    for col, (icon, title, desc) in zip([s1, s2, s3, s4], steps):
        with col:
            st.markdown(f"""
            <div class="stat-card">
                <h2>{icon}</h2>
                <p><b>{title}</b><br>{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    # Disclaimer
    st.markdown("""
    <div class="disclaimer-box">
        ⚕️ <b>Medical Disclaimer:</b> This platform provides AI-generated informational content only.
        It does not constitute medical advice, diagnosis, or treatment. Always consult a qualified
        healthcare professional before making any medical decisions.
    </div>
    """, unsafe_allow_html=True)


show_landing()
