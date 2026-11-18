-- ============================================================================
-- OpsPulse — Employee Performance & Departmental KPI Tracker
-- File: 02_kpi_views.sql
-- Description: Analytical KPI views powering weekly scorecards, leaderboards,
--              delay Pareto diagnostics, and executive dashboards.
-- ============================================================================

DROP VIEW IF EXISTS vw_overdue_milestones;
DROP VIEW IF EXISTS vw_operational_delays;
DROP VIEW IF EXISTS vw_weekly_scorecard;
DROP VIEW IF EXISTS vw_department_kpi_summary;
DROP VIEW IF EXISTS vw_employee_performance;
DROP VIEW IF EXISTS vw_task_metrics;

-- ----------------------------------------------------------------------------
-- 1. Enriched Task-Level Metrics View
-- ----------------------------------------------------------------------------
CREATE VIEW vw_task_metrics AS
SELECT
    t.task_id,
    t.task_title,
    t.employee_id,
    e.full_name                                              AS employee_name,
    e.seniority_level,
    t.department_id,
    d.department_name,
    t.milestone_id,
    m.milestone_name,
    t.task_category,
    t.priority,
    t.assigned_date,
    t.due_date,
    t.completed_date,
    t.status,
    t.sla_hours,
    t.turnaround_hours,
    t.estimated_hours,
    t.actual_hours,
    t.delay_hours,
    t.delay_reason,
    t.quality_score,
    t.rework_flag,
    t.iso_year,
    t.iso_week,
    t.week_label,
    t.month_label,
    t.quarter,
    CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END       AS is_completed,
    CASE
        WHEN t.status = 'Completed' AND t.completed_date <= t.due_date THEN 1
        ELSE 0
    END                                                      AS is_on_time,
    CASE
        WHEN t.status = 'Completed' AND t.turnaround_hours <= t.sla_hours THEN 1
        ELSE 0
    END                                                      AS is_sla_met,
    CASE
        WHEN t.status IN ('Overdue', 'Blocked') THEN 1
        ELSE 0
    END                                                      AS is_at_risk_or_overdue,
    ROUND(
        CASE WHEN t.actual_hours > 0 THEN (t.estimated_hours / t.actual_hours) * 100.0
             ELSE 100.0 END,
        2
    )                                                        AS efficiency_pct,
    CASE
        WHEN t.delay_hours = 0 THEN 'No Delay'
        WHEN t.delay_hours <= 8 THEN 'Minor (<=8h)'
        WHEN t.delay_hours <= 24 THEN 'Moderate (8-24h)'
        ELSE 'Severe (>24h)'
    END                                                      AS delay_severity
FROM tasks t
JOIN employees e   ON t.employee_id = e.employee_id
JOIN departments d ON t.department_id = d.department_id
JOIN milestones m  ON t.milestone_id = m.milestone_id;

-- ----------------------------------------------------------------------------
-- 2. Employee Performance Scorecard View (with Ranking & Productivity Index)
-- ----------------------------------------------------------------------------
CREATE VIEW vw_employee_performance AS
WITH emp_agg AS (
    SELECT
        e.employee_id,
        e.full_name,
        e.department_id,
        d.department_name,
        e.role_title,
        e.seniority_level,
        e.location,
        COUNT(t.task_id)                                     AS total_tasks,
        SUM(t.is_completed)                                  AS completed_tasks,
        SUM(CASE WHEN t.status = 'Overdue' THEN 1 ELSE 0 END) AS overdue_tasks,
        SUM(CASE WHEN t.status = 'Blocked' THEN 1 ELSE 0 END) AS blocked_tasks,
        ROUND(100.0 * SUM(t.is_completed) / NULLIF(COUNT(t.task_id), 0), 2) AS completion_rate_pct,
        ROUND(100.0 * SUM(t.is_on_time) / NULLIF(SUM(t.is_completed), 0), 2) AS on_time_rate_pct,
        ROUND(100.0 * SUM(t.is_sla_met) / NULLIF(SUM(t.is_completed), 0), 2) AS sla_compliance_pct,
        ROUND(AVG(CASE WHEN t.is_completed = 1 THEN t.turnaround_hours END), 2) AS avg_turnaround_hrs,
        ROUND(SUM(t.delay_hours), 2)                         AS total_delay_hrs,
        ROUND(SUM(t.actual_hours), 2)                        AS total_logged_hrs,
        ROUND(AVG(CASE WHEN t.is_completed = 1 THEN t.quality_score END), 2) AS avg_quality_score,
        ROUND(100.0 * SUM(t.rework_flag) / NULLIF(SUM(t.is_completed), 0), 2) AS rework_rate_pct
    FROM employees e
    JOIN departments d ON e.department_id = d.department_id
    LEFT JOIN vw_task_metrics t ON e.employee_id = t.employee_id
    GROUP BY
        e.employee_id, e.full_name, e.department_id, d.department_name,
        e.role_title, e.seniority_level, e.location
),
scored AS (
    SELECT
        *,
        -- Composite Productivity Index (0-100):
        -- 35% Completion Rate + 30% On-Time SLA + 20% Quality (scaled to 100) + 15% First-Pass Yield (100 - Rework)
        ROUND(
            (0.35 * COALESCE(completion_rate_pct, 0)) +
            (0.30 * COALESCE(sla_compliance_pct, 0)) +
            (0.20 * COALESCE(avg_quality_score * 20.0, 0)) +
            (0.15 * (100.0 - COALESCE(rework_rate_pct, 0))),
            2
        ) AS productivity_index
    FROM emp_agg
)
SELECT
    *,
    DENSE_RANK() OVER (ORDER BY productivity_index DESC)     AS org_rank,
    DENSE_RANK() OVER (PARTITION BY department_id ORDER BY productivity_index DESC) AS dept_rank,
    CASE
        WHEN productivity_index >= 88.0 THEN 'Top Performer'
        WHEN productivity_index >= 80.0 THEN 'Exceeds Target'
        WHEN productivity_index >= 72.0 THEN 'On Track'
        ELSE 'Needs Support'
    END                                                      AS performance_tier
