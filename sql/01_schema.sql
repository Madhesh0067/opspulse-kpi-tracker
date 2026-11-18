-- ============================================================================
-- OpsPulse — Employee Performance & Departmental KPI Tracker
-- File: 01_schema.sql
-- Description: Normalized relational warehouse schema (SQLite / ANSI SQL)
-- Author: Madhesh Srinivasan (2026)
-- ============================================================================

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS milestones;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;

-- 1. Departments Dimension Table
CREATE TABLE departments (
    department_id        TEXT PRIMARY KEY,
    department_name      TEXT NOT NULL UNIQUE,
    department_head      TEXT NOT NULL,
    cost_center          TEXT NOT NULL,
    target_completion_pct REAL NOT NULL CHECK (target_completion_pct BETWEEN 0 AND 100),
    target_sla_hours     REAL NOT NULL CHECK (target_sla_hours > 0),
    target_ontime_pct    REAL NOT NULL CHECK (target_ontime_pct BETWEEN 0 AND 100),
    monthly_budget_usd   REAL NOT NULL CHECK (monthly_budget_usd >= 0)
);

-- 2. Employees Dimension Table
CREATE TABLE employees (
    employee_id          TEXT PRIMARY KEY,
    full_name            TEXT NOT NULL,
    email                TEXT NOT NULL UNIQUE,
    department_id        TEXT NOT NULL,
    role_title           TEXT NOT NULL,
    seniority_level      TEXT NOT NULL CHECK (seniority_level IN ('Junior', 'Mid', 'Senior', 'Lead')),
    location             TEXT NOT NULL,
    hire_date            DATE NOT NULL,
    weekly_capacity_hrs  REAL NOT NULL DEFAULT 40.0 CHECK (weekly_capacity_hrs > 0),
    status               TEXT NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'On Leave', 'Inactive')),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

-- 3. Departmental Milestones Table
CREATE TABLE milestones (
    milestone_id         TEXT PRIMARY KEY,
    milestone_name       TEXT NOT NULL,
    department_id        TEXT NOT NULL,
    owner_employee_id    TEXT NOT NULL,
    quarter              TEXT NOT NULL CHECK (quarter IN ('2026-Q1', '2026-Q2', '2026-Q3', '2026-Q4')),
    priority             TEXT NOT NULL CHECK (priority IN ('Critical', 'High', 'Medium', 'Low')),
    planned_due_date     DATE NOT NULL,
    actual_completed_date DATE,
    status               TEXT NOT NULL CHECK (status IN ('Completed', 'In Progress', 'Overdue', 'At Risk')),
    completion_pct       REAL NOT NULL CHECK (completion_pct BETWEEN 0 AND 100),
    blocker_summary      TEXT,
    FOREIGN KEY (department_id) REFERENCES departments(department_id),
    FOREIGN KEY (owner_employee_id) REFERENCES employees(employee_id)
);

-- 4. Granular Task & Operational Activity Fact Table
CREATE TABLE tasks (
    task_id              TEXT PRIMARY KEY,
    task_title           TEXT NOT NULL,
    employee_id          TEXT NOT NULL,
    department_id        TEXT NOT NULL,
    milestone_id         TEXT NOT NULL,
    task_category        TEXT NOT NULL,
    priority             TEXT NOT NULL CHECK (priority IN ('Critical', 'High', 'Medium', 'Low')),
    assigned_date        DATE NOT NULL,
    due_date             DATE NOT NULL,
    completed_date       DATE,
    status               TEXT NOT NULL CHECK (status IN ('Completed', 'In Progress', 'Overdue', 'Blocked')),
    sla_hours            REAL NOT NULL CHECK (sla_hours > 0),
    turnaround_hours     REAL,
    estimated_hours      REAL NOT NULL CHECK (estimated_hours > 0),
    actual_hours         REAL NOT NULL CHECK (actual_hours >= 0),
    delay_hours          REAL NOT NULL DEFAULT 0.0 CHECK (delay_hours >= 0),
    delay_reason         TEXT NOT NULL DEFAULT 'None',
    quality_score        REAL CHECK (quality_score IS NULL OR quality_score BETWEEN 1.0 AND 5.0),
    rework_flag          INTEGER NOT NULL DEFAULT 0 CHECK (rework_flag IN (0, 1)),
    iso_year             INTEGER NOT NULL,
    iso_week             INTEGER NOT NULL CHECK (iso_week BETWEEN 1 AND 53),
    week_label           TEXT NOT NULL,
    month_label          TEXT NOT NULL,
    quarter              TEXT NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (department_id) REFERENCES departments(department_id),
    FOREIGN KEY (milestone_id) REFERENCES milestones(milestone_id)
);

-- Performance Indexes for BI & Scorecard Queries
CREATE INDEX idx_tasks_dept_week    ON tasks(department_id, week_label);
CREATE INDEX idx_tasks_emp_status   ON tasks(employee_id, status);
CREATE INDEX idx_tasks_milestone    ON tasks(milestone_id);
CREATE INDEX idx_tasks_delay_reason ON tasks(delay_reason);
CREATE INDEX idx_tasks_dates        ON tasks(assigned_date, due_date, completed_date);
CREATE INDEX idx_milestones_status  ON milestones(status, planned_due_date);
