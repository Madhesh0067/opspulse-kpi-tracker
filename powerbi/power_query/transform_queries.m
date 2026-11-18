// ============================================================================
// OpsPulse — Employee Performance & Departmental KPI Tracker
// File: transform_queries.m
// Description: Power Query (M) ETL scripts for Power BI Desktop
// Usage: Set the `DataFolderPath` parameter to your local `data/raw` folder.
// ============================================================================

// --- Parameter: DataFolderPath ---
// "C:\path\to\opspulse-kpi-tracker\data\raw" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]

// ============================================================================
// 1. DimDepartments
// ============================================================================
let
    Source = Csv.Document(
        File.Contents(DataFolderPath & "\departments.csv"),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]
    ),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    TypedColumns = Table.TransformColumnTypes(PromotedHeaders, {
        {"department_id", type text},
        {"department_name", type text},
        {"department_head", type text},
        {"cost_center", type text},
        {"target_completion_pct", type number},
        {"target_sla_hours", type number},
        {"target_ontime_pct", type number},
        {"monthly_budget_usd", Currency.Type}
    })
in
    TypedColumns;

// ============================================================================
// 2. DimEmployees
// ============================================================================
let
    Source = Csv.Document(
        File.Contents(DataFolderPath & "\employees.csv"),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]
    ),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    TypedColumns = Table.TransformColumnTypes(PromotedHeaders, {
        {"employee_id", type text},
        {"full_name", type text},
        {"email", type text},
        {"department_id", type text},
        {"role_title", type text},
        {"seniority_level", type text},
        {"location", type text},
        {"hire_date", type date},
        {"weekly_capacity_hrs", type number},
        {"status", type text}
    })
in
    TypedColumns;

// ============================================================================
// 3. DimMilestones
// ============================================================================
let
    Source = Csv.Document(
        File.Contents(DataFolderPath & "\milestones.csv"),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]
    ),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    CleanNullDates = Table.ReplaceValue(PromotedHeaders, "", null, Replacer.ReplaceValue, {"actual_completed_date"}),
    TypedColumns = Table.TransformColumnTypes(CleanNullDates, {
        {"milestone_id", type text},
        {"milestone_name", type text},
        {"department_id", type text},
        {"owner_employee_id", type text},
        {"quarter", type text},
        {"priority", type text},
        {"planned_due_date", type date},
        {"actual_completed_date", type date},
        {"status", type text},
        {"completion_pct", type number},
        {"blocker_summary", type text}
    })
in
    TypedColumns;

// ============================================================================
// 4. FactTasks
// ============================================================================
let
    Source = Csv.Document(
        File.Contents(DataFolderPath & "\tasks.csv"),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]
    ),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    CleanNulls = Table.ReplaceValue(PromotedHeaders, "", null, Replacer.ReplaceValue, {"completed_date", "turnaround_hours", "quality_score"}),
    TypedColumns = Table.TransformColumnTypes(CleanNulls, {
        {"task_id", type text},
        {"task_title", type text},
        {"employee_id", type text},
        {"department_id", type text},
        {"milestone_id", type text},
        {"task_category", type text},
        {"priority", type text},
        {"assigned_date", type date},
        {"due_date", type date},
        {"completed_date", type date},
        {"status", type text},
        {"sla_hours", type number},
        {"turnaround_hours", type number},
        {"estimated_hours", type number},
        {"actual_hours", type number},
        {"delay_hours", type number},
        {"delay_reason", type text},
        {"quality_score", type number},
        {"rework_flag", Int64.Type},
        {"iso_year", Int64.Type},
        {"iso_week", Int64.Type},
        {"week_label", type text},
        {"month_label", type text},
        {"quarter", type text}
    }),
    AddDelaySeverity = Table.AddColumn(TypedColumns, "DelaySeverity", each
        if [delay_hours] = 0 then "No Delay"
        else if [delay_hours] <= 8 then "Minor (<=8h)"
        else if [delay_hours] <= 24 then "Moderate (8-24h)"
        else "Severe (>24h)", type text)
in
    AddDelaySeverity;

// ============================================================================
// 5. DimDate (Dynamic 2026 Calendar Dimension)
// ============================================================================
let
    StartDate = #date(2026, 1, 1),
    EndDate = #date(2026, 12, 31),
    DayCount = Duration.Days(EndDate - StartDate) + 1,
    DateList = List.Dates(StartDate, DayCount, #duration(1, 0, 0, 0)),
    ToTable = Table.FromList(DateList, Splitter.SplitByNothing(), {"Date"}),
    TypedDate = Table.TransformColumnTypes(ToTable, {{"Date", type date}}),
    AddYear = Table.AddColumn(TypedDate, "Year", each Date.Year([Date]), Int64.Type),
    AddQuarter = Table.AddColumn(AddYear, "Quarter", each Text.From([Year]) & "-Q" & Text.From(Date.QuarterOfYear([Date])), type text),
    AddMonthNum = Table.AddColumn(AddQuarter, "MonthNum", each Date.Month([Date]), Int64.Type),
    AddMonthName = Table.AddColumn(AddMonthNum, "MonthName", each Date.ToText([Date], "MMM yyyy"), type text),
    AddIsoWeek = Table.AddColumn(AddMonthName, "ISOWeek", each Date.WeekOfYear([Date], Day.Monday), Int64.Type),
    AddYearWeekNum = Table.AddColumn(AddIsoWeek, "YearWeekNum", each [Year] * 100 + [ISOWeek], Int64.Type),
    AddWeekLabel = Table.AddColumn(AddYearWeekNum, "WeekLabel", each Text.From([Year]) & "-W" & Text.PadStart(Text.From([ISOWeek]), 2, "0"), type text)
in
    AddWeekLabel;
