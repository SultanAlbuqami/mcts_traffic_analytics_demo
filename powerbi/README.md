# Power BI Starter Pack

This folder contains everything needed to build a governed Power BI model from the pipeline's curated exports — **without** a pre-built `.pbix` file (which is binary and not version-controllable).

> **Why no PBIX?**  
> `.pbix` files are binary blobs. They cannot be meaningfully reviewed in PRs, diffed, or audited.  
> This pack gives you the schema, relationships, DAX measures, and Tabular Editor scripts to build and rebuild the model in minutes.

---

## Prerequisites

- Power BI Desktop (free): https://powerbi.microsoft.com/en-us/desktop/
- (Optional) Tabular Editor 2 (free OSS): https://github.com/TabularEditor/TabularEditor
- Pipeline outputs in `out/powerbi/` (run `python -m traffic_analytics_demo.cli all` first)

---

## Step-by-Step: Build the Power BI Model

### Step 1 — Run the Pipeline

```bash
python -m traffic_analytics_demo.cli all --days 365 --seed 42
```

Output CSVs will appear in `out/powerbi/`:

| File | Role |
|------|------|
| `dim_date.csv` | Date dimension |
| `dim_road.csv` | Road segment dimension |
| `fact_accident.csv` | Accident fact table |
| `fact_violation.csv` | Violation fact table |
| `fact_sensor.csv` | Sensor reading fact table |
| `fact_road_day.csv` | Daily road-level aggregated fact |
| `scenario_summary.csv` | Scenario intervention rankings |
| `scenario_region_impact.csv` | Regional scenario impact |

### Step 2 — Import CSVs into Power BI Desktop

1. Open Power BI Desktop → **Get Data → Text/CSV**
2. Import each file from `out/powerbi/`
3. In Power Query Editor, ensure types are correct:
   - Date columns → `Date` type
   - Integer counts → `Whole Number`
   - Rates/floats → `Decimal Number`
   - IDs → `Text`
4. Click **Close & Apply**

### Step 3 — Define Relationships (Model View)

In the **Model** view, create these relationships (all many-to-one):

| From Table | From Column | To Table | To Column | Cardinality |
|-----------|-------------|----------|-----------|-------------|
| `fact_accident` | `road_id` | `dim_road` | `road_id` | Many → One |
| `fact_accident` | `date` | `dim_date` | `date` | Many → One |
| `fact_violation` | `road_id` | `dim_road` | `road_id` | Many → One |
| `fact_violation` | `date` | `dim_date` | `date` | Many → One |
| `fact_sensor` | `road_id` | `dim_road` | `road_id` | Many → One |
| `fact_sensor` | `date` | `dim_date` | `date` | Many → One |
| `fact_road_day` | `road_id` | `dim_road` | `road_id` | Many → One |
| `fact_road_day` | `date` | `dim_date` | `date` | Many → One |

Cross-filter direction: **Single** (fact → dimension) for all.

### Step 4 — Add DAX Measures

Open the pre-written measures file: `out/powerbi/measures.dax`  
Copy and paste each measure into the appropriate table in Power BI Desktop.

Key measures are also documented in `out/powerbi/model_notes.md`.

The `tabular_editor/` subfolder contains a Tabular Editor script to bulk-add measures automatically.

### Step 5 — Build Visuals

Recommended page layout:

| Page | Content |
|------|---------|
| Executive Summary | KPI cards: total accidents, fatalities, top-risk segment |
| Risk Map | Matrix or map visual: road × severity score |
| Violation Trends | Line chart: violation type over time |
| Model Insights | Table: holdout predictions + actual outcomes |
| Scenario Planner | Bar chart: intervention ROI ranking |

### Step 6 — Naming Conventions

Follow these display name conventions for measures:

| Prefix | Meaning |
|--------|---------|
| `# ` | Count (e.g., `# Accidents`) |
| `Σ ` | Sum (e.g., `Σ Fatalities`) |
| `% ` | Percentage / rate (e.g., `% Severe Rate`) |
| `~ ` | Average (e.g., `~ Speed P95`) |

---

## Files in This Folder

```
powerbi/
├── README.md                     ← This file
└── tabular_editor/
    ├── add_measures.csx          ← Tabular Editor C# script to add measures
    └── relationships.json        ← Relationship definition reference
```

---

## Related Docs

- [`docs/how_to_show_in_powerbi.md`](../docs/how_to_show_in_powerbi.md) — presentation-ready guidance
- [`out/powerbi/model_notes.md`](../out/powerbi/model_notes.md) — pipeline-generated model notes (after pipeline run)
- [`out/powerbi/measures.dax`](../out/powerbi/measures.dax) — pipeline-generated DAX measures
