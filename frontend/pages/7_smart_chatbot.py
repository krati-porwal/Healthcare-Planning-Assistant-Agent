"""
Smart Chatbot — Protected page (requires authentication).
Multi-turn medical chatbot with conversation memory + Gemini AI.
Uses langchain_google_genai ChatGoogleGenerativeAI with manual message history.
"""
import streamlit as st
import os
import sys
from utils.auth_helper import check_auth_or_redirect, clear_auth_session
from utils.styles import apply_styles

apply_styles()

# Guard: redirect to login if not authenticated
check_auth_or_redirect()

# Ensure backend imports work
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_root = os.path.dirname(_project_root)
if _root not in sys.path:
    sys.path.insert(0, _root)

# ── LangChain + Gemini Setup ────────────────────────────────────────────────
_LANGCHAIN_OK = False
_import_err = ""

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_root, ".env"))

    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

    _llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=os.getenv("GEMINI_API_KEY", ""),
        temperature=0.7,
        convert_system_message_to_human=True,
    )

    SYSTEM_MSG = SystemMessage(content=(
        "You are an expert, empathetic healthcare advisor chatbot. "
        "You have access to the full conversation history with this user. "
        "Provide helpful, evidence-based health information. "
        "Always remind the user to consult a medical professional for actual diagnoses. "
        "Keep responses concise (2-4 paragraphs). Use bullet points when listing information."
    ))

    _LANGCHAIN_OK = True
except ImportError as e:
    _import_err = str(e)
except Exception as e:
    _import_err = str(e)


# Window size — keep last N messages to avoid context overflow
MAX_MEMORY_MESSAGES = 20


def _get_langchain_messages(history: list[dict]) -> list:
    """Convert chat history dicts to LangChain message objects."""
    messages = [SYSTEM_MSG]
    # Keep only the last MAX_MEMORY_MESSAGES entries
    window = history[-MAX_MEMORY_MESSAGES:]
    for msg in window:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    return messages


def _get_ai_response(user_input: str, history: list[dict]) -> str:
    """Invoke the LLM with full message history + new user input."""
    messages = _get_langchain_messages(history)
    messages.append(HumanMessage(content=user_input))
    try:
        response = _llm.invoke(messages)
        return response.content.strip()
    except Exception as e:
        return f"⚠️ Error: {e}"


def show_smart_chatbot():
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div class="user-pill">
            <b>👤 {st.session_state.get('user_name', 'User')}</b><br>
            <span>{st.session_state.get('user_email', '')}</span>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🏠 Home", use_container_width=True, key="smart_home"):
            st.switch_page("pages/4_dashboard.py")

        if st.button("🗑️ Clear Conversation", use_container_width=True, key="smart_clear"):
            st.session_state.pop("smart_chat_history", None)
            st.rerun()

        if st.button("🚪 Logout", use_container_width=True, key="smart_logout"):
            clear_auth_session()

    # Header
    user_name = st.session_state.get("user_name", "User")
    st.markdown(f"""
    <div class="hero-header">
        <h1>🧠 Smart Health Chatbot</h1>
        <p>Hi {user_name}! I remember our conversation. Ask me anything about health.</p>
    </div>
    """, unsafe_allow_html=True)

    if not _LANGCHAIN_OK:
        st.error(
            f"⚠️ LangChain/Gemini setup failed: {_import_err}\n\n"
            "Please install: `pip install langchain-google-genai`\n"
            "And set `GEMINI_API_KEY` in your `.env` file."
        )
        return

    # Initialize chat history
    if "smart_chat_history" not in st.session_state:
        st.session_state.smart_chat_history = []

    # Display history
    for msg in st.session_state.smart_chat_history:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="chat-bubble-user">{msg["content"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="chat-bubble-ai">🧠 {msg["content"]}</div>',
                unsafe_allow_html=True,
            )

    # Chat input
    user_input = st.chat_input("Ask a health question...")

    if user_input:
        st.session_state.smart_chat_history.append({"role": "user", "content": user_input})
        st.markdown(
            f'<div class="chat-bubble-user">{user_input}</div>',
            unsafe_allow_html=True,
        )

        with st.spinner("Thinking..."):
            response = _get_ai_response(user_input, st.session_state.smart_chat_history)

        st.session_state.smart_chat_history.append({"role": "assistant", "content": response})
        st.markdown(
            f'<div class="chat-bubble-ai">🧠 {response}</div>',
            unsafe_allow_html=True,
        )
        st.rerun()

    # Memory info
    if st.session_state.smart_chat_history:
        n = len(st.session_state.smart_chat_history)
        st.caption(f"💾 {n} messages · memory window = last {MAX_MEMORY_MESSAGES}")


show_smart_chatbot()
