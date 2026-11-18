"""
OpsPulse — Employee Performance & Departmental KPI Tracker
Script: run_pipeline.py
Description: End-to-end automated pipeline orchestrator:
             1. Generates deterministic 2026 operational dataset
             2. Builds & validates SQLite KPI warehouse + exports processed CSVs
             3. Generates formula-driven MS Excel / Google Sheets workbook
             4. Generates executive PNG charts, Markdown scorecard & web dashboard feed
"""

from __future__ import annotations

import time

from build_excel_tracker import build_excel_workbook
from build_warehouse import build_warehouse
from generate_charts_and_reports import generate_all_reports
from generate_dataset import generate_all


def main() -> None:
    t0 = time.perf_counter()
    print("=" * 70)
    print("  OpsPulse — End-to-End KPI Warehouse & Reporting Pipeline (2026)")
    print("=" * 70)

    print("\n[1/4] Generating 2026 multi-department operational dataset...")
    raw_counts = generate_all()
    print(f"      Done -> {raw_counts}")

    print("\n[2/4] Building SQLite warehouse, KPI views & quality checks...")
    wh = build_warehouse()
    print(f"      QA Passed -> {wh['qa']}")
    print(f"      Exported CSVs -> {wh['exports']}")

    print("\n[3/4] Building formula-driven Excel tracker (OpsPulse_KPI_Tracker.xlsx)...")
    xlsx_path = build_excel_workbook()
    print(f"      Saved -> {xlsx_path}")

    print("\n[4/4] Generating executive charts, weekly scorecard & dashboard feed...")
    headline = generate_all_reports()
    print(f"      Headline KPIs -> Completion: {headline['completion_rate_pct']}% | "
          f"SLA: {headline['sla_compliance_pct']}% | Avg TAT: {headline['avg_turnaround_hrs']}h | "
          f"Delay Hrs: {headline['total_delay_hrs']:,.1f}h")

    elapsed = time.perf_counter() - t0
    print("\n" + "=" * 70)
    print(f"  Pipeline completed cleanly in {elapsed:.2f}s")
    print("=" * 70)


if __name__ == "__main__":
    main()
