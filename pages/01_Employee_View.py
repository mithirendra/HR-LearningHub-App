import streamlit as st
import pandas as pd
from utils import (
    setup_page, load_all_data,
    render_sidebar_brand, render_sidebar_user, render_sidebar_nav,
    render_hero, render_footer, section_label, page_title,
    status_badge, bar_color, level_pct, progress_pct,
    PRIORITY_COLOURS, trigger_pipeline, locked_section
)
from utils import auth_check
from datetime import date

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
auth_check("Employee")
setup_page("Employee View")

# ============================================================
# LOAD DATA
# ============================================================
data       = load_all_data()
master_df  = data["master"]
skills_df  = data["skills"]
enrol_df   = data["enrol"]
courses_df = data["courses"]
tna_df     = data["tna"]

# ============================================================
# EMPLOYEE — from session state
# ============================================================
selected_id = st.session_state.user_id
emp         = master_df[master_df["employee_id"] == selected_id].iloc[0]
emp_skills  = skills_df[skills_df["employee_id"] == selected_id]
emp_enrol   = (
    enrol_df[enrol_df["employee_id"] == selected_id]
    .merge(courses_df, on="course_id", how="left")
)

total_skills = len(emp_skills)
enrolled     = len(emp_enrol[emp_enrol["status"].isin(["Enrolled", "In Progress"])])
completed    = len(emp_enrol[emp_enrol["status"] == "Completed"])
gap_score    = (
    round(len(emp_skills[emp_skills["skill_level"] == "Beginner"]) / total_skills * 100)
    if total_skills else 0
)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    render_sidebar_brand()
    render_sidebar_user(emp["name"], emp["role"], emp["department"])
    active_nav = render_sidebar_nav([
        ("Overview",        True),
        ("My Skills",       False),
        ("Recommendations", False),
        ("My Courses",      False),
        ("Skills Growth",   False),
    ], group_label="My Learning")

# ============================================================
# HERO
# ============================================================
render_hero(
    eyebrow  = f"Employee View · {emp['department']} Department",
    title    = emp["name"],
    subtitle = f"{emp['role']} · {emp['department']} · LearningHub"
)

# ============================================================
# METRIC CARDS
# ============================================================
c1, c2, c3, c4 = st.columns(4)
c1.metric("Skills Declared", total_skills)
c2.metric("Courses Enrolled", enrolled)
c3.metric("Completed",        completed)
c4.metric("Gap Score",        f"{gap_score}%")

st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

