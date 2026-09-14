import streamlit as st
import uuid
from ..config import AVAILABLE_ROLES, EXPERIENCE_LEVELS, INTERVIEW_TYPES, DIFFICULTY_MODES, DEFAULT_QUESTIONS_COUNT
from ..models.interview import InterviewConfig, InterviewSession
from ..services.resume_parser import extract_text_from_pdf
from ..services.gemini_service import GeminiService
from ..database.db import save_interview_start
from ..utils.helpers import setup_logger

logger = setup_logger("HomeView")

def render_home_view():
    """Render modern dark interview setup and landing screen."""
    st.markdown("""
        <div style="margin-bottom: 2rem;">
            <div style="display: inline-flex; align-items: center; gap: 0.5rem; background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 9999px; padding: 4px 12px; margin-bottom: 1rem;">
                <span style="width: 6px; height: 6px; border-radius: 50%; background: #3B82F6; display: inline-block;"></span>
                <span style="font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #93C5FD;">Dynamic Cognitive Assessment</span>
            </div>
            <h1 style="font-size: 2.5rem; font-weight: 800; letter-spacing: -0.03em; color: #FFFFFF; margin: 0 0 0.85rem 0; line-height: 1.15;">
                An interview that adapts to <span style="background: linear-gradient(135deg, #60A5FA 0%, #C084FC 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">how you think.</span>
            </h1>
            <p style="font-size: 1.05rem; line-height: 1.6; color: #94A3B8; max-width: 680px; margin: 0;">
                Practice realistic technical and behavioral interviews calibrated in real-time. The AI observes conceptual depth, tracks weak spots, and formulates targeted follow-up challenges.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Clean native container for configuration
    with st.container(border=True):
        st.markdown("""
            <div style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #60A5FA; margin-bottom: 1.25rem;">
                ✦ Session Configuration
            </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            role_choice = st.selectbox("Target Role", AVAILABLE_ROLES, index=0)
            custom_role = None
            if role_choice == "Custom...":
                custom_role = st.text_input("Enter custom role title", placeholder="e.g. Distributed Systems Engineer")

            experience_choice = st.selectbox("Experience Level", EXPERIENCE_LEVELS, index=0)

        with col2:
            interview_type = st.selectbox("Interview Focus", INTERVIEW_TYPES, index=0)
            difficulty_mode = st.selectbox("Difficulty Progression", DIFFICULTY_MODES, index=0)

        col3, col4 = st.columns([1, 1])
        with col3:
            total_questions = st.slider(
                "Session Length (Questions)",
                min_value=3,
                max_value=10,
                value=DEFAULT_QUESTIONS_COUNT,
                help="Recommended: 5 questions for thorough topic coverage."
            )

        with col4:
            st.markdown("<div style='font-size: 0.85rem; color: #94A3B8; margin-bottom: 0.35rem; font-weight: 600;'>Resume Grounding (Optional PDF)</div>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader(
                "Upload Resume (PDF)",
                type=["pdf"],
                label_visibility="collapsed",
                help="Extracts projects and tech stack to formulate personalized questions."
            )

        resume_text = None
        if uploaded_file is not None:
            with st.spinner("Analyzing resume highlights..."):
                resume_text = extract_text_from_pdf(uploaded_file.getvalue())
                if resume_text:
                    st.markdown("""
                        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 6px; padding: 0.6rem 0.85rem; font-size: 0.85rem; color: #34D399; margin-top: 0.5rem;">
                            ✓ <strong>Resume Active:</strong> Questions will adapt to your declared projects and stack.
                        </div>
                    """, unsafe_allow_html=True)

        effective_role = (custom_role.strip() if custom_role and custom_role.strip() else "Software Engineer") if role_choice == "Custom..." else role_choice

        st.markdown("<div style='margin-top: 1.25rem;'></div>", unsafe_allow_html=True)

        btn_col1, btn_col2 = st.columns([2, 1])
        with btn_col1:
            if st.button("Start Interview →", type="primary", use_container_width=True):
                session_id = str(uuid.uuid4())
                config = InterviewConfig(
                    role=effective_role,
                    experience_level=experience_choice,
                    interview_type=interview_type,
                    difficulty_mode=difficulty_mode,
                    total_questions=total_questions,
                    resume_context=resume_text
                )
                
                initial_difficulty = "Medium" if "Adaptive" in difficulty_mode else difficulty_mode
                session = InterviewSession(
                    session_id=session_id,
                    config=config,
                    current_difficulty=initial_difficulty
                )

                # Save session
                save_interview_start(session_id, config)

                # Initialize session state
                st.session_state.current_session = session
                st.session_state.current_view = "interview"
                st.session_state.current_eval = None
                st.session_state.user_answer = ""
                st.session_state.answer_submitted = False
                st.session_state.final_report = None
                st.rerun()

        with btn_col2:
            if st.button("Previous Sessions", type="secondary", use_container_width=True):
                st.session_state.current_view = "history"
                st.rerun()
