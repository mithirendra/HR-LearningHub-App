import streamlit as st
import pandas as pd
from utils import (
    setup_page, load_all_data,
    render_sidebar_brand, render_sidebar_user, render_sidebar_nav,
    render_hero, render_footer, section_label, page_title,
    status_badge, bar_color, level_pct, PRIORITY_COLOURS,
    STATUS_COLOURS, COLOURS, trigger_pipeline, locked_section
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
auth_check("HR")
setup_page("HR View")

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
forecast_df = data["forecast"]

# ============================================================
# ORG STATS
# ============================================================
total_emp      = len(master_df)
total_depts    = master_df["department"].nunique()
critical_gaps  = len(tna_df[tna_df["priority"] == "Critical"])
completion_rate = round(len(enrol_df[enrol_df["status"] == "Completed"]) / len(enrol_df) * 100) if len(enrol_df) > 0 else 0
zero_activity  = master_df[~master_df["employee_id"].isin(enrol_df["employee_id"].unique())]
avg_gap        = round(tna_df["gap_score"].mean()) if not tna_df.empty else 0

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    render_sidebar_brand()
    render_sidebar_user(st.session_state.user_name, "HR Director", "Organisation")
    active_nav = render_sidebar_nav([
        ("Dashboard",        True),
        ("TNA",              False),
        ("Skills Forecast",  False),
        ("Analytics",        False),
        ("Zero Activity",    False),
        ("Course Recommendations", False),
    ], group_label="HR Intelligence")

# ============================================================
# HERO
# ============================================================
render_hero(
    eyebrow  = f"HR View · Organisation-Wide · {total_emp} Employees",
    title    = "L&D Intelligence Centre",
    subtitle = f"Organisation-wide skills and learning analytics · {total_depts} departments"
)

# ============================================================
# METRIC CARDS
# ============================================================
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Employees",   total_emp)
c2.metric("Critical Gaps",     critical_gaps)
c3.metric("Completion Rate",   f"{completion_rate}%")
c4.metric("Zero Activity",     len(zero_activity))

st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)


# ============================================================
# DASHBOARD
# ============================================================
if active_nav == "Dashboard":

    page_title("Organisation Dashboard", "High-level summary of learning health, skills gaps and activity across all departments.")

    section_label("Department Gap Overview")

    departments = master_df["department"].unique().tolist()

    # Header
    st.markdown("""
    <div style="display:grid;grid-template-columns:150px repeat(4,1fr) 80px;
    background:#ffece1;padding:8px 14px;border-radius:10px 10px 0 0;gap:8px;
    font-family:'Montserrat',sans-serif;border:1px solid #f0d9cc;border-bottom:none;">
        <div style="font-size:9px;font-weight:700;color:#505050;text-transform:uppercase;letter-spacing:0.5px;">Department</div>
        <div style="font-size:9px;font-weight:700;color:#505050;text-align:center;text-transform:uppercase;letter-spacing:0.5px;">Employees</div>
        <div style="font-size:9px;font-weight:700;color:#505050;text-align:center;text-transform:uppercase;letter-spacing:0.5px;">Avg Gap</div>
        <div style="font-size:9px;font-weight:700;color:#505050;text-align:center;text-transform:uppercase;letter-spacing:0.5px;">Critical</div>
        <div style="font-size:9px;font-weight:700;color:#505050;text-align:center;text-transform:uppercase;letter-spacing:0.5px;">Completion</div>
        <div style="font-size:9px;font-weight:700;color:#505050;text-align:center;text-transform:uppercase;letter-spacing:0.5px;">Status</div>
    </div>
    """, unsafe_allow_html=True)

    for idx, dept in enumerate(departments):
        dept_emp    = master_df[master_df["department"] == dept]
        dept_ids    = dept_emp["employee_id"].tolist()
        dept_enrol  = enrol_df[enrol_df["employee_id"].isin(dept_ids)]
        dept_tna    = tna_df[tna_df["department"] == dept]
        emp_count   = len(dept_emp)
        dept_gap    = round(dept_tna["gap_score"].mean()) if not dept_tna.empty else 0
        dept_crit   = len(dept_tna[dept_tna["priority"] == "Critical"])
        dept_comp   = round(len(dept_enrol[dept_enrol["status"] == "Completed"]) / len(dept_enrol) * 100) if len(dept_enrol) > 0 else 0
        gap_color   = bar_color(100 - dept_gap)
        comp_color  = bar_color(dept_comp)
        status_text = "At Risk" if dept_gap > 60 or dept_comp < 40 else "Needs Attention" if dept_gap > 40 or dept_comp < 60 else "On Track"
        status_bg   = "#fdecea" if status_text == "At Risk" else "#fff3e0" if status_text == "Needs Attention" else "#e8f5e9"
        status_fg   = "#c62828" if status_text == "At Risk" else "#e65100" if status_text == "Needs Attention" else "#2e7d32"
        radius      = "0 0 10px 10px" if idx == len(departments) - 1 else "0"

        st.markdown(f"""
        <div style="display:grid;grid-template-columns:150px repeat(4,1fr) 80px;
        padding:8px 14px;border:1px solid #f0d9cc;border-top:none;gap:8px;align-items:center;
        background:#fff;border-radius:{radius};font-family:'Montserrat',sans-serif;">
            <div style="font-size:11px;font-weight:700;color:#000;">{dept}</div>
            <div style="font-size:11px;color:#505050;text-align:center;">{emp_count}</div>
            <div style="font-size:11px;font-weight:700;color:{gap_color};text-align:center;">{dept_gap} pts</div>
            <div style="font-size:11px;font-weight:700;color:#c62828;text-align:center;">{dept_crit}</div>
            <div style="text-align:center;">
                <div style="font-size:10px;font-weight:700;color:{comp_color};margin-bottom:3px;">{dept_comp}%</div>
                <div style="height:5px;background:#f0d9cc;border-radius:3px;overflow:hidden;">
                    <div style="width:{dept_comp}%;height:5px;background:{comp_color};border-radius:3px;"></div>
                </div>
            </div>
            <div style="text-align:center;"><span style="background:{status_bg};color:{status_fg};font-size:9px;font-weight:700;padding:2px 8px;border-radius:20px;">{status_text}</span></div>
        </div>
        """, unsafe_allow_html=True)

    # Top priority skills org wide
    section_label("Top Priority Skills — Organisation Wide")

    top_skills = tna_df.groupby("skill")["gap_score"].mean().sort_values(ascending=False).head(8).reset_index()

    for _, row in top_skills.iterrows():
        score = round(row["gap_score"])
        color = bar_color(100 - score)
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;font-family:'Montserrat',sans-serif;">
            <div style="font-size:12px;font-weight:600;color:#000;width:180px;flex-shrink:0;">{row['skill']}</div>
            <div style="flex:1;height:8px;background:#f0d9cc;border-radius:4px;overflow:hidden;">
                <div style="width:{min(score,100)}%;height:8px;background:{color};border-radius:4px;"></div>
            </div>
            <div style="font-size:11px;font-weight:700;color:{color};width:60px;text-align:right;">{score} pts gap</div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# TNA