# ============================================================
# OVERVIEW
# ============================================================
if active_nav == "Overview":
    page_title("Overview", "Your skills snapshot, top course recommendations and learning progress.")

    col_l, col_r = st.columns(2, gap="large")

    with col_l:
        section_label("Skills Snapshot")
        if emp_skills.empty:
            st.info("No skills declared yet.")
        else:
            for _, row in emp_skills.iterrows():
                pct   = level_pct(row["skill_level"])
                color = bar_color(pct)
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:9px;
                font-family:'Montserrat',sans-serif;">
                    <div style="font-size:11px;font-weight:600;color:#000;
                    width:130px;flex-shrink:0;">{row['skill_name']}</div>
                    <div style="flex:1;height:6px;background:#f0d9cc;border-radius:3px;overflow:hidden;">
                        <div style="width:{pct}%;height:6px;background:{color};border-radius:3px;"></div>
                    </div>
                    <div style="font-size:10px;font-weight:700;color:{color};
                    width:80px;text-align:right;">{row['skill_level']}</div>
                </div>
                """, unsafe_allow_html=True)

    with col_r:
        section_label("Recommended Courses")
        dept_tna   = tna_df[tna_df["department"] == emp["department"]].sort_values("gap_score", ascending=False)
        top_skills = dept_tna["skill"].head(6).tolist()
        recs = []
        for skill in top_skills:
            match = courses_df[courses_df["skills_covered"].str.contains(skill, na=False)]
            if not match.empty:
                course  = match.iloc[0]
                tna_row = dept_tna[dept_tna["skill"] == skill].iloc[0]
                recs.append({
                    "title":    course["title"],
                    "format":   course["format"],
                    "duration": course["duration_hours"],
                    "gap_pts":  int(tna_row["gap_score"]),
                    "priority": tna_row["priority"],
                })
            if len(recs) == 4:
                break
        if not recs:
            st.info("No recommendations available for this department yet.")
        else:
            for i, rec in enumerate(recs, 1):
                fg, bg = PRIORITY_COLOURS.get(rec["priority"], ("#9a8880", "#f0d9cc"))
                st.markdown(f"""
                <div style="background:#fff;border:1px solid #f0d9cc;border-radius:11px;
                padding:11px 14px;display:flex;gap:10px;align-items:flex-start;
                margin-bottom:8px;font-family:'Montserrat',sans-serif;">
                    <div style="width:24px;height:24px;border-radius:6px;background:#ffece1;
                    display:flex;align-items:center;justify-content:center;font-size:11px;
                    font-weight:700;color:#f49052;flex-shrink:0;">{str(i).zfill(2)}</div>
                    <div style="flex:1;">
                        <div style="font-size:11px;font-weight:700;color:#000;margin-bottom:2px;">
                            {rec['title']}</div>
                        <div style="font-size:10px;color:#9a8880;">
                            {rec['format']} · {rec['duration']} hrs</div>
                        <span style="display:inline-block;margin-top:4px;font-size:9px;font-weight:700;
                        padding:2px 8px;border-radius:9px;background:{bg};color:{fg};">
                            {rec['priority']} Priority</span>
                    </div>
                    <div style="text-align:right;flex-shrink:0;">
                        <div style="font-size:15px;font-weight:700;color:#f49052;">+{rec['gap_pts']}</div>
                        <div style="font-size:9px;color:#9a8880;text-transform:uppercase;
                        letter-spacing:0.4px;">Gap pts</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    section_label("My Learning Progress")
    if emp_enrol.empty:
        st.info("No courses enrolled yet.")
    else:
        for _, row in emp_enrol.iterrows():
            pct   = progress_pct(row["status"])
            color = bar_color(pct)
            label = "Done" if row["status"] == "Completed" else f"{pct}%"
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:9px;
            font-family:'Montserrat',sans-serif;">
                <div style="font-size:11px;font-weight:600;color:#000;width:200px;
                flex-shrink:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                    {row['title']}</div>
                {status_badge(row['status'])}
                <div style="flex:1;height:6px;background:#f0d9cc;border-radius:3px;overflow:hidden;">
                    <div style="width:{pct}%;height:6px;background:{color};border-radius:3px;"></div>
                </div>
                <div style="font-size:10px;font-weight:700;color:{color};
                width:34px;text-align:right;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

