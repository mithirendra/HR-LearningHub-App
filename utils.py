import streamlit as st
import pandas as pd
import base64
from pipeline import run_pipeline

   
# ============================================================
# BRAND CONSTANTS
# ============================================================
COLOURS = {
    "bg":        "#fffbf8",
    "sidebar":   "#1a1008",
    "accent":    "#f49052",
    "card":      "#ffffff",
    "border":    "#f0d9cc",
    "text":      "#505050",
    "muted":     "#9a8880",
    "complete":  "#2e7d32",
    "inprog":    "#e65100",
    "pending":   "#c62828",
}

PRIORITY_COLOURS = {
    "Critical": ("#c62828", "#fdecea"),
    "High":     ("#e65100", "#fff3e0"),
    "Medium":   ("#2e7d32", "#e8f5e9"),
    "Low":      ("#9a8880", "#f0d9cc"),
}

STATUS_COLOURS = {
    "Completed":   ("#2e7d32", "#e8f5e9"),
    "In Progress": ("#e65100", "#fff3e0"),
    "Enrolled":    ("#c62828", "#fdecea"),
    "Dropped":     ("#9a8880", "#f0d9cc"),
}

DOMAIN_MAP = {
    "Digital":    ["Power BI", "Tableau", "Excel", "Python", "SQL", "Machine Learning"],
    "Leadership": ["Leadership", "Coaching", "Stakeholder Management", "Change Management"],
    "Technical":  ["Data Analysis", "Risk Management", "Agile", "Project Management"],
    "Functional": ["Employment Law", "Recruitment", "Budgeting", "Communication"],
}

# ============================================================
# DATA
# ============================================================
@st.cache_data
def load_all_data():
    """Load and cache all six CSVs. Call once per session."""
    return {
        "master":   pd.read_csv("data/employee_master.csv"),
        "skills":   pd.read_csv("data/employee_skills.csv"),
        "enrol":    pd.read_csv("data/enrolment_data.csv"),
        "courses":  pd.read_csv("data/course_catalogue.csv"),
        "tna":      pd.read_csv("data/tna_data.csv"),
        "needed":   pd.read_csv("data/skills_needed.csv"),
        "forecast": pd.read_csv("data/skills_forecast.csv"),
        "managers": pd.read_csv("data/manager_master.csv"),
        "hr_users": pd.read_csv("data/hr_users.csv"),
    }

# ============================================================
# STYLING
# ============================================================
def inject_fonts():
    """Inject Montserrat via link tag — more reliable than @import."""
    st.markdown(
        '<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&display=swap" rel="stylesheet">',
        unsafe_allow_html=True
    )

