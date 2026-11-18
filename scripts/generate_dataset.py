"""
OpsPulse — Employee Performance & Departmental KPI Tracker
Script: generate_dataset.py
Description: Deterministically generates a realistic 2026 multi-departmental
             operational dataset (departments, employees, milestones, tasks)
             with authentic SLA profiles, seasonal bottlenecks, and delay drivers.
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 202604
AS_OF_DATE = date(2026, 11, 15)
START_DATE = date(2026, 1, 5)  # Monday of 2026-W02 -> covers W01..W46

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"

DEPARTMENTS = [
    {
        "department_id": "DEPT-ENG",
        "department_name": "Engineering",
        "department_head": "Arjun Raghavan",
        "cost_center": "CC-101",
        "target_completion_pct": 88.0,
        "target_sla_hours": 36.0,
        "target_ontime_pct": 80.0,
        "monthly_budget_usd": 145000,
    },
    {
        "department_id": "DEPT-OPS",
        "department_name": "Operations & Logistics",
        "department_head": "Meera Krishnan",
        "cost_center": "CC-102",
        "target_completion_pct": 90.0,
        "target_sla_hours": 24.0,
        "target_ontime_pct": 82.0,
        "monthly_budget_usd": 112000,
    },
    {
        "department_id": "DEPT-SUP",
        "department_name": "Customer Support",
        "cost_center": "CC-103",
        "department_head": "Karthik Subramanian",
        "target_completion_pct": 92.0,
        "target_sla_hours": 12.0,
        "target_ontime_pct": 84.0,
        "monthly_budget_usd": 78000,
    },
    {
        "department_id": "DEPT-FIN",
        "department_name": "Finance & Compliance",
        "department_head": "Ananya Iyer",
        "cost_center": "CC-104",
        "target_completion_pct": 91.0,
        "target_sla_hours": 28.0,
        "target_ontime_pct": 82.0,
        "monthly_budget_usd": 84000,
    },
    {
        "department_id": "DEPT-PRD",
        "department_name": "Product & Design",
        "department_head": "Rohan Deshmukh",
        "cost_center": "CC-105",
        "target_completion_pct": 87.0,
        "target_sla_hours": 32.0,
        "target_ontime_pct": 80.0,
        "monthly_budget_usd": 96000,
    },
    {
        "department_id": "DEPT-SLS",
        "department_name": "Sales & Partnerships",
        "department_head": "Divya Nair",
        "cost_center": "CC-106",
        "target_completion_pct": 89.0,
        "target_sla_hours": 20.0,
        "target_ontime_pct": 82.0,
        "monthly_budget_usd": 105000,
    },
]

ROLES_BY_DEPT = {
    "DEPT-ENG": ["Backend Engineer", "Data Engineer", "DevOps Engineer", "QA Automation Engineer", "Senior Software Engineer", "Tech Lead"],
    "DEPT-OPS": ["Operations Analyst", "Supply Chain Coordinator", "Fulfillment Specialist", "Process Lead", "Logistics Planner", "Inventory Analyst"],
    "DEPT-SUP": ["Support Specialist", "Technical Support Engineer", "Escalation Lead", "CX Analyst", "Onboarding Specialist", "Senior Support Associate"],
    "DEPT-FIN": ["Financial Analyst", "Compliance Auditor", "AP/AR Specialist", "Tax Operations Analyst", "Risk Controller", "Senior Finance Lead"],
    "DEPT-PRD": ["Product Analyst", "UI/UX Designer", "Product Manager", "UX Researcher", "Design Systems Lead", "Associate PM"],
    "DEPT-SLS": ["Account Executive", "Revenue Ops Analyst", "Partnerships Manager", "Sales Operations Specialist", "Enterprise SDR", "Deal Desk Lead"],
}

EMPLOYEE_NAMES = [
    # Engineering (8)
    "Aarav Sharma", "Neha Patel", "Vikram Menon", "Sneha Reddy",
    "Siddharth Verma", "Kavya Narayanan", "Pranav Kulkarni", "Ishita Banerjee",
    # Operations & Logistics (8)
    "Rahul Nair", "Pooja Sundaram", "Deepak Joshi", "Lakshmi Venkatesh",
    "Harish Gowda", "Shruti Malhotra", "Nikhil Tiwari", "Anjali Menon",
    # Customer Support (8)
    "Manoj Kumar", "Swathi Raj", "Varun Choudhary", "Keerthi Selvam",
    "Rakesh Pillai", "Nandini Rao", "Suresh Babu", "Preethi Mohan",
    # Finance & Compliance (8)
    "Gautam Sinha", "Revathi Srinivasan", "Abhishek Mishra", "Priya Balasubramanian",
    "Kiran Deshpande", "Bhavna Kapoor", "Tarun Agarwal", "Meghna Das",
    # Product & Design (8)
    "Aditi Kulkarni", "Rishabh Mehta", "Tanvi Shah", "Vivek Natarajan",
    "Simran Kaur", "Akash Chatterjee", "Niharika Verma", "Devansh Gupta",
    # Sales & Partnerships (8)
    "Raghavendra Rao", "Shreya Bhattacharya", "Kunal Khanna", "Aishwarya Iyer",
    "Sandeep Hegde", "Pallavi Joshi", "Yashwant Singh", "Ritika Bose",
]

LOCATIONS = ["Chennai", "Bengaluru", "Hyderabad", "Pune", "Remote"]

MILESTONE_TEMPLATES = {
    "DEPT-ENG": [
        ("API Latency Optimization v2", "2026-Q1", "High", date(2026, 3, 20)),
        ("Warehouse ETL Schema Migration", "2026-Q2", "Critical", date(2026, 6, 15)),
        ("Automated CI/CD Security Gates", "2026-Q2", "High", date(2026, 6, 30)),
        ("Microservices Telemetry Rollout", "2026-Q3", "Critical", date(2026, 9, 25)),
        ("Zero-Downtime DB Failover Drill", "2026-Q4", "Critical", date(2026, 10, 30)),
        ("Self-Serve Analytics API Release", "2026-Q4", "High", date(2026, 12, 10)),
    ],
    "DEPT-OPS": [
        ("Regional Hub Dispatch Redesign", "2026-Q1", "High", date(2026, 3, 18)),
        ("Vendor SLA Renegotiation Pack", "2026-Q2", "Medium", date(2026, 6, 12)),
        ("Warehouse Barcode Automation", "2026-Q3", "Critical", date(2026, 9, 15)),
        ("Q3 Carrier Bottleneck Recovery", "2026-Q3", "Critical", date(2026, 10, 10)),
        ("Cold-Chain Audit Compliance", "2026-Q4", "High", date(2026, 11, 5)),
        ("Peak-Season Capacity Readiness", "2026-Q4", "Critical", date(2026, 11, 28)),
    ],
    "DEPT-SUP": [
        ("Tier-1 Knowledge Base Overhaul", "2026-Q1", "Medium", date(2026, 3, 15)),
        ("Omnichannel Ticket Routing", "2026-Q2", "High", date(2026, 6, 10)),
        ("First-Contact Resolution Playbook", "2026-Q2", "Medium", date(2026, 6, 26)),
        ("VIP Escalation Desk Launch", "2026-Q3", "High", date(2026, 9, 18)),
        ("CSAT Automated Feedback Loop", "2026-Q4", "Medium", date(2026, 11, 1)),
        ("Holiday SLA Surge Staffing Plan", "2026-Q4", "High", date(2026, 12, 5)),
    ],
    "DEPT-FIN": [
        ("FY25 Statutory Audit Closeout", "2026-Q1", "Critical", date(2026, 3, 28)),
        ("Automated Invoice Reconciliation", "2026-Q2", "High", date(2026, 6, 19)),
        ("GST & Tax Filing Standardization", "2026-Q3", "High", date(2026, 9, 14)),
        ("Procurement Approval Workflow v3", "2026-Q3", "Critical", date(2026, 10, 22)),
        ("SOC2 Control Evidence Refresh", "2026-Q4", "Critical", date(2026, 11, 8)),
        ("2027 Departmental Budget Lock", "2026-Q4", "High", date(2026, 12, 15)),
    ],
    "DEPT-PRD": [
        ("Customer Journey Funnel Audit", "2026-Q1", "Medium", date(2026, 3, 14)),
        ("Design System 3.0 Component Kit", "2026-Q2", "High", date(2026, 6, 20)),
        ("Self-Onboarding UX Simplification", "2026-Q3", "High", date(2026, 9, 10)),
        ("Executive Mobile Dashboard Specs", "2026-Q3", "High", date(2026, 10, 18)),
        ("Accessibility WCAG 2.2 Compliance", "2026-Q4", "Medium", date(2026, 11, 22)),
        ("2027 Product Roadmap Alignment", "2026-Q4", "High", date(2026, 12, 12)),
    ],
    "DEPT-SLS": [
        ("CRM Pipeline Hygiene Automation", "2026-Q1", "Medium", date(2026, 3, 22)),
        ("Enterprise Partner Tier Program", "2026-Q2", "High", date(2026, 6, 24)),
        ("Deal Desk Discount Guardrails", "2026-Q3", "High", date(2026, 9, 20)),
        ("Renewal Risk Playbook Rollout", "2026-Q4", "High", date(2026, 11, 4)),
        ("APAC Channel Expansion Launch", "2026-Q4", "Critical", date(2026, 11, 25)),
        ("Q4 Quota Acceleration Sprint", "2026-Q4", "High", date(2026, 12, 18)),
    ],
}

TASK_CATEGORIES = {
    "DEPT-ENG": ["Feature Delivery", "Bug Fix", "Data Pipeline", "Code Review", "Infra Maintenance"],
    "DEPT-OPS": ["Dispatch Audit", "Vendor Coordination", "Inventory Sync", "SLA Recovery", "Process SOP"],
    "DEPT-SUP": ["Ticket Escalation", "Onboarding Call", "Root Cause Analysis", "KB Article", "Account Health"],
    "DEPT-FIN": ["Invoice Audit", "Compliance Check", "Budget Variance", "Reconciliation", "Policy Review"],
    "DEPT-PRD": ["Wireframe Design", "User Research", "PRD Spec", "Usability QA", "Analytics Review"],
    "DEPT-SLS": ["Proposal Review", "Contract Redline", "Partner Enablement", "CRM Audit", "Renewal Outreach"],
}

# Department-specific operational profiles (creates realistic, discoverable business insights)
DEPT_PROFILES = {
    "DEPT-ENG": {
        "base_complete_prob": 0.915,
        "base_delay_prob": 0.16,
        "delay_weights": {"Scope Creep": 0.34, "Dependency Wait": 0.32, "Resource Bottleneck": 0.18, "Tooling Issue": 0.10, "Approval Lag": 0.06},
        "quality_mean": 4.55,
        "rework_prob": 0.06,
    },
    "DEPT-OPS": {
        "base_complete_prob": 0.825,  # Bottleneck dept: misses 90% target -> Red insight
        "base_delay_prob": 0.34,
        "delay_weights": {"Vendor Delay": 0.36, "Resource Bottleneck": 0.30, "Dependency Wait": 0.18, "Tooling Issue": 0.10, "Approval Lag": 0.06},
        "quality_mean": 4.05,
        "rework_prob": 0.12,
    },
    "DEPT-SUP": {
        "base_complete_prob": 0.945,  # Benchmark velocity dept -> Green
        "base_delay_prob": 0.13,
        "delay_weights": {"Tooling Issue": 0.35, "Dependency Wait": 0.30, "Resource Bottleneck": 0.20, "Approval Lag": 0.15},
        "quality_mean": 4.52,
        "rework_prob": 0.05,
    },
    "DEPT-FIN": {
        "base_complete_prob": 0.885,  # Amber due to quarter-end approval lag
        "base_delay_prob": 0.23,
        "delay_weights": {"Approval Lag": 0.45, "Dependency Wait": 0.25, "Scope Creep": 0.15, "Resource Bottleneck": 0.15},
        "quality_mean": 4.62,
        "rework_prob": 0.04,
    },
    "DEPT-PRD": {
        "base_complete_prob": 0.895,  # Green
        "base_delay_prob": 0.17,
        "delay_weights": {"Dependency Wait": 0.36, "Scope Creep": 0.30, "Approval Lag": 0.22, "Resource Bottleneck": 0.12},
        "quality_mean": 4.44,
        "rework_prob": 0.07,
    },
    "DEPT-SLS": {
        "base_complete_prob": 0.880,  # Amber
        "base_delay_prob": 0.21,
        "delay_weights": {"Approval Lag": 0.40, "Vendor Delay": 0.20, "Dependency Wait": 0.22, "Resource Bottleneck": 0.18},
        "quality_mean": 4.35,
        "rework_prob": 0.06,
    },
}

BLOCKER_NOTES = {
    "DEPT-ENG": "Blocked on legacy schema freeze & cross-team API contract sign-off.",
    "DEPT-OPS": "Tier-2 carrier SLA slippage and scanner hardware backorder.",
    "DEPT-SUP": "Pending CRM webhook migration for automated CSAT survey triggers.",
    "DEPT-FIN": "Waiting on multi-level VP approval workflows and external auditor sample list.",
    "DEPT-PRD": "Design handoff delayed by shifting executive dashboard KPI definitions.",
    "DEPT-SLS": "Legal redline queue backlog on enterprise renewal templates.",
}


def weighted_choice(rng: random.Random, weights: dict[str, float]) -> str:
    keys = list(weights.keys())
    probs = list(weights.values())
    return rng.choices(keys, weights=probs, k=1)[0]


def get_quarter(d: date) -> str:
    q = (d.month - 1) // 3 + 1
    return f"{d.year}-Q{q}"


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_all() -> dict[str, int]:
    rng = random.Random(SEED)

    # 1. Departments
    write_csv(
        RAW_DIR / "departments.csv",
        list(DEPARTMENTS[0].keys()),
        DEPARTMENTS,
    )

    # 2. Employees (8 per department = 48 total)
    employees = []
    emp_skill = {}
    seniority_cycle = ["Lead", "Senior", "Senior", "Mid", "Mid", "Mid", "Junior", "Junior"]

    idx = 0
    for dept in DEPARTMENTS:
        dept_id = dept["department_id"]
        roles = ROLES_BY_DEPT[dept_id]
        for i in range(8):
            emp_id = f"EMP-{idx + 1:03d}"
            full_name = EMPLOYEE_NAMES[idx]
            email_slug = full_name.lower().replace(" ", ".")
            seniority = seniority_cycle[i]
            role = roles[i % len(roles)]
            hire_offset = rng.randint(180, 1600)
            hire_dt = date(2025, 11, 1) - timedelta(days=hire_offset)

            employees.append({
                "employee_id": emp_id,
                "full_name": full_name,
                "email": f"{email_slug}@opspulse.io",
                "department_id": dept_id,
                "role_title": role,
                "seniority_level": seniority,
                "location": LOCATIONS[(idx + i) % len(LOCATIONS)],
                "hire_date": hire_dt.isoformat(),
                "weekly_capacity_hrs": 40.0,
                "status": "Active",
            })

            # Individual skill factor creates natural Top Performers vs Needs Support spread
            base_factor = {"Lead": 1.07, "Senior": 1.04, "Mid": 1.00, "Junior": 0.94}[seniority]
            emp_skill[emp_id] = max(0.80, min(1.14, base_factor + rng.uniform(-0.11, 0.09)))
            idx += 1

    write_csv(RAW_DIR / "employees.csv", list(employees[0].keys()), employees)

    # Group employees by department
    emps_by_dept: dict[str, list[dict]] = {}
    for e in employees:
        emps_by_dept.setdefault(e["department_id"], []).append(e)

    # 3. Milestones (36 total: 6 per department across Q1-Q4 2026)
    milestones = []
    m_counter = 1
    for dept in DEPARTMENTS:
        dept_id = dept["department_id"]
        dept_emps = emps_by_dept[dept_id]
        for title, quarter, priority, due_dt in MILESTONE_TEMPLATES[dept_id]:
            m_id = f"MS-{m_counter:03d}"
            owner = dept_emps[(m_counter - 1) % 3]["employee_id"]  # Leads & Seniors own milestones

            if due_dt < date(2026, 9, 1):
                status = "Completed"
                actual_dt = (due_dt + timedelta(days=rng.randint(-4, 5))).isoformat()
                comp_pct = 100.0
                blocker = ""
            elif due_dt <= AS_OF_DATE:
                # Realistic mix of Completed vs Overdue escalations in Q3/Q4
                is_overdue = (dept_id in ("DEPT-OPS", "DEPT-FIN", "DEPT-ENG", "DEPT-PRD") and due_dt >= date(2026, 9, 15))
                if dept_id == "DEPT-SLS" and due_dt >= date(2026, 11, 1):
                    is_overdue = True
                if is_overdue:
                    status = "Overdue"
                    actual_dt = ""
                    comp_pct = round(rng.uniform(58.0, 86.0), 1)
                    blocker = BLOCKER_NOTES[dept_id]
                else:
                    status = "Completed"
                    actual_dt = (due_dt + timedelta(days=rng.randint(-3, 2))).isoformat()
                    comp_pct = 100.0
                    blocker = ""
            else:
                # Upcoming Q4 milestones: some At Risk, some In Progress
                if priority == "Critical" and dept_id in ("DEPT-OPS", "DEPT-SLS"):
                    status = "At Risk"
                    comp_pct = round(rng.uniform(42.0, 64.0), 1)
                    blocker = BLOCKER_NOTES[dept_id]
                else:
                    status = "In Progress"
                    comp_pct = round(rng.uniform(62.0, 82.0), 1)
                    blocker = ""
                actual_dt = ""

            milestones.append({
                "milestone_id": m_id,
                "milestone_name": title,
                "department_id": dept_id,
                "owner_employee_id": owner,
                "quarter": quarter,
                "priority": priority,
                "planned_due_date": due_dt.isoformat(),
                "actual_completed_date": actual_dt,
                "status": status,
                "completion_pct": comp_pct,
                "blocker_summary": blocker,
            })
            m_counter += 1

    write_csv(RAW_DIR / "milestones.csv", list(milestones[0].keys()), milestones)

    milestones_by_dept_q: dict[tuple[str, str], list[dict]] = {}
    milestones_by_dept: dict[str, list[dict]] = {}
    for m in milestones:
        milestones_by_dept_q.setdefault((m["department_id"], m["quarter"]), []).append(m)
        milestones_by_dept.setdefault(m["department_id"], []).append(m)

    # 4. Granular 2026 Tasks (46 ISO weeks: Jan 1 - Nov 15, 2026, ~2,450 tasks)
    tasks = []
    dept_lookup = {d["department_id"]: d for d in DEPARTMENTS}
    priorities = ["Critical", "High", "Medium", "Low"]
    priority_weights = [0.14, 0.30, 0.40, 0.16]
    priority_sla_mult = {"Critical": 0.65, "High": 0.85, "Medium": 1.0, "Low": 1.35}

    task_num = 1
    current_date = date(2026, 1, 1)
    while current_date <= AS_OF_DATE:
        # Tasks are assigned mostly on weekdays
        if current_date.weekday() < 5:
            iso_year, iso_week, _ = current_date.isocalendar()
            week_label = f"{iso_year}-W{iso_week:02d}"
            month_label = current_date.strftime("%Y-%m")
            quarter = get_quarter(current_date)

            # ~10-12 tasks across org per business day (~2,400+ over 228 business days)
            daily_tasks = rng.randint(9, 13)
            for _ in range(daily_tasks):
                dept = rng.choice(DEPARTMENTS)
                dept_id = dept["department_id"]
                prof = DEPT_PROFILES[dept_id]
                emp = rng.choice(emps_by_dept[dept_id])
                emp_id = emp["employee_id"]
                skill = emp_skill[emp_id]

                # Match milestone for dept & quarter
                q_ms = milestones_by_dept_q.get((dept_id, quarter)) or milestones_by_dept[dept_id]
                ms = rng.choice(q_ms)

                category = rng.choice(TASK_CATEGORIES[dept_id])
                priority = rng.choices(priorities, weights=priority_weights, k=1)[0]

                sla_hours = round(dept["target_sla_hours"] * priority_sla_mult[priority], 1)
                due_days = max(1, int(round(sla_hours / 8.0)))
                due_dt = current_date + timedelta(days=due_days)

                est_hours = round(rng.uniform(2.0, min(18.0, sla_hours * 0.65)), 1)

                # Seasonal realism:
                # - Operations experiences Q3 vendor bottleneck (W28-W38)
                # - Finance has quarter-end approval lag spikes (W12-13, W25-26, W38-39)
                # - Organization improves in Q4 after OpsPulse adoption (W41+)
                delay_prob = prof["base_delay_prob"] / skill
                complete_prob = min(0.985, prof["base_complete_prob"] * skill)

                if dept_id == "DEPT-OPS" and 28 <= iso_week <= 38:
                    delay_prob += 0.22
                    complete_prob -= 0.08
                if dept_id == "DEPT-FIN" and iso_week in (12, 13, 25, 26, 38, 39):
                    delay_prob += 0.16
                if iso_week >= 41:
                    delay_prob *= 0.85
                    complete_prob = min(0.98, complete_prob + 0.025)

                # Determine task status
                days_from_asof = (AS_OF_DATE - current_date).days
                if days_from_asof <= 2 and rng.random() < 0.25:
                    status = "In Progress"
                elif rng.random() < complete_prob:
                    status = "Completed"
                else:
                    if due_dt < AS_OF_DATE:
                        status = "Blocked" if rng.random() < 0.28 else "Overdue"
                    else:
                        status = "In Progress"

                # Turnaround, delay, quality, rework
                is_delayed = rng.random() < delay_prob
                if status == "Completed":
                    if is_delayed:
                        delay_reason = weighted_choice(rng, prof["delay_weights"])
                        delay_hours = round(rng.uniform(3.0, sla_hours * 1.15), 1)
                        turnaround_hours = round(sla_hours + delay_hours * rng.uniform(0.65, 1.05), 1)
                    else:
                        delay_reason = "None"
                        delay_hours = 0.0
                        turnaround_hours = round(sla_hours * rng.uniform(0.35, 0.96) / skill, 1)

                    comp_days = max(0, int(round(turnaround_hours / 8.0)))
                    completed_dt = min(AS_OF_DATE, current_date + timedelta(days=comp_days))
                    actual_hours = round(max(1.0, est_hours * rng.uniform(0.82, 1.28) + (delay_hours * 0.15)), 1)
                    quality_score = round(max(2.2, min(5.0, rng.gauss(prof["quality_mean"] * (0.96 + 0.04 * skill), 0.35))), 2)
                    rework_flag = 1 if rng.random() < (prof["rework_prob"] / skill) else 0
                elif status in ("Overdue", "Blocked"):
                    delay_reason = weighted_choice(rng, prof["delay_weights"])
                    overdue_days = max(1, min(14, (AS_OF_DATE - due_dt).days))
                    delay_hours = round(overdue_days * rng.uniform(3.0, 6.5), 1)
                    turnaround_hours = ""
                    completed_dt = None
                    actual_hours = round(est_hours * rng.uniform(0.6, 1.35), 1)
                    quality_score = ""
                    rework_flag = 0
                else:
                    # In Progress
                    delay_reason = "None"
                    delay_hours = 0.0
                    turnaround_hours = ""
                    completed_dt = None
                    actual_hours = round(est_hours * rng.uniform(0.25, 0.75), 1)
                    quality_score = ""
                    rework_flag = 0

                tasks.append({
                    "task_id": f"TSK-{task_num:05d}",
                    "task_title": f"{category} — {ms['milestone_name'][:26]} #{task_num % 97 + 1}",
                    "employee_id": emp_id,
                    "department_id": dept_id,
                    "milestone_id": ms["milestone_id"],
                    "task_category": category,
                    "priority": priority,
                    "assigned_date": current_date.isoformat(),
                    "due_date": due_dt.isoformat(),
                    "completed_date": completed_dt.isoformat() if completed_dt else "",
                    "status": status,
                    "sla_hours": sla_hours,
                    "turnaround_hours": turnaround_hours,
                    "estimated_hours": est_hours,
                    "actual_hours": actual_hours,
                    "delay_hours": delay_hours,
                    "delay_reason": delay_reason,
                    "quality_score": quality_score,
                    "rework_flag": rework_flag,
                    "iso_year": iso_year,
                    "iso_week": iso_week,
                    "week_label": week_label,
                    "month_label": month_label,
                    "quarter": quarter,
                })
                task_num += 1

        current_date += timedelta(days=1)

    write_csv(RAW_DIR / "tasks.csv", list(tasks[0].keys()), tasks)

    return {
        "departments": len(DEPARTMENTS),
        "employees": len(employees),
        "milestones": len(milestones),
        "tasks": len(tasks),
    }


if __name__ == "__main__":
    counts = generate_all()
    print("Generated OpsPulse 2026 raw datasets:", counts)
