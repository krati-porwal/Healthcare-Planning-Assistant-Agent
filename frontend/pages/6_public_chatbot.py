"""
Public Chatbot — No login required, no data storage.
Ephemeral single-session chat using Gemini API directly.
"""
import streamlit as st
import os
import sys
from utils.styles import apply_styles

apply_styles()

# Ensure backend imports work
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_root = os.path.dirname(_project_root)
if _root not in sys.path:
    sys.path.insert(0, _root)

# ── Gemini Setup ─────────────────────────────────────────────────────────────
try:
    import google.generativeai as genai
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_root, ".env"))
    genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
    _model = genai.GenerativeModel("gemini-2.0-flash")
    _GEMINI_OK = True
except Exception:
    _GEMINI_OK = False

SYSTEM_PROMPT = (
    "You are a helpful and empathetic healthcare advisor chatbot. "
    "You can discuss symptoms, medications, general health advice, and wellness tips. "
    "Always remind the user that your responses are informational only and they should "
    "consult a qualified medical professional for actual medical decisions. "
    "Keep responses concise (2-4 paragraphs). Use bullet points when listing information."
)


def get_ai_response(user_msg: str, history: list[dict]) -> str:
    """Get a response from Gemini, including recent chat context."""
    if not _GEMINI_OK:
        return "⚠️ Gemini API is not configured. Please set `GEMINI_API_KEY` in your `.env` file."

    # Build context from last few messages
    context_lines = [SYSTEM_PROMPT, ""]
    for msg in history[-6:]:
        role = "User" if msg["role"] == "user" else "Assistant"
        context_lines.append(f"{role}: {msg['content']}")
    context_lines.append(f"User: {user_msg}")
    context_lines.append("Assistant:")

    try:
        response = _model.generate_content("\n".join(context_lines))
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Error generating response: {e}"


def show_public_chatbot():
    st.markdown("""
    <div class="hero-header">
        <h1>💬 Public Health Chatbot</h1>
        <p>Ask health questions — no login required. Powered by Gemini AI.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="disclaimer-box">
        ⚕️ <b>Disclaimer:</b> This chatbot provides general health information only.
        It does not store your data. Always consult a medical professional for actual health decisions.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Initialize chat history (ephemeral — lost on page refresh)
    if "pub_chat_history" not in st.session_state:
        st.session_state.pub_chat_history = []

    # Display chat history
    for msg in st.session_state.pub_chat_history:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="chat-bubble-user">{msg["content"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="chat-bubble-ai">🤖 {msg["content"]}</div>',
                unsafe_allow_html=True,
            )

    # Chat input
    user_input = st.chat_input("Ask a health question...")

    if user_input:
        # Add user message
        st.session_state.pub_chat_history.append({"role": "user", "content": user_input})
        st.markdown(
            f'<div class="chat-bubble-user">{user_input}</div>',
            unsafe_allow_html=True,
        )

        # Get AI response
        with st.spinner("Thinking..."):
            ai_reply = get_ai_response(user_input, st.session_state.pub_chat_history)

        st.session_state.pub_chat_history.append({"role": "assistant", "content": ai_reply})
        st.markdown(
            f'<div class="chat-bubble-ai">🤖 {ai_reply}</div>',
            unsafe_allow_html=True,
        )
        st.rerun()

    # Clear chat button
    if st.session_state.pub_chat_history:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.pub_chat_history = []
            st.rerun()

    # Upsell for logged-in chatbot
    if not st.session_state.get("authenticated"):
        st.markdown("---")
        st.info("💡 **Want conversation memory?** [Login](pages/2_login.py) to use our **Smart Chatbot** with full context retention.")


show_public_chatbot()
