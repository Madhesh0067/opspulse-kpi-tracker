"""
OpsPulse — Employee Performance & Departmental KPI Tracker
Script: build_excel_tracker.py
Description: Builds a centralized, formula-driven MS Excel / Google Sheets
             compatible workbook (excel/OpsPulse_KPI_Tracker.xlsx) featuring:
               1. Executive_Dashboard  (Live KPI cards, Dept scorecard, Delay Pareto, 3 native charts)
               2. Weekly_Scorecard     (46-week automated scorecard with WoW deltas & RAG)
               3. Employee_Leaderboard (48 employees with Productivity Index, RANK & Tier)
               4. Overdue_Milestones   (Leadership escalation queue)
               5. Task_Log             (Full 2026 operational ledger with helper formulas)
               6. Departments_Ref      (Department targets & metadata)
               7. Employees_Ref        (Employee roster directory)
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "opspulse.db"
OUT_XLSX = ROOT_DIR / "excel" / "OpsPulse_KPI_Tracker.xlsx"

# Theme Palette
NAVY = "0F172A"
SLATE_HDR = "1E293B"
BLUE = "2563EB"
LIGHT_BG = "F8FAFC"
ZEBRA_BG = "F1F5F9"
WHITE = "FFFFFF"
BORDER_CLR = "CBD5E1"
GREEN_BG = "DCFCE7"
GREEN_TXT = "166534"
AMBER_BG = "FEF3C7"
AMBER_TXT = "92400E"
RED_BG = "FEE2E2"
RED_TXT = "991B1B"

THIN_SIDE = Side(style="thin", color=BORDER_CLR)
CELL_BORDER = Border(left=THIN_SIDE, right=THIN_SIDE, top=THIN_SIDE, bottom=THIN_SIDE)


def style_banner(ws, title: str, subtitle: str, max_col: int) -> None:
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max_col)
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=max_col)
    c1 = ws.cell(row=1, column=1, value=title)
    c1.font = Font(name="Calibri", size=16, bold=True, color=WHITE)
    c1.fill = PatternFill("solid", fgColor=NAVY)
    c1.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[1].height = 30

    c2 = ws.cell(row=2, column=1, value=subtitle)
    c2.font = Font(name="Calibri", size=10, italic=True, color="CBD5E1")
    c2.fill = PatternFill("solid", fgColor=SLATE_HDR)
    c2.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[2].height = 20


def style_table_header(ws, row_idx: int, headers: list[str], start_col: int = 1) -> None:
    ws.row_dimensions[row_idx].height = 24
    for offset, text in enumerate(headers):
        cell = ws.cell(row=row_idx, column=start_col + offset, value=text)
        cell.font = Font(name="Calibri", size=10, bold=True, color=WHITE)
        cell.fill = PatternFill("solid", fgColor=SLATE_HDR)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = CELL_BORDER


def apply_rag_rules(ws, cell_range: str) -> None:
    ws.conditional_formatting.add(
        cell_range,
        CellIsRule(operator="equal", formula=['"Green"'], fill=PatternFill("solid", fgColor=GREEN_BG), font=Font(color=GREEN_TXT, bold=True)),
    )
    ws.conditional_formatting.add(
        cell_range,
        CellIsRule(operator="equal", formula=['"Amber"'], fill=PatternFill("solid", fgColor=AMBER_BG), font=Font(color=AMBER_TXT, bold=True)),
    )
    ws.conditional_formatting.add(
        cell_range,
        CellIsRule(operator="equal", formula=['"Red"'], fill=PatternFill("solid", fgColor=RED_BG), font=Font(color=RED_TXT, bold=True)),
    )


def autosize_columns(ws, min_width: int = 11, max_width: int = 38) -> None:
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = 0
        for cell in col:
            if cell.row <= 2:
                continue
            val = cell.value
            if val is None:
                continue
            s = str(val)
            if s.startswith("="):
                s = "1234567890"
            max_len = max(max_len, len(s))
        ws.column_dimensions[col_letter].width = max(min_width, min(max_width, max_len + 3))


def build_excel_workbook() -> Path:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    departments = conn.execute("SELECT * FROM departments ORDER BY department_id").fetchall()
    employees = conn.execute(
        """
        SELECT e.*, d.department_name
        FROM employees e JOIN departments d ON e.department_id = d.department_id
        ORDER BY e.employee_id
        """
    ).fetchall()
    tasks = conn.execute(
        """
        SELECT
            task_id, task_title, employee_id, employee_name, department_name,
            milestone_id, task_category, priority, assigned_date, status,
            sla_hours, turnaround_hours, estimated_hours, actual_hours,
            delay_hours, delay_reason, quality_score, rework_flag,
            week_label, month_label, quarter
        FROM vw_task_metrics
        ORDER BY assigned_date, task_id
        """
    ).fetchall()
    weeks = conn.execute(
        "SELECT week_label, week_start_date FROM vw_weekly_scorecard ORDER BY iso_year, iso_week"
    ).fetchall()
    delay_reasons = conn.execute(
        "SELECT delay_reason FROM vw_operational_delays ORDER BY total_delay_hrs DESC"
    ).fetchall()
    overdue_milestones = conn.execute("SELECT * FROM vw_overdue_milestones").fetchall()
    conn.close()

    wb = Workbook()

    # Create sheets in executive reading order
    ws_dash = wb.active
    ws_dash.title = "Executive_Dashboard"
    ws_weekly = wb.create_sheet("Weekly_Scorecard")
    ws_emp = wb.create_sheet("Employee_Leaderboard")
    ws_ms = wb.create_sheet("Overdue_Milestones")
    ws_tasks = wb.create_sheet("Task_Log")
    ws_depts = wb.create_sheet("Departments_Ref")
    ws_emp_ref = wb.create_sheet("Employees_Ref")

    for ws in [ws_dash, ws_weekly, ws_emp, ws_ms, ws_tasks, ws_depts, ws_emp_ref]:
        ws.views.sheetView[0].showGridLines = True

    # =========================================================================
    # SHEET 5: Task_Log (Central Fact Ledger with Live Helper Formulas)
    # =========================================================================
    task_headers = [
        "task_id", "task_title", "employee_id", "employee_name", "department_name",
        "milestone_id", "task_category", "priority", "assigned_date", "status",
        "sla_hours", "turnaround_hours", "estimated_hours", "actual_hours",
        "delay_hours", "delay_reason", "quality_score", "rework_flag",
        "week_label", "month_label", "quarter",
        "is_completed", "is_sla_met", "is_overdue_or_blocked"
    ]
    style_table_header(ws_tasks, 1, task_headers)
    for idx, t in enumerate(tasks, start=2):
        row_vals = [
            t["task_id"], t["task_title"], t["employee_id"], t["employee_name"], t["department_name"],
            t["milestone_id"], t["task_category"], t["priority"], t["assigned_date"], t["status"],
            t["sla_hours"], t["turnaround_hours"], t["estimated_hours"], t["actual_hours"],
            t["delay_hours"], t["delay_reason"], t["quality_score"], t["rework_flag"],
            t["week_label"], t["month_label"], t["quarter"],
            f'=IF(J{idx}="Completed",1,0)',
            f'=IF(AND(J{idx}="Completed",L{idx}<=K{idx}),1,0)',
            f'=IF(OR(J{idx}="Overdue",J{idx}="Blocked"),1,0)',
        ]
        ws_tasks.append(row_vals)
    ws_tasks.freeze_panes = "A2"
    ws_tasks.auto_filter.ref = f"A1:X{len(tasks) + 1}"
    task_end = len(tasks) + 1

    # =========================================================================
    # SHEET 6: Departments_Ref
    # =========================================================================
    dept_ref_headers = [
        "department_id", "department_name", "department_head", "cost_center",
        "target_completion_pct", "target_sla_hours", "target_ontime_pct", "monthly_budget_usd"
    ]
    style_table_header(ws_depts, 1, dept_ref_headers)
    for d in departments:
        ws_depts.append([
            d["department_id"], d["department_name"], d["department_head"], d["cost_center"],
            d["target_completion_pct"] / 100.0, d["target_sla_hours"],
            d["target_ontime_pct"] / 100.0, d["monthly_budget_usd"]
        ])
    for r in range(2, len(departments) + 2):
        ws_depts.cell(r, 5).number_format = "0.0%"
        ws_depts.cell(r, 7).number_format = "0.0%"
        ws_depts.cell(r, 8).number_format = "$#,##0"
    ws_depts.freeze_panes = "A2"

    # =========================================================================
    # SHEET 7: Employees_Ref
    # =========================================================================
    emp_ref_headers = [
        "employee_id", "full_name", "email", "department_name",
        "role_title", "seniority_level", "location", "hire_date", "weekly_capacity_hrs", "status"
    ]
    style_table_header(ws_emp_ref, 1, emp_ref_headers)
    for e in employees:
        ws_emp_ref.append([
            e["employee_id"], e["full_name"], e["email"], e["department_name"],
            e["role_title"], e["seniority_level"], e["location"], e["hire_date"],
            e["weekly_capacity_hrs"], e["status"]
        ])
    ws_emp_ref.freeze_panes = "A2"

    # =========================================================================
    # SHEET 2: Weekly_Scorecard (Automated Weekly KPI Rollups + WoW Formulas)
    # =========================================================================
    style_banner(
        ws_weekly,
        "OpsPulse — Automated Weekly Performance Scorecard (2026)",
        "Live formula-driven ISO weekly rollup from Task_Log | Tracks completion velocity, SLA compliance, turnaround time, and WoW momentum",
        11,
    )
    weekly_headers = [
        "Week", "Week Start", "Assigned", "Completed", "Overdue / Blocked",
        "Completion %", "WoW Delta", "SLA Compliance %", "Avg Turnaround (h)",
        "Delay Hours", "RAG Status"
    ]
    style_table_header(ws_weekly, 4, weekly_headers)

    for idx, w in enumerate(weeks, start=5):
        wk = w["week_label"]
        ws_weekly.cell(idx, 1, wk)
        ws_weekly.cell(idx, 2, w["week_start_date"])
        ws_weekly.cell(idx, 3, f'=COUNTIF(Task_Log!$S$2:$S${task_end}, A{idx})')
        ws_weekly.cell(idx, 4, f'=SUMIFS(Task_Log!$V$2:$V${task_end}, Task_Log!$S$2:$S${task_end}, A{idx})')
        ws_weekly.cell(idx, 5, f'=SUMIFS(Task_Log!$X$2:$X${task_end}, Task_Log!$S$2:$S${task_end}, A{idx})')
        ws_weekly.cell(idx, 6, f'=IFERROR(D{idx}/C{idx}, 0)')
        ws_weekly.cell(idx, 7, 0 if idx == 5 else f'=IFERROR(F{idx}-F{idx-1}, 0)')
        ws_weekly.cell(idx, 8, f'=IFERROR(SUMIFS(Task_Log!$W$2:$W${task_end}, Task_Log!$S$2:$S${task_end}, A{idx})/D{idx}, 0)')
        ws_weekly.cell(idx, 9, f'=IFERROR(AVERAGEIFS(Task_Log!$L$2:$L${task_end}, Task_Log!$S$2:$S${task_end}, A{idx}, Task_Log!$V$2:$V${task_end}, 1), 0)')
        ws_weekly.cell(idx, 10, f'=SUMIFS(Task_Log!$O$2:$O${task_end}, Task_Log!$S$2:$S${task_end}, A{idx})')
        ws_weekly.cell(idx, 11, f'=IF(AND(F{idx}>=0.88, H{idx}>=0.82), "Green", IF(AND(F{idx}>=0.80, H{idx}>=0.74), "Amber", "Red"))')

        fill = PatternFill("solid", fgColor=ZEBRA_BG if idx % 2 == 0 else WHITE)
        for col_i in range(1, 12):
            c = ws_weekly.cell(idx, col_i)
            c.border = CELL_BORDER
            c.fill = fill
            c.font = Font(name="Calibri", size=10)
            c.alignment = Alignment(horizontal="center" if col_i in (1, 2, 11) else "right", vertical="center")
        ws_weekly.cell(idx, 3).number_format = "#,##0"
        ws_weekly.cell(idx, 4).number_format = "#,##0"
        ws_weekly.cell(idx, 5).number_format = "#,##0"
        ws_weekly.cell(idx, 6).number_format = "0.0%"
        ws_weekly.cell(idx, 7).number_format = "+0.0%;-0.0%;0.0%"
        ws_weekly.cell(idx, 8).number_format = "0.0%"
        ws_weekly.cell(idx, 9).number_format = "0.0"
        ws_weekly.cell(idx, 10).number_format = "#,##0.0"

    weekly_end = 4 + len(weeks)
    apply_rag_rules(ws_weekly, f"K5:K{weekly_end}")
    ws_weekly.freeze_panes = "A5"

    # =========================================================================
    # SHEET 3: Employee_Leaderboard (Live Formulas + Productivity Index + RANK)
    # =========================================================================
    style_banner(
        ws_emp,
        "OpsPulse — Employee Performance & Productivity Leaderboard",
        "Composite Productivity Index = 35% Completion + 30% SLA Compliance + 20% Quality (scaled) + 15% First-Pass Yield",
        13,
    )
    emp_headers = [
        "Org Rank", "Employee ID", "Full Name", "Department", "Role",
        "Total Tasks", "Completed", "Completion %", "SLA Compliance %",
        "Avg Turnaround (h)", "Avg Quality (1-5)", "Productivity Index", "Performance Tier"
    ]
    style_table_header(ws_emp, 4, emp_headers)
    emp_end = 4 + len(employees)

    for idx, e in enumerate(employees, start=5):
        ws_emp.cell(idx, 1, f'=RANK(L{idx}, $L$5:$L${emp_end})')
        ws_emp.cell(idx, 2, e["employee_id"])
        ws_emp.cell(idx, 3, e["full_name"])
        ws_emp.cell(idx, 4, e["department_name"])
        ws_emp.cell(idx, 5, e["role_title"])
        ws_emp.cell(idx, 6, f'=COUNTIF(Task_Log!$C$2:$C${task_end}, B{idx})')
        ws_emp.cell(idx, 7, f'=SUMIFS(Task_Log!$V$2:$V${task_end}, Task_Log!$C$2:$C${task_end}, B{idx})')
        ws_emp.cell(idx, 8, f'=IFERROR(G{idx}/F{idx}, 0)')
        ws_emp.cell(idx, 9, f'=IFERROR(SUMIFS(Task_Log!$W$2:$W${task_end}, Task_Log!$C$2:$C${task_end}, B{idx})/G{idx}, 0)')
        ws_emp.cell(idx, 10, f'=IFERROR(AVERAGEIFS(Task_Log!$L$2:$L${task_end}, Task_Log!$C$2:$C${task_end}, B{idx}, Task_Log!$V$2:$V${task_end}, 1), 0)')
        ws_emp.cell(idx, 11, f'=IFERROR(AVERAGEIFS(Task_Log!$Q$2:$Q${task_end}, Task_Log!$C$2:$C${task_end}, B{idx}, Task_Log!$V$2:$V${task_end}, 1), 0)')
        rework_expr = f'IFERROR(SUMIFS(Task_Log!$R$2:$R${task_end}, Task_Log!$C$2:$C${task_end}, B{idx})/G{idx}, 0)'
        ws_emp.cell(idx, 12, f'=ROUND(35*H{idx} + 30*I{idx} + 20*(K{idx}/5) + 15*(1-{rework_expr}), 1)')
        ws_emp.cell(idx, 13, f'=IF(L{idx}>=88,"Top Performer",IF(L{idx}>=80,"Exceeds Target",IF(L{idx}>=72,"On Track","Needs Support")))')

        fill = PatternFill("solid", fgColor=ZEBRA_BG if idx % 2 == 0 else WHITE)
        for col_i in range(1, 14):
            c = ws_emp.cell(idx, col_i)
            c.border = CELL_BORDER
            c.fill = fill
            c.font = Font(name="Calibri", size=10, bold=(col_i in (1, 12)))
            c.alignment = Alignment(horizontal="left" if col_i in (3, 4, 5) else ("center" if col_i in (1, 2, 13) else "right"))
        ws_emp.cell(idx, 6).number_format = "#,##0"
        ws_emp.cell(idx, 7).number_format = "#,##0"
        ws_emp.cell(idx, 8).number_format = "0.0%"
        ws_emp.cell(idx, 9).number_format = "0.0%"
        ws_emp.cell(idx, 10).number_format = "0.0"
        ws_emp.cell(idx, 11).number_format = "0.00"
        ws_emp.cell(idx, 12).number_format = "0.0"

    ws_emp.conditional_formatting.add(
        f"M5:M{emp_end}",
        CellIsRule(operator="equal", formula=['"Top Performer"'], fill=PatternFill("solid", fgColor=GREEN_BG), font=Font(color=GREEN_TXT, bold=True)),
    )
    ws_emp.conditional_formatting.add(
        f"M5:M{emp_end}",
        CellIsRule(operator="equal", formula=['"Needs Support"'], fill=PatternFill("solid", fgColor=RED_BG), font=Font(color=RED_TXT, bold=True)),
    )
    ws_emp.freeze_panes = "A5"

    # =========================================================================
    # SHEET 4: Overdue_Milestones (Leadership Escalation Tracker)
    # =========================================================================
    style_banner(
        ws_ms,
        "OpsPulse — Overdue & At-Risk Milestones Escalation Queue",
        "Actionable leadership log highlighting overdue milestones, open delayed tasks, and active workflow blockers",
        11,
    )
    ms_headers = [
        "Milestone ID", "Milestone Name", "Department", "Owner", "Quarter",
        "Priority", "Planned Due", "Status", "% Complete", "Open Delayed Tasks", "Blocker Summary"
    ]
    style_table_header(ws_ms, 4, ms_headers)
    for idx, m in enumerate(overdue_milestones, start=5):
        ws_ms.cell(idx, 1, m["milestone_id"])
        ws_ms.cell(idx, 2, m["milestone_name"])
        ws_ms.cell(idx, 3, m["department_name"])
        ws_ms.cell(idx, 4, m["owner_name"])
        ws_ms.cell(idx, 5, m["quarter"])
        ws_ms.cell(idx, 6, m["priority"])
        ws_ms.cell(idx, 7, m["planned_due_date"])
        ws_ms.cell(idx, 8, m["status"])
        ws_ms.cell(idx, 9, m["completion_pct"] / 100.0)
        ws_ms.cell(idx, 10, f'=SUMIFS(Task_Log!$X$2:$X${task_end}, Task_Log!$F$2:$F${task_end}, A{idx})')
        ws_ms.cell(idx, 11, m["blocker_summary"])

        for col_i in range(1, 12):
            c = ws_ms.cell(idx, col_i)
            c.border = CELL_BORDER
            c.font = Font(name="Calibri", size=10)
            c.alignment = Alignment(horizontal="left" if col_i in (2, 3, 4, 11) else "center", vertical="center", wrap_text=(col_i == 11))
        ws_ms.cell(idx, 9).number_format = "0.0%"
        ws_ms.row_dimensions[idx].height = 24

    ms_end = 4 + len(overdue_milestones)
    ws_ms.conditional_formatting.add(
        f"H5:H{ms_end}",
        CellIsRule(operator="equal", formula=['"Overdue"'], fill=PatternFill("solid", fgColor=RED_BG), font=Font(color=RED_TXT, bold=True)),
    )
    ws_ms.conditional_formatting.add(
        f"H5:H{ms_end}",
        CellIsRule(operator="equal", formula=['"At Risk"'], fill=PatternFill("solid", fgColor=AMBER_BG), font=Font(color=AMBER_TXT, bold=True)),
    )
    ws_ms.freeze_panes = "A5"

    # =========================================================================
    # SHEET 1: Executive_Dashboard (KPI Cards + Dept Scorecard + Delay Pareto + Charts)
    # =========================================================================
    style_banner(
        ws_dash,
        "OpsPulse — Executive Performance & Departmental KPI Dashboard",
        "Centralized 2026 Operational Intelligence | All KPIs dynamically linked to Task_Log via live Excel/Sheets formulas",
        11,
    )

    # KPI Headline Cards (Rows 4-6)
    kpi_cards = [
        ("TOTAL TASKS", f"=COUNTA(Task_Log!A2:A{task_end})", "#,##0", 1, 2),
        ("COMPLETION RATE", f"=IFERROR(SUM(Task_Log!V2:V{task_end})/COUNTA(Task_Log!A2:A{task_end}),0)", "0.0%", 3, 4),
        ("SLA COMPLIANCE", f"=IFERROR(SUM(Task_Log!W2:W{task_end})/SUM(Task_Log!V2:V{task_end}),0)", "0.0%", 5, 6),
        ("AVG TURNAROUND (H)", f"=IFERROR(AVERAGEIF(Task_Log!V2:V{task_end},1,Task_Log!L2:L{task_end}),0)", "0.0", 7, 8),
        ("TOTAL DELAY HRS", f"=SUM(Task_Log!O2:O{task_end})", "#,##0.0", 9, 10),
        ("ESCALATIONS", f"=COUNTA(Overdue_Milestones!A5:A{ms_end})", "#,##0", 11, 11),
    ]
    ws_dash.row_dimensions[4].height = 18
    ws_dash.row_dimensions[5].height = 30
    for label, formula, num_fmt, c_start, c_end in kpi_cards:
        if c_end > c_start:
            ws_dash.merge_cells(start_row=4, start_column=c_start, end_row=4, end_column=c_end)
            ws_dash.merge_cells(start_row=5, start_column=c_start, end_row=5, end_column=c_end)
        lbl_cell = ws_dash.cell(4, c_start, label)
        lbl_cell.font = Font(name="Calibri", size=9, bold=True, color="475569")
        lbl_cell.fill = PatternFill("solid", fgColor=ZEBRA_BG)
        lbl_cell.alignment = Alignment(horizontal="center", vertical="center")

        val_cell = ws_dash.cell(5, c_start, formula)
        val_cell.font = Font(name="Calibri", size=18, bold=True, color=NAVY)
        val_cell.fill = PatternFill("solid", fgColor=WHITE)
        val_cell.alignment = Alignment(horizontal="center", vertical="center")
        val_cell.number_format = num_fmt

        for r in (4, 5):
            for col_i in range(c_start, c_end + 1):
                ws_dash.cell(r, col_i).border = CELL_BORDER

    # Section 1: Departmental KPI Scorecard (Rows 7-15)
    ws_dash.merge_cells("A7:K7")
    sec1 = ws_dash.cell(7, 1, "DEPARTMENTAL KPI SCORECARD (ACTUALS VS TARGETS)")
    sec1.font = Font(name="Calibri", size=11, bold=True, color=BLUE)
    ws_dash.row_dimensions[7].height = 22

    dept_headers = [
        "Department", "Dept Head", "Total Tasks", "Completed", "Completion %",
        "Target %", "Variance", "SLA Compliance %", "Avg Turnaround (h)", "Delay Hours", "RAG Status"
    ]
    style_table_header(ws_dash, 8, dept_headers)

    for idx, d in enumerate(departments, start=9):
        ref_row = idx - 7  # Row in Departments_Ref (2..7)
        ws_dash.cell(idx, 1, f"=Departments_Ref!B{ref_row}")
        ws_dash.cell(idx, 2, f"=Departments_Ref!C{ref_row}")
        ws_dash.cell(idx, 3, f'=COUNTIF(Task_Log!$E$2:$E${task_end}, A{idx})')
        ws_dash.cell(idx, 4, f'=SUMIFS(Task_Log!$V$2:$V${task_end}, Task_Log!$E$2:$E${task_end}, A{idx})')
        ws_dash.cell(idx, 5, f'=IFERROR(D{idx}/C{idx}, 0)')
        ws_dash.cell(idx, 6, f"=Departments_Ref!E{ref_row}")
        ws_dash.cell(idx, 7, f"=E{idx}-F{idx}")
        ws_dash.cell(idx, 8, f'=IFERROR(SUMIFS(Task_Log!$W$2:$W${task_end}, Task_Log!$E$2:$E${task_end}, A{idx})/D{idx}, 0)')
        ws_dash.cell(idx, 9, f'=IFERROR(AVERAGEIFS(Task_Log!$L$2:$L${task_end}, Task_Log!$E$2:$E${task_end}, A{idx}, Task_Log!$V$2:$V${task_end}, 1), 0)')
        ws_dash.cell(idx, 10, f'=SUMIFS(Task_Log!$O$2:$O${task_end}, Task_Log!$E$2:$E${task_end}, A{idx})')
        ws_dash.cell(idx, 11, f'=IF(AND(E{idx}>=F{idx}, H{idx}>=0.80), "Green", IF(E{idx}>=(F{idx}-0.05), "Amber", "Red"))')

        fill = PatternFill("solid", fgColor=ZEBRA_BG if idx % 2 == 0 else WHITE)
        for col_i in range(1, 12):
            c = ws_dash.cell(idx, col_i)
            c.border = CELL_BORDER
            c.fill = fill
            c.font = Font(name="Calibri", size=10, bold=(col_i == 1))
            c.alignment = Alignment(horizontal="left" if col_i in (1, 2) else ("center" if col_i == 11 else "right"))
        ws_dash.cell(idx, 3).number_format = "#,##0"
        ws_dash.cell(idx, 4).number_format = "#,##0"
        ws_dash.cell(idx, 5).number_format = "0.0%"
        ws_dash.cell(idx, 6).number_format = "0.0%"
        ws_dash.cell(idx, 7).number_format = "+0.0%;-0.0%;0.0%"
        ws_dash.cell(idx, 8).number_format = "0.0%"
        ws_dash.cell(idx, 9).number_format = "0.0"
        ws_dash.cell(idx, 10).number_format = "#,##0.0"

    dept_end = 8 + len(departments)
    apply_rag_rules(ws_dash, f"K9:K{dept_end}")

    # Section 2: Operational Delay Root-Cause Pareto (Rows 17-25)
    ws_dash.merge_cells("A17:F17")
    sec2 = ws_dash.cell(17, 1, "OPERATIONAL DELAY ROOT-CAUSE BREAKDOWN (PARETO)")
    sec2.font = Font(name="Calibri", size=11, bold=True, color=BLUE)
    ws_dash.row_dimensions[17].height = 22

    delay_headers = ["Delay Root Cause", "Incidents", "Total Delay Hrs", "Avg Delay (h)", "% Share of Delay", "Cumulative %"]
    style_table_header(ws_dash, 18, delay_headers)
    delay_start = 19
    delay_end = delay_start + len(delay_reasons) - 1

    for offset, dr in enumerate(delay_reasons):
        r = delay_start + offset
        ws_dash.cell(r, 1, dr["delay_reason"])
        ws_dash.cell(r, 2, f'=COUNTIFS(Task_Log!$P$2:$P${task_end}, A{r}, Task_Log!$O$2:$O${task_end}, ">0")')
        ws_dash.cell(r, 3, f'=SUMIFS(Task_Log!$O$2:$O${task_end}, Task_Log!$P$2:$P${task_end}, A{r})')
        ws_dash.cell(r, 4, f'=IFERROR(C{r}/B{r}, 0)')
        ws_dash.cell(r, 5, f'=IFERROR(C{r}/SUM($C${delay_start}:$C${delay_end}), 0)')
        ws_dash.cell(r, 6, f'=SUM($E${delay_start}:E{r})')

        fill = PatternFill("solid", fgColor=ZEBRA_BG if r % 2 == 0 else WHITE)
        for col_i in range(1, 7):
            c = ws_dash.cell(r, col_i)
            c.border = CELL_BORDER
            c.fill = fill
            c.font = Font(name="Calibri", size=10, bold=(col_i == 1))
            c.alignment = Alignment(horizontal="left" if col_i == 1 else "right")
        ws_dash.cell(r, 2).number_format = "#,##0"
        ws_dash.cell(r, 3).number_format = "#,##0.0"
        ws_dash.cell(r, 4).number_format = "0.0"
        ws_dash.cell(r, 5).number_format = "0.0%"
        ws_dash.cell(r, 6).number_format = "0.0%"

    # Native Embedded Excel Charts on Executive_Dashboard
    # Chart 1: Departmental Completion % vs Target %
    chart_dept = BarChart()
    chart_dept.type = "col"
    chart_dept.style = 10
    chart_dept.title = "Departmental Completion Rate vs. Target"
    chart_dept.y_axis.number_format = "0%"
    data_ref = Reference(ws_dash, min_col=5, max_col=6, min_row=8, max_row=dept_end)
    cats_ref = Reference(ws_dash, min_col=1, min_row=9, max_row=dept_end)
    chart_dept.add_data(data_ref, titles_from_data=True)
    chart_dept.set_categories(cats_ref)
    chart_dept.width = 16
    chart_dept.height = 9.5
    ws_dash.add_chart(chart_dept, "A27")

    # Chart 2: Delay Hours by Root Cause
    chart_delay = BarChart()
    chart_delay.type = "bar"
    chart_delay.style = 11
    chart_delay.title = "Operational Delay Hours by Root Cause"
    delay_data = Reference(ws_dash, min_col=3, min_row=18, max_row=delay_end)
    delay_cats = Reference(ws_dash, min_col=1, min_row=19, max_row=delay_end)
    chart_delay.add_data(delay_data, titles_from_data=True)
    chart_delay.set_categories(delay_cats)
    chart_delay.legend = None
    chart_delay.width = 14
    chart_delay.height = 9.5
    ws_dash.add_chart(chart_delay, "G17")

    # Chart 3: Weekly Completion Rate Trend (from Weekly_Scorecard)
    chart_trend = LineChart()
    chart_trend.style = 12
    chart_trend.title = "2026 Weekly Completion & SLA Trend"
    chart_trend.y_axis.number_format = "0%"
    trend_comp = Reference(ws_weekly, min_col=6, min_row=4, max_row=weekly_end)
    trend_sla = Reference(ws_weekly, min_col=8, min_row=4, max_row=weekly_end)
    trend_cats = Reference(ws_weekly, min_col=1, min_row=5, max_row=weekly_end)
    chart_trend.add_data(trend_comp, titles_from_data=True)
    chart_trend.add_data(trend_sla, titles_from_data=True)
    chart_trend.set_categories(trend_cats)
    chart_trend.width = 17
    chart_trend.height = 9.5
    ws_dash.add_chart(chart_trend, "G32")

    # Auto-fit columns across all sheets
    for ws in [ws_dash, ws_weekly, ws_emp, ws_ms, ws_tasks, ws_depts, ws_emp_ref]:
        autosize_columns(ws)
    ws_dash.column_dimensions["A"].width = 24
    ws_dash.column_dimensions["B"].width = 20
    ws_ms.column_dimensions["K"].width = 48

    OUT_XLSX.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT_XLSX)
    return OUT_XLSX


if __name__ == "__main__":
    path = build_excel_workbook()
    print(f"Built Excel KPI Tracker successfully: {path}")