FROM scored;

-- ----------------------------------------------------------------------------
-- 3. Departmental KPI Summary View (Actuals vs Targets)
-- ----------------------------------------------------------------------------
CREATE VIEW vw_department_kpi_summary AS
SELECT
    d.department_id,
    d.department_name,
    d.department_head,
    d.target_completion_pct,
    d.target_sla_hours,
    d.target_ontime_pct,
    COUNT(DISTINCT t.employee_id)                            AS active_employees,
    COUNT(t.task_id)                                         AS total_tasks,
    SUM(t.is_completed)                                      AS completed_tasks,
    SUM(CASE WHEN t.status = 'Overdue' THEN 1 ELSE 0 END)    AS overdue_tasks,
    SUM(CASE WHEN t.status = 'Blocked' THEN 1 ELSE 0 END)    AS blocked_tasks,
    ROUND(100.0 * SUM(t.is_completed) / NULLIF(COUNT(t.task_id), 0), 2) AS completion_rate_pct,
    ROUND(
        (100.0 * SUM(t.is_completed) / NULLIF(COUNT(t.task_id), 0)) - d.target_completion_pct,
        2
    )                                                        AS completion_variance_pct,
    ROUND(100.0 * SUM(t.is_on_time) / NULLIF(SUM(t.is_completed), 0), 2) AS on_time_rate_pct,
    ROUND(100.0 * SUM(t.is_sla_met) / NULLIF(SUM(t.is_completed), 0), 2) AS sla_compliance_pct,
    ROUND(AVG(CASE WHEN t.is_completed = 1 THEN t.turnaround_hours END), 2) AS avg_turnaround_hrs,
    ROUND(SUM(t.delay_hours), 2)                             AS total_delay_hrs,
    ROUND(AVG(CASE WHEN t.delay_hours > 0 THEN t.delay_hours END), 2) AS avg_delay_when_delayed_hrs,
    ROUND(AVG(CASE WHEN t.is_completed = 1 THEN t.quality_score END), 2) AS avg_quality_score,
    ROUND(100.0 * SUM(t.rework_flag) / NULLIF(SUM(t.is_completed), 0), 2) AS rework_rate_pct,
    CASE
        WHEN (100.0 * SUM(t.is_completed) / NULLIF(COUNT(t.task_id), 0)) >= d.target_completion_pct
         AND (100.0 * SUM(t.is_on_time) / NULLIF(SUM(t.is_completed), 0)) >= d.target_ontime_pct
            THEN 'Green'
        WHEN (100.0 * SUM(t.is_completed) / NULLIF(COUNT(t.task_id), 0)) >= (d.target_completion_pct - 5.0)
            THEN 'Amber'
        ELSE 'Red'
    END                                                      AS rag_status
FROM departments d
LEFT JOIN vw_task_metrics t ON d.department_id = t.department_id
GROUP BY
    d.department_id, d.department_name, d.department_head,
    d.target_completion_pct, d.target_sla_hours, d.target_ontime_pct;

