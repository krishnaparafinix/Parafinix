"""
ui/theme.py — All CSS, the logo, and brand constants in one place.
Change the look of the whole app from this single file.
"""

THEME_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"], .stApp { font-family: 'Inter', -apple-system, sans-serif; }
    .stApp { background: #F7F9F9; }
    #MainMenu, footer, header { visibility: hidden; }

    /* Text colour fix — forces dark, readable text regardless of browser theme */
    .stApp, .stApp p, .stApp label, .stApp span, .stApp div,
    h1, h2, h3, h4, .stMarkdown, [data-testid="stWidgetLabel"] { color: #1F3346 !important; }
    .stTextInput input, .stTextArea textarea { color: #1F3346 !important; background: #FFFFFF !important; }
    .stTabs button { color: #5B6B79 !important; }
    .stTabs button[aria-selected="true"] { color: #12B8A6 !important; }
    .stButton > button { color: #FFFFFF !important; }

    .pfx-header { display: flex; align-items: center; gap: 14px; padding: 4px 0 10px 0; }
    .pfx-mark { width: 46px; height: 46px; border-radius: 13px;
        background: linear-gradient(135deg, #12B8A6 0%, #0E7C8C 100%);
        flex-shrink: 0; display: flex; align-items: center; justify-content: center; }
    .pfx-word { font-size: 1.9rem; font-weight: 800; letter-spacing: -1px;
        background: linear-gradient(90deg, #0FB5A4 0%, #16C79A 55%, #2BD4B0 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; line-height: 1; color: #12B8A6 !important; }
    .pfx-tag { font-size: 0.68rem; font-weight: 500; letter-spacing: 3px; color: #7A8A88; margin-top: 3px; }

    .stButton > button { background: linear-gradient(135deg, #12B8A6 0%, #0E7C8C 100%);
        border-radius: 9px; border: none; padding: 11px 22px; font-weight: 600;
        font-size: 0.9rem; transition: all 0.2s ease; }
    .stButton > button:hover { background: linear-gradient(135deg, #0FB5A4 0%, #0A6673 100%);
        transform: translateY(-1px); box-shadow: 0 4px 12px rgba(18,184,166,0.25); }

    div[data-testid="metric-container"] { background: white; border-radius: 12px;
        padding: 14px 16px; border: 1px solid #E4EBEA; }
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        border-radius: 9px; border: 1px solid #D8E0DE; }
    section[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E4EBEA; }

    .pass { color: #14876B; font-weight: 600; }
    .flag { color: #B8860B; font-weight: 600; }
    .miss { color: #C0392B; font-weight: 600; }

    .pfx-card { background: white; border-radius: 14px; padding: 22px;
        border: 1px solid #E4EBEA; margin-bottom: 16px; }
    .folder-card { background: white; border-radius: 12px; padding: 16px 18px;
        border: 1px solid #E4EBEA; margin-bottom: 10px; border-left: 4px solid #12B8A6; }
    .folder-name { font-weight: 700; color: #1F3346; font-size: 1.05rem; }
    .folder-meta { font-size: 0.8rem; color: #7A8A88; margin-top: 3px; }
    hr { border: none; border-top: 1px solid #E4EBEA; margin: 16px 0; }
</style>
"""

LOGO_HEADER = """
<div class="pfx-header">
    <div class="pfx-mark">
        <svg viewBox="0 0 92 92" xmlns="http://www.w3.org/2000/svg" width="46" height="46">
            <path d="M 30 68 L 30 34 Q 30 27 37 27 L 52 27 Q 63 27 63 39 Q 63 51 52 51 L 42 51"
                fill="none" stroke="#FFFFFF" stroke-width="8" stroke-linecap="round"/>
            <circle cx="58" cy="66" r="6" fill="#F5B841"/>
        </svg>
    </div>
    <div>
        <div class="pfx-word">Parafinix</div>
        <div class="pfx-tag">YOUR REPORT WINGMAN</div>
    </div>
</div>
"""
