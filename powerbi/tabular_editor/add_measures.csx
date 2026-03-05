// Tabular Editor 2 C# Script — Add Core Measures
// ─────────────────────────────────────────────────────────────────────────────
// Usage:
//   1. Open your Power BI model in Tabular Editor 2 (External Tools tab in PBI Desktop)
//   2. Go to: Advanced Scripting → paste this script → Run (F5)
//   3. Save the model → return to Power BI Desktop
//
// Prerequisites:
//   - Tables must already exist: fact_accident, fact_violation, fact_sensor,
//     fact_road_day, dim_road, dim_date
//   - Run after importing CSVs and defining relationships.
// ─────────────────────────────────────────────────────────────────────────────

// Helper: get or create a measure in the target table
Action<string, string, string, string> AddMeasure = (tableName, measureName, dax, formatString) => {
    var table = Model.Tables[tableName];
    if (table == null) {
        Error($"Table not found: {tableName}");
        return;
    }
    if (table.Measures.ContainsName(measureName)) {
        Info($"Measure already exists (skipped): {measureName}");
        return;
    }
    var m = table.AddMeasure(measureName, dax);
    if (!string.IsNullOrEmpty(formatString)) m.FormatString = formatString;
    m.IsHidden = false;
};

// ── Accident Measures ────────────────────────────────────────────────────────
AddMeasure("fact_accident", "# Accidents",
    "COUNTROWS(fact_accident)", "#,0");

AddMeasure("fact_accident", "Σ Fatalities",
    "SUM(fact_accident[fatalities])", "#,0");

AddMeasure("fact_accident", "Σ Injuries",
    "SUM(fact_accident[injuries])", "#,0");

AddMeasure("fact_accident", "% Fatal Rate",
    "DIVIDE([Σ Fatalities], [# Accidents], 0)", "0.00%");

// ── Violation Measures ───────────────────────────────────────────────────────
AddMeasure("fact_violation", "# Violations",
    "COUNTROWS(fact_violation)", "#,0");

AddMeasure("fact_violation", "# Speeding Violations",
    "CALCULATE(COUNTROWS(fact_violation), fact_violation[violation_type] = \"Speeding\")", "#,0");

AddMeasure("fact_violation", "# Phone Use Violations",
    "CALCULATE(COUNTROWS(fact_violation), fact_violation[violation_type] = \"PhoneUse\")", "#,0");

// ── Sensor Measures ──────────────────────────────────────────────────────────
AddMeasure("fact_sensor", "~ Avg Speed",
    "AVERAGE(fact_sensor[avg_speed])", "0.0");

AddMeasure("fact_sensor", "Σ Total Volume",
    "SUM(fact_sensor[volume])", "#,0");

// ── Road-Day Aggregate Measures ──────────────────────────────────────────────
AddMeasure("fact_road_day", "% Severe Rate",
    "AVERAGE(fact_road_day[severe_rate])", "0.00%");

AddMeasure("fact_road_day", "~ Violations per 1000 Vehicles",
    "AVERAGE(fact_road_day[violations_per_1000_volume])", "0.00");

AddMeasure("fact_road_day", "# High-Risk Road-Days",
    "CALCULATE(COUNTROWS(fact_road_day), fact_road_day[severe] >= 1)", "#,0");

Info("✓ Measures added successfully. Save the model to apply changes.");
