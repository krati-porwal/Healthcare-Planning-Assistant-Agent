"""
Healthcare Planner — Protected page (requires authentication).
3-step workflow: Profile → Questions → Treatment Plan.
"""
import streamlit as st
import json
import time
from utils.auth_helper import check_auth_or_redirect, clear_auth_session
from utils.planner_helper import api_start_session, api_start_plan, api_respond_plan, direct_plan
from utils.styles import apply_styles

apply_styles()

# Guard: redirect to login if not authenticated
check_auth_or_redirect()


def render_progress(step):
    steps_labels = ["Profile & Goal", "Medical Questions", "Your Plan"]
    html = '<div class="progress-container" style="display: flex; gap: 10px; margin-bottom: 20px;">'
    for i, label in enumerate(steps_labels, start=1):
        cls = "step-active" if i == step else ("step-done" if i < step else "step-todo")
        icon = "●" if i == step else ("✓" if i < step else "○")
        html += f'<div class="step-badge {cls}" style="flex: 1; text-align: center;">{icon} {label}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def show_planner():
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div class="user-pill">
            <b>👤 {st.session_state.get('user_name', 'User')}</b><br>
            <span>{st.session_state.get('user_email', '')}</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.session_state["use_direct_mode"] = st.checkbox(
            "🔗 Use Direct Mode (No DB)",
            value=st.session_state.get("use_direct_mode", True),
        )

        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("pages/4_dashboard.py")

        if st.button("🔄 Restart Planner", use_container_width=True):
            for k in ["step", "goal", "answers", "result", "questions", "subtasks"]:
                st.session_state.pop(k, None)
            st.rerun()

        if st.button("🚪 Logout", use_container_width=True):
            clear_auth_session()

    if "step" not in st.session_state:
        st.session_state.step = 1

    step = st.session_state.step
    if step == 1:
        render_step1()
    elif step == 2:
        render_step2()
    elif step == 3:
        render_step3()


def render_step1():
    st.markdown(
        '<div class="hero-header"><h1>🎯 Healthcare Goal Decomposer</h1>'
        '<p>Tell us your health concern, and our agents will create an execution plan.</p></div>',
        unsafe_allow_html=True,
    )
    render_progress(1)

    with st.form("step1_form"):
        name = st.text_input("Patient Name", value=st.session_state.get("user_name", ""))
        email = st.text_input("Patient Email", value=st.session_state.get("user_email", ""))
        location = st.text_input("Location", placeholder="e.g. Mumbai")
        budget = st.number_input("Budget (Optional, ₹)", min_value=0, value=0)
        goal = st.text_area(
            "What is your healthcare goal?",
            placeholder="e.g. I need a treatment plan for Breast Cancer Stage 1",
        )
        submit = st.form_submit_button("Generate Plan →", use_container_width=True)

        if submit:
            if not goal:
                st.error("Please describe your healthcare goal.")
                return

            with st.spinner("Agents are decomposing your goal..."):
                if st.session_state.get("use_direct_mode"):
                    import uuid
                    st.session_state.session_id = str(uuid.uuid4())
                    st.session_state.patient_city = location
                    st.session_state.goal = goal
                    st.session_state.step = 2
                    st.rerun()
                else:
                    res = api_start_session(name, email, location, budget if budget > 0 else None)
                    if "error" in res:
                        st.error(res["error"])
                    else:
                        st.session_state.session_id = res["session_id"]
                        st.session_state.user_id = res["user_id"]
                        plan_res = api_start_plan(res["session_id"], res["user_id"], goal)
                        if "error" in plan_res:
                            st.error(plan_res["error"])
                        else:
                            st.session_state.questions = plan_res.get("questions", [])
                            st.session_state.subtasks = plan_res.get("subtasks", [])
                            st.session_state.goal = goal
                            st.session_state.step = 2
                            st.rerun()


