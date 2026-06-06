import pandas as pd

# ============================================================
# COURSE RECOMMENDER — Component 2
# Rule-based engine that matches skills gaps to courses.
# Ranked by gap impact — highest gap points closed first.
# Used by Employee, Manager and HR views.
# ============================================================

def get_employee_recommendations(employee_id, master_df, skills_df, enrol_df, courses_df, tna_df, top_n=10):
    """
    Generate ranked course recommendations for a single employee.

    Logic:
    1. Get employee's department and declared skills
    2. Pull TNA gap scores for that department
    3. Identify skills the employee is missing or weak on
    4. Match to courses covering those skills
    5. Exclude already completed courses
    6. Rank by gap impact score
    7. Return top_n recommendations

    Returns list of dicts with course details and gap impact.
    """

    # Get employee record
    emp = master_df[master_df["employee_id"] == employee_id]
    if emp.empty:
        return []
    emp        = emp.iloc[0]
    department = emp["department"]

    # Employee's declared skills with levels
    emp_skills = skills_df[skills_df["employee_id"] == employee_id]
    skill_level_map = dict(zip(emp_skills["skill_name"], emp_skills["skill_level"]))

    # Courses already completed — exclude these
    completed_courses = enrol_df[
        (enrol_df["employee_id"] == employee_id) &
        (enrol_df["status"] == "Completed")
    ]["course_id"].tolist()

    # TNA gap scores for this department — sorted by priority
    dept_tna = tna_df[tna_df["department"] == department].sort_values("gap_score", ascending=False)

    # Score each skill gap based on:
    # - TNA gap score (primary driver)
    # - Employee's current level on that skill (bonus if they have it but need improvement)
    LEVEL_SCORE = {"Beginner": 30, "Intermediate": 65, "Advanced": 90}
    PRIORITY_WEIGHT = {"Critical": 1.5, "High": 1.2, "Medium": 1.0, "Low": 0.8}

    skill_impact = {}
    for _, row in dept_tna.iterrows():
        skill    = row["skill"]
        base_gap = float(row["gap_score"])
        priority = row["priority"]
        weight   = PRIORITY_WEIGHT.get(priority, 1.0)

        # If employee already has this skill at advanced level, reduce impact
        current_level = skill_level_map.get(skill)
        if current_level == "Advanced":
            weight *= 0.3
        elif current_level == "Intermediate":
            weight *= 0.7

        skill_impact[skill] = round(base_gap * weight)

    # Match skills to courses
    recs    = []
    seen    = set()

    for skill, impact in sorted(skill_impact.items(), key=lambda x: x[1], reverse=True):
        if impact <= 0:
            continue

        # Find courses covering this skill
        matches = courses_df[
            courses_df["skills_covered"].str.contains(skill, na=False, case=False)
        ]

        for _, course in matches.iterrows():
            if course["course_id"] in seen:
                continue
            if course["course_id"] in completed_courses:
                continue

            # Check enrolment status
            enrol_status = enrol_df[
                (enrol_df["employee_id"] == employee_id) &
                (enrol_df["course_id"] == course["course_id"])
            ]
            status = enrol_status.iloc[0]["status"] if not enrol_status.empty else None

            recs.append({
                "course_id":      course["course_id"],
                "title":          course["title"],
                "format":         course["format"],
                "duration_hours": int(course["duration_hours"]),
                "level":          course["level"],
                "skills_covered": course["skills_covered"],
                "gap_skill":      skill,
                "gap_pts":        impact,
                "priority":       dept_tna[dept_tna["skill"] == skill]["priority"].values[0] if skill in dept_tna["skill"].values else "Low",
                "enrolled":       status is not None,
                "status":         status,
            })
            seen.add(course["course_id"])

        if len(recs) >= top_n:
            break

    return recs[:top_n]


def get_team_recommendations(manager_id, master_df, skills_df, enrol_df, courses_df, tna_df, top_n=10):
    """
    Generate aggregated course recommendations for a manager's team.

    Logic:
    1. Get all employees under this manager
    2. For each employee, get their gap skills
    3. Count how many team members need each skill
    4. Rank courses by (team impact = gap score × number of team members who need it)

    Returns list of dicts with course details and team impact.
    """

    team = master_df[master_df["manager_id"] == manager_id]
    if team.empty:
        return []

    team_ids   = team["employee_id"].tolist()
    department = team["department"].mode()[0]
    dept_tna   = tna_df[tna_df["department"] == department].sort_values("gap_score", ascending=False)

    PRIORITY_WEIGHT = {"Critical": 1.5, "High": 1.2, "Medium": 1.0, "Low": 0.8}

    # For each gap skill, count how many team members lack or are weak in it
    skill_team_impact = {}
    for _, row in dept_tna.iterrows():
        skill    = row["skill"]
        base_gap = float(row["gap_score"])
        priority = row["priority"]
        weight   = PRIORITY_WEIGHT.get(priority, 1.0)
        count    = 0

        for emp_id in team_ids:
            emp_skills = skills_df[
                (skills_df["employee_id"] == emp_id) &
                (skills_df["skill_name"] == skill)
            ]
            if emp_skills.empty:
                count += 1  # no skill at all
            elif emp_skills.iloc[0]["skill_level"] == "Beginner":
                count += 0.5  # has skill but weak

        skill_team_impact[skill] = round(base_gap * weight * count)

    # Match to courses
    recs = []
    seen = set()

    for skill, impact in sorted(skill_team_impact.items(), key=lambda x: x[1], reverse=True):
        if impact <= 0:
            continue

        matches = courses_df[
            courses_df["skills_covered"].str.contains(skill, na=False, case=False)
        ]

        for _, course in matches.iterrows():
            if course["course_id"] in seen:
                continue

            # Count team members enrolled vs not
            enrolled_count = len(enrol_df[
                (enrol_df["employee_id"].isin(team_ids)) &
                (enrol_df["course_id"] == course["course_id"])
            ])

            recs.append({
                "course_id":       course["course_id"],
                "title":           course["title"],
                "format":          course["format"],
                "duration_hours":  int(course["duration_hours"]),
                "level":           course["level"],
                "gap_skill":       skill,
                "gap_pts":         impact,
                "priority":        dept_tna[dept_tna["skill"] == skill]["priority"].values[0] if skill in dept_tna["skill"].values else "Low",
                "team_enrolled":   enrolled_count,
                "team_size":       len(team_ids),
            })
            seen.add(course["course_id"])

        if len(recs) >= top_n:
            break

    return recs[:top_n]


def get_org_recommendations(master_df, skills_df, enrol_df, courses_df, tna_df, top_n=15):
    """
    Generate organisation-wide course recommendations for HR.

    Logic:
    1. Aggregate gap scores across all departments
    2. Weight by number of employees affected
    3. Rank courses by total org impact

    Returns list of dicts with course details and org impact.
    """

    PRIORITY_WEIGHT = {"Critical": 1.5, "High": 1.2, "Medium": 1.0, "Low": 0.8}

    # Aggregate skill gaps across all departments
    skill_org_impact = {}
    for skill in tna_df["skill"].unique():
        skill_rows  = tna_df[tna_df["skill"] == skill]
        avg_gap     = skill_rows["gap_score"].mean()
        priority    = skill_rows.sort_values("gap_score", ascending=False).iloc[0]["priority"]
        weight      = PRIORITY_WEIGHT.get(priority, 1.0)
        dept_count  = skill_rows["department"].nunique()
        skill_org_impact[skill] = round(avg_gap * weight * dept_count)

    recs = []
    seen = set()

    for skill, impact in sorted(skill_org_impact.items(), key=lambda x: x[1], reverse=True):
        if impact <= 0:
            continue

        matches = courses_df[
            courses_df["skills_covered"].str.contains(skill, na=False, case=False)
        ]

        for _, course in matches.iterrows():
            if course["course_id"] in seen:
                continue

            total_completions = len(enrol_df[
                (enrol_df["course_id"] == course["course_id"]) &
                (enrol_df["status"] == "Completed")
            ])

            depts_affected = tna_df[
                tna_df["skill"] == skill
            ]["department"].unique().tolist()

            skill_row = tna_df[tna_df["skill"] == skill].sort_values("gap_score", ascending=False).iloc[0]

            recs.append({
                "course_id":          course["course_id"],
                "title":              course["title"],
                "format":             course["format"],
                "duration_hours":     int(course["duration_hours"]),
                "level":              course["level"],
                "gap_skill":          skill,
                "gap_pts":            impact,
                "priority":           skill_row["priority"],
                "depts_affected":     len(depts_affected),
                "dept_names":         ", ".join(depts_affected[:3]) + ("..." if len(depts_affected) > 3 else ""),
                "total_completions":  total_completions,
            })
            seen.add(course["course_id"])

        if len(recs) >= top_n:
            break

    return recs[:top_n]