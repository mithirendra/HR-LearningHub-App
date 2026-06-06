import pandas as pd
import numpy as np
from datetime import datetime

# ============================================================
# SKILLS FEED PIPELINE — Component 6
# Reads employee skills + manager skills needed
# Recalculates TNA gap scores
# Writes updated tna_data.csv
# Run automatically whenever new skills data is uploaded
# ============================================================

def run_pipeline(verbose=True):
    """
    Main pipeline function.
    Called on app startup and after any skills upload.
    Returns summary dict for logging.
    """

    if verbose:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Skills Feed Pipeline starting...")

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------
    master   = pd.read_csv("data/employee_master.csv")
    skills   = pd.read_csv("data/employee_skills.csv")
    needed   = pd.read_csv("data/skills_needed.csv")

    # --------------------------------------------------------
    # SKILL LEVEL → NUMERIC SCORE
    # Used to calculate current supply per skill
    # --------------------------------------------------------
    LEVEL_SCORE = {"Beginner": 30, "Intermediate": 65, "Advanced": 90}

    def level_to_score(level):
        return LEVEL_SCORE.get(level, 0)

    # --------------------------------------------------------
    # PRIORITY → DEMAND SCORE
    # Manager-declared priority maps to a numeric demand target
    # --------------------------------------------------------
    PRIORITY_DEMAND = {"Critical": 90, "High": 75, "Medium": 60, "Low": 45}

    # --------------------------------------------------------
    # CALCULATE CURRENT SUPPLY
    # For each department + skill: average proficiency score
    # across all employees in that department who have the skill
    # --------------------------------------------------------
    skills_with_dept = skills.merge(
        master[["employee_id", "department", "role"]],
        on="employee_id",
        how="left"
    )

    skills_with_dept["score"] = skills_with_dept["skill_level"].apply(level_to_score)

    current_supply = (
        skills_with_dept
        .groupby(["department", "role", "skill_name"])["score"]
        .mean()
        .round(1)
        .reset_index()
        .rename(columns={"skill_name": "skill", "score": "current_supply"})
    )

    # --------------------------------------------------------
    # CALCULATE FUTURE DEMAND
    # From manager-declared skills needed, map priority to demand
    # --------------------------------------------------------
    needed["future_demand"] = needed["priority"].map(PRIORITY_DEMAND)

    # Aggregate demand per department + skill
    # If same skill declared multiple times, take the highest demand
    future_demand = (
        needed
        .groupby(["department", "skill_name"])["future_demand"]
        .max()
        .reset_index()
        .rename(columns={"skill_name": "skill"})
    )

    # --------------------------------------------------------
    # BUILD TNA — merge supply and demand
    # For skills with supply but no declared demand: keep as low risk
    # For skills with demand but no current supply: critical gap
    # --------------------------------------------------------

    # Get all unique dept/role combos from master
    dept_roles = master[["department", "role"]].drop_duplicates()

    # Cross join dept_roles with future_demand to get all combinations
    tna_rows = []

    for _, dr in dept_roles.iterrows():
        dept = dr["department"]
        role = dr["role"]

        # Demanded skills for this department
        dept_demand = future_demand[future_demand["department"] == dept]

        for _, demand_row in dept_demand.iterrows():
            skill = demand_row["skill"]

            # Find current supply for this dept/role/skill
            supply_match = current_supply[
                (current_supply["department"] == dept) &
                (current_supply["role"] == role) &
                (current_supply["skill"] == skill)
            ]

            c_supply = round(supply_match["current_supply"].values[0]) if not supply_match.empty else 0
            f_demand = int(demand_row["future_demand"])
            gap      = max(0, f_demand - c_supply)

            # Assign priority based on gap size
            if gap >= 50:   priority = "Critical"
            elif gap >= 30: priority = "High"
            elif gap >= 15: priority = "Medium"
            else:           priority = "Low"

            tna_rows.append({
                "department":     dept,
                "role":           role,
                "skill":          skill,
                "current_supply": c_supply,
                "future_demand":  f_demand,
                "gap_score":      gap,
                "priority":       priority,
                "last_updated":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })

    tna_df = pd.DataFrame(tna_rows)

    # --------------------------------------------------------
    # WRITE UPDATED TNA
    # --------------------------------------------------------
    tna_df.to_csv("data/tna_data.csv", index=False)

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------
    summary = {
        "total_records":    len(tna_df),
        "critical_gaps":    len(tna_df[tna_df["priority"] == "Critical"]),
        "high_gaps":        len(tna_df[tna_df["priority"] == "High"]),
        "departments":      tna_df["department"].nunique(),
        "skills_tracked":   tna_df["skill"].nunique(),
        "run_at":           datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    if verbose:
        print(f"  ✓ TNA recalculated — {summary['total_records']} records")
        print(f"  ✓ Critical gaps: {summary['critical_gaps']}")
        print(f"  ✓ High gaps: {summary['high_gaps']}")
        print(f"  ✓ Departments tracked: {summary['departments']}")
        print(f"  ✓ Skills tracked: {summary['skills_tracked']}")
        print(f"  Pipeline complete.\n")

    return summary


# ============================================================
# RUN STANDALONE — python pipeline.py
# ============================================================
if __name__ == "__main__":
    run_pipeline()