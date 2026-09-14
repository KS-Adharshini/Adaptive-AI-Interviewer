import streamlit as st
from ..database.db import get_all_interviews
from .views_results import render_results_view
from ..utils.helpers import setup_logger, clean_html

logger = setup_logger("HistoryView")

def render_history_view():
    """Render historical interview sessions saved locally in SQLite."""
    inspect_id = st.session_state.get("inspect_interview_id")
    if inspect_id:
        if st.button("← Return to All Sessions", type="secondary"):
            st.session_state.inspect_interview_id = None
            st.rerun()
        render_results_view(target_session_id=inspect_id)
        return

    st.markdown("""
        <div style="margin-bottom: 1.75rem;">
            <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; color: #60A5FA; font-weight: 700; margin-bottom: 0.5rem; font-family: 'JetBrains Mono', monospace;">
                Audit Log & Persistence
            </div>
            <h2 style="font-size: 2rem; font-weight: 800; letter-spacing: -0.03em; color: #FFFFFF; margin: 0 0 0.5rem 0;">
                Completed Interviews
            </h2>
            <p style="font-size: 0.95rem; color: #94A3B8; margin: 0;">
                All assessments, transcripts, and evaluation metrics stored securely in local SQLite database.
            </p>
        </div>
    """, unsafe_allow_html=True)

    interviews = get_all_interviews()
    if not interviews:
        with st.container(border=True):
            st.markdown("""
                <div style="text-align: center; padding: 2rem 1rem;">
                    <div style="font-size: 1.1rem; font-weight: 700; color: #F8FAFC; margin-bottom: 0.5rem;">
                        No recorded sessions found
                    </div>
                    <div style="font-size: 0.9rem; color: #94A3B8; margin-bottom: 1.25rem;">
                        Configure and launch your first adaptive interview session to view performance metrics here.
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Start First Interview →", type="primary", use_container_width=True):
                st.session_state.current_view = "home"
                st.rerun()
        return

    # Render interview records
    for row in interviews:
        i_id = row["id"]
        role = row["role"]
        exp = row["experience"]
        date_raw = row["created_at"]
        date_str = date_raw[:10] if date_raw else "Recent"
        score = row.get("overall_score", 0.0)
        mode = row.get("difficulty_mode", "Adaptive")
        total_q = row.get("total_questions", 5)
        completed = bool(row.get("completed", 0))

        score_text = f"{score:.0f}%" if completed else "Incomplete"
        score_color = "#34D399" if score >= 75 else ("#60A5FA" if score >= 55 else "#FB7185")

        with st.container(border=True):
            col_info, col_score, col_btn = st.columns([3, 1, 1.2])
            with col_info:
                st.markdown(clean_html(f"""
                    <div style="font-size: 1.05rem; font-weight: 700; color: #FFFFFF;">{role}</div>
                    <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 0.25rem;">
                        <span style="font-family: 'JetBrains Mono', monospace; color: #64748B;">{date_str}</span> • {exp} • {mode} • {total_q} Questions
                    </div>
                """), unsafe_allow_html=True)
            with col_score:
                st.markdown(clean_html(f"""
                    <div style="text-align: center;">
                        <div style="font-size: 1.4rem; font-weight: 800; color: {score_color}; font-family: 'JetBrains Mono', monospace;">
                            {score_text}
                        </div>
                    </div>
                """), unsafe_allow_html=True)
            with col_btn:
                if st.button("View Report", key=f"btn_view_{i_id}", type="secondary", use_container_width=True):
                    st.session_state.inspect_interview_id = i_id
                    st.rerun()
