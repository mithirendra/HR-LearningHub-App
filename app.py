import streamlit as st
import pandas as pd
import os

# ============================================================
# PAGE CONFIG
# ============================================================
from PIL import Image

favicon = Image.open("assets/mitma_favicon.png")

st.set_page_config(
    page_title="LearningHub - Demo | Mitma Consulting",
    page_icon=favicon,
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================================
# FONTS
# ============================================================
st.markdown(
    '<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&display=swap" rel="stylesheet">',
    unsafe_allow_html=True
)

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        opacity: 0;
        animation: fadeIn 0.3s ease-in 0.2s forwards;
    }
            
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stSidebarNav"] { display: none !important; }
    [data-testid="stSidebarNavItems"] { display: none !important; }
    [data-testid="stSidebarNavLink"] { display: none !important; }
    section[data-testid="stSidebar"] ul { display: none !important; }
    section[data-testid="stSidebar"] nav { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
                
    html, body, div, p, span, button, input, select, textarea,
    [class*="st-"], [data-testid], .stMarkdown {
        font-family: 'Montserrat', sans-serif !important;
    }
            
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
    [data-testid="stSidebarCollapseButton"] { display: none; }
    [data-testid="stSidebar"] { display: none; }
    .stApp { background-color: #fffbf8; }
    .block-container { padding-top: 3rem !important; max-width: 480px !important; }

    /* Role selector cards */
    div[data-testid="stRadio"] > div {
        display: flex !important;
        gap: 10px !important;
        justify-content: center !important;
    }
            
    div[data-testid="stRadio"] label {
        flex: 1 !important;
        border: 1.5px solid #f0d9cc !important;
        border-radius: 12px !important;
        padding: 14px 8px !important;
        text-align: center !important;
        cursor: pointer !important;
        background: #fff !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        gap: 6px !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        color: #505050 !important;
    }
            
    div[data-testid="stRadio"] label:has(input:checked) {
        border-color: #f49052 !important;
        color: #000 !important;
        font-weight: 700 !important;
        background: #fff8f4 !important;
    }
            
    div[data-testid="stRadio"] input[type="radio"] { display: none !important; }
    div[data-testid="stRadio"] > label { display: none !important; }

    /* Inputs */
    .stTextInput > div > div > input {
        background: #ffece1 !important;
        border: 1px solid #f0d9cc !important;
        border-radius: 8px !important;
        font-size: 13px !important;
        padding: 10px 14px !important;
    }
            
    .stSelectbox > div > div {
        background: #ffece1 !important;
        border: 1px solid #f0d9cc !important;
        border-radius: 8px !important;
    }

    /* Sign in button — full width and centered */
    div[data-testid="stButton"] {
        display: flex !important;
        justify-content: center !important;
    }
            
    div[data-testid="stButton"] > button {
        width: 100% !important;
        background-color: #f49052 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        padding: 12px !important;
        margin-top: 8px !important;
    }
            
    div[data-testid="stButton"] > button:hover {
        background-color: #505050 !important;
    }
            
</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE DEFAULTS
# ============================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "role" not in st.session_state:
    st.session_state.role = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None

# ============================================================
# REDIRECT IF ALREADY LOGGED IN
# ============================================================
if st.session_state.authenticated:
    if st.session_state.role == "Employee":
        st.switch_page("pages/01_Employee_View.py")
    elif st.session_state.role == "Manager":
        st.switch_page("pages/02_Manager_View.py")
    elif st.session_state.role == "HR":
        st.switch_page("pages/03_HR_View.py")

# ============================================================
# LOAD USER DATA
# ============================================================
@st.cache_data
def load_users():
    employees = pd.read_csv("data/employee_master.csv")
    managers  = pd.read_csv("data/manager_master.csv")
    hr_users  = pd.read_csv("data/hr_users.csv")
    return employees, managers, hr_users

employees_df, managers_df, hr_df = load_users()

# ============================================================
# LOGO — use st.image, more reliable than base64 HTML
# ============================================================
import base64

def load_logo(path="assets/mitma_logo_color.png"):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None

logo_b64 = load_logo()

if logo_b64:
    st.markdown(
        f'<div style="display:flex;justify-content:center;margin-bottom:8px;">'
        f'<a href="https://mitmaconsulting.framer.ai" target="_blank">'
        f'<img src="data:image/png;base64,{logo_b64}" style="width:130px;">'
        f'</a></div>',
        unsafe_allow_html=True
    )
# ============================================================
# APP TITLE
# ============================================================
st.markdown("""
<div style="text-align:center;margin:16px 0 32px;font-family:'Montserrat',sans-serif;">
    <div style="font-size:28px;font-weight:700;color:#000;margin-bottom:6px;">LearningHub</div>
    <div style="font-size:13px;color:#9a8880;font-weight:400;">L&D Intelligence Platform</div>
    <span style="display:inline-block;margin-top:6px;background:#f49052;color:#fff;
    font-size:8px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;
    padding:2px 9px;border-radius:20px;">Demo Version</span>
</div>
""", unsafe_allow_html=True)

# ============================================================
# LOGIN CARD
# ============================================================
with st.container(border=True):

    st.markdown("""
    <div style="font-family:'Montserrat',sans-serif;margin-bottom:16px;">
        <div style="font-size:18px;font-weight:700;color:#000;margin-bottom:4px;">Sign in</div>
        <div style="font-size:12px;color:#9a8880;">Select your role to continue</div>
    </div>
    """, unsafe_allow_html=True)

    # --- ROLE SELECTOR ---
    selected_role = st.radio(
        "Role",
        ["👤  Employee", "📊  Manager", "🏢  HR Admin"],
        horizontal=True,
        label_visibility="collapsed"
    )
    role_clean = selected_role.split("  ")[1].strip()

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # --- EMAIL ---
    st.markdown(
        '<div style="font-size:12px;font-weight:600;color:#505050;margin-bottom:6px;'
        'font-family:Montserrat,sans-serif;">Email</div>',
        unsafe_allow_html=True
    )

    if role_clean == "Employee":
        email_map = employees_df.set_index("email")[["employee_id", "name"]].to_dict("index")
    elif role_clean == "Manager":
        raw = managers_df.set_index("email")[["manager_id", "name"]].to_dict("index")
        email_map = {k: {"employee_id": v["manager_id"], "name": v["name"]} for k, v in raw.items()}
    else:
        raw = hr_df.set_index("email")[["user_id", "name"]].to_dict("index")
        email_map = {k: {"employee_id": v["user_id"], "name": v["name"]} for k, v in raw.items()}

    selected_email = st.selectbox(
        "Email",
        list(email_map.keys()),
        label_visibility="collapsed"
    )

    # --- ERROR PLACEHOLDER ---
    error_placeholder = st.empty()

    # --- SIGN IN BUTTON ---
    if st.button("Enter Demo →", use_container_width=True):
            user_record = email_map[selected_email]
            st.session_state.authenticated = True
            st.session_state.role          = "HR" if role_clean == "HR Admin" else role_clean
            st.session_state.user_id       = user_record["employee_id"]
            st.session_state.user_name     = user_record["name"]
            st.session_state.user_email    = selected_email

            if st.session_state.role == "Employee":
                st.switch_page("pages/01_Employee_View.py")
            elif st.session_state.role == "Manager":
                st.switch_page("pages/02_Manager_View.py")
            elif st.session_state.role == "HR":
                st.switch_page("pages/03_HR_View.py")

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<div style="text-align:center;margin-top:32px;font-family:'Montserrat',sans-serif;">
    <div style="font-size:10px;color:#c4b0a8;">
        © 2026 Mitma Consulting · Mitma LearningHub Demo Version 0 · Built by Mithirendra Maniam
    </div>
</div>
""", unsafe_allow_html=True)