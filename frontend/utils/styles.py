import streamlit as st

def apply_styles():
    """Apply professional medical-themed CSS to the Streamlit app."""
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Light, clean medical theme */
    .stApp {
        background-color: #f8fafc;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0;
    }

    /* Hero header */
    .hero-header {
        text-align: center;
        padding: 3rem 1rem;
        background: linear-gradient(135deg, #2563eb 0%, #0ea5e9 100%);
        border-radius: 20px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .hero-header h1 {
        color: white !important;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    .hero-header p {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
    }

    /* Card styling */
    .feature-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.5rem;
        transition: all 0.3s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        border-color: #3b82f6;
    }
    .feature-card i {
        font-size: 2rem;
        color: #2563eb;
        margin-bottom: 1rem;
    }

    /* Step badges */
    .step-badge {
        display: inline-block;
        padding: 0.4rem 1.2rem;
        border-radius: 99px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .step-active { background: #dbeafe; color: #1e40af; }
    .step-done { background: #dcfce7; color: #166534; }
    .step-todo { background: #f1f5f9; color: #475569; }

    /* Auth card container */
    .auth-container {
        max-width: 500px;
        margin: 2rem auto;
        padding: 2.5rem;
        background: white;
        border-radius: 24px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15);
        border: 1px solid #f1f5f9;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        transform: scale(1.02);
    }

    /* Results layout */
    .result-section {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        border: 1px solid #e2e8f0;
        margin-bottom: 2rem;
    }

    /* User Pill */
    .user-pill {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 15px;
        background: #f1f5f9;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    .user-pill b { color: #1e293b; }
    .user-pill span { color: #64748b; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)
