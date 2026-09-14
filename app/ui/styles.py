"""
Complete High-End Dark Design System for Adaptive AI Interviewer
Provides comprehensive styling for Streamlit native containers, widgets,
buttons, cards, badges, and typography.
"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* --- Root Variables --- */
:root {
    --bg-dark: #07090E;
    --surface-card: #0F1626;
    --surface-elevated: #151F34;
    --border-color: rgba(255, 255, 255, 0.08);
    --border-hover: rgba(59, 130, 246, 0.4);
    --text-pure: #FFFFFF;
    --text-muted: #94A3B8;
    --primary-blue: #3B82F6;
    --primary-gradient: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
}

/* --- Global Background & Base Font --- */
html, body, .stApp {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    background-color: var(--bg-dark) !important;
    background: radial-gradient(circle at 50% 0%, rgba(37, 99, 235, 0.12) 0%, rgba(7, 9, 14, 1) 65%) !important;
    background-attachment: fixed !important;
    color: #F8FAFC !important;
}

#MainMenu, footer, header {
    display: none !important;
    visibility: hidden !important;
}

.block-container {
    max-width: 880px !important;
    padding-top: 1.5rem !important;
    padding-bottom: 3.5rem !important;
}

/* --- Typography Overrides --- */
h1, h2, h3, h4, h5, h6 {
    color: #FFFFFF !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    letter-spacing: -0.02em !important;
}

div[data-testid="stMarkdownContainer"] p,
div[data-testid="stMarkdownContainer"] span {
    color: #E2E8F0 !important;
}

label[data-testid="stWidgetLabel"] p,
label[data-testid="stWidgetLabel"] span {
    color: #94A3B8 !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
}

/* --- Streamlit Native Container (border=True) Styling --- */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #0F1626 !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 14px !important;
    padding: 1.5rem !important;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3) !important;
    margin-bottom: 1.25rem !important;
}

/* --- Buttons --- */
button[data-testid="stBaseButton-primary"], button[kind="primary"] {
    background: var(--primary-gradient) !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    transition: all 0.2s ease !important;
}

button[data-testid="stBaseButton-primary"]:hover, button[kind="primary"]:hover {
    background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
    box-shadow: 0 6px 20px rgba(37, 99, 235, 0.55) !important;
    transform: translateY(-1px) !important;
}

button[data-testid="stBaseButton-secondary"], button[kind="secondary"] {
    background: #151F34 !important;
    color: #E2E8F0 !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    transition: all 0.2s ease !important;
}

button[data-testid="stBaseButton-secondary"]:hover, button[kind="secondary"]:hover {
    background: #1C2945 !important;
    color: #FFFFFF !important;
    border-color: rgba(59, 130, 246, 0.4) !important;
    transform: translateY(-1px) !important;
}

/* --- Input Fields & Select Boxes --- */
div[data-baseweb="select"] > div {
    background-color: #121A2A !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 8px !important;
    color: #FFFFFF !important;
}

div[data-baseweb="select"] > div:hover {
    border-color: rgba(59, 130, 246, 0.4) !important;
}

div[data-baseweb="select"] span, div[data-baseweb="select"] div {
    color: #F8FAFC !important;
}

div[data-baseweb="popover"] ul {
    background-color: #121A2A !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
}

div[data-baseweb="popover"] li {
    color: #E2E8F0 !important;
}

div[data-baseweb="popover"] li:hover {
    background-color: #1E293B !important;
    color: #FFFFFF !important;
}

div[data-baseweb="base-input"] input,
div[data-baseweb="base-input"] textarea {
    background-color: #0C121F !important;
    color: #F8FAFC !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 8px !important;
    font-family: inherit !important;
}

div[data-baseweb="base-input"] textarea:focus,
div[data-baseweb="base-input"] input:focus {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.25) !important;
}

/* --- File Uploader --- */
div[data-testid="stFileUploader"] {
    background: #0C121F !important;
    border: 1px dashed rgba(255, 255, 255, 0.12) !important;
    border-radius: 10px !important;
    padding: 0.5rem !important;
}

div[data-testid="stFileUploader"]:hover {
    border-color: rgba(59, 130, 246, 0.4) !important;
}

/* --- Question Focus Card --- */
.question-focus-card {
    background: linear-gradient(180deg, #101728 0%, #0D1322 100%);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 14px;
    padding: 2.25rem 2.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    position: relative;
    overflow: hidden;
}

.question-focus-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #3B82F6 0%, #8B5CF6 50%, #10B981 100%);
}

.question-headline {
    font-size: 1.4rem;
    font-weight: 600;
    line-height: 1.5;
    color: #FFFFFF;
    letter-spacing: -0.01em;
    margin-bottom: 0.5rem;
}

/* --- Badges --- */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 3px 10px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.03em;
}

.pill-easy {
    background: rgba(16, 185, 129, 0.12);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.25);
}

.pill-medium {
    background: rgba(59, 130, 246, 0.12);
    color: #60A5FA;
    border: 1px solid rgba(59, 130, 246, 0.25);
}

.pill-hard {
    background: rgba(244, 63, 94, 0.12);
    color: #FB7185;
    border: 1px solid rgba(244, 63, 94, 0.25);
}

.pill-followup {
    background: rgba(245, 158, 11, 0.12);
    color: #FBBF24;
    border: 1px solid rgba(245, 158, 11, 0.25);
}

/* --- Diagnostic Card --- */
.diagnostic-container {
    background: linear-gradient(180deg, #111A2E 0%, #0D1424 100%);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 14px;
    padding: 2rem;
    margin-top: 1.5rem;
    margin-bottom: 1.75rem;
    box-shadow: 0 12px 35px rgba(0, 0, 0, 0.45);
}

/* --- Report Hero --- */
.report-hero-box {
    background: linear-gradient(180deg, #101728 0%, #0C111E 100%);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 2.75rem 2rem;
    margin-bottom: 1.75rem;
    text-align: center;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5);
}

.score-giant {
    font-size: 4.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #FFFFFF 0%, #94A3B8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.04em;
    line-height: 1;
    margin: 0.5rem 0 0.25rem 0;
}

/* --- Progress Dots --- */
.dot-completed {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #3B82F6;
    display: inline-block;
    box-shadow: 0 0 8px rgba(59, 130, 246, 0.6);
}

.dot-active {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background-color: #FFFFFF;
    display: inline-block;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.4), 0 0 10px rgba(255, 255, 255, 0.8);
    transform: scale(1.15);
}

.dot-pending {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: rgba(255, 255, 255, 0.15);
    display: inline-block;
}

/* --- Clean Lists --- */
.list-item-strength {
    background: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(16, 185, 129, 0.18);
    border-left: 3px solid #10B981;
    border-radius: 6px;
    padding: 0.6rem 0.85rem;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
    color: #E2E8F0;
}

.list-item-gap {
    background: rgba(244, 63, 94, 0.08);
    border: 1px solid rgba(244, 63, 94, 0.18);
    border-left: 3px solid #F43F5E;
    border-radius: 6px;
    padding: 0.6rem 0.85rem;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
    color: #E2E8F0;
}
</style>
"""