# ============================================================
elif active_nav == "TNA":

    page_title("Training Needs Analysis", "Gap scores by department, role and skill. Recalculates automatically when new skills data is uploaded.")

    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        dept_filter = st.selectbox("Filter by Department", ["All"] + sorted(tna_df["department"].unique().tolist()))
    with col_filter2:
        priority_filter = st.selectbox("Filter by Priority", ["All", "Critical", "High", "Medium", "Low"])

    filtered_tna = tna_df.copy()
    if dept_filter != "All":
        filtered_tna = filtered_tna[filtered_tna["department"] == dept_filter]
    if priority_filter != "All":
        filtered_tna = filtered_tna[filtered_tna["priority"] == priority_filter]

    filtered_tna = filtered_tna.sort_values("gap_score", ascending=False)

    section_label(f"TNA Results — {len(filtered_tna)} records")

    if filtered_tna.empty:
        st.info("No TNA records match the selected filters.")
    else:
        # Header
        st.markdown("""
        <div style="display:grid;grid-template-columns:120px 120px 2fr 80px 80px 80px 90px;
        background:#ffece1;padding:8px 14px;border-radius:10px 10px 0 0;gap:8px;
        font-family:'Montserrat',sans-serif;border:1px solid #f0d9cc;border-bottom:none;">
            <div style="font-size:9px;font-weight:700;color:#505050;text-transform:uppercase;letter-spacing:0.5px;">Department</div>
            <div style="font-size:9px;font-weight:700;color:#505050;text-transform:uppercase;letter-spacing:0.5px;">Role</div>
            <div style="font-size:9px;font-weight:700;color:#505050;text-transform:uppercase;letter-spacing:0.5px;">Skill</div>
            <div style="font-size:9px;font-weight:700;color:#505050;text-align:center;text-transform:uppercase;letter-spacing:0.5px;">Supply</div>
            <div style="font-size:9px;font-weight:700;color:#505050;text-align:center;text-transform:uppercase;letter-spacing:0.5px;">Demand</div>
            <div style="font-size:9px;font-weight:700;color:#505050;text-align:center;text-transform:uppercase;letter-spacing:0.5px;">Gap</div>
            <div style="font-size:9px;font-weight:700;color:#505050;text-align:center;text-transform:uppercase;letter-spacing:0.5px;">Priority</div>
        </div>
        """, unsafe_allow_html=True)

        display_tna = filtered_tna.head(50)
        for idx, (_, row) in enumerate(display_tna.iterrows()):
            fg, bg  = PRIORITY_COLOURS.get(row["priority"], ("#9a8880","#f0d9cc"))
            gap_col = bar_color(100 - int(row["gap_score"]))
            radius  = "0 0 10px 10px" if idx == len(display_tna) - 1 else "0"
            st.markdown(f"""
            <div style="display:grid;grid-template-columns:120px 120px 2fr 80px 80px 80px 90px;
            padding:7px 14px;border:1px solid #f0d9cc;border-top:none;gap:8px;align-items:center;
            background:#fff;border-radius:{radius};font-family:'Montserrat',sans-serif;">
                <div style="font-size:11px;color:#505050;">{row['department']}</div>
                <div style="font-size:11px;color:#505050;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{row['role']}</div>
                <div style="font-size:11px;font-weight:600;color:#000;">{row['skill']}</div>
                <div style="font-size:11px;color:#505050;text-align:center;">{int(row['current_supply'])}</div>
                <div style="font-size:11px;color:#505050;text-align:center;">{int(row['future_demand'])}</div>
                <div style="font-size:11px;font-weight:700;color:{gap_col};text-align:center;">{int(row['gap_score'])}</div>
                <div style="text-align:center;"><span style="background:{bg};color:{fg};font-size:9px;font-weight:700;padding:2px 8px;border-radius:20px;">{row['priority']}</span></div>
            </div>
            """, unsafe_allow_html=True)

        if len(filtered_tna) > 50:
            st.caption(f"Showing top 50 of {len(filtered_tna)} records. Use filters to narrow down.")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    if st.button("🔄 Recalculate TNA Now"):
        summary = trigger_pipeline()
        st.success(f"✓ TNA recalculated — {summary['total_records']} records · {summary['critical_gaps']} critical gaps · {summary['skills_tracked']} skills tracked.")
        st.cache_data.clear()


