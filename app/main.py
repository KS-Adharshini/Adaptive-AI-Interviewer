import os
import sys
from pathlib import Path

# Ensure application modules can be resolved cleanly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from app.database.db import init_db
from app.services.gemini_service import GeminiService
from app.ui.styles import CUSTOM_CSS
from app.ui.views_home import render_home_view
from app.ui.views_interview import render_interview_view
from app.ui.views_results import render_results_view
from app.ui.views_history import render_history_view
from app.ui.views_settings import render_settings_view

# Configure Streamlit page parameters
st.set_page_config(
    page_title="Adaptive AI Interviewer",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Apply editorial dark minimalist styles
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialize SQLite database schema
init_db()

# Initialize session state variables
if "current_view" not in st.session_state:
    st.session_state.current_view = "home"
if "current_session" not in st.session_state:
    st.session_state.current_session = None
if "current_eval" not in st.session_state:
    st.session_state.current_eval = None
if "answer_submitted" not in st.session_state:
    st.session_state.answer_submitted = False
if "final_report" not in st.session_state:
    st.session_state.final_report = None
if "inspect_interview_id" not in st.session_state:
    st.session_state.inspect_interview_id = None

# Gemini client check for live header badge
gemini = GeminiService()
is_configured = gemini.is_configured()
status_badge = (
    f'<span class="brand-badge" style="background: rgba(16, 185, 129, 0.12); color: #34D399; border-color: rgba(16, 185, 129, 0.25);">● {gemini.model_name}</span>'
    if is_configured else
    '<span class="brand-badge" style="background: rgba(245, 158, 11, 0.12); color: #FBBF24; border-color: rgba(245, 158, 11, 0.25);">● Sandbox Mode</span>'
)

# Top Brand Bar
st.markdown(f"""
    <div class="brand-container">
        <div>
            <div class="brand-title">
                <span style="background: linear-gradient(135deg, #60A5FA 0%, #A78BFA 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">⚡ ADAPTIVE</span>
                <span style="font-weight: 400; color: #94A3B8;">INTERVIEWER</span>
            </div>
            <div class="brand-subtitle">Autonomous Adaptive Technical Assessment Platform</div>
        </div>
        <div>
            {status_badge}
        </div>
    </div>
""", unsafe_allow_html=True)

# Sleek segmented navigation
has_active_session = st.session_state.current_session is not None and not st.session_state.current_session.completed
current_v = st.session_state.current_view

nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)

with nav_col1:
    btn_type = "primary" if current_v == "home" else "secondary"
    if st.button("Configure", key="nav_home", type=btn_type, use_container_width=True):
        st.session_state.current_view = "home"
        st.session_state.inspect_interview_id = None
        st.rerun()

with nav_col2:
    btn_type = "primary" if current_v == "interview" else "secondary"
    label = "Active Session ●" if has_active_session else "Session"
    if st.button(label, key="nav_session", type=btn_type, use_container_width=True, disabled=not has_active_session):
        st.session_state.current_view = "interview"
        st.session_state.inspect_interview_id = None
        st.rerun()

with nav_col3:
    btn_type = "primary" if current_v == "history" else "secondary"
    if st.button("History", key="nav_history", type=btn_type, use_container_width=True):
        st.session_state.current_view = "history"
        st.session_state.inspect_interview_id = None
        st.rerun()

with nav_col4:
    btn_type = "primary" if current_v == "settings" else "secondary"
    if st.button("Settings", key="nav_settings", type=btn_type, use_container_width=True):
        st.session_state.current_view = "settings"
        st.session_state.inspect_interview_id = None
        st.rerun()

st.markdown("<div style='margin-bottom: 1.75rem;'></div>", unsafe_allow_html=True)

# Page Router
if current_v == "home":
    render_home_view()
elif current_v == "interview":
    render_interview_view()
elif current_v == "results":
    render_results_view()
elif current_v == "history":
    render_history_view()
elif current_v == "settings":
    render_settings_view()
else:
    render_home_view()
