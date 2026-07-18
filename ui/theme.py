"""
ui/theme.py — All CSS, the logo, and brand constants in one place.
Change the look of the whole app from this single file.
"""
THEME_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"], .stApp { font-family: 'Inter', -apple-system, sans-serif; }
    .stApp { background: #F8FAFC; }
    #MainMenu, footer, header { visibility: hidden; }

    @keyframes pfxPulseDot {
        0%, 100% { box-shadow: 0 0 0 0 rgba(16,185,129,0.45); }
        50% { box-shadow: 0 0 0 7px rgba(16,185,129,0); }
    }
    @keyframes pfxFadeInUp {
        from { opacity: 0; transform: translateY(6px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .stApp, .stApp p, .stApp label, .stApp span, .stApp div,
    h1, h2, h3, h4, .stMarkdown, [data-testid="stWidgetLabel"] { color: #0B1F3A !important; }
    .stTextInput input, .stTextArea textarea { color: #0B1F3A !important; background: #FFFFFF !important; }
    .stTabs button { color: #64748B !important; transition: color 0.15s ease !important; }
    .stTabs button[aria-selected="true"] { color: #3B82F6 !important; }
    .stButton > button { color: #FFFFFF !important; }

    .pfx-header { display: flex; align-items: center; gap: 14px; padding: 4px 0 10px 0;
        animation: pfxFadeInUp 0.4s ease both; }
    .pfx-mark { width: 46px; height: 46px; border-radius: 13px;
        background: #0B1F3A;
        flex-shrink: 0; display: flex; align-items: center; justify-content: center; position: relative; }
    .pfx-mark .pfx-node { animation: pfxPulseDot 2.2s ease-in-out infinite; border-radius: 50%; }
    .pfx-word { font-size: 1.9rem; font-weight: 800; letter-spacing: -1px;
        color: #0B1F3A; line-height: 1; }
    .pfx-tag { font-size: 0.68rem; font-weight: 600; letter-spacing: 3px; color: #10B981; margin-top: 3px; }

    .stButton > button {
        background: #10B981 !important; border-radius: 9px !important; border: none !important; padding: 11px 22px !important;
        font-weight: 600 !important; font-size: 0.9rem !important;
        transition: background 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease !important; }
    .stButton > button:hover {
        background: #0E9A6E !important; transform: translateY(-1px) !important;
        box-shadow: 0 4px 14px rgba(16,185,129,0.35) !important; }
    .stButton > button:active { transform: translateY(0) !important; }

    div[data-testid="metric-container"] { background: white !important; border-radius: 12px !important;
        padding: 14px 16px !important; border: 1px solid #E2E8F0 !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
        animation: pfxFadeInUp 0.4s ease both; }
    div[data-testid="metric-container"]:hover {
        border-color: #3B82F6 !important; box-shadow: 0 4px 12px rgba(59,130,246,0.15) !important; }

    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        border-radius: 9px !important; border: 1px solid #E2E8F0 !important;
        transition: border-color 0.15s ease !important; }
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
        border-color: #3B82F6 !important; }

    section[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E2E8F0; }

    .pass { color: #0E9A6E; font-weight: 600; }
    .flag { color: #B8860B; font-weight: 600; }
    .miss { color: #C0392B; font-weight: 600; }

    .pfx-card { background: white !important; border-radius: 14px !important; padding: 22px !important;
        border: 1px solid #E2E8F0 !important; margin-bottom: 16px !important;
        transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease !important;
        animation: pfxFadeInUp 0.35s ease both; }
    .pfx-card:hover {
        border-color: #3B82F6 !important; transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(11,31,58,0.14) !important; }

    .folder-card { background: white !important; border-radius: 12px !important; padding: 16px 18px !important;
        border: 1px solid #E2E8F0 !important; margin-bottom: 10px !important; border-left: 4px solid #10B981 !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease !important;
        animation: pfxFadeInUp 0.35s ease both; }
    .folder-card:hover {
        transform: translateX(4px) !important;
        box-shadow: 0 4px 16px rgba(11,31,58,0.12) !important;
        border-left-color: #3B82F6 !important; }
    .folder-name { font-weight: 700; color: #0B1F3A; font-size: 1.05rem; }
    .folder-meta { font-size: 0.8rem; color: #64748B; margin-top: 3px; }

    hr { border: none; border-top: 1px solid #E2E8F0; margin: 16px 0; }
</style>
"""

LOGO_HEADER = """
<div class="pfx-header">
    <div class="pfx-mark">
        <svg viewBox="0 0 92 92" xmlns="http://www.w3.org/2000/svg" width="46" height="46">
            <path d="M 30 68 L 30 34 Q 30 27 37 27 L 52 27 Q 63 27 63 39 Q 63 51 52 51 L 42 51"
                fill="none" stroke="#FFFFFF" stroke-width="8" stroke-linecap="round"/>
            <circle class="pfx-node" cx="58" cy="66" r="6" fill="#10B981"/>
        </svg>
    </div>
    <div>
        <div class="pfx-word">Parafinix</div>
        <div class="pfx-tag">YOUR REPORT WINGMAN</div>
    </div>
</div>
"""