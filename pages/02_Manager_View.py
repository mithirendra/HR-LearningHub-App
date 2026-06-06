import streamlit as st
import pandas as pd
from utils import (
    setup_page, load_all_data,
    render_sidebar_brand, render_sidebar_user, render_sidebar_nav,
    render_hero, render_footer, section_label, page_title,
    status_badge, bar_color, level_pct, progress_pct,
    PRIORITY_COLOURS, STATUS_COLOURS, DOMAIN_MAP, COLOURS, trigger_pipeline, locked_section
)
from utils import auth_check

# ============================================================
# SIGN OUT
# ============================================================
if st.query_params.get("signout") == "1":
    st.query_params.clear()
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.switch_page("app.py")

# ============================================================
# AUTH + PAGE SETUP
# ============================================================
auth_check("Manager")
setup_page("Manager View")

# ============================================================
# LOAD DATA
# ============================================================
data       = load_all_data()
master_df  = data["master"]
skills_df  = data["skills"]
enrol_df   = data["enrol"]
courses_df = data["courses"]
tna_df     = data["tna"]
needed_df  = data["needed"]

# ============================================================
# MANAGER — from session state
# ============================================================
selected_mgr_id = st.session_state.user_id
mgr_team        = master_df[master_df["manager_id"] == selected_mgr_id]
mgr_dept        = mgr_team["department"].mode()[0] if not mgr_team.empty else "Unknown"

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    render_sidebar_brand()
    render_sidebar_user(st.session_state.user_name, "Manager", mgr_dept)
    active_nav = render_sidebar_nav([
        ("Team Overview",  True),
        ("Skills Upload",  False),
        ("Assign Courses", False),
        ("Team Status",    False),
        ("Team Recommendations", False),
    ], group_label="My Team")

# ============================================================
# TEAM DATA
# ============================================================
team        = master_df[master_df["manager_id"] == selected_mgr_id]
team_ids    = team["employee_id"].tolist()
team_enrol  = enrol_df[enrol_df["employee_id"].isin(team_ids)]
team_skills = skills_df[skills_df["employee_id"].isin(team_ids)]

total_members  = len(team)
active_courses = len(team_enrol[team_enrol["status"].isin(["Enrolled", "In Progress"])])
completed      = len(team_enrol[team_enrol["status"] == "Completed"])
team_gap       = (
    round(len(team_skills[team_skills["skill_level"] == "Beginner"]) / len(team_skills) * 100)
    if not team_skills.empty else 0
)

# ============================================================
# HERO
# ============================================================
render_hero(
    eyebrow  = f"Manager View · {mgr_dept} Department",
    title    = "Team Learning Command",
    subtitle = f"{st.session_state.user_name} · {mgr_dept} · {total_members} direct reports"
)

# ============================================================
# METRIC CARDS
# ============================================================
c1, c2, c3, c4 = st.columns(4)
c1.metric("Team Members",   total_members)
c2.metric("Active Courses", active_courses)
c3.metric("Completed",      completed)
c4.metric("Team Gap Score", f"{team_gap}%")

st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)