def inject_css():
    """Inject full Mitma brand CSS."""
    st.markdown(f"""
    <style>
        [data-testid="stAppViewContainer"] {{
            opacity: 0;
            animation: fadeIn 0.3s ease-in 0.2s forwards;
        }}
                
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        [data-testid="stHeader"] {{ display: none !important; }}
        [data-testid="stSidebarNav"] {{ display: none !important; }}
        [data-testid="stSidebarNavItems"] {{ display: none !important; }}
        [data-testid="stSidebarNavLink"] {{ display: none !important; }}
        section[data-testid="stSidebar"] ul {{ display: none !important; }}
        section[data-testid="stSidebar"] nav {{ display: none !important; }}     
        [data-testid="stDecoration"] {{ display: none !important; }}
                
        html, body, div, p, span, button, input, select, textarea,
        [class*="st-"], [data-testid], .stMarkdown, .stSelectbox,
        .stMetric, .stButton, .element-container {{
            font-family: 'Montserrat', sans-serif !important;
        }}
                
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        [data-testid="stSidebarCollapseButton"] {{ display: none; }}
        .stApp {{ background-color: {COLOURS['bg']}; }}
        [data-testid="stSidebar"] {{ background-color: {COLOURS['sidebar']} !important; text-align: center !important; }}
        [data-testid="stSidebarContent"] {{ background-color: {COLOURS['sidebar']} !important; text-align: center !important; }}
        [data-testid="stSidebar"] .stSelectbox {{ text-align: left !important; }}
        .block-container {{ padding-top: 2rem !important; }}
        div[data-testid="metric-container"] {{
            background: {COLOURS['card']};
            border: 1px solid {COLOURS['border']};
            border-radius: 12px;
            padding: 12px 16px;
        }}

        div[data-testid="metric-container"] label {{
            font-size: 10px !important;
            font-weight: 700 !important;
            color: {COLOURS['muted']} !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-family: 'Montserrat', sans-serif !important;
        }}

        div[data-testid="metric-container"] div[data-testid="stMetricValue"] {{
            font-size: 26px !important;
            font-weight: 700 !important;
            color: #000 !important;
            font-family: 'Montserrat', sans-serif !important;
        }}

        .stButton > button {{
            background-color: {COLOURS['accent']} !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-family: 'Montserrat', sans-serif !important;
            font-weight: 700 !important;
        }}

        .stButton > button:hover {{ background-color: {COLOURS['text']} !important; }}
        .stSelectbox > div > div {{
            background: #ffece1 !important;
            border: 1px solid {COLOURS['border']} !important;
            font-family: 'Montserrat', sans-serif !important;
        }}

        .stTextInput > div > div > input {{
            background: #ffece1 !important;
            border: 1px solid {COLOURS['border']} !important;
            font-family: 'Montserrat', sans-serif !important;
        }}

        div[data-testid="stForm"] {{
            background: {COLOURS['card']} !important;
            border: 1px solid {COLOURS['border']} !important;
            border-radius: 12px !important;
            padding: 20px !important;
        }}

        /* Sign out button — white background, dark text */
        section[data-testid="stSidebar"] div.stButton {{
            width: 100% !important;
            display: block !important;
        }}

        section[data-testid="stSidebar"] div.stButton > button {{
            width: 100% !important;
            background-color: transparent !important;
            color: #c4a090 !important;
            border: 1px solid #3a2010 !important;
            font-size: 13px !important;
            font-weight: 600 !important;
        }}

        section[data-testid="stSidebar"] div.stButton > button:hover {{
            background-color: #c62828 !important;
            color: #fff !important;
            border-color: #c62828 !important;
        }}

        section[data-testid="stSidebar"] div[data-testid="stButton"] button {{
            background: transparent !important;
            color: #c4a090 !important;
            border: none !important;
            text-align: left !important;
            width: 100% !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            padding: 8px 10px !important;
            border-radius: 8px !important;
            font-family: 'Montserrat', sans-serif !important;
            margin-bottom: 2px !important;
            display: block !important;
        }}
        section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {{
            background: #2e1e0e !important;
            color: #fff !important;
        }}

    </style>
    """, unsafe_allow_html=True)

def setup_page(title):
    """Run at the top of every page: page config, fonts, CSS."""
    from PIL import Image
    try:
        favicon = Image.open("assets/mitma_favicon.png")
    except FileNotFoundError:
        favicon = "📚"

    st.set_page_config(
        page_title=f"{title} - Mitma LearningHub",
        page_icon=favicon,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    inject_fonts()
    inject_css()

# ============================================================
# LOGO
# ============================================================
def load_logo(path="assets/mitma_logo_bw.png"):
    """Load logo as base64. Returns empty string if file not found."""
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None

def logo_html():
    """Return centred, linked logo HTML block."""
    b64 = load_logo()
    if not b64:
        return ""
    return (
        f'<div style="display:flex;justify-content:center;margin-top:10px;">'
        f'<a href="https://mitmaconsulting.framer.ai" target="_blank">'
        f'<img src="data:image/png;base64,{b64}" style="width:120px;"></a></div>'
    )

# ============================================================
# SIDEBAR
# ============================================================
def render_sidebar_brand():
    """Render Mitma wordmark, LearningHub title and logo."""
    st.markdown(f"""
    <div style="padding:8px 0 16px;font-family:'Montserrat',sans-serif;text-align:center;">
        <div style="font-size:9px;font-weight:700;color:{COLOURS['accent']};letter-spacing:2px;
        text-transform:uppercase;margin-bottom:4px;">Mitma Consulting</div>
        <div style="font-size:16px;font-weight:700;color:#fff;">
            Learning<span style="color:{COLOURS['accent']};">Hub</span>
        </div>
        {logo_html()}
        <span style="display:inline-block;margin-top:6px;background:#f49052;color:#fff;
        font-size:8px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;
        padding:2px 9px;border-radius:20px;">Demo Version</span>
    </div>
    <div style="height:1px;background:#3a2010;margin-bottom:16px;"></div>
    """, unsafe_allow_html=True)

def render_sidebar_user(name, role, department):
    """Render the selected user card in the sidebar."""
    st.markdown(f"""
    <div style="margin:12px 0;padding:12px;background:#2e1e0e;border-radius:10px;
    font-family:'Montserrat',sans-serif;text-align:center;margin-bottom:40px;">
        <div style="font-size:13px;font-weight:700;color:#fff;">{name}</div>
        <div style="font-size:12px;color:#c4a090;margin-top:2px;">{role} · {department}</div>
    </div>
    <div style="height:1px;background:#3a2010;margin:12px 0;"></div>
    """, unsafe_allow_html=True)

def render_sidebar_nav(items, group_label="Navigation", state_key="nav_active"):
    """
    Active nav item renders as styled HTML div.
    Inactive items render as st.button styled to match.
    No radio buttons.
    """
    if state_key not in st.session_state:
        st.session_state[state_key] = next((l for l, a in items if a), items[0][0])

    active = st.session_state[state_key]

    st.markdown(f"""
    <div style="font-size:11px;font-weight:700;color:#c4a090;letter-spacing:1.5px;
    text-transform:uppercase;margin-bottom:10px;font-family:'Montserrat',sans-serif;">
    {group_label}</div>
    """, unsafe_allow_html=True)

    for label, _ in items:
        if label == active:
            st.markdown(f"""
            <div style="background:#f49052;color:#fff;padding:8px 10px;border-radius:8px;
            margin-bottom:2px;font-size:13px;font-weight:600;
            font-family:'Montserrat',sans-serif;">{label}</div>
            """, unsafe_allow_html=True)
        else:
            if st.button(label, key=f"{state_key}_{label}"):
                st.session_state[state_key] = label
                st.rerun()

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    st.markdown("<div style='height:1px;background:#3a2010;margin-bottom:16px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <style>
    .signout-btn{width:100%;padding:10px 0;background:#2e1e0e;color:#c4a090;
    border:1px solid #3a2010;border-radius:8px;font-size:13px;font-weight:600;
    font-family:'Montserrat',sans-serif;cursor:pointer;letter-spacing:0.3px;transition:all 0.2s ease;}
    .signout-btn:hover{background-color:#f49052 !important;color:#fff !important;border-color:#c62828 !important;}
    </style>
    <form action="" method="get">
        <input type="hidden" name="signout" value="1">
        <button type="submit" class="signout-btn">Sign Out</button>
    </form>
    """, unsafe_allow_html=True)

    return active

# ============================================================
# COMPONENTS
# ============================================================
def render_hero(eyebrow, title, subtitle):
    """Render the dark Mitma hero banner."""
    st.markdown(f"""
    <div style="background:{COLOURS['sidebar']};border-radius:14px;padding:24px 28px;
    margin-bottom:24px;position:relative;overflow:hidden;font-family:'Montserrat',sans-serif;">
        <div style="position:absolute;right:20px;top:50%;transform:translateY(-50%);
        width:120px;height:120px;border-radius:50%;border:1px solid #2e1e0e;opacity:0.4;"></div>
        <div style="position:absolute;right:42px;top:50%;transform:translateY(-50%);
        width:78px;height:78px;border-radius:50%;border:1px solid #3e2e1e;opacity:0.4;"></div>
        <div style="font-size:9px;font-weight:700;color:{COLOURS['accent']};letter-spacing:2px;
        text-transform:uppercase;margin-bottom:6px;">{eyebrow}</div>
        <div style="font-size:22px;font-weight:700;color:#fff;margin-bottom:2px;">{title}</div>
        <div style="font-size:12px;color:#c4a090;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def section_label(text):
    """Render a full-width Mitma section divider label."""
    st.markdown(f"""
    <div style="font-size:9px;font-weight:700;color:{COLOURS['muted']};letter-spacing:1.5px;
    text-transform:uppercase;margin:20px 0 12px;display:flex;align-items:center;
    gap:8px;font-family:'Montserrat',sans-serif;">
        {text}<div style="flex:1;height:1px;background:{COLOURS['border']};"></div>
    </div>
    """, unsafe_allow_html=True)

def status_badge(status):
    """Return an inline HTML status pill string."""
    fg, bg = STATUS_COLOURS.get(status, ("#9a8880", "#f0d9cc"))
    return (
        f'<span style="background:{bg};color:{fg};font-size:9px;font-weight:700;'
        f'padding:2px 9px;border-radius:20px;font-family:Montserrat,sans-serif;">'
        f'{status}</span>'
    )

def priority_badge(priority):
    """Return an inline HTML priority pill string."""
    fg, bg = PRIORITY_COLOURS.get(priority, ("#9a8880", "#f0d9cc"))
    return (
        f'<span style="background:{bg};color:{fg};font-size:9px;font-weight:700;'
        f'padding:2px 9px;border-radius:20px;font-family:Montserrat,sans-serif;">'
        f'{priority}</span>'
    )

def render_footer():
    """Render the standard Mitma page footer."""
    st.markdown("""
    <div style="margin-top:40px;padding-top:16px;border-top:1px solid #f0d9cc;
    text-align:center;font-family:'Montserrat',sans-serif;">
        <div style="font-size:10px;color:#c4b0a8;">
            © 2026 Mitma Consulting · Mitma LearningHub Demo Version 0 · Built by MM
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# CALCULATIONS
# ============================================================
def bar_color(pct):
    """Return Mitma status colour based on percentage value."""
    if pct >= 75: return COLOURS["complete"]
    elif pct >= 40: return COLOURS["accent"]
    return COLOURS["pending"]

def level_pct(level):
    """Convert skill level string to percentage."""
    return {"Beginner": 30, "Intermediate": 65, "Advanced": 90}.get(level, 50)

def progress_pct(status):
    """Map enrolment status to a display percentage."""
    return {"Completed": 100, "In Progress": 55, "Enrolled": 5, "Dropped": 0}.get(status, 0)

def domain_score(emp_id, domain, skills_df):
    """Calculate average skill score for an employee within a domain."""
    domain_skills = DOMAIN_MAP[domain]
    emp_skills    = skills_df[
        (skills_df["employee_id"] == emp_id) &
        (skills_df["skill_name"].isin(domain_skills))
    ]
    if emp_skills.empty:
        return 0
    return round(emp_skills["skill_level"].apply(level_pct).mean())

def auth_check(required_role=None):
    """
    Call at the top of every page.
    Redirects to login if not authenticated.
    Redirects to login if role does not match required_role.
    """
    if not st.session_state.get("authenticated", False):
        st.switch_page("app.py")

    if required_role and st.session_state.get("role") != required_role:
        st.warning(f"This page is for {required_role} users only.")
        st.switch_page("app.py")

def trigger_pipeline():
    """Run the Skills Feed Pipeline and clear the data cache.
    Call this after any skills upload or manager skills declaration."""
    summary = run_pipeline(verbose=False)
    st.cache_data.clear()
    return summary

def page_title(title, subtitle=""):
    """Render a page title with optional one-line subtitle."""
    sub = f'<div style="font-size:13px;color:#9a8880;margin-top:4px;font-family:Montserrat,sans-serif;">{subtitle}</div>' if subtitle else ""
    st.markdown(f"""
    <div style="margin-bottom:20px;font-family:Montserrat,sans-serif;">
        <div style="font-size:20px;font-weight:700;color:#000;">{title}</div>
        {sub}
    </div>
    """, unsafe_allow_html=True)

def locked_section(description="This feature is available in the full version of LearningHub."):
    """Render a Full Version Only lock notice with logo and CTAs."""
    b64 = load_logo()
    lock_logo = load_logo("assets/mitma_logo_color.png")
    logo = (
        f'<div style="margin:16px 0;">'
        f'<a href="https://mitmaconsulting.framer.ai" target="_blank">'
        f'<img src="data:image/png;base64,{lock_logo}" style="width:120px;"></a>'
        f'</div>'
        if lock_logo else ""
    )
    st.markdown(f"""
    <div style="background:#fff;border:2px dashed #f0d9cc;border-radius:14px;
    padding:48px 32px;text-align:center;font-family:'Montserrat',sans-serif;margin-top:8px;">
        <div style="font-size:32px;margin-bottom:14px;">🔒</div>
        <div style="font-size:17px;font-weight:700;color:#000;margin-bottom:8px;">Full Version Only</div>
        <div style="font-size:13px;color:#9a8880;margin-bottom:16px;max-width:400px;
        margin-left:auto;margin-right:auto;line-height:1.6;">{description}</div>
        {logo}
        <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-top:16px;">
            <a href="https://mitmaconsulting.framer.ai/contact" target="_blank"
            style="background:#f49052;color:#fff;padding:11px 22px;border-radius:8px;
            font-size:13px;font-weight:700;text-decoration:none;font-family:'Montserrat',sans-serif;">
                Contact Mitma Consulting →
            </a>
            <a href="https://www.linkedin.com/in/mithirendra-maniam/" target="_blank"
            style="background:#f49052;color:#fff;padding:11px 22px;border-radius:8px;
            font-size:13px;font-weight:700;text-decoration:none;font-family:'Montserrat',sans-serif;">
                Connect on LinkedIn →
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)