/**
 * ============================================================================
 * OpsPulse — Employee Performance & Departmental KPI Tracker
 * File: OpsPulse_AppsScript.gs
 * Platform: Google Sheets (Apps Script V8 Runtime)
 * Author: Madhesh Srinivasan (2026)
 *
 * Capabilities:
 *   1. Adds a custom "OpsPulse KPI" menu in Google Sheets.
 *   2. Automatically recalculates & refreshes weekly scorecards and SLA alerts.
 *   3. Flags overdue milestones and high-delay tasks with RAG color coding.
 *   4. Emails an automated HTML Executive Weekly Scorecard Digest every Monday.
 *   5. Archives point-in-time weekly snapshots for historical auditing.
 * ============================================================================
 */

const CONFIG = {
  SHEETS: {
    DASHBOARD: 'Executive_Dashboard',
    WEEKLY: 'Weekly_Scorecard',
    EMPLOYEES: 'Employee_Leaderboard',
    MILESTONES: 'Overdue_Milestones',
    TASKS: 'Task_Log',
    DEPARTMENTS: 'Departments_Ref'
  },
  TARGETS: {
    COMPLETION_GREEN: 0.88,
    COMPLETION_AMBER: 0.80,
    SLA_GREEN: 0.82,
    SLA_AMBER: 0.74
  },
  ALERT_RECIPIENTS: 'leadership@company.example.com', // Update with leadership emails
  SENDER_NAME: 'OpsPulse Automated BI'
};

/**
 * Adds custom OpsPulse menu when the spreadsheet opens.
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('OpsPulse KPI')
    .addItem('Refresh Weekly Scorecard & Alerts', 'refreshOpsPulseScorecards')
    .addItem('Highlight SLA Breaches & Overdue Tasks', 'highlightOperationalGaps')
    .addSeparator()
    .addItem('Send Weekly Executive Email Digest', 'sendWeeklyExecutiveDigest')
    .addItem('Archive Weekly Snapshot Tab', 'archiveWeeklySnapshot')
    .addSeparator()
    .addItem('Install Monday 8 AM Auto-Trigger', 'createWeeklyTrigger')
    .addToUi();
}

/**
 * Core refresh routine: recalculates formulas, updates timestamps,
 * applies RAG highlighting, and logs refresh audit timestamp.
 */
function refreshOpsPulseScorecards() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  SpreadsheetApp.flush();

  highlightOperationalGaps();

  const dash = ss.getSheetByName(CONFIG.SHEETS.DASHBOARD);
  if (dash) {
    const timestamp = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm z');
    dash.getRange('I2').setValue('Last Synced: ' + timestamp);
  }

  Logger.log('OpsPulse scorecards refreshed successfully.');
}

/**
 * Scans Task_Log and Overdue_Milestones to visually escalate overdue, blocked,
 * and severe-delay (>24h) items.
 */
function highlightOperationalGaps() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const taskSheet = ss.getSheetByName(CONFIG.SHEETS.TASKS);
  if (!taskSheet) return;

  const lastRow = taskSheet.getLastRow();
  if (lastRow < 2) return;

  // Columns in Task_Log: Status = Col 10 (J), Delay_Hours = Col 15 (O)
  const statusValues = taskSheet.getRange(2, 10, lastRow - 1, 1).getValues();
  const delayValues = taskSheet.getRange(2, 15, lastRow - 1, 1).getValues();
  const bgColors = [];

  for (let i = 0; i < statusValues.length; i++) {
    const status = String(statusValues[i][0]).trim();
    const delayHrs = Number(delayValues[i][0]) || 0;

    if (status === 'Overdue' || delayHrs > 24) {
      bgColors.push(['#FDE8E8']); // Soft red escalation
    } else if (status === 'Blocked' || delayHrs > 8) {
      bgColors.push(['#FEF3C7']); // Soft amber warning
    } else if (status === 'Completed') {
      bgColors.push(['#ECFDF5']); // Soft green completed
    } else {
      bgColors.push(['#FFFFFF']);
    }
  }

  taskSheet.getRange(2, 10, lastRow - 1, 1).setBackgrounds(bgColors);
}

/**
 * Computes summary metrics from Task_Log and sends a formatted HTML
 * Weekly Executive Scorecard email to leadership.
 */
