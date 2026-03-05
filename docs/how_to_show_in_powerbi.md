# Power BI - How To Show It in the Interview

Goal: prove that you understand **data modeling, KPI design, drill-down, and executive reporting**, not only Python.

## 1) Import the exported model

Open Power BI Desktop, then import files from `out/powerbi/`:

- `dim_date.csv`
- `dim_road.csv`
- `fact_accident.csv`
- `fact_violation.csv`
- `fact_sensor.csv`
- `fact_road_day.csv`

## 2) Build relationships

Recommended relationships:

- `fact_accident[road_id] -> dim_road[road_id]`
- `fact_violation[road_id] -> dim_road[road_id]`
- `fact_sensor[road_id] -> dim_road[road_id]`
- `fact_road_day[road_id] -> dim_road[road_id]`
- `fact_*[date] -> dim_date[date]`

## 3) Use the prepared measures

Open `out/powerbi/measures.dax` and create the measures in Power BI.

Minimum measures to highlight:

- `Accidents`
- `Fatalities`
- `Injuries`
- `Severe Accidents`
- `Severe Rate`
- `Violations`
- `Avg Sensor Speed`
- `Road-Day Fatality Flag Rate`

## 4) Suggested pages

### Page 1 - Executive Overview
- KPI cards
- Weekly trend
- Region slicer
- Road type slicer
- Hotspot table

### Page 2 - Diagnostics
- Violations by type
- Accidents vs exposure
- Severe rate by road type
- Region comparison

### Page 3 - Predictive Monitoring
- Top high-risk road-days from `fact_road_day`
- Weather context
- Drill-down by region and city

## 5) Presentation notes

- "I separated dimensions and facts to keep the model scalable and reusable."
- "The exported files are not just raw extracts; they are shaped for BI consumption."
- "I included a road-day fact so the dashboard can connect operational exposure with outcomes."
- "The same KPI logic can be reused across Streamlit and Power BI."