def render_step2():
    st.markdown("### 📋 Medical Profile Collection")
    render_progress(2)
    st.info(f"**Goal:** {st.session_state.goal}")

    if st.session_state.get("use_direct_mode"):
        questions = [
            {"field": "age", "question": "What is your age?"},
            {"field": "gender", "question": "What is your gender?"},
            {"field": "symptoms", "question": "Please describe your symptoms."},
            {"field": "medical_history", "question": "Any previous medical history?"},
            {"field": "budget_limit", "question": "What is your maximum budget?"},
            {"field": "surgery_allowed", "question": "Is surgery an option?", "type": "select", "options": ["yes", "no"]},
        ]
    else:
        questions = st.session_state.get("questions", [])

    with st.form("step2_form"):
        answers = st.session_state.get("answers", {})
        for q in questions:
            field = q["field"]
            if q.get("type") == "select":
                answers[field] = st.selectbox(q["question"], options=q["options"], key=f"q_{field}")
            else:
                answers[field] = st.text_input(q["question"], key=f"q_{field}")

        submit = st.form_submit_button("Execute Agent Pipeline 🧠", use_container_width=True)

        if submit:
            with st.spinner("Executing 21-step Agentic Workflow..."):
                if st.session_state.get("use_direct_mode"):
                    # Inject patient_city for location-aware hospital ranking
                    patient_city = st.session_state.get("patient_city", "")
                    if patient_city:
                        answers["patient_city"] = patient_city
                    result = direct_plan(st.session_state.goal, answers)
                else:
                    result = api_respond_plan(
                        st.session_state.session_id,
                        st.session_state.user_id,
                        answers,
                    )

                if "error" in result:
                    st.error(result["error"])
                else:
                    st.session_state.result = result
                    st.session_state.step = 3
                    st.rerun()


def render_step3():
    st.markdown("### ✅ Your Personalized Healthcare Plan")
    render_progress(3)

    result = st.session_state.get("result")
    if not result:
        st.error("No results found.")
        return

    tp = result.get("treatment_plan", {})

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.markdown(f"#### 💊 Treatment Strategy: {tp.get('treatment_type', 'N/A')}")
        st.markdown(f"**Disease:** {tp.get('disease_type', 'N/A')}")
        st.markdown(f"**Timeline:** {tp.get('timeline', 'N/A')}")
        st.markdown(f"**Specialist:** {tp.get('specialist', 'N/A')}")
        st.markdown("---")
        st.markdown("**Explanation:**")
        st.write(result.get("explanation", "No detailed explanation provided."))
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("#### 🏥 Top Recommended Hospitals")
        for hosp in result.get("recommended_hospitals", []):
            st.markdown(f"""
            <div class="feature-card" style="margin-bottom: 10px; padding: 1rem;">
                <b style="color: #60a5fa;">{hosp.get('name')}</b><br>
                <small>📍 {hosp.get('location')}</small><br>
                <span style="font-size: 0.8rem; background: rgba(255,255,255,0.1); padding: 2px 8px; border-radius: 4px;">
                    Rank #{hosp.get('priority_rank')}
                </span>
            </div>
            """, unsafe_allow_html=True)

    # PDF Download
    st.markdown("---")
    try:
        from backend.utils.report_generator import generate_pdf_report, _FPDF_AVAILABLE

        patient_name = st.session_state.get("user_name", "Patient")
        pdf_bytes = generate_pdf_report(result, patient_name)
        mime = "application/pdf" if _FPDF_AVAILABLE else "text/plain"
        ext = "pdf" if _FPDF_AVAILABLE else "txt"
        st.download_button(
            label=f"⬇️ Download Treatment Plan ({ext.upper()})",
            data=pdf_bytes,
            file_name=f"healthcare_plan.{ext}",
            mime=mime,
            use_container_width=True,
        )
    except Exception as e:
        st.warning(f"⚠️ PDF generation unavailable: {e}")

    # JSON Download
    with st.expander("📄 View Raw JSON Output", expanded=False):
        st.json(result)
        st.download_button(
            label="⬇️ Download Plan as JSON",
            data=json.dumps(result, indent=2),
            file_name="healthcare_plan.json",
            mime="application/json",
        )

    st.markdown("---")
    disclaimer = result.get("disclaimer", "Always consult a doctor before starting any treatment.")
    st.markdown(f"""
    <div class="disclaimer-box">⚕️ <b>Medical Disclaimer:</b> {disclaimer}</div>
    """, unsafe_allow_html=True)

    if st.button("Start New Plan 🔄", use_container_width=True):
        st.session_state.step = 1
        st.rerun()


show_planner()