# ============================================================
# SKILLS FORECAST
# ============================================================
elif active_nav == "Skills Forecast":
    page_title("Skills Forecast", "Projected demand for skills over 12, 24 and 36 months.")
    locked_section("Skills demand forecasting across 12, 24 and 36 month horizons. Available in the full version.")


# ============================================================
# ANALYTICS
# ============================================================
elif active_nav == "Analytics":

    import plotly.graph_objects as go
    import plotly.express as px

    page_title("L&D Analytics", "Organisation-wide learning completion, gap closure and skills build rates.")

    # --------------------------------------------------------
    # CHART 1 — Completion rate by department
    # --------------------------------------------------------
    section_label("Completion Rate by Department")

    dept_data = []
    for dept in sorted(master_df["department"].unique()):
        dept_ids   = master_df[master_df["department"] == dept]["employee_id"].tolist()
        dept_enrol = enrol_df[enrol_df["employee_id"].isin(dept_ids)]
        total      = len(dept_enrol)
        done       = len(dept_enrol[dept_enrol["status"] == "Completed"])
        pct        = round(done / total * 100) if total > 0 else 0
        dept_data.append({"Department": dept, "Completion %": pct, "Completed": done, "Total": total})

    dept_df = pd.DataFrame(dept_data).sort_values("Completion %", ascending=True)

    colors = ["#2e7d32" if v >= 75 else "#f49052" if v >= 40 else "#c62828" for v in dept_df["Completion %"]]

    fig1 = go.Figure(go.Bar(
        x=dept_df["Completion %"],
        y=dept_df["Department"],
        orientation="h",
        marker_color=colors,
        text=[f"{v}%" for v in dept_df["Completion %"]],
        textposition="outside",
        customdata=dept_df[["Completed", "Total"]].values,
        hovertemplate="<b>%{y}</b><br>Completion: %{x}%<br>%{customdata[0]} of %{customdata[1]} courses<extra></extra>"
    ))
    fig1.update_layout(
        height=280,
        margin=dict(l=0, r=60, t=10, b=10),
        plot_bgcolor="#fffbf8",
        paper_bgcolor="#ffffff",
        font=dict(family="Montserrat", size=11, color="#505050"),
        xaxis=dict(range=[0, 115], showgrid=True, gridcolor="#f0d9cc", zeroline=False),
        yaxis=dict(showgrid=False),
        bargap=0.3,
    )
    st.plotly_chart(fig1, width='stretch')

    # --------------------------------------------------------
    # CHART 2 + CHART 3 — Side by side
    # --------------------------------------------------------
    col_l, col_r = st.columns(2, gap="large")

    with col_l:
        section_label("Enrolment Status Breakdown")

        status_data = enrol_df.groupby("status").size().reset_index(name="count")
        status_colors = {
            "Completed":   "#2e7d32",
            "In Progress": "#f49052",
            "Enrolled":    "#c4a090",
            "Dropped":     "#c62828",
        }
        fig2 = go.Figure(go.Pie(
            labels=status_data["status"],
            values=status_data["count"],
            hole=0.55,
            marker_colors=[status_colors.get(s, "#9a8880") for s in status_data["status"]],
            textinfo="label+percent",
            textfont=dict(family="Montserrat", size=11),
            hovertemplate="<b>%{label}</b><br>%{value} courses<br>%{percent}<extra></extra>"
        ))
        fig2.update_layout(
            height=260,
            margin=dict(l=0, r=0, t=10, b=10),
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            font=dict(family="Montserrat", size=11, color="#505050"),
            showlegend=False,
        )
        st.plotly_chart(fig2, width='stretch')

    with col_r:
        section_label("Top 8 Skills Being Built")

        skills_being_built = (
            skills_df.groupby("skill_name").size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
            .head(8)
        )

        fig3 = go.Figure(go.Bar(
            x=skills_being_built["count"],
            y=skills_being_built["skill_name"],
            orientation="h",
            marker_color="#f49052",
            text=skills_being_built["count"],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>%{x} employees<extra></extra>"
        ))
        fig3.update_layout(
            height=260,
            margin=dict(l=0, r=40, t=10, b=10),
            plot_bgcolor="#fffbf8",
            paper_bgcolor="#ffffff",
            font=dict(family="Montserrat", size=11, color="#505050"),
            xaxis=dict(showgrid=True, gridcolor="#f0d9cc", zeroline=False),
            yaxis=dict(showgrid=False, autorange="reversed"),
            bargap=0.3,
        )
        st.plotly_chart(fig3, width='stretch')

    # --------------------------------------------------------
    # CHART 4 — Skills needed vs skills being built
    # --------------------------------------------------------
    section_label("Skills Needed vs Skills Being Built")

    needed_skills = (
        needed_df.groupby("skill_name").size()
        .reset_index(name="needed_count")
        .rename(columns={"skill_name": "skill"})
    )
    built_skills = (
        skills_df.groupby("skill_name").size()
        .reset_index(name="built_count")
        .rename(columns={"skill_name": "skill"})
    )
    comparison = needed_skills.merge(built_skills, on="skill", how="outer").fillna(0)
    comparison = comparison.sort_values("needed_count", ascending=False).head(10)

    fig4 = go.Figure()
    fig4.add_trace(go.Bar(
        name="Needed",
        x=comparison["skill"],
        y=comparison["needed_count"],
        marker_color="#c62828",
        hovertemplate="<b>%{x}</b><br>Needed: %{y}<extra></extra>"
    ))
    fig4.add_trace(go.Bar(
        name="Being Built",
        x=comparison["skill"],
        y=comparison["built_count"],
        marker_color="#2e7d32",
        hovertemplate="<b>%{x}</b><br>Being built: %{y}<extra></extra>"
    ))
    fig4.update_layout(
        barmode="group",
        height=300,
        margin=dict(l=0, r=0, t=10, b=80),
        plot_bgcolor="#fffbf8",
        paper_bgcolor="#ffffff",
        font=dict(family="Montserrat", size=11, color="#505050"),
        xaxis=dict(showgrid=False, tickangle=-30),
        yaxis=dict(showgrid=True, gridcolor="#f0d9cc", zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        bargap=0.2,
        bargroupgap=0.05,
    )
    st.plotly_chart(fig4, width='stretch')

    # --------------------------------------------------------
    # CHART 5 — Top courses by completion
    # --------------------------------------------------------
    section_label("Top 10 Courses by Completion")

    top_courses = (
        enrol_df[enrol_df["status"] == "Completed"]
        .groupby("course_id").size()
        .reset_index(name="completions")
        .merge(courses_df[["course_id", "title", "format"]], on="course_id", how="left")
        .sort_values("completions", ascending=True)
        .tail(10)
    )

    fig5 = go.Figure(go.Bar(
        x=top_courses["completions"],
        y=top_courses["title"],
        orientation="h",
        marker_color="#f49052",
        text=top_courses["completions"],
        textposition="outside",
        customdata=top_courses["format"].values,
        hovertemplate="<b>%{y}</b><br>%{x} completions<br>Format: %{customdata}<extra></extra>"
    ))
    fig5.update_layout(
        height=320,
        margin=dict(l=0, r=40, t=10, b=10),
        plot_bgcolor="#fffbf8",
        paper_bgcolor="#ffffff",
        font=dict(family="Montserrat", size=11, color="#505050"),
        xaxis=dict(showgrid=True, gridcolor="#f0d9cc", zeroline=False),
        yaxis=dict(showgrid=False),
        bargap=0.3,
    )
    st.plotly_chart(fig5, width='stretch')


# ============================================================
# ZERO ACTIVITY
# ============================================================
elif active_nav == "Zero Activity":

    page_title("Zero Activity Alerts", "Employees with no learning activity. These are potential attrition risk signals.")

    enrolled_ids = enrol_df["employee_id"].unique().tolist()
    inactive     = master_df[~master_df["employee_id"].isin(enrolled_ids)]

    c1, c2, c3 = st.columns(3)
    c1.metric("Zero Activity",     len(inactive))
    c2.metric("Total Employees",   total_emp)
    c3.metric("Inactivity Rate",   f"{round(len(inactive)/total_emp*100)}%" if total_emp > 0 else "0%")

    section_label(f"{len(inactive)} employees with no learning enrolment")

    if inactive.empty:
        st.success("No inactive employees. All employees have at least one course enrolment.")
    else:
        # Header
        st.markdown("""
        <div style="display:grid;grid-template-columns:2fr 1fr 1fr 120px;
        background:#ffece1;padding:8px 14px;border-radius:10px 10px 0 0;gap:8px;
        font-family:'Montserrat',sans-serif;border:1px solid #f0d9cc;border-bottom:none;">
            <div style="font-size:9px;font-weight:700;color:#505050;text-transform:uppercase;letter-spacing:0.5px;">Employee</div>
            <div style="font-size:9px;font-weight:700;color:#505050;text-transform:uppercase;letter-spacing:0.5px;">Department</div>
            <div style="font-size:9px;font-weight:700;color:#505050;text-transform:uppercase;letter-spacing:0.5px;">Role</div>
            <div style="font-size:9px;font-weight:700;color:#505050;text-align:center;text-transform:uppercase;letter-spacing:0.5px;">Status</div>
        </div>
        """, unsafe_allow_html=True)

        for idx, (_, row) in enumerate(inactive.iterrows()):
            radius = "0 0 10px 10px" if idx == len(inactive) - 1 else "0"
            st.markdown(f"""
            <div style="display:grid;grid-template-columns:2fr 1fr 1fr 120px;
            padding:8px 14px;border:1px solid #f0d9cc;border-top:none;gap:8px;align-items:center;
            background:#fff;border-radius:{radius};font-family:'Montserrat',sans-serif;">
                <div style="font-size:11px;font-weight:600;color:#000;">{row['name']}</div>
                <div style="font-size:11px;color:#505050;">{row['department']}</div>
                <div style="font-size:11px;color:#505050;">{row['role']}</div>
                <div style="text-align:center;"><span style="background:#fdecea;color:#c62828;font-size:9px;font-weight:700;padding:2px 9px;border-radius:20px;">No Activity</span></div>
            </div>
            """, unsafe_allow_html=True)

        section_label("Zero Activity by Department")

        dept_inactive = inactive.groupby("department").size().reset_index(name="count").sort_values("count", ascending=False)
        for _, row in dept_inactive.iterrows():
            dept_total = len(master_df[master_df["department"] == row["department"]])
            pct        = round(row["count"] / dept_total * 100) if dept_total > 0 else 0
            color      = bar_color(100 - pct)
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:9px;font-family:'Montserrat',sans-serif;">
                <div style="font-size:12px;font-weight:600;color:#000;width:120px;flex-shrink:0;">{row['department']}</div>
                <div style="flex:1;height:8px;background:#f0d9cc;border-radius:4px;overflow:hidden;">
                    <div style="width:{pct}%;height:8px;background:{color};border-radius:4px;"></div>
                </div>
                <div style="font-size:11px;font-weight:700;color:{color};width:60px;text-align:right;">{int(row['count'])} inactive</div>
            </div>
            """, unsafe_allow_html=True)

# ============================================================
# COURSE RECOMMENDATIONS
# ============================================================
elif active_nav == "Course Recommendations":

    page_title("Course Recommender", "Organisation-wide course recommendations ranked by gap impact.")
    locked_section("AI-ranked course recommendations for the entire organisation based on TNA gap scores. Available in the full version.")

# ============================================================
# FOOTER
# ============================================================
render_footer()