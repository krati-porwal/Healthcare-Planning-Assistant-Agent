import streamlit as st

def apply_styles():
    """Apply professional medical-themed CSS to the Streamlit app."""
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Dark medical theme */
    .stApp {
        background: linear-gradient(135deg, #0f1724 0%, #1a2744 50%, #0f2235 100%);
        min-height: 100vh;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: rgba(15,23,42,0.95) !important;
        border-right: 1px solid rgba(255,255,255,0.07);
    }

    /* Hero header */
    .hero-header {
        text-align: center;
        padding: 2.5rem 1rem;
        background: linear-gradient(135deg, rgba(30,58,138,0.6), rgba(15,172,142,0.3));
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 2rem;
        backdrop-filter: blur(10px);
    }
    .hero-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .hero-header p {
        color: #94a3b8;
        font-size: 1.1rem;
    }

    /* Card styling */
    .feature-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1.5rem;
        transition: all 0.3s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .feature-card:hover {
        border-color: rgba(96,165,250,0.4);
        background: rgba(255,255,255,0.08);
        transform: translateY(-3px);
    }
    .feature-card h3 { color: #e2e8f0 !important; }
    .feature-card p { color: #94a3b8; }

    /* Auth card container */
    .auth-container {
        max-width: 500px;
        margin: 2rem auto;
        padding: 2.5rem;
        background: rgba(255,255,255,0.05);
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
    }

    /* Text inputs */
    .stTextInput > div > div > input {
        background-color: rgba(255,255,255,0.07) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 8px !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important;
        color: white !important;
        border: none !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(59,130,246,0.4) !important;
    }

    /* Labels and text */
    label { color: #cbd5e1 !important; }
    h2, h3, h4 { color: #e2e8f0 !important; }
    p { color: #94a3b8; }

    /* User Pill */
    .user-pill {
        background: rgba(52,211,153,0.12);
        border: 1px solid rgba(52,211,153,0.3);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
    }
    .user-pill b { color: #34d399; font-size: 0.95rem; }
    .user-pill span { color: #64748b; font-size: 0.8rem; }

    /* Step badges */
    .step-badge {
        display: inline-block;
        padding: 0.4rem 1.2rem;
        border-radius: 99px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .step-active { background: rgba(96,165,250,0.2); color: #60a5fa; border: 1px solid #60a5fa44; }
    .step-done   { background: rgba(52,211,153,0.2); color: #34d399; border: 1px solid #34d39944; }
    .step-todo   { background: rgba(148,163,184,0.1); color: #64748b; border: 1px solid #33415544; }
</style>
""", unsafe_allow_html=True)
