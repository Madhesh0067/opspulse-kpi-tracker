# Power BI Desktop Build Guide

Follow these steps to assemble the live Power BI `.pbix` report from the artifacts in this repository:

1. **Generate or Refresh Data**
   ```bash
   python scripts/run_pipeline.py
   ```
   This populates `data/raw/*.csv`, `data/processed/*.csv`, and `data/opspulse.db`.

2. **Load Tables via Power Query (M)**
   - Open **Power BI Desktop → Transform Data → Manage Parameters → New Parameter**.
   - Name: `DataFolderPath`, Type: `Text`, Current Value: `<your-repo-path>\data\raw`.
   - Open the **Advanced Editor** for each blank query and paste the 5 M queries from [`power_query/transform_queries.m`](./power_query/transform_queries.m) (`DimDepartments`, `DimEmployees`, `DimMilestones`, `FactTasks`, `DimDate`).
   - Click **Close & Apply**.

3. **Configure Star-Schema Relationships**
   - In **Model View**, connect:
     - `DimDepartments[department_id]` 1 → * `FactTasks[department_id]`
     - `DimEmployees[employee_id]` 1 → * `FactTasks[employee_id]`
     - `DimMilestones[milestone_id]` 1 → * `FactTasks[milestone_id]`
     - `DimDate[Date]` 1 → * `FactTasks[assigned_date]`
   - Mark `DimDate` as the official Date Table (`Table Tools → Mark as date table → Date`).

4. **Import DAX Measures**
   - Create a dedicated `_Measures` table (`Enter Data → Load`).
   - Copy the 35+ measures from [`dax/kpi_measures.dax`](./dax/kpi_measures.dax) into `_Measures` (or bulk-import using Tabular Editor).

5. **Apply the Executive Theme**
   - Go to **View → Themes → Browse for themes** and select [`OpsPulse_Theme.json`](./OpsPulse_Theme.json).

6. **Build or Preview**
   - Lay out the 4 report pages per [`data_model_schema.md`](./data_model_schema.md).
   - Want an immediate browser preview of the exact dashboard design without opening Power BI Desktop? Open [`../dashboard/index.html`](../dashboard/index.html)!
