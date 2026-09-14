import streamlit as st
from ..models.interview import InterviewSession
from ..models.evaluation import FinalReport
from ..services.evaluator import EvaluatorService
from ..database.db import finalize_interview_record, get_interview_details
from ..utils.helpers import setup_logger, clean_html

logger = setup_logger("ResultsView")

def render_results_view(target_session_id: str = None):
    """Render comprehensive final diagnostic report in modern dark theme."""
    evaluator = EvaluatorService()

    if target_session_id:
        details = get_interview_details(target_session_id)
        if not details or not details.get("interview", {}).get("report"):
            st.error("Report data not found for this session.")
            if st.button("← Back to History"):
                st.session_state.current_view = "history"
                st.rerun()
            return
        report = FinalReport(**details["interview"]["report"])
        role = details["interview"]["role"]
        exp = details["interview"]["experience"]
        date_str = details["interview"]["created_at"][:10]
        timeline = details["timeline"]
    else:
        session: InterviewSession = st.session_state.get("current_session")
        if not session:
            st.warning("No completed interview found.")
            if st.button("Start New Interview"):
                st.session_state.current_view = "home"
                st.rerun()
            return

        role = session.config.role
        exp = session.config.experience_level
        date_str = session.created_at.strftime("%Y-%m-%d")

        if not st.session_state.get("final_report"):
            with st.spinner("Compiling comprehensive interview diagnostic..."):
                report = evaluator.generate_final_report(session)
                st.session_state.final_report = report
                finalize_interview_record(session.session_id, report.overall_percentage, report)
        else:
            report = st.session_state.get("final_report")

        timeline = []
        for i, q in enumerate(session.questions):
            ans = session.answers[i].answer_text if i < len(session.answers) else ""
            timeline.append({
                "question": q.model_dump(),
                "answer": {"answer_text": ans},
                "evaluation": None
            })

    # --- 1. HERO SUMMARY CARD ---
    st.markdown(clean_html(f"""
        <div class="report-hero-box">
            <div style="font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #94A3B8;">
                Assessment Report • {role}
            </div>
            <div class="score-giant">
                {report.overall_percentage:.0f}%
            </div>
            <div style="font-size: 0.88rem; font-family: 'JetBrains Mono', monospace; color: #60A5FA; letter-spacing: 0.05em;">
                COMPOSITE PERFORMANCE SCORE
            </div>
            <div class="report-summary-text">
                {report.summary}
            </div>
        </div>
    """), unsafe_allow_html=True)

    # --- 2. MULTI-DIMENSIONAL SCORES GRID ---
    with st.container(border=True):
        st.markdown("""
            <div style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #60A5FA; margin-bottom: 1rem;">
                📊 Evaluated Core Competencies
            </div>
        """, unsafe_allow_html=True)
        st.markdown(clean_html(f"""
            <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 0.75rem; text-align: center;">
                <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06); padding: 1rem 0.5rem; border-radius: 8px;">
                    <div style="font-size: 0.7rem; text-transform: uppercase; color: #94A3B8; font-weight: 600;">Technical</div>
                    <div style="font-size: 1.4rem; font-weight: 800; color: #FFFFFF; margin-top: 0.35rem;">{report.technical_score:.0f}%</div>
                </div>
                <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06); padding: 1rem 0.5rem; border-radius: 8px;">
                    <div style="font-size: 0.7rem; text-transform: uppercase; color: #94A3B8; font-weight: 600;">Problem Solving</div>
                    <div style="font-size: 1.4rem; font-weight: 800; color: #FFFFFF; margin-top: 0.35rem;">{report.problem_solving_score:.0f}%</div>
                </div>
                <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06); padding: 1rem 0.5rem; border-radius: 8px;">
                    <div style="font-size: 0.7rem; text-transform: uppercase; color: #94A3B8; font-weight: 600;">Communication</div>
                    <div style="font-size: 1.4rem; font-weight: 800; color: #FFFFFF; margin-top: 0.35rem;">{report.communication_score:.0f}%</div>
                </div>
                <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06); padding: 1rem 0.5rem; border-radius: 8px;">
                    <div style="font-size: 0.7rem; text-transform: uppercase; color: #94A3B8; font-weight: 600;">Depth</div>
                    <div style="font-size: 1.4rem; font-weight: 800; color: #FFFFFF; margin-top: 0.35rem;">{report.depth_score:.0f}%</div>
                </div>
                <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06); padding: 1rem 0.5rem; border-radius: 8px;">
                    <div style="font-size: 0.7rem; text-transform: uppercase; color: #94A3B8; font-weight: 600;">Consistency</div>
                    <div style="font-size: 1.4rem; font-weight: 800; color: #FFFFFF; margin-top: 0.35rem;">{report.consistency_score:.0f}%</div>
                </div>
            </div>
        """), unsafe_allow_html=True)

    # --- 3. STRENGTHS & NEEDS IMPROVEMENT ---
    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.markdown("""
                <div style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #10B981; margin-bottom: 0.75rem;">
                    ✓ Demonstrated Strengths
                </div>
            """, unsafe_allow_html=True)
            for s in report.strongest_areas:
                st.markdown(f"<div class='list-item-strength'>✓ {s}</div>", unsafe_allow_html=True)

    with col_b:
        with st.container(border=True):
            st.markdown("""
                <div style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #F43F5E; margin-bottom: 0.75rem;">
                    △ Areas to Sharpen
                </div>
            """, unsafe_allow_html=True)
            for w in report.needs_improvement:
                st.markdown(f"<div class='list-item-gap'>△ {w}</div>", unsafe_allow_html=True)

    # --- 4. TOPIC PERFORMANCE BARS ---
    if report.topic_breakdown:
        with st.container(border=True):
            st.markdown("""
                <div style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #60A5FA; margin-bottom: 1rem;">
                    📈 Domain Mastery by Topic
                </div>
            """, unsafe_allow_html=True)
            for topic, score in report.topic_breakdown.items():
                pct = min(100, int(score * 10))
                st.markdown(clean_html(f"""
                    <div style="margin-bottom: 0.85rem;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.88rem; margin-bottom: 0.35rem;">
                            <span style="font-weight: 500; color: #E2E8F0;">{topic}</span>
                            <span style="font-family: 'JetBrains Mono', monospace; font-weight: 600; color: #60A5FA;">{score:.1f} / 10</span>
                        </div>
                        <div style="background-color: rgba(255, 255, 255, 0.08); height: 7px; border-radius: 4px; overflow: hidden;">
                            <div style="background: linear-gradient(90deg, #3B82F6 0%, #8B5CF6 100%); width: {pct}%; height: 100%; border-radius: 4px;"></div>
                        </div>
                    </div>
                """), unsafe_allow_html=True)

    # --- 5. PREPARATION ROADMAP ---
    with st.container(border=True):
        st.markdown("""
            <div style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #60A5FA; margin-bottom: 1rem;">
                🎯 Recommended Action Roadmap
            </div>
        """, unsafe_allow_html=True)
        for i, step in enumerate(report.recommended_preparation_plan):
            st.markdown(clean_html(f"""
                <div style="display: flex; gap: 0.75rem; margin-bottom: 0.65rem; font-size: 0.92rem; color: #CBD5E1; line-height: 1.5; background: rgba(255, 255, 255, 0.02); padding: 0.65rem 0.85rem; border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.05);">
                    <span style="font-family: 'JetBrains Mono', monospace; font-weight: 700; color: #60A5FA;">{i+1:02d}</span>
                    <span>{step}</span>
                </div>
            """), unsafe_allow_html=True)

        if report.key_concepts_to_revise:
            st.markdown("<div style='margin-top: 1rem; font-size: 0.75rem; text-transform: uppercase; color: #94A3B8; font-weight: 700; letter-spacing: 0.05em;'>Key Technical Terms to Revisit</div>", unsafe_allow_html=True)
            badges_html = " ".join([f"<span class='status-pill pill-hard' style='margin-right: 0.4rem; margin-top: 0.4rem;'>{c}</span>" for c in report.key_concepts_to_revise])
            st.markdown(f"<div style='margin-top: 0.4rem;'>{badges_html}</div>", unsafe_allow_html=True)

    # --- 6. DETAILED TRANSCRIPT ACCORDION ---
    with st.expander("📄 Review Full Session Transcript & Evaluations"):
        for item in timeline:
            q_info = item.get("question", {})
            ans_info = item.get("answer", {})
            q_num = q_info.get("question_number", 1)
            q_text = q_info.get("question_text") or q_info.get("question")
            ans_text = ans_info.get("answer_text", "No answer recorded.")
            topic = q_info.get("topic", "")
            diff = q_info.get("difficulty", "")

            st.markdown(f"**Question {q_num:02d}** `[{topic} | {diff}]`")
            st.markdown(f"> *{q_text}*")
            st.markdown(f"**Candidate Response:**\n```text\n{ans_text}\n```")
            st.markdown("---")

    # --- 7. ACTIONS ---
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Start Another Interview", type="primary", use_container_width=True):
            st.session_state.current_session = None
            st.session_state.current_eval = None
            st.session_state.final_report = None
            st.session_state.current_view = "home"
            st.rerun()

    with col_btn2:
        if st.button("Return to History", type="secondary", use_container_width=True):
            st.session_state.current_view = "history"
            st.rerun()
