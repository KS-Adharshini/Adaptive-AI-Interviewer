import os
import streamlit as st
from ..config import GEMINI_API_KEY, GEMINI_MODEL, DATABASE_PATH, DEFAULT_QUESTIONS_COUNT
from ..services.gemini_service import GeminiService
from ..database.db import get_all_interviews
from ..utils.helpers import setup_logger, clean_html

logger = setup_logger("SettingsView")

def render_settings_view():
    """Render application configuration and API management interface."""
    st.markdown("""
        <div style="margin-bottom: 1.75rem;">
            <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; color: #60A5FA; font-weight: 700; margin-bottom: 0.5rem; font-family: 'JetBrains Mono', monospace;">
                Configuration & Telemetry
            </div>
            <h2 style="font-size: 2rem; font-weight: 800; letter-spacing: -0.03em; color: #FFFFFF; margin: 0 0 0.5rem 0;">
                Platform Settings
            </h2>
            <p style="font-size: 0.95rem; color: #94A3B8; margin: 0;">
                Configure your Gemini API connectivity, runtime models, and local database settings.
            </p>
        </div>
    """, unsafe_allow_html=True)

    current_key = st.session_state.get("custom_api_key") or os.getenv("GEMINI_API_KEY", "")
    gemini = GeminiService(api_key=current_key)
    is_active = gemini.is_configured()

    # --- Section 1: Gemini API Status ---
    with st.container(border=True):
        st.markdown("""
            <div style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #60A5FA; margin-bottom: 1rem;">
                ⚡ Gemini API Inference Engine
            </div>
        """, unsafe_allow_html=True)

        if is_active:
            masked_key = current_key[:6] + "..." + current_key[-4:] if len(current_key) > 10 else "Configured"
            st.markdown(clean_html(f"""
                <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 8px; padding: 0.85rem 1rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 0.9rem; font-weight: 700; color: #34D399;">● Live AI Inference Connected</div>
                        <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 0.2rem;">Model: <code style="color: #60A5FA;">{gemini.model_name}</code> | Key: <code>{masked_key}</code></div>
                    </div>
                    <span class="status-pill pill-easy">Online</span>
                </div>
            """), unsafe_allow_html=True)
        else:
            st.markdown(clean_html("""
                <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.2); border-radius: 8px; padding: 0.85rem 1rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 0.9rem; font-weight: 700; color: #FBBF24;">● Sandbox Mode Active</div>
                        <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 0.2rem;">Running local mock engine. Provide a Gemini API key below to activate live AI reasoning.</div>
                    </div>
                    <span class="status-pill pill-medium">Sandbox</span>
                </div>
            """), unsafe_allow_html=True)

        new_key_input = st.text_input(
            "Update or Override Gemini API Key",
            value="",
            type="password",
            placeholder="Paste your Gemini API key (AIzaSy...)",
            help="Saved in memory for this session, or set permanently in .env"
        )

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Apply API Key", type="primary", use_container_width=True):
                if new_key_input.strip():
                    st.session_state.custom_api_key = new_key_input.strip()
                    os.environ["GEMINI_API_KEY"] = new_key_input.strip()
                    st.success("API key updated for current session!")
                    st.rerun()
                else:
                    st.warning("Please enter a valid key string.")

        with col_btn2:
            if st.button("Test Connection Ping", type="secondary", use_container_width=True):
                with st.spinner("Pinging Gemini API..."):
                    test_gemini = GeminiService(api_key=new_key_input.strip() if new_key_input.strip() else current_key)
                    if test_gemini.test_connection():
                        st.success("✓ Gemini API connection test succeeded!")
                    else:
                        st.error("✗ Connection test failed. Check the key and internet access.")

    # --- Section 2: Storage & Database ---
    with st.container(border=True):
        st.markdown("""
            <div style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #60A5FA; margin-bottom: 1rem;">
                💾 Local SQLite Persistence
            </div>
        """, unsafe_allow_html=True)

        past_records = get_all_interviews()
        st.markdown(f"""
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 8px; padding: 0.85rem 1rem;">
                    <div style="font-size: 0.72rem; text-transform: uppercase; color: #94A3B8; font-weight: 600;">Database Location</div>
                    <div style="font-size: 0.85rem; font-family: 'JetBrains Mono', monospace; color: #E2E8F0; margin-top: 0.35rem; word-break: break-all;">{DATABASE_PATH}</div>
                </div>
                <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 8px; padding: 0.85rem 1rem;">
                    <div style="font-size: 0.72rem; text-transform: uppercase; color: #94A3B8; font-weight: 600;">Persisted Records</div>
                    <div style="font-size: 1.3rem; font-weight: 800; color: #60A5FA; margin-top: 0.2rem;">{len(past_records)} sessions</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # --- Section 3: Architecture & Security ---
    with st.container(border=True):
        st.markdown("""
            <div style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #60A5FA; margin-bottom: 0.75rem;">
                🛡️ Security & Architecture Standards
            </div>
            <ul style="margin: 0; padding-left: 1.25rem; font-size: 0.9rem; color: #CBD5E1; line-height: 1.7;">
                <li><strong>Zero Local GPU Load:</strong> All LLM inference runs remotely on the Google Gemini API.</li>
                <li><strong>Complete Data Isolation:</strong> Interview questions, transcripts, and resumes remain local to your machine.</li>
                <li><strong>Key Sanitization:</strong> Keys are accessed via environment variables and never logged or exposed in raw output.</li>
            </ul>
        """, unsafe_allow_html=True)
