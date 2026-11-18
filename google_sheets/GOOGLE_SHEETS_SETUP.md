# Google Sheets Integration & Weekly Automation Guide

OpsPulse is designed for seamless dual-compatibility between **Microsoft Excel** and **Google Sheets**. All formulas in `excel/OpsPulse_KPI_Tracker.xlsx` use universal spreadsheet functions (`SUMIFS`, `COUNTIFS`, `AVERAGEIFS`, `IFERROR`, `RANK`, `INDEX/MATCH`) that translate cleanly into Google Sheets without `#NAME?` errors.

---

## Quick Setup (3 Minutes)

1. **Upload the Workbook**
   - Upload `excel/OpsPulse_KPI_Tracker.xlsx` to Google Drive.
   - Right-click the file → **Open with → Google Sheets**.
   - Click **File → Save as Google Sheets** to unlock Apps Script automation.

2. **Attach the OpsPulse Automation Script**
   - In Google Sheets, navigate to **Extensions → Apps Script**.
   - Delete any placeholder code in `Code.gs` and paste the full contents of [`OpsPulse_AppsScript.gs`](./OpsPulse_AppsScript.gs).
   - Update `CONFIG.ALERT_RECIPIENTS` with your leadership email list.
   - Click **Save** and reload the spreadsheet.

3. **Enable Automated Weekly Scorecards**
   - A new **`OpsPulse KPI`** menu appears in the top toolbar.
   - Click **`OpsPulse KPI → Install Monday 8 AM Auto-Trigger`** to automate weekly scorecards, SLA breach highlighting, snapshot archiving, and executive HTML email digests.

---

## Native Google Sheets `QUERY()` Recipes

If your team prefers dynamic Google Sheets `QUERY()` views on top of `Task_Log`, paste these directly into any new tab:

### 1. Live Departmental Completion & Delay Summary
```excel
=QUERY(Task_Log!A1:X,
  "SELECT E, COUNT(A), SUM(V), SUM(V)/COUNT(A), AVG(L), SUM(O)
   WHERE A IS NOT NULL
   GROUP BY E
   ORDER BY SUM(O) DESC
   LABEL E 'Department', COUNT(A) 'Total Tasks', SUM(V) 'Completed',
         SUM(V)/COUNT(A) 'Completion Rate', AVG(L) 'Avg Turnaround (h)', SUM(O) 'Delay Hours'", 1)
```

### 2. Operational Delay Root-Cause Pareto Table
```excel
=QUERY(Task_Log!A1:X,
  "SELECT P, COUNT(A), SUM(O), AVG(O)
   WHERE O > 0 AND P <> 'None'
   GROUP BY P
   ORDER BY SUM(O) DESC
   LABEL P 'Delay Root Cause', COUNT(A) 'Incidents', SUM(O) 'Total Delay Hrs', AVG(O) 'Avg Delay Hrs'", 1)
```

### 3. Critical Overdue Escalation Filter
```excel
=QUERY(Task_Log!A1:X,
  "SELECT A, B, D, E, H, J, O, P
   WHERE J = 'Overdue' AND H = 'Critical'
   ORDER BY O DESC", 1)
```