function sendWeeklyExecutiveDigest() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const taskSheet = ss.getSheetByName(CONFIG.SHEETS.TASKS);
  const milestoneSheet = ss.getSheetByName(CONFIG.SHEETS.MILESTONES);

  if (!taskSheet) {
    throw new Error('Task_Log sheet not found.');
  }

  const rows = taskSheet.getDataRange().getValues();
  const headers = rows[0];
  const idx = {
    dept: headers.indexOf('department_name'),
    status: headers.indexOf('status'),
    turnaround: headers.indexOf('turnaround_hours'),
    sla: headers.indexOf('sla_hours'),
    delayHrs: headers.indexOf('delay_hours'),
    delayReason: headers.indexOf('delay_reason'),
    week: headers.indexOf('week_label')
  };

  let total = 0, completed = 0, overdue = 0, slaMet = 0;
  let turnaroundSum = 0, delaySum = 0;
  const delayByReason = {};

  for (let r = 1; r < rows.length; r++) {
    const row = rows[r];
    if (!row[0]) continue;
    total++;

    const status = String(row[idx.status]);
    const turnaround = Number(row[idx.turnaround]) || 0;
    const sla = Number(row[idx.sla]) || 0;
    const delayHrs = Number(row[idx.delayHrs]) || 0;
    const reason = String(row[idx.delayReason] || 'None');

    if (status === 'Completed') {
      completed++;
      turnaroundSum += turnaround;
      if (turnaround <= sla) slaMet++;
    } else if (status === 'Overdue') {
      overdue++;
    }

    if (delayHrs > 0) {
      delaySum += delayHrs;
      if (reason !== 'None') {
        delayByReason[reason] = (delayByReason[reason] || 0) + delayHrs;
      }
    }
  }

  const completionPct = total ? ((completed / total) * 100).toFixed(1) : '0.0';
  const slaPct = completed ? ((slaMet / completed) * 100).toFixed(1) : '0.0';
  const avgTurnaround = completed ? (turnaroundSum / completed).toFixed(1) : '0.0';

  const topDelay = Object.entries(delayByReason)
    .sort((a, b) => b[1] - a[1])[0] || ['None', 0];

  const overdueMilestonesCount = milestoneSheet ? Math.max(0, milestoneSheet.getLastRow() - 3) : 0;
  const reportDate = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'MMMM dd, yyyy');

  const htmlBody = `
    <div style="font-family: 'Segoe UI', Arial, sans-serif; color: #1E293B; max-width: 640px;">
      <div style="background: #0F172A; color: #FFFFFF; padding: 20px 24px; border-radius: 8px 8px 0 0;">
        <h2 style="margin: 0; font-size: 20px;">OpsPulse — Weekly Executive KPI Digest</h2>
        <p style="margin: 4px 0 0; color: #94A3B8; font-size: 13px;">Generated on ${reportDate}</p>
      </div>
      <div style="border: 1px solid #E2E8F0; border-top: none; padding: 20px 24px; border-radius: 0 0 8px 8px;">
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 18px;">
          <tr>
            <td style="padding: 10px; background: #F8FAFC; border: 1px solid #E2E8F0;">
              <div style="font-size: 11px; color: #64748B;">COMPLETION RATE</div>
              <div style="font-size: 22px; font-weight: 700; color: #0F172A;">${completionPct}%</div>
            </td>
            <td style="padding: 10px; background: #F8FAFC; border: 1px solid #E2E8F0;">
              <div style="font-size: 11px; color: #64748B;">SLA COMPLIANCE</div>
              <div style="font-size: 22px; font-weight: 700; color: #0F172A;">${slaPct}%</div>
            </td>
            <td style="padding: 10px; background: #F8FAFC; border: 1px solid #E2E8F0;">
              <div style="font-size: 11px; color: #64748B;">AVG TURNAROUND</div>
              <div style="font-size: 22px; font-weight: 700; color: #0F172A;">${avgTurnaround}h</div>
            </td>
          </tr>
        </table>
        <p style="font-size: 14px; line-height: 1.6;">
          <strong>Operational Highlights & Escalations:</strong><br/>
          • <strong>Total Tasks Monitored:</strong> ${total.toLocaleString()} (${completed.toLocaleString()} completed, ${overdue} overdue)<br/>
          • <strong>Total Delay Impact:</strong> ${delaySum.toFixed(1)} hours lost<br/>
          • <strong>#1 Delay Driver:</strong> ${topDelay[0]} (${topDelay[1].toFixed(1)} hrs)<br/>
          • <strong>Overdue / At-Risk Milestones:</strong> ${overdueMilestonesCount} requiring leadership review
        </p>
        <p style="margin-top: 18px;">
          <a href="${ss.getUrl()}" style="background: #2563EB; color: #FFFFFF; padding: 10px 18px; text-decoration: none; border-radius: 6px; font-weight: 600;">
            Open Live OpsPulse Tracker
          </a>
        </p>
      </div>
    </div>
  `;

  MailApp.sendEmail({
    to: CONFIG.ALERT_RECIPIENTS,
    subject: `[OpsPulse] Weekly KPI Executive Scorecard — ${reportDate}`,
    htmlBody: htmlBody,
    name: CONFIG.SENDER_NAME
  });

  Logger.log('Executive digest emailed to ' + CONFIG.ALERT_RECIPIENTS);
}

/**
 * Duplicates Executive_Dashboard values into an immutable weekly archive tab.
 */
function archiveWeeklySnapshot() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dash = ss.getSheetByName(CONFIG.SHEETS.DASHBOARD);
  if (!dash) return;

  const stamp = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd');
  const archiveName = 'Snapshot_' + stamp;
  const existing = ss.getSheetByName(archiveName);
  if (existing) ss.deleteSheet(existing);

  const copy = dash.copyTo(ss).setName(archiveName);
  const range = copy.getDataRange();
  range.copyTo(range, SpreadsheetApp.CopyPasteType.PASTE_VALUES, false);
}

/**
 * Schedules automated weekly scorecard refresh and email digest every Monday at 8:00 AM.
 */
function createWeeklyTrigger() {
  // Remove duplicate triggers first
  ScriptApp.getProjectTriggers().forEach(trigger => {
    if (trigger.getHandlerFunction() === 'runWeeklyAutomation') {
      ScriptApp.deleteTrigger(trigger);
    }
  });

  ScriptApp.newTrigger('runWeeklyAutomation')
    .timeBased()
    .onWeekDay(ScriptApp.WeekDay.MONDAY)
    .atHour(8)
    .create();

  SpreadsheetApp.getUi().alert('Weekly Monday 8:00 AM OpsPulse automation trigger installed.');
}

function runWeeklyAutomation() {
  refreshOpsPulseScorecards();
  archiveWeeklySnapshot();
  sendWeeklyExecutiveDigest();
}
