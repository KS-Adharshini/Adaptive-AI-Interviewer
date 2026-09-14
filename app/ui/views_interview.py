import streamlit as st
from ..models.interview import InterviewSession, QuestionItem, CandidateAnswer, TopicMetric
from ..services.interview_engine import AdaptiveEngine
from ..services.evaluator import EvaluatorService
from ..database.db import (
    save_question_record,
    save_answer_record,
    save_evaluation_record,
    finalize_interview_record
)
from ..utils.helpers import setup_logger, clean_html

logger = setup_logger("InterviewView")

def render_interview_view():
    """Render the focused, distraction-free interview assessment screen."""
    session: InterviewSession = st.session_state.get("current_session")
    if not session:
        st.warning("No active session found. Starting a new setup.")
        st.session_state.current_view = "home"
        st.rerun()
        return

    engine = AdaptiveEngine()
    evaluator = EvaluatorService()

    q_index = len(session.questions)
    ans_count = len(session.answers)

    # Generate next question if needed
    if q_index == ans_count and q_index < session.config.total_questions:
        with st.spinner("Calibrating next question..."):
            last_eval = st.session_state.get("current_eval")
            next_q = engine.generate_next_question(session, last_eval=last_eval)
            session.questions.append(next_q)
            save_question_record(session.session_id, next_q)
            st.session_state.answer_submitted = False
            st.session_state.current_eval = None
            st.rerun()
            return

    current_q: QuestionItem = session.questions[-1]
    is_submitted = st.session_state.get("answer_submitted", False)

    # --- 1. HEADER METADATA BAR ---
    col_m1, col_m2 = st.columns([3, 2])
    with col_m1:
        st.markdown(clean_html(f"""
            <div style="display: flex; align-items: center; gap: 0.6rem; padding: 0.4rem 0;">
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; font-weight: 700; color: #60A5FA; background: rgba(59, 130, 246, 0.12); padding: 3px 8px; border-radius: 4px;">
                    Q{current_q.question_number:02d} / {session.config.total_questions:02d}
                </span>
                <span style="font-size: 0.88rem; font-weight: 600; color: #FFFFFF;">
                    {session.config.role}
                </span>
            </div>
        """), unsafe_allow_html=True)

    with col_m2:
        diff_pill = f"pill-{current_q.difficulty.lower()}"
        follow_up_badge = '<span class="status-pill pill-followup">⚡ Follow-Up</span>' if current_q.is_follow_up else ''
        st.markdown(clean_html(f"""
            <div style="display: flex; gap: 0.5rem; justify-content: flex-end; align-items: center; padding: 0.4rem 0;">
                {follow_up_badge}
                <span class="status-pill {diff_pill}">● {current_q.difficulty}</span>
                <span style="font-size: 0.78rem; color: #94A3B8; font-weight: 500; background: rgba(255, 255, 255, 0.05); padding: 3px 8px; border-radius: 4px;">{current_q.topic}</span>
            </div>
        """), unsafe_allow_html=True)

    # --- 2. FOCUS QUESTION CARD ---
    concept_chip = f"<div style='font-size: 0.8rem; font-family: \"JetBrains Mono\", monospace; color: #94A3B8; background: rgba(255, 255, 255, 0.05); padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.08); margin-top: 0.75rem; display: inline-block;'>Target: <strong>{current_q.target_concept}</strong></div>" if current_q.target_concept else ""
    st.markdown(clean_html(f"""
        <div class="question-focus-card">
            <div class="question-headline">
                {current_q.question}
            </div>
            {concept_chip}
        </div>
    """), unsafe_allow_html=True)

    # --- 3. PROGRESS TRACKER ---
    total_q = session.config.total_questions
    dots_html = []
    for i in range(1, total_q + 1):
        if i < current_q.question_number:
            dots_html.append('<span class="dot-completed" title="Completed"></span>')
        elif i == current_q.question_number:
            dots_html.append('<span class="dot-active" title="Active"></span>')
        else:
            dots_html.append('<span class="dot-pending" title="Pending"></span>')

    st.markdown(clean_html(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem;">
            <div style="display: flex; align-items: center; gap: 0.6rem;">
                {"".join(dots_html)}
            </div>
            <div style="font-size: 0.78rem; font-family: 'JetBrains Mono', monospace; color: #64748B;">
                STAGE: {session.config.difficulty_mode.upper()}
            </div>
        </div>
    """), unsafe_allow_html=True)

    # --- 4. RESPONSE AREA ---
    if not is_submitted:
        st.markdown("<div style='font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #94A3B8; margin-bottom: 0.5rem;'>Your Technical Response</div>", unsafe_allow_html=True)
        user_response = st.text_area(
            "Response Input",
            key=f"answer_input_{current_q.question_number}",
            height=200,
            placeholder="Formulate your response thoroughly. Detail algorithmic complexity, architectural trade-offs, practical failure modes, and edge cases...",
            label_visibility="collapsed"
        )

        col_left, col_right = st.columns([3, 1])
        with col_left:
            if st.button("Submit Response →", type="primary", use_container_width=True):
                if not user_response or len(user_response.strip()) < 5:
                    st.error("Please enter a response before submitting.")
                else:
                    with st.spinner("Analyzing response depth and precision..."):
                        ans_obj = CandidateAnswer(
                            question_number=current_q.question_number,
                            answer_text=user_response.strip()
                        )
                        session.answers.append(ans_obj)
                        save_answer_record(session.session_id, current_q.question_number, user_response.strip())

                        eval_result = evaluator.evaluate_answer(
                            role=session.config.role,
                            experience_level=session.config.experience_level,
                            question=current_q,
                            candidate_answer=user_response.strip()
                        )
                        save_evaluation_record(session.session_id, current_q.question_number, eval_result)

                        topic = current_q.topic
                        if topic not in session.topic_metrics:
                            session.topic_metrics[topic] = TopicMetric(topic=topic)
                        t_metric = session.topic_metrics[topic]
                        t_metric.total_score += eval_result.overall_score
                        t_metric.attempts += 1
                        if eval_result.missing_concepts:
                            t_metric.weak_concepts.extend(eval_result.missing_concepts)

                        next_diff, new_high, new_low = engine.calculate_next_difficulty(
                            current_difficulty=session.current_difficulty,
                            last_score=eval_result.overall_score,
                            consecutive_high=session.consecutive_high,
                            consecutive_low=session.consecutive_low,
                            mode=session.config.difficulty_mode
                        )
                        session.current_difficulty = next_diff
                        session.consecutive_high = new_high
                        session.consecutive_low = new_low

                        st.session_state.current_eval = eval_result
                        st.session_state.answer_submitted = True
                        st.rerun()

        with col_right:
            if st.button("End Early", type="secondary", use_container_width=True):
                if st.session_state.get("confirm_end"):
                    st.session_state.current_view = "results"
                    st.session_state.confirm_end = False
                    st.rerun()
                else:
                    st.session_state.confirm_end = True
                    st.info("Click again to confirm early completion.")

    else:
        # --- 5. EVALUATION FEEDBACK CARD ---
        eval_data = st.session_state.get("current_eval")
        if eval_data:
            strengths_items = "".join([f"<div class='list-item-strength'>✓ {s}</div>" for s in eval_data.strengths]) or "<div class='list-item-strength'>Solid core formulation.</div>"
            weaknesses_items = "".join([f"<div class='list-item-gap'>△ {w}</div>" for w in eval_data.weaknesses]) or "<div class='list-item-gap'>No glaring omissions.</div>"

            follow_up_banner = ""
            if eval_data.should_follow_up:
                follow_up_banner = f"""
                <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 8px; padding: 0.85rem 1rem; margin-top: 1.25rem; font-size: 0.88rem; color: #FBBF24;">
                    <strong>Adaptive Follow-Up Scheduled:</strong> {eval_data.follow_up_reason or 'The interviewer will challenge the identified omission in the next step.'}
                </div>
                """

            st.markdown(clean_html(f"""
                <div class="diagnostic-container">
                    <div style="display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 1rem; margin-bottom: 1.25rem;">
                        <div style="font-size: 0.85rem; font-weight: 700; text-transform: uppercase; color: #94A3B8; letter-spacing: 0.06em;">
                            Diagnostic Evaluation
                        </div>
                        <div style="font-size: 2.2rem; font-weight: 800; color: #FFFFFF; letter-spacing: -0.03em;">
                            {eval_data.overall_score:.1f} <span style="font-size: 1.1rem; color: #64748B; font-weight: 400;">/ 10</span>
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; margin-bottom: 1.25rem;">
                        <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 8px; padding: 0.75rem; text-align: center;">
                            <div style="font-size: 0.7rem; text-transform: uppercase; color: #94A3B8; font-weight: 600;">Correctness</div>
                            <div style="font-size: 1.2rem; font-weight: 700; color: #FFFFFF; margin-top: 0.2rem;">{eval_data.correctness:.1f}</div>
                        </div>
                        <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 8px; padding: 0.75rem; text-align: center;">
                            <div style="font-size: 0.7rem; text-transform: uppercase; color: #94A3B8; font-weight: 600;">Depth</div>
                            <div style="font-size: 1.2rem; font-weight: 700; color: #FFFFFF; margin-top: 0.2rem;">{eval_data.technical_depth:.1f}</div>
                        </div>
                        <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 8px; padding: 0.75rem; text-align: center;">
                            <div style="font-size: 0.7rem; text-transform: uppercase; color: #94A3B8; font-weight: 600;">Clarity</div>
                            <div style="font-size: 1.2rem; font-weight: 700; color: #FFFFFF; margin-top: 0.2rem;">{eval_data.clarity:.1f}</div>
                        </div>
                        <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 8px; padding: 0.75rem; text-align: center;">
                            <div style="font-size: 0.7rem; text-transform: uppercase; color: #94A3B8; font-weight: 600;">Completeness</div>
                            <div style="font-size: 1.2rem; font-weight: 700; color: #FFFFFF; margin-top: 0.2rem;">{eval_data.completeness:.1f}</div>
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                        <div>
                            <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: #34D399; margin-bottom: 0.5rem; letter-spacing: 0.05em;">
                                Articulated Well
                            </div>
                            {strengths_items}
                        </div>
                        <div>
                            <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: #FB7185; margin-bottom: 0.5rem; letter-spacing: 0.05em;">
                                Missing Nuances / Gaps
                            </div>
                            {weaknesses_items}
                        </div>
                    </div>
                    {follow_up_banner}
                </div>
            """), unsafe_allow_html=True)

        is_last = current_q.question_number >= session.config.total_questions
        button_label = "Finish Interview & View Final Report →" if is_last else "Proceed to Next Question →"

        if st.button(button_label, type="primary", use_container_width=True):
            if is_last:
                st.session_state.current_view = "results"
                st.rerun()
            else:
                st.session_state.answer_submitted = False
                st.rerun()