# ============================================================
# TEAM OVERVIEW
# ============================================================
if active_nav == "Team Overview":

    page_title("Team Overview", "Skills gap heatmap and learning status for every member of your team.")

    section_label("Team Skills Gap — by Member & Domain")

    if team.empty:
        st.info("No team members found for this manager.")
    else:
        # Header row
        st.markdown("""
        <div style="display:grid;grid-template-columns:180px repeat(4,1fr);
        background:#ffece1;padding:8px 14px;border-radius:10px 10px 0 0;gap:4px;
        font-family:'Montserrat',sans-serif;border:1px solid #f0d9cc;border-bottom:none;">
            <div style="font-size:9px;font-weight:700;color:#505050;text-transform:uppercase;letter-spacing:0.5px;">Member</div>
            <div style="font-size:9px;font-weight:700;color:#505050;text-align:center;text-transform:uppercase;letter-spacing:0.5px;">Digital</div>
            <div style="font-size:9px;font-weight:700;color:#505050;text-align:center;text-transform:uppercase;letter-spacing:0.5px;">Leadership</div>
            <div style="font-size:9px;font-weight:700;color:#505050;text-align:center;text-transform:uppercase;letter-spacing:0.5px;">Technical</div>
            <div style="font-size:9px;font-weight:700;color:#505050;text-align:center;text-transform:uppercase;letter-spacing:0.5px;">Functional</div>
        </div>
        """, unsafe_allow_html=True)

        # Each member row rendered individually
        last_idx = len(team) - 1
        for idx, (_, member) in enumerate(team.iterrows()):
            d = round(skills_df[(skills_df["employee_id"]==member["employee_id"]) & (skills_df["skill_name"].isin(DOMAIN_MAP["Digital"]))]["skill_level"].apply(level_pct).mean()) if not skills_df[(skills_df["employee_id"]==member["employee_id"]) & (skills_df["skill_name"].isin(DOMAIN_MAP["Digital"]))].empty else 0
            l = round(skills_df[(skills_df["employee_id"]==member["employee_id"]) & (skills_df["skill_name"].isin(DOMAIN_MAP["Leadership"]))]["skill_level"].apply(level_pct).mean()) if not skills_df[(skills_df["employee_id"]==member["employee_id"]) & (skills_df["skill_name"].isin(DOMAIN_MAP["Leadership"]))].empty else 0
            t = round(skills_df[(skills_df["employee_id"]==member["employee_id"]) & (skills_df["skill_name"].isin(DOMAIN_MAP["Technical"]))]["skill_level"].apply(level_pct).mean()) if not skills_df[(skills_df["employee_id"]==member["employee_id"]) & (skills_df["skill_name"].isin(DOMAIN_MAP["Technical"]))].empty else 0
            f = round(skills_df[(skills_df["employee_id"]==member["employee_id"]) & (skills_df["skill_name"].isin(DOMAIN_MAP["Functional"]))]["skill_level"].apply(level_pct).mean()) if not skills_df[(skills_df["employee_id"]==member["employee_id"]) & (skills_df["skill_name"].isin(DOMAIN_MAP["Functional"]))].empty else 0
            dc, lc, tc, fc = bar_color(d), bar_color(l), bar_color(t), bar_color(f)
            radius = "0 0 10px 10px" if idx == last_idx else "0"
            st.markdown(f"""
            <div style="display:grid;grid-template-columns:180px repeat(4,1fr);
            padding:8px 14px;border:1px solid #f0d9cc;border-top:none;gap:4px;align-items:center;
            background:#fff;border-radius:{radius};font-family:'Montserrat',sans-serif;">
                <div style="font-size:11px;font-weight:600;color:#000;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{member['name']}</div>
                <div style="display:flex;flex-direction:column;align-items:center;gap:3px;">
                    <div style="font-size:9px;font-weight:700;color:{dc};">{d}%</div>
                    <div style="width:100%;height:5px;background:#f0d9cc;border-radius:3px;overflow:hidden;"><div style="width:{d}%;height:5px;background:{dc};border-radius:3px;"></div></div>
                </div>
                <div style="display:flex;flex-direction:column;align-items:center;gap:3px;">
                    <div style="font-size:9px;font-weight:700;color:{lc};">{l}%</div>
                    <div style="width:100%;height:5px;background:#f0d9cc;border-radius:3px;overflow:hidden;"><div style="width:{l}%;height:5px;background:{lc};border-radius:3px;"></div></div>
                </div>
                <div style="display:flex;flex-direction:column;align-items:center;gap:3px;">
                    <div style="font-size:9px;font-weight:700;color:{tc};">{t}%</div>
                    <div style="width:100%;height:5px;background:#f0d9cc;border-radius:3px;overflow:hidden;"><div style="width:{t}%;height:5px;background:{tc};border-radius:3px;"></div></div>
                </div>
                <div style="display:flex;flex-direction:column;align-items:center;gap:3px;">
                    <div style="font-size:9px;font-weight:700;color:{fc};">{f}%</div>
                    <div style="width:100%;height:5px;background:#f0d9cc;border-radius:3px;overflow:hidden;"><div style="width:{f}%;height:5px;background:{fc};border-radius:3px;"></div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    section_label("Team Member Summary")

    # Header
    st.markdown("""
    <div style="display:grid;grid-template-columns:2fr 1fr 80px 80px 100px;
    background:#ffece1;padding:8px 14px;border-radius:10px 10px 0 0;gap:8px;
    font-family:'Montserrat',sans-serif;border:1px solid #f0d9cc;border-bottom:none;">
        <div style="font-size:9px;font-weight:700;color:#505050;text-transform:uppercase;letter-spacing:0.5px;">Name</div>
        <div style="font-size:9px;font-weight:700;color:#505050;text-transform:uppercase;letter-spacing:0.5px;">Role</div>
        <div style="font-size:9px;font-weight:700;color:#505050;text-align:center;text-transform:uppercase;letter-spacing:0.5px;">Skills</div>
        <div style="font-size:9px;font-weight:700;color:#505050;text-align:center;text-transform:uppercase;letter-spacing:0.5px;">Active</div>
        <div style="font-size:9px;font-weight:700;color:#505050;text-align:center;text-transform:uppercase;letter-spacing:0.5px;">Progress</div>
    </div>
    """, unsafe_allow_html=True)

    last_idx = len(team) - 1
    for idx, (_, member) in enumerate(team.iterrows()):
        active     = len(enrol_df[(enrol_df["employee_id"]==member["employee_id"]) & (enrol_df["status"].isin(["Enrolled","In Progress"]))])
        done       = len(enrol_df[(enrol_df["employee_id"]==member["employee_id"]) & (enrol_df["status"]=="Completed")])
        skill_cnt  = len(skills_df[skills_df["employee_id"]==member["employee_id"]])
        radius     = "0 0 10px 10px" if idx == last_idx else "0"
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:2fr 1fr 80px 80px 100px;
        padding:8px 14px;border:1px solid #f0d9cc;border-top:none;gap:8px;align-items:center;
        background:#fff;border-radius:{radius};font-family:'Montserrat',sans-serif;">
            <div style="font-size:11px;font-weight:600;color:#000;">{member['name']}</div>
            <div style="font-size:11px;color:#505050;">{member['role']}</div>
            <div style="font-size:11px;color:#505050;text-align:center;">{skill_cnt}</div>
            <div style="font-size:11px;color:#505050;text-align:center;">{active}</div>
            <div style="text-align:center;"><span style="background:#e8f5e9;color:#2e7d32;font-size:9px;font-weight:700;padding:2px 9px;border-radius:20px;">{done} done</span></div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# SKILLS UPLOAD
# ============================================================
elif active_nav == "Skills Upload":

    page_title("Skills Upload", "Declare the skills your team needs over the next 12 months. This feeds directly into the TNA.")

    section_label("Declare a Skill Needed")

    with st.form("skills_upload_form", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            skill_name = st.text_input("Skill Name")
        with col2:
            priority = st.selectbox("Priority", ["Critical", "High", "Medium", "Low"])
        with col3:
            timeline = st.selectbox("Timeline (months)", [3, 6, 9, 12])
        with col4:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button("＋ Add Skill")

        if submitted:
            if skill_name.strip() == "":
                st.warning("Please enter a skill name.")
            else:
                new_row = pd.DataFrame([{
                    "manager_id":      selected_mgr_id,
                    "department":      mgr_dept,
                    "skill_name":      skill_name.strip(),
                    "priority":        priority,
                    "timeline_months": timeline,
                }])
                updated = pd.concat([needed_df, new_row], ignore_index=True)
                updated.to_csv("data/skills_needed.csv", index=False)
                summary = trigger_pipeline()
                st.success(f"✓ '{skill_name}' added. TNA recalculated — {summary['critical_gaps']} critical gaps.")
                st.cache_data.clear()

    section_label("Skills Declared by This Manager")

    current_needed     = pd.read_csv("data/skills_needed.csv")
    mgr_needed_current = current_needed[current_needed["manager_id"] == selected_mgr_id]

    if mgr_needed_current.empty:
        st.info("No skills declared yet.")
    else:
        st.markdown("""
        <div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr;
        background:#ffece1;padding:8px 14px;border-radius:10px 10px 0 0;gap:8px;
        font-family:'Montserrat',sans-serif;border:1px solid #f0d9cc;border-bottom:none;">
            <div style="font-size:9px;font-weight:700;color:#505050;text-transform:uppercase;letter-spacing:0.5px;">Skill</div>
            <div style="font-size:9px;font-weight:700;color:#505050;text-align:center;text-transform:uppercase;letter-spacing:0.5px;">Priority</div>
            <div style="font-size:9px;font-weight:700;color:#505050;text-align:center;text-transform:uppercase;letter-spacing:0.5px;">Timeline</div>
            <div style="font-size:9px;font-weight:700;color:#505050;text-align:center;text-transform:uppercase;letter-spacing:0.5px;">Department</div>
        </div>
        """, unsafe_allow_html=True)

        last_idx = len(mgr_needed_current) - 1
        for idx, (_, row) in enumerate(mgr_needed_current.iterrows()):
            fg, bg = PRIORITY_COLOURS.get(row["priority"], ("#9a8880","#f0d9cc"))
            radius = "0 0 10px 10px" if idx == last_idx else "0"
            st.markdown(f"""
            <div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr;
            padding:8px 14px;border:1px solid #f0d9cc;border-top:none;gap:8px;align-items:center;
            background:#fff;border-radius:{radius};font-family:'Montserrat',sans-serif;">
                <div style="font-size:11px;font-weight:600;color:#000;">{row['skill_name']}</div>
                <div style="text-align:center;"><span style="background:{bg};color:{fg};font-size:9px;font-weight:700;padding:2px 9px;border-radius:20px;">{row['priority']}</span></div>
                <div style="font-size:11px;color:#505050;text-align:center;">{int(row['timeline_months'])} months</div>
                <div style="font-size:11px;color:#505050;text-align:center;">{row['department']}</div>
            </div>
            """, unsafe_allow_html=True)


# ============================================================
# ASSIGN COURSES
# ============================================================
elif active_nav == "Assign Courses":

    page_title("Assign Courses", "Assign mandatory courses to team members. Assigned courses appear in their My Courses view.")

    section_label("Assign a Course")

    with st.form("assign_course_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            member_options = team.set_index("employee_id")["name"].to_dict()
            assign_to      = st.selectbox("Team Member", list(member_options.keys()),
                                          format_func=lambda x: member_options[x])
        with col2:
            course_options = courses_df.set_index("course_id")["title"].to_dict()
            assign_course  = st.selectbox("Course", list(course_options.keys()),
                                          format_func=lambda x: course_options[x])
        with col3:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            assign_submitted = st.form_submit_button("📋 Assign Course")

        if assign_submitted:
            already = enrol_df[
                (enrol_df["employee_id"] == assign_to) &
                (enrol_df["course_id"]   == assign_course)
            ]
            if not already.empty:
                st.warning(f"{member_options[assign_to]} is already enrolled in this course.")
            else:
                new_enrol = pd.DataFrame([{
                    "employee_id":     assign_to,
                    "course_id":       assign_course,
                    "status":          "Enrolled",
                    "completion_date": None,
                    "score":           None,
                }])
                updated_enrol = pd.concat([enrol_df, new_enrol], ignore_index=True)
                updated_enrol.to_csv("data/enrolment_data.csv", index=False)
                st.success(f"✓ {course_options[assign_course]} assigned to {member_options[assign_to]}.")
                st.cache_data.clear()

    section_label("Current Team Enrolments")

    team_enrol_display = (
        enrol_df[enrol_df["employee_id"].isin(team_ids)]
        .merge(courses_df[["course_id","title","format","duration_hours"]], on="course_id", how="left")
        .merge(master_df[["employee_id","name"]], on="employee_id", how="left")
    )

    if team_enrol_display.empty:
        st.info("No enrolments found for this team.")
    else:
        st.markdown("""
        <div style="display:grid;grid-template-columns:1.5fr 2fr 1fr 80px 100px;
        background:#ffece1;padding:8px 14px;border-radius:10px 10px 0 0;gap:8px;
        font-family:'Montserrat',sans-serif;border:1px solid #f0d9cc;border-bottom:none;">
            <div style="font-size:9px;font-weight:700;color:#505050;text-transform:uppercase;letter-spacing:0.5px;">Member</div>
            <div style="font-size:9px;font-weight:700;color:#505050;text-transform:uppercase;letter-spacing:0.5px;">Course</div>
            <div style="font-size:9px;font-weight:700;color:#505050;text-align:center;text-transform:uppercase;letter-spacing:0.5px;">Format</div>
            <div style="font-size:9px;font-weight:700;color:#505050;text-align:center;text-transform:uppercase;letter-spacing:0.5px;">Hrs</div>
            <div style="font-size:9px;font-weight:700;color:#505050;text-align:center;text-transform:uppercase;letter-spacing:0.5px;">Status</div>
        </div>
        """, unsafe_allow_html=True)

        last_idx = len(team_enrol_display) - 1
        for idx, (_, row) in enumerate(team_enrol_display.iterrows()):
            badge  = status_badge(row["status"])
            radius = "0 0 10px 10px" if idx == last_idx else "0"
            st.markdown(f"""
            <div style="display:grid;grid-template-columns:1.5fr 2fr 1fr 80px 100px;
            padding:8px 14px;border:1px solid #f0d9cc;border-top:none;gap:8px;align-items:center;
            background:#fff;border-radius:{radius};font-family:'Montserrat',sans-serif;">
                <div style="font-size:11px;font-weight:600;color:#000;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{row['name']}</div>
                <div style="font-size:11px;color:#505050;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{row['title']}</div>
                <div style="font-size:11px;color:#505050;text-align:center;">{row['format']}</div>
                <div style="font-size:11px;color:#505050;text-align:center;">{int(row['duration_hours'])}</div>
                <div style="text-align:center;">{badge}</div>
            </div>
            """, unsafe_allow_html=True)


# ============================================================
# TEAM STATUS
# ============================================================
elif active_nav == "Team Status":

    page_title("Team Status", "Full learning status breakdown across all team members.")
    locked_section("Full team learning status, completion tracking and progress detail. Available in the full version.")

# ============================================================
# RECOMMENDATIONS
# ============================================================
elif active_nav == "Team Recommendations":
    
    page_title("Team Recommendations", "Courses with the highest impact across your entire team.")
    locked_section("AI-ranked course recommendations for your entire team based on collective gap scores. Available in the full version.")

# ============================================================
# FOOTER
# ============================================================
render_footer()