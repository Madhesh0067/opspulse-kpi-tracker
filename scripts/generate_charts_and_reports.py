"""
OpsPulse — Employee Performance & Departmental KPI Tracker
Script: generate_charts_and_reports.py
Description: Queries the SQLite warehouse to generate:
               1. High-resolution executive charts (reports/figures/*.png)
               2. Automated Weekly Executive Scorecard Markdown report
               3. Live JSON data feed (dashboard/data.js) for the interactive dashboard
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "opspulse.db"
FIG_DIR = ROOT_DIR / "reports" / "figures"
REPORT_MD = ROOT_DIR / "reports" / "weekly_executive_scorecard.md"
DASH_DATA_JS = ROOT_DIR / "dashboard" / "data.js"

# Clean executive styling
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.edgecolor": "#CBD5E1",
    "axes.linewidth": 0.9,
    "axes.grid": True,
    "grid.color": "#E2E8F0",
    "grid.linestyle": "--",
    "grid.alpha": 0.7,
    "figure.facecolor": "#FFFFFF",
    "axes.facecolor": "#FFFFFF",
})

PALETTE = {
    "navy": "#0F172A",
    "blue": "#2563EB",
    "sky": "#0EA5E9",
    "green": "#10B981",
    "amber": "#F59E0B",
    "red": "#EF4444",
    "purple": "#8B5CF6",
    "slate": "#64748B",
}


def fetch_frames() -> dict[str, pd.DataFrame]:
    conn = sqlite3.connect(DB_PATH)
    try:
        return {
            "depts": pd.read_sql_query("SELECT * FROM vw_department_kpi_summary ORDER BY completion_rate_pct DESC", conn),
            "weekly": pd.read_sql_query("SELECT * FROM vw_weekly_scorecard ORDER BY iso_year, iso_week", conn),
            "employees": pd.read_sql_query("SELECT * FROM vw_employee_performance ORDER BY org_rank ASC", conn),
            "delays": pd.read_sql_query("SELECT * FROM vw_operational_delays", conn),
            "milestones": pd.read_sql_query("SELECT * FROM vw_overdue_milestones", conn),
            "tasks": pd.read_sql_query("SELECT * FROM vw_task_metrics", conn),
            "dept_delay_matrix": pd.read_sql_query(
                """
                SELECT department_name, delay_reason, COUNT(*) AS incidents, ROUND(SUM(delay_hours), 1) AS delay_hours
                FROM vw_task_metrics
                WHERE delay_hours > 0 AND delay_reason <> 'None'
                GROUP BY department_name, delay_reason
                """,
                conn,
            ),
            "quarterly": pd.read_sql_query(
                """
                SELECT
                    quarter,
                    COUNT(*) AS total_tasks,
                    ROUND(100.0 * SUM(is_completed) / COUNT(*), 2) AS completion_rate_pct,
                    ROUND(100.0 * SUM(is_sla_met) / NULLIF(SUM(is_completed), 0), 2) AS sla_compliance_pct,
                    ROUND(AVG(CASE WHEN is_completed = 1 THEN turnaround_hours END), 2) AS avg_turnaround_hrs,
                    ROUND(SUM(delay_hours), 1) AS total_delay_hrs
                FROM vw_task_metrics
                GROUP BY quarter
                ORDER BY quarter
                """,
                conn,
            ),
        }
    finally:
        conn.close()


def plot_department_kpis(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(11, 5.4), dpi=160)
    x = np.arange(len(df))
    w = 0.28

    rag_colors = [
        PALETTE["green"] if s == "Green" else (PALETTE["amber"] if s == "Amber" else PALETTE["red"])
        for s in df["rag_status"]
    ]

    bars_comp = ax.bar(x - w, df["completion_rate_pct"], width=w, label="Completion Rate %", color=PALETTE["blue"], zorder=3)
    bars_sla = ax.bar(x, df["sla_compliance_pct"], width=w, label="SLA Compliance %", color=PALETTE["sky"], zorder=3)
    bars_tgt = ax.bar(x + w, df["target_completion_pct"], width=w, label="Target Completion %", color="#CBD5E1", edgecolor="#64748B", linewidth=0.8, zorder=3)

    for b in bars_comp:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + 0.8, f"{h:.1f}%", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=PALETTE["navy"])
    for b in bars_sla:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + 0.8, f"{h:.1f}%", ha="center", va="bottom", fontsize=8, color=PALETTE["slate"])

    # RAG status pill markers at top
    for i, (status, col) in enumerate(zip(df["rag_status"], rag_colors)):
        ax.text(i, 102.5, status.upper(), ha="center", va="center", fontsize=8, fontweight="bold", color="#FFFFFF",
                bbox=dict(boxstyle="round,pad=0.25", facecolor=col, edgecolor="none"))

    ax.set_xticks(x)
    ax.set_xticklabels(df["department_name"], rotation=15, ha="right", fontsize=9.5, fontweight="bold")
    ax.set_ylim(55, 108)
    ax.set_ylabel("Percentage (%)", fontweight="bold")
    ax.set_title("OpsPulse 2026 — Departmental Completion Rate, SLA Compliance & Targets (RAG Status)", fontsize=12.5, fontweight="bold", pad=14, color=PALETTE["navy"])
    ax.legend(loc="lower left", frameon=True, facecolor="#FFFFFF")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "01_department_kpi_vs_target.png")
    plt.close(fig)


def plot_weekly_trend(df: pd.DataFrame) -> None:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6.6), dpi=160, sharex=True, gridspec_kw={"height_ratios": [1.3, 1]})
    x = np.arange(len(df))

    ax1.plot(x, df["completion_rate_pct"], color=PALETTE["blue"], alpha=0.45, linewidth=1.4, marker="o", markersize=3.5, label="Weekly Completion %")
    ax1.plot(x, df["rolling_4w_completion_pct"], color=PALETTE["navy"], linewidth=2.5, label="4-Week Rolling Avg Completion %")
    ax1.plot(x, df["sla_compliance_pct"], color=PALETTE["sky"], linewidth=1.8, linestyle="--", label="Weekly SLA Compliance %")
    ax1.axhline(88.0, color=PALETTE["green"], linestyle=":", linewidth=1.4, label="Org Completion Target (88%)")
    ax1.axvspan(27, 37, color=PALETTE["red"], alpha=0.07, label="Q3 Operations Vendor Bottleneck (W28-W38)")
    ax1.set_ylabel("Rate (%)", fontweight="bold")
    ax1.set_ylim(60, 102)
    ax1.set_title("OpsPulse 2026 — Automated Weekly Scorecard Momentum & Turnaround Trend", fontsize=12.5, fontweight="bold", pad=12, color=PALETTE["navy"])
    ax1.legend(loc="lower left", ncol=3, fontsize=8.5, frameon=True)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    ax2.bar(x, df["total_delay_hrs"], color=PALETTE["amber"], alpha=0.75, label="Weekly Delay Hours Lost", zorder=2)
    ax2_twin = ax2.twinx()
    ax2_twin.plot(x, df["rolling_4w_turnaround_hrs"], color=PALETTE["red"], linewidth=2.2, label="4-Week Rolling Turnaround (h)")
    ax2.set_ylabel("Delay Hours", fontweight="bold", color="#B45309")
    ax2_twin.set_ylabel("Turnaround (Hrs)", fontweight="bold", color=PALETTE["red"])
    ax2.set_xticks(x[::4])
    ax2.set_xticklabels(df["week_label"].iloc[::4], rotation=25, ha="right", fontsize=8.5)
    ax2.spines["top"].set_visible(False)
    ax2_twin.spines["top"].set_visible(False)

    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=8.5, frameon=True)

    fig.tight_layout()
    fig.savefig(FIG_DIR / "02_weekly_scorecard_trend.png")
    plt.close(fig)


def plot_delay_pareto(df: pd.DataFrame) -> None:
    fig, ax1 = plt.subplots(figsize=(10.5, 5.2), dpi=160)
    x = np.arange(len(df))

    bars = ax1.bar(x, df["total_delay_hrs"], color=PALETTE["blue"], width=0.58, zorder=3, label="Total Delay Hours")
    for b, cnt in zip(bars, df["delayed_task_count"]):
        h = b.get_height()
        ax1.text(b.get_x() + b.get_width() / 2, h + max(df["total_delay_hrs"]) * 0.02,
                 f"{h:,.0f}h\n({cnt} tasks)", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=PALETTE["navy"])

    ax2 = ax1.twinx()
    ax2.plot(x, df["cumulative_share_pct"], color=PALETTE["red"], marker="o", linewidth=2.4, markersize=6, label="Cumulative % Share", zorder=5)
    ax2.axhline(80.0, color=PALETTE["amber"], linestyle="--", linewidth=1.3, label="80% Pareto Threshold")
    for i, pct in enumerate(df["cumulative_share_pct"]):
        offset_y = -6.0 if i == 2 else 3.2
        ax2.text(i, pct + offset_y, f"{pct:.1f}%", ha="center", va="bottom", fontsize=8.5, color=PALETTE["red"], fontweight="bold",
                 bbox=dict(boxstyle="round,pad=0.18", facecolor="#FFFFFF", edgecolor="none", alpha=0.85))

    ax1.set_xticks(x)
    ax1.set_xticklabels(df["delay_reason"], rotation=15, ha="right", fontsize=9.5, fontweight="bold")
    ax1.set_ylabel("Total Delay Hours Lost", fontweight="bold", color=PALETTE["blue"])
    ax1.set_ylim(0, max(df["total_delay_hrs"]) * 1.28)
    ax2.set_ylabel("Cumulative Share (%)", fontweight="bold", color=PALETTE["red"])
    ax2.set_ylim(0, 114)
    ax1.set_title("OpsPulse 2026 — Operational Delay Root-Cause Pareto Analysis", fontsize=12.5, fontweight="bold", pad=14, color=PALETTE["navy"])
    ax1.spines["top"].set_visible(False)
    ax2.spines["top"].set_visible(False)

    l1, lb1 = ax1.get_legend_handles_labels()
    l2, lb2 = ax2.get_legend_handles_labels()
    ax1.legend(l1 + l2, lb1 + lb2, loc="center right", frameon=True)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "03_operational_delay_pareto.png")
    plt.close(fig)


def plot_employee_matrix(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 5.6), dpi=160)
    dept_colors = {
        "Engineering": "#2563EB",
        "Operations & Logistics": "#EF4444",
        "Customer Support": "#10B981",
        "Finance & Compliance": "#8B5CF6",
        "Product & Design": "#0EA5E9",
        "Sales & Partnerships": "#F59E0B",
    }

    med_tasks = df["total_tasks"].median()
    ax.axvline(med_tasks, color="#94A3B8", linestyle="--", linewidth=1.1)
    ax.axhline(84.0, color="#94A3B8", linestyle="--", linewidth=1.1)

    for dept_name, grp in df.groupby("department_name"):
        ax.scatter(
            grp["total_tasks"],
            grp["productivity_index"],
            s=95,
            alpha=0.85,
            color=dept_colors.get(dept_name, PALETTE["slate"]),
            edgecolors="#FFFFFF",
            linewidth=0.9,
            label=dept_name,
            zorder=3,
        )

    # Annotate top 3 & bottom 2
    for _, row in pd.concat([df.head(3), df.tail(2)]).iterrows():
        ax.annotate(
            row["full_name"],
            (row["total_tasks"], row["productivity_index"]),
            textcoords="offset points",
            xytext=(6, 4),
            fontsize=8,
            fontweight="bold",
            color=PALETTE["navy"],
        )

    y_min = max(55, df["productivity_index"].min() - 4.5)
    y_max = min(100, df["productivity_index"].max() + 4.5)
    ax.set_ylim(y_min, y_max)
    ax.text(df["total_tasks"].max() + 0.5, y_max - 1.2, "High Volume / High Output\n(Star Performers)", ha="right", va="top", fontsize=8.5, color=PALETTE["green"], fontweight="bold")
    ax.text(df["total_tasks"].max() + 0.5, y_min + 1.0, "High Volume / Lower Index\n(Workload Rebalance Needed)", ha="right", va="bottom", fontsize=8.5, color=PALETTE["red"], fontweight="bold")

    ax.set_xlabel("Total Assigned Tasks (2026 YTD)", fontweight="bold")
    ax.set_ylabel("Composite Productivity Index (0-100)", fontweight="bold")
    ax.set_title("OpsPulse 2026 — Employee Workload vs. Productivity Index Matrix", fontsize=12.5, fontweight="bold", pad=12, color=PALETTE["navy"])
    ax.legend(loc="lower left", ncol=2, fontsize=8.5, frameon=True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "04_employee_productivity_matrix.png")
    plt.close(fig)


def write_weekly_markdown_report(frames: dict[str, pd.DataFrame]) -> dict[str, object]:
    tasks = frames["tasks"]
    depts = frames["depts"]
    weekly = frames["weekly"]
    delays = frames["delays"]
    milestones = frames["milestones"]
    employees = frames["employees"]

    total_tasks = len(tasks)
    completed = int(tasks["is_completed"].sum())
    comp_rate = round(100.0 * completed / total_tasks, 2)
    on_time_rate = round(100.0 * tasks["is_on_time"].sum() / completed, 2)
    sla_rate = round(100.0 * tasks["is_sla_met"].sum() / completed, 2)
    avg_turnaround = round(float(tasks.loc[tasks["is_completed"] == 1, "turnaround_hours"].mean()), 2)
    total_delay = round(float(tasks["delay_hours"].sum()), 1)
    overdue_tasks = int((tasks["status"] == "Overdue").sum())
    blocked_tasks = int((tasks["status"] == "Blocked").sum())

    latest_w = weekly.iloc[-1]
    top_dept = depts.iloc[0]
    bot_dept = depts.sort_values("completion_variance_pct").iloc[0]
    top_delay = delays.iloc[0]
    top_2_delay_share = round(float(delays.head(2)["share_of_delay_hrs_pct"].sum()), 1)

    lines = [
        "# OpsPulse — Automated Weekly Executive KPI Scorecard",
        "",
        f"**Reporting Period:** 2026 YTD (ISO Weeks `2026-W01` – `{latest_w['week_label']}`) | **Snapshot Date:** 2026-11-18  ",
        "**Data Source:** `data/opspulse.db` (`vw_department_kpi_summary`, `vw_weekly_scorecard`, `vw_operational_delays`, `vw_overdue_milestones`)",
        "",
        "---",
        "",
        "## 1. Executive Headline KPIs (YTD 2026)",
        "",
        "| Metric | YTD Actual | Status / Note |",
        "| :--- | :---: | :--- |",
        f"| **Total Tasks Monitored** | **{total_tasks:,}** | Across 6 departments & 48 employees |",
        f"| **Overall Task Completion Rate** | **{comp_rate:.1f}%** | {completed:,} completed / {overdue_tasks} overdue / {blocked_tasks} blocked |",
        f"| **On-Time Delivery Rate** | **{on_time_rate:.1f}%** | Completed on or before due date |",
        f"| **SLA Compliance Rate** | **{sla_rate:.1f}%** | Completed within departmental SLA hours |",
        f"| **Average Turnaround Time** | **{avg_turnaround:.1f} hrs** | Weighted across all completed tasks |",
        f"| **Total Operational Delay Lost** | **{total_delay:,.1f} hrs** | Top driver: **{top_delay['delay_reason']}** ({top_delay['share_of_delay_hrs_pct']:.1f}%) |",
        f"| **Overdue / At-Risk Milestones** | **{len(milestones)}** | Escalated for executive intervention |",
        "",
        "---",
        "",
        "## 2. Departmental Performance Scorecard",
        "",
        "| Department | Dept Head | Tasks | Completion % | Target % | Variance | SLA % | Avg TAT (h) | Delay Hrs | RAG |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for _, r in depts.iterrows():
        sign = "+" if r["completion_variance_pct"] >= 0 else ""
        lines.append(
            f"| {r['department_name']} | {r['department_head']} | {int(r['total_tasks'])} | "
            f"{r['completion_rate_pct']:.1f}% | {r['target_completion_pct']:.1f}% | "
            f"{sign}{r['completion_variance_pct']:.1f}% | {r['sla_compliance_pct']:.1f}% | "
            f"{r['avg_turnaround_hrs']:.1f} | {r['total_delay_hrs']:,.1f} | **{r['rag_status']}** |"
        )

    lines += [
        "",
        "---",
        "",
        "## 3. Operational Delay Root-Cause Pareto",
        "",
        "| Delay Root Cause | Incidents | Total Delay Hrs | Avg Delay (h) | Critical Impacted | % Share | Cumulative % |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for _, r in delays.iterrows():
        lines.append(
            f"| {r['delay_reason']} | {int(r['delayed_task_count'])} | {r['total_delay_hrs']:,.1f} | "
            f"{r['avg_delay_hrs']:.1f} | {int(r['critical_tasks_impacted'])} | "
            f"{r['share_of_delay_hrs_pct']:.1f}% | {r['cumulative_share_pct']:.1f}% |"
        )

    lines += [
        "",
        "---",
        "",
        "## 4. Overdue & At-Risk Milestones Escalation Queue",
        "",
        "| ID | Milestone | Department | Owner | Priority | Due Date | Status | % Done | Open Delayed Tasks | Blocker |",
        "| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |",
    ]
    for _, r in milestones.iterrows():
        lines.append(
            f"| {r['milestone_id']} | {r['milestone_name']} | {r['department_name']} | {r['owner_name']} | "
            f"**{r['priority']}** | {r['planned_due_date']} | {r['status']} | {r['completion_pct']:.0f}% | "
            f"{int(r['open_delayed_tasks'])} | {r['blocker_summary']} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 5. Top 5 Performers (Composite Productivity Index)",
        "",
        "| Rank | Employee | Department | Role | Completed | Completion % | SLA % | Quality | Productivity Index |",
        "| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |",
    ]
    for _, r in employees.head(5).iterrows():
        lines.append(
            f"| #{int(r['org_rank'])} | {r['full_name']} | {r['department_name']} | {r['role_title']} | "
            f"{int(r['completed_tasks'])} | {r['completion_rate_pct']:.1f}% | {r['sla_compliance_pct']:.1f}% | "
            f"{r['avg_quality_score']:.2f}/5 | **{r['productivity_index']:.1f}** |"
        )

    lines += [
        "",
        "---",
        "",
        "## 6. Key Executive Insights & Recommended Actions",
        "",
        f"1. **Primary Bottleneck — {bot_dept['department_name']}:** Trailing its {bot_dept['target_completion_pct']:.0f}% completion target by `{bot_dept['completion_variance_pct']:.1f}%` with `{bot_dept['total_delay_hrs']:,.1f}` lost delay hours. Driven heavily by Q3 carrier/vendor slippage and resource bottlenecks.",
        f"2. **Benchmark Team — {top_dept['department_name']}:** Leading the organization at `{top_dept['completion_rate_pct']:.1f}%` completion and `{top_dept['sla_compliance_pct']:.1f}%` SLA compliance — playbook should be replicated for intake triage.",
        f"3. **80/20 Delay Focus:** The top 2 delay categories account for **{top_2_delay_share}%** of total operational delay hours. Enforcing pre-sprint dependency sign-off and automated VP approval reminders in Finance/Sales can recover >35% of lost hours.",
        f"4. **Immediate Milestone Escalation:** `{len(milestones)}` milestones are Overdue or At Risk, with Critical items in Operations & Logistics and Finance & Compliance requiring executive unblocking this week.",
        "",
    ]

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed,
        "completion_rate_pct": comp_rate,
        "on_time_rate_pct": on_time_rate,
        "sla_compliance_pct": sla_rate,
        "avg_turnaround_hrs": avg_turnaround,
        "total_delay_hrs": total_delay,
        "overdue_tasks": overdue_tasks,
        "blocked_tasks": blocked_tasks,
        "overdue_milestones": len(milestones),
        "top_dept": top_dept["department_name"],
        "bottleneck_dept": bot_dept["department_name"],
        "top_delay_reason": top_delay["delay_reason"],
    }


def export_dashboard_js(frames: dict[str, pd.DataFrame], headline: dict[str, object]) -> None:
    payload = {
        "generated_at": "2026-11-18",
        "headline": headline,
        "departments": frames["depts"].to_dict(orient="records"),
        "weekly": frames["weekly"].to_dict(orient="records"),
        "employees": frames["employees"].to_dict(orient="records"),
        "delays": frames["delays"].to_dict(orient="records"),
        "milestones": frames["milestones"].to_dict(orient="records"),
        "dept_delay_matrix": frames["dept_delay_matrix"].to_dict(orient="records"),
        "quarterly": frames["quarterly"].to_dict(orient="records"),
        "tasks_slim": frames["tasks"][[
            "department_name", "quarter", "priority", "status",
            "is_completed", "is_on_time", "is_sla_met",
            "turnaround_hours", "delay_hours", "delay_reason", "week_label"
        ]].fillna({"turnaround_hours": 0}).to_dict(orient="records"),
    }
    DASH_DATA_JS.parent.mkdir(parents=True, exist_ok=True)
    DASH_DATA_JS.write_text("window.OPSPULSE_DATA = " + json.dumps(payload, separators=(",", ":")) + ";\n", encoding="utf-8")


def generate_all_reports() -> dict[str, object]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    frames = fetch_frames()
    plot_department_kpis(frames["depts"])
    plot_weekly_trend(frames["weekly"])
    plot_delay_pareto(frames["delays"])
    plot_employee_matrix(frames["employees"])
    headline = write_weekly_markdown_report(frames)
    export_dashboard_js(frames, headline)
    return headline


if __name__ == "__main__":
    summary = generate_all_reports()
    print("Generated charts, weekly scorecard report, and dashboard data:", summary)