-- ----------------------------------------------------------------------------
-- 4. Automated Weekly Performance Scorecard View (WoW & 4-Week Rolling Avg)
-- ----------------------------------------------------------------------------
CREATE VIEW vw_weekly_scorecard AS
WITH weekly_base AS (
    SELECT
        iso_year,
        iso_week,
        week_label,
        MIN(assigned_date)                                   AS week_start_date,
        COUNT(task_id)                                       AS tasks_assigned,
        SUM(is_completed)                                    AS tasks_completed,
        SUM(CASE WHEN status = 'Overdue' THEN 1 ELSE 0 END)  AS tasks_overdue,
        SUM(CASE WHEN status = 'Blocked' THEN 1 ELSE 0 END)  AS tasks_blocked,
        ROUND(100.0 * SUM(is_completed) / NULLIF(COUNT(task_id), 0), 2) AS completion_rate_pct,
        ROUND(100.0 * SUM(is_on_time) / NULLIF(SUM(is_completed), 0), 2) AS on_time_rate_pct,
        ROUND(100.0 * SUM(is_sla_met) / NULLIF(SUM(is_completed), 0), 2) AS sla_compliance_pct,
        ROUND(AVG(CASE WHEN is_completed = 1 THEN turnaround_hours END), 2) AS avg_turnaround_hrs,
        ROUND(SUM(delay_hours), 2)                           AS total_delay_hrs,
        ROUND(AVG(CASE WHEN is_completed = 1 THEN quality_score END), 2) AS avg_quality_score
    FROM vw_task_metrics
    GROUP BY iso_year, iso_week, week_label
)
SELECT
    *,
    ROUND(
        completion_rate_pct - LAG(completion_rate_pct) OVER (ORDER BY iso_year, iso_week),
        2
    )                                                        AS wow_completion_delta_pct,
    ROUND(
        AVG(completion_rate_pct) OVER (
            ORDER BY iso_year, iso_week
            ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
        ),
        2
    )                                                        AS rolling_4w_completion_pct,
    ROUND(
        AVG(avg_turnaround_hrs) OVER (
            ORDER BY iso_year, iso_week
            ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
        ),
        2
    )                                                        AS rolling_4w_turnaround_hrs,
    CASE
        WHEN completion_rate_pct >= 88.0 AND sla_compliance_pct >= 82.0 THEN 'Green'
        WHEN completion_rate_pct >= 80.0 AND sla_compliance_pct >= 74.0 THEN 'Amber'
        ELSE 'Red'
    END                                                      AS weekly_rag_status
FROM weekly_base;

-- ----------------------------------------------------------------------------
-- 5. Operational Delay Root-Cause Pareto View
-- ----------------------------------------------------------------------------
CREATE VIEW vw_operational_delays AS
WITH delay_agg AS (
    SELECT
        delay_reason,
        COUNT(task_id)                                       AS delayed_task_count,
        ROUND(SUM(delay_hours), 2)                           AS total_delay_hrs,
        ROUND(AVG(delay_hours), 2)                           AS avg_delay_hrs,
        SUM(CASE WHEN priority = 'Critical' THEN 1 ELSE 0 END) AS critical_tasks_impacted
    FROM tasks
    WHERE delay_hours > 0 AND delay_reason <> 'None'
    GROUP BY delay_reason
),
grand_total AS (
    SELECT SUM(total_delay_hrs) AS all_delay_hrs FROM delay_agg
)
SELECT
    d.delay_reason,
    d.delayed_task_count,
    d.total_delay_hrs,
    d.avg_delay_hrs,
    d.critical_tasks_impacted,
    ROUND(100.0 * d.total_delay_hrs / NULLIF(g.all_delay_hrs, 0), 2) AS share_of_delay_hrs_pct,
    ROUND(
        100.0 * SUM(d.total_delay_hrs) OVER (ORDER BY d.total_delay_hrs DESC)
        / NULLIF(g.all_delay_hrs, 0),
        2
    )                                                        AS cumulative_share_pct
FROM delay_agg d
CROSS JOIN grand_total g
ORDER BY d.total_delay_hrs DESC;

-- ----------------------------------------------------------------------------
-- 6. Overdue & At-Risk Milestones Escalation View
-- ----------------------------------------------------------------------------
CREATE VIEW vw_overdue_milestones AS
SELECT
    m.milestone_id,
    m.milestone_name,
    d.department_name,
    e.full_name                                              AS owner_name,
    m.quarter,
    m.priority,
    m.planned_due_date,
    m.status,
    m.completion_pct,
    CAST(julianday('2026-11-18') - julianday(m.planned_due_date) AS INTEGER) AS days_past_due,
    COUNT(t.task_id)                                         AS linked_tasks,
    SUM(CASE WHEN t.status IN ('Overdue', 'Blocked') THEN 1 ELSE 0 END) AS open_delayed_tasks,
    ROUND(COALESCE(SUM(t.delay_hours), 0), 2)                AS accumulated_delay_hrs,
    COALESCE(m.blocker_summary, 'Under review')              AS blocker_summary
FROM milestones m
JOIN departments d ON m.department_id = d.department_id
JOIN employees e   ON m.owner_employee_id = e.employee_id
LEFT JOIN tasks t  ON m.milestone_id = t.milestone_id
WHERE m.status IN ('Overdue', 'At Risk')
GROUP BY
    m.milestone_id, m.milestone_name, d.department_name, e.full_name,
    m.quarter, m.priority, m.planned_due_date, m.status, m.completion_pct, m.blocker_summary
ORDER BY
    CASE m.priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END,
    days_past_due DESC;
