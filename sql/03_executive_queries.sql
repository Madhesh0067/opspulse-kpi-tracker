-- ============================================================================
-- OpsPulse — Employee Performance & Departmental KPI Tracker
-- File: 03_executive_queries.sql
-- Description: Ready-to-run ad-hoc executive SQL queries for leadership reviews
-- ============================================================================

-- Q1: Executive KPI Headline Snapshot (YTD 2026)
SELECT
    COUNT(*)                                                 AS total_tasks,
    SUM(is_completed)                                        AS completed_tasks,
    ROUND(100.0 * SUM(is_completed) / COUNT(*), 2)           AS completion_rate_pct,
    ROUND(100.0 * SUM(is_on_time) / NULLIF(SUM(is_completed), 0), 2) AS on_time_delivery_pct,
    ROUND(100.0 * SUM(is_sla_met) / NULLIF(SUM(is_completed), 0), 2) AS sla_compliance_pct,
    ROUND(AVG(CASE WHEN is_completed = 1 THEN turnaround_hours END), 2) AS avg_turnaround_hrs,
    SUM(CASE WHEN status = 'Overdue' THEN 1 ELSE 0 END)      AS overdue_tasks,
    ROUND(SUM(delay_hours), 1)                               AS total_delay_hours_lost
FROM vw_task_metrics;

-- Q2: Departmental SLA & Completion Performance Ranked by Bottleneck Risk
SELECT
    department_name,
    department_head,
    total_tasks,
    completion_rate_pct,
    target_completion_pct,
    completion_variance_pct,
    sla_compliance_pct,
    avg_turnaround_hrs,
    total_delay_hrs,
    rag_status
FROM vw_department_kpi_summary
ORDER BY completion_variance_pct ASC;

-- Q3: Top 10 Highest-Performing Employees Across Organization
SELECT
    org_rank,
    full_name,
    department_name,
    role_title,
    completed_tasks,
    completion_rate_pct,
    sla_compliance_pct,
    avg_quality_score,
    productivity_index,
    performance_tier
FROM vw_employee_performance
ORDER BY org_rank ASC
LIMIT 10;

-- Q4: Employees Requiring Workload Rebalancing / Coaching Support
SELECT
    full_name,
    department_name,
    role_title,
    total_tasks,
    overdue_tasks,
    blocked_tasks,
    completion_rate_pct,
    rework_rate_pct,
    total_delay_hrs,
    productivity_index
FROM vw_employee_performance
WHERE performance_tier = 'Needs Support' OR overdue_tasks >= 4
ORDER BY productivity_index ASC;

-- Q5: Operational Delay Root-Cause Pareto Analysis (80/20 Rule)
SELECT * FROM vw_operational_delays;

-- Q6: Department x Delay Reason Heatmap Matrix (Workflow Gap Pinpointing)
SELECT
    department_name,
    delay_reason,
    COUNT(*)                                                 AS incidents,
    ROUND(SUM(delay_hours), 1)                               AS delay_hours,
    ROUND(AVG(delay_hours), 1)                               AS avg_delay_per_incident
FROM vw_task_metrics
WHERE delay_hours > 0 AND delay_reason <> 'None'
GROUP BY department_name, delay_reason
ORDER BY delay_hours DESC
LIMIT 15;

-- Q7: Quarterly Performance Trend (Q1 -> Q4 2026)
SELECT
    quarter,
    COUNT(*)                                                 AS total_tasks,
    ROUND(100.0 * SUM(is_completed) / COUNT(*), 2)           AS completion_rate_pct,
    ROUND(100.0 * SUM(is_sla_met) / NULLIF(SUM(is_completed), 0), 2) AS sla_compliance_pct,
    ROUND(AVG(CASE WHEN is_completed = 1 THEN turnaround_hours END), 2) AS avg_turnaround_hrs,
    ROUND(SUM(delay_hours), 1)                               AS total_delay_hrs
FROM vw_task_metrics
GROUP BY quarter
ORDER BY quarter;

-- Q8: Last 8 Weeks Automated Scorecard Momentum
SELECT
    week_label,
    tasks_assigned,
    tasks_completed,
    completion_rate_pct,
    wow_completion_delta_pct,
    rolling_4w_completion_pct,
    sla_compliance_pct,
    avg_turnaround_hrs,
    total_delay_hrs,
    weekly_rag_status
FROM vw_weekly_scorecard
ORDER BY iso_year DESC, iso_week DESC
LIMIT 8;

-- Q9: SLA Compliance Breakdown by Task Priority
SELECT
    priority,
    COUNT(*)                                                 AS total_tasks,
    SUM(is_completed)                                        AS completed_tasks,
    ROUND(100.0 * SUM(is_sla_met) / NULLIF(SUM(is_completed), 0), 2) AS sla_compliance_pct,
    ROUND(AVG(CASE WHEN is_completed = 1 THEN turnaround_hours END), 2) AS avg_turnaround_hrs,
    ROUND(AVG(sla_hours), 2)                                 AS avg_target_sla_hrs,
    ROUND(SUM(delay_hours), 1)                               AS total_delay_hrs
FROM vw_task_metrics
GROUP BY priority
ORDER BY CASE priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END;

-- Q10: Executive Escalation Queue — Overdue & At-Risk Milestones
SELECT * FROM vw_overdue_milestones;