# ============================================================
# MY SKILLS
# ============================================================
elif active_nav == "My Skills":
    page_title("My Skills", "All skills you have declared and your current proficiency levels.")


    section_label("Declared Skills")

    if emp_skills.empty:
        st.info("No skills declared yet.")
    else:
        for _, row in emp_skills.iterrows():
            pct      = level_pct(row["skill_level"])
            color    = bar_color(pct)
            badge_bg = "#e8f5e9" if color == "#2e7d32" else "#fff3e0" if color == "#f49052" else "#fdecea"
            st.markdown(f"""
            <div style="background:#fff;border:1px solid #f0d9cc;border-radius:11px;
            padding:12px 16px;margin-bottom:8px;display:flex;align-items:center;
            gap:14px;font-family:'Montserrat',sans-serif;">
                <div style="font-size:12px;font-weight:600;color:#000;width:160px;flex-shrink:0;">
                    {row['skill_name']}</div>
                <span style="background:{badge_bg};color:{color};font-size:10px;font-weight:700;
                padding:3px 10px;border-radius:20px;flex-shrink:0;">{row['skill_level']}</span>
                <div style="flex:1;height:6px;background:#f0d9cc;border-radius:3px;overflow:hidden;">
                    <div style="width:{pct}%;height:6px;background:{color};border-radius:3px;"></div>
                </div>
                <div style="font-size:10px;color:#9a8880;width:90px;text-align:right;flex-shrink:0;">
                    {row['date_uploaded']}</div>
            </div>
            """, unsafe_allow_html=True)

    section_label("Declare a New Skill")

    with st.form("add_skill_form", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            all_skills = sorted(
                courses_df["skills_covered"]
                .str.split(", ").explode().dropna().unique().tolist()
            )
            new_skill = st.selectbox("Skill", all_skills)
        with col2:
            new_level = st.selectbox("Level", ["Beginner", "Intermediate", "Advanced"])
        with col3:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            add_submitted = st.form_submit_button("＋ Add Skill")

        if add_submitted:
            already = emp_skills[emp_skills["skill_name"] == new_skill]
            if not already.empty:
                st.warning(f"{new_skill} is already in your profile.")
            else:
                new_row = pd.DataFrame([{
                    "employee_id":   selected_id,
                    "skill_name":    new_skill,
                    "skill_level":   new_level,
                    "date_uploaded": date.today().strftime("%Y-%m-%d"),
                }])
                updated = pd.concat([
                    pd.read_csv("data/employee_skills.csv"), new_row
                ], ignore_index=True)
                updated.to_csv("data/employee_skills.csv", index=False)
                summary = trigger_pipeline()
                st.success(f"✓ {new_skill} added. TNA recalculated — {summary['critical_gaps']} critical gaps found.")
                st.cache_data.clear()

# ============================================================
# RECOMMENDATIONS
# ============================================================
elif active_nav == "Recommendations":
    
    from recommender import get_employee_recommendations

    page_title("Recommended Courses", "Courses ranked by gap impact — the highest gap points closed first.")

    recs = get_employee_recommendations(
        selected_id, master_df, skills_df, enrol_df, courses_df, tna_df, top_n=10
    )

    if not recs:
        st.info("No recommendations available yet. Declare your skills in My Skills to get personalised recommendations.")
    else:
        section_label(f"{len(recs)} courses recommended for you")
        for i, rec in enumerate(recs, 1):
            fg, bg         = PRIORITY_COLOURS.get(rec["priority"], ("#9a8880","#f0d9cc"))
            status_text    = f'<span style="background:#e8f5e9;color:#2e7d32;font-size:9px;font-weight:700;padding:2px 8px;border-radius:9px;margin-left:6px;">Enrolled</span>' if rec["enrolled"] else ""
            st.markdown(f"""
            <div style="background:#fff;border:1px solid #f0d9cc;border-radius:12px;
            padding:14px 18px;display:flex;gap:14px;align-items:flex-start;
            margin-bottom:10px;font-family:'Montserrat',sans-serif;">
                <div style="width:30px;height:30px;border-radius:8px;background:#ffece1;
                display:flex;align-items:center;justify-content:center;font-size:13px;
                font-weight:700;color:#f49052;flex-shrink:0;">{str(i).zfill(2)}</div>
                <div style="flex:1;">
                    <div style="font-size:13px;font-weight:700;color:#000;margin-bottom:3px;">
                        {rec['title']}{status_text}</div>
                    <div style="font-size:11px;color:#9a8880;margin-bottom:5px;">
                        {rec['format']} · {rec['duration_hours']} hrs · {rec['level']} · Closes gap: {rec['gap_skill']}</div>
                    <span style="font-size:9px;font-weight:700;padding:2px 9px;
                    border-radius:9px;background:{bg};color:{fg};">{rec['priority']} Priority</span>
                </div>
                <div style="text-align:right;flex-shrink:0;">
                    <div style="font-size:20px;font-weight:700;color:#f49052;">+{rec['gap_pts']}</div>
                    <div style="font-size:9px;color:#9a8880;text-transform:uppercase;letter-spacing:0.4px;">Gap pts</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ============================================================
# MY COURSES
# ============================================================
elif active_nav == "My Courses":
    page_title("My Courses", "All your enrolled, in-progress and completed courses.")
    locked_section("Track every course you are enrolled in, monitor progress and view completion scores. Available in the full version.")

# ============================================================
# SKILLS GROWTH
# ============================================================
elif active_nav == "Skills Growth":
    page_title("Skills Growth", "Your skills breakdown by level and the gaps remaining for your department.")
    locked_section("View your skills progression over time, level breakdown and department gap analysis. Available in the full version.")

# ============================================================
# FOOTER
# ============================================================
render_footer()