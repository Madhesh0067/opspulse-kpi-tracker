# OpsPulse — Automated Weekly Executive KPI Scorecard

**Reporting Period:** 2026 YTD (ISO Weeks `2026-W01` – `2026-W46`) | **Snapshot Date:** 2026-11-18  
**Data Source:** `data/opspulse.db` (`vw_department_kpi_summary`, `vw_weekly_scorecard`, `vw_operational_delays`, `vw_overdue_milestones`)

---

## 1. Executive Headline KPIs (YTD 2026)

| Metric | YTD Actual | Status / Note |
| :--- | :---: | :--- |
| **Total Tasks Monitored** | **2,474** | Across 6 departments & 48 employees |
| **Overall Task Completion Rate** | **87.6%** | 2,168 completed / 214 overdue / 88 blocked |
| **On-Time Delivery Rate** | **82.2%** | Completed on or before due date |
| **SLA Compliance Rate** | **78.3%** | Completed within departmental SLA hours |
| **Average Turnaround Time** | **20.4 hrs** | Weighted across all completed tasks |
| **Total Operational Delay Lost** | **27,088.7 hrs** | Top driver: **Dependency Wait** (24.0%) |
| **Overdue / At-Risk Milestones** | **11** | Escalated for executive intervention |

---

## 2. Departmental Performance Scorecard

| Department | Dept Head | Tasks | Completion % | Target % | Variance | SLA % | Avg TAT (h) | Delay Hrs | RAG |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Customer Support | Karthik Subramanian | 382 | 94.0% | 92.0% | +2.0% | 89.1% | 8.7 | 1,849.6 | **Green** |
| Engineering | Arjun Raghavan | 395 | 93.9% | 88.0% | +5.9% | 83.0% | 27.2 | 2,655.9 | **Green** |
| Product & Design | Rohan Deshmukh | 389 | 89.2% | 87.0% | +2.2% | 80.7% | 24.2 | 3,769.1 | **Green** |
| Finance & Compliance | Ananya Iyer | 461 | 87.0% | 91.0% | -4.0% | 80.0% | 22.6 | 5,349.2 | **Amber** |
| Sales & Partnerships | Divya Nair | 418 | 84.7% | 89.0% | -4.3% | 76.5% | 16.2 | 5,305.5 | **Amber** |
| Operations & Logistics | Meera Krishnan | 429 | 78.3% | 90.0% | -11.7% | 58.6% | 23.0 | 8,159.4 | **Red** |

---

## 3. Operational Delay Root-Cause Pareto

| Delay Root Cause | Incidents | Total Delay Hrs | Avg Delay (h) | Critical Impacted | % Share | Cumulative % |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Dependency Wait | 169 | 6,505.3 | 38.5 | 22 | 24.0% | 24.0% |
| Approval Lag | 157 | 6,255.5 | 39.8 | 16 | 23.1% | 47.1% |
| Resource Bottleneck | 162 | 5,401.8 | 33.3 | 37 | 19.9% | 67.0% |
| Vendor Delay | 113 | 4,061.3 | 35.9 | 14 | 15.0% | 82.0% |
| Scope Creep | 93 | 3,311.3 | 35.6 | 13 | 12.2% | 94.3% |
| Tooling Issue | 50 | 1,553.5 | 31.1 | 11 | 5.7% | 100.0% |

---

## 4. Overdue & At-Risk Milestones Escalation Queue

| ID | Milestone | Department | Owner | Priority | Due Date | Status | % Done | Open Delayed Tasks | Blocker |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| MS-009 | Warehouse Barcode Automation | Operations & Logistics | Deepak Joshi | **Critical** | 2026-09-15 | Overdue | 86% | 25 | Tier-2 carrier SLA slippage and scanner hardware backorder. |
| MS-004 | Microservices Telemetry Rollout | Engineering | Aarav Sharma | **Critical** | 2026-09-25 | Overdue | 70% | 2 | Blocked on legacy schema freeze & cross-team API contract sign-off. |
| MS-010 | Q3 Carrier Bottleneck Recovery | Operations & Logistics | Rahul Nair | **Critical** | 2026-10-10 | Overdue | 78% | 21 | Tier-2 carrier SLA slippage and scanner hardware backorder. |
| MS-022 | Procurement Approval Workflow v3 | Finance & Compliance | Gautam Sinha | **Critical** | 2026-10-22 | Overdue | 70% | 9 | Waiting on multi-level VP approval workflows and external auditor sample list. |
| MS-005 | Zero-Downtime DB Failover Drill | Engineering | Neha Patel | **Critical** | 2026-10-30 | Overdue | 67% | 0 | Blocked on legacy schema freeze & cross-team API contract sign-off. |
| MS-023 | SOC2 Control Evidence Refresh | Finance & Compliance | Revathi Srinivasan | **Critical** | 2026-11-08 | Overdue | 84% | 5 | Waiting on multi-level VP approval workflows and external auditor sample list. |
| MS-035 | APAC Channel Expansion Launch | Sales & Partnerships | Shreya Bhattacharya | **Critical** | 2026-11-25 | At Risk | 46% | 2 | Legal redline queue backlog on enterprise renewal templates. |
| MS-012 | Peak-Season Capacity Readiness | Operations & Logistics | Deepak Joshi | **Critical** | 2026-11-28 | At Risk | 59% | 3 | Tier-2 carrier SLA slippage and scanner hardware backorder. |
| MS-028 | Executive Mobile Dashboard Specs | Product & Design | Aditi Kulkarni | **High** | 2026-10-18 | Overdue | 73% | 7 | Design handoff delayed by shifting executive dashboard KPI definitions. |
| MS-034 | Renewal Risk Playbook Rollout | Sales & Partnerships | Raghavendra Rao | **High** | 2026-11-04 | Overdue | 70% | 0 | Legal redline queue backlog on enterprise renewal templates. |
| MS-011 | Cold-Chain Audit Compliance | Operations & Logistics | Pooja Sundaram | **High** | 2026-11-05 | Overdue | 76% | 1 | Tier-2 carrier SLA slippage and scanner hardware backorder. |

---

## 5. Top 5 Performers (Composite Productivity Index)

| Rank | Employee | Department | Role | Completed | Completion % | SLA % | Quality | Productivity Index |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| #1 | Manoj Kumar | Customer Support | Support Specialist | 47 | 100.0% | 91.5% | 4.47/5 | **95.3** |
| #2 | Varun Choudhary | Customer Support | Escalation Lead | 54 | 96.4% | 92.6% | 4.50/5 | **94.2** |
| #3 | Suresh Babu | Customer Support | Support Specialist | 51 | 98.1% | 92.2% | 4.45/5 | **94.2** |
| #4 | Nandini Rao | Customer Support | Senior Support Associate | 41 | 97.6% | 92.7% | 4.46/5 | **94.1** |
| #5 | Swathi Raj | Customer Support | Technical Support Engineer | 49 | 100.0% | 87.8% | 4.51/5 | **93.1** |

---

## 6. Key Executive Insights & Recommended Actions

1. **Primary Bottleneck — Operations & Logistics:** Trailing its 90% completion target by `-11.7%` with `8,159.4` lost delay hours. Driven heavily by Q3 carrier/vendor slippage and resource bottlenecks.
2. **Benchmark Team — Customer Support:** Leading the organization at `94.0%` completion and `89.1%` SLA compliance — playbook should be replicated for intake triage.
3. **80/20 Delay Focus:** The top 2 delay categories account for **47.1%** of total operational delay hours. Enforcing pre-sprint dependency sign-off and automated VP approval reminders in Finance/Sales can recover >35% of lost hours.
4. **Immediate Milestone Escalation:** `11` milestones are Overdue or At Risk, with Critical items in Operations & Logistics and Finance & Compliance requiring executive unblocking this week.
