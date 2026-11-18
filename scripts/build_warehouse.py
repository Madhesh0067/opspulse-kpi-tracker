"""
OpsPulse — Employee Performance & Departmental KPI Tracker
Script: build_warehouse.py
Description: Creates the SQLite analytical warehouse (data/opspulse.db), loads raw CSVs,
             executes KPI views (sql/02_kpi_views.sql), validates data integrity,
             and exports processed executive CSV datasets.
"""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
SQL_DIR = ROOT_DIR / "sql"
DB_PATH = ROOT_DIR / "data" / "opspulse.db"


def _coerce_null(val: str):
    return None if val == "" else val


def load_csv_to_table(conn: sqlite3.Connection, csv_path: Path, table_name: str) -> int:
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        placeholders = ", ".join(["?"] * len(cols))
        sql = f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES ({placeholders})"
        rows = [tuple(_coerce_null(row[c]) for c in cols) for row in reader]
        conn.executemany(sql, rows)
        return len(rows)


def export_query_to_csv(conn: sqlite3.Connection, query: str, out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cur = conn.execute(query)
    cols = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(cols)
        writer.writerows(rows)
    return len(rows)


def run_quality_checks(conn: sqlite3.Connection) -> dict[str, object]:
    checks = {}
    # 1. Foreign key integrity check
    fk_errors = conn.execute("PRAGMA foreign_key_check;").fetchall()
    assert len(fk_errors) == 0, f"Foreign key violations detected: {fk_errors}"
    checks["foreign_key_violations"] = 0

    # 2. Null key check
    null_tasks = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE task_id IS NULL OR employee_id IS NULL OR department_id IS NULL"
    ).fetchone()[0]
    assert null_tasks == 0, f"Null keys found in tasks: {null_tasks}"
    checks["null_primary_or_fk"] = 0

    # 3. KPI sanity bounds
    kpis = conn.execute(
        """
        SELECT
            COUNT(*),
            ROUND(100.0 * SUM(is_completed) / COUNT(*), 2),
            ROUND(100.0 * SUM(is_sla_met) / NULLIF(SUM(is_completed), 0), 2),
            ROUND(AVG(CASE WHEN is_completed = 1 THEN turnaround_hours END), 2)
        FROM vw_task_metrics
        """
    ).fetchone()
    assert kpis[0] > 0 and 0 <= kpis[1] <= 100 and 0 <= kpis[2] <= 100
    checks["total_tasks"] = kpis[0]
    checks["completion_rate_pct"] = kpis[1]
    checks["sla_compliance_pct"] = kpis[2]
    checks["avg_turnaround_hrs"] = kpis[3]
    return checks


def build_warehouse() -> dict[str, object]:
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")

        # Apply schema
        schema_sql = (SQL_DIR / "01_schema.sql").read_text(encoding="utf-8")
        conn.executescript(schema_sql)

        # Load tables in FK order
        loaded = {
            "departments": load_csv_to_table(conn, RAW_DIR / "departments.csv", "departments"),
            "employees": load_csv_to_table(conn, RAW_DIR / "employees.csv", "employees"),
            "milestones": load_csv_to_table(conn, RAW_DIR / "milestones.csv", "milestones"),
            "tasks": load_csv_to_table(conn, RAW_DIR / "tasks.csv", "tasks"),
        }
        conn.commit()

        # Apply KPI Views
        views_sql = (SQL_DIR / "02_kpi_views.sql").read_text(encoding="utf-8")
        conn.executescript(views_sql)
        conn.commit()

        # Validate data quality
        qa = run_quality_checks(conn)

        # Export processed analytical tables
        exports = {
            "department_kpi_summary.csv": export_query_to_csv(
                conn, "SELECT * FROM vw_department_kpi_summary ORDER BY completion_variance_pct ASC", PROCESSED_DIR / "department_kpi_summary.csv"
            ),
            "employee_kpi_summary.csv": export_query_to_csv(
                conn, "SELECT * FROM vw_employee_performance ORDER BY org_rank ASC", PROCESSED_DIR / "employee_kpi_summary.csv"
            ),
            "weekly_scorecards.csv": export_query_to_csv(
                conn, "SELECT * FROM vw_weekly_scorecard ORDER BY iso_year, iso_week", PROCESSED_DIR / "weekly_scorecards.csv"
            ),
            "operational_delays_pareto.csv": export_query_to_csv(
                conn, "SELECT * FROM vw_operational_delays", PROCESSED_DIR / "operational_delays_pareto.csv"
            ),
            "overdue_milestones.csv": export_query_to_csv(
                conn, "SELECT * FROM vw_overdue_milestones", PROCESSED_DIR / "overdue_milestones.csv"
            ),
        }

        return {"loaded": loaded, "qa": qa, "exports": exports}
    finally:
        conn.close()


if __name__ == "__main__":
    summary = build_warehouse()
    print("Warehouse built successfully:", summary)
