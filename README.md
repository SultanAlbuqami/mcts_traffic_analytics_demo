# MCTS Traffic Safety - Governed Analytics Demo

مشروع تحليلات مرورية محكوم الحوكمة يركز على الدمج بين المصادر، الجودة، التحليلات التنفيذية، والتسليم الجاهز لـ Power BI. الفكرة ليست بناء منتج ضخم، بل بناء مشروع صغير لكنه متماسك ويثبت القدرة على:

- جمع ودمج مصادر متعددة مع `traceability`
- بناء ETL واضح وقابل لإعادة التشغيل
- تطبيق فحوص جودة بيانات قبل النشر
- إنتاج تحليلات تنفيذية وتقارير قرار
- تشغيل نموذج predictive مع تقييم أداء وتحليل مجموعات
- تسليم مخرجات جاهزة لـ Power BI
- شرح الحوكمة والامتثال والقيود بوضوح

> البيانات صناعية بالكامل `Synthetic` وآمنة للعرض.

## What This Demo Proves

| Job expectation | Evidence in the project |
|---|---|
| Multi-source integration + traceability | `data_gen.py`, `ingest.py`, processed datasets with `source_system`, `ingest_batch_id`, `record_hash` |
| Cleaning / transformation pipelines | `transform.py` + reproducible CLI |
| Data quality mindset | `quality.py`, `out/quality_report.md`, automated tests |
| Advanced analytics / predictive modeling | `model.py`, `out/model_report.md`, `out/model_holdout_predictions.csv` |
| Prescriptive planning | `scenario.py`, `out/scenario_report.md`, intervention ranking in Streamlit |
| Executive reporting | `report.py`, `out/executive_report.md`, Streamlit app |
| Power BI readiness | `out/powerbi/*.csv`, `out/powerbi/measures.dax`, `out/powerbi/model_notes.md` |
| Governance / compliance awareness | `docs/governance.md`, traceability fields, documentation |
| Operational maturity | `out/run_summary.json`, `out/pipeline.log`, CI workflow, Dockerfile |

## Quick Start

### 1) Create environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / WSL
source .venv/bin/activate
```

### 2) Install dependencies
```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

### 3) Run the full demo pipeline
```bash
python -m traffic_analytics_demo.cli all
```

### 3a) Run a faster smoke-sized pipeline
```bash
python -m traffic_analytics_demo.cli all --days 30 --seed 7 --road-segments 24 --accidents 500 --violations 1600 --sensors-rows 5000
```

### 4) Launch the dashboard
```bash
streamlit run app/streamlit_app.py
```

### 5) Run tests
```bash
python -m pytest -q
```

## Generated Outputs

After running the pipeline you will find:

- `data/raw/` raw source files
- `data/processed/` integrated and cleaned datasets
- `out/quality_report.md` governed data quality summary
- `out/model_report.md` model validation and group checks
- `out/model_holdout_predictions.csv` highest-risk road-days from the holdout set
- `out/executive_report.md` executive report ready for presentation
- `out/stakeholder_pack.md` multi-level brief (executive, operations, governance, analytics)
- `out/diagnostic_report.md` diagnostic and root-cause style summary
- `out/scenario_report.md` intervention scenario analysis report
- `out/scenario_summary.csv` ranked intervention packages
- `out/scenario_top_opportunities.csv` highest-leverage road-days by scenario
- `out/scenario_region_impact.csv` regional scenario impact view
- `out/data_dictionary.md` generated data dictionary for processed datasets
- `out/lineage_summary.csv` lineage and traceability summary by dataset
- `out/pipeline_manifest.json` pipeline execution manifest and output inventory
- `out/run_summary.json` step-by-step run telemetry with durations and status
- `out/pipeline.log` structured operational log
- `out/solution_overview.md` short summary of scope, status, and limitations
- `out/powerbi/` star schema CSVs + Power BI guidance + suggested DAX measures

Power BI export includes:

- `dim_date.csv`
- `dim_road.csv`
- `fact_accident.csv`
- `fact_violation.csv`
- `fact_sensor.csv`
- `fact_road_day.csv`
- `scenario_summary.csv`
- `scenario_region_impact.csv`
- `measures.dax`
- `model_notes.md`

## Runtime Configuration

The project supports environment overrides for isolated runs, CI, and smoke testing:

- `TRAFFIC_ANALYTICS_DATA_DIR`
- `TRAFFIC_ANALYTICS_RAW_DIR`
- `TRAFFIC_ANALYTICS_STAGED_DIR`
- `TRAFFIC_ANALYTICS_CURATED_DIR`
- `TRAFFIC_ANALYTICS_PROCESSED_DIR`
- `TRAFFIC_ANALYTICS_OUT_DIR`
- `TRAFFIC_ANALYTICS_POWERBI_DIR`
- `TRAFFIC_ANALYTICS_LOG_LEVEL`
- `TRAFFIC_ANALYTICS_DEFAULT_DAYS`
- `TRAFFIC_ANALYTICS_DEFAULT_SEED`
- `TRAFFIC_ANALYTICS_STREAMLIT_PORT`
- `TRAFFIC_ANALYTICS_LLM_PROVIDER` (`mock`, `local_gateway`, `disabled`)
- `TRAFFIC_ANALYTICS_LLM_MODEL`
- `TRAFFIC_ANALYTICS_LLM_GATEWAY_URL`
- `TRAFFIC_ANALYTICS_LLM_TIMEOUT_SECONDS`

## Delivery Tooling

- `Makefile` includes `quick`, `smoke`, `docker-build`, and `docker-run` targets
- `Dockerfile` packages the CLI + Streamlit app for container execution
- `.github/workflows/ci.yml` runs compile, tests, pipeline build, and Streamlit smoke checks

## Project Structure

```text
app/                         Streamlit presentation layer
docs/                        Governance, architecture, and delivery notes
src/traffic_analytics_demo/  ETL, quality, model, reporting, Power BI export
tests/                       Smoke + end-to-end tests
data/                        Raw and processed datasets
out/                         Reports and Power BI handoff artifacts
```

## Supporting Docs

- `docs/how_to_show_in_powerbi.md`
- `docs/governance.md`
- `docs/kpi_catalog.md`
- `docs/architecture_overview.md`
- `docs/saudi_compliance_reference.md`
- `docs/ministerial_committee_alignment.md`
- `docs/job_role_coverage.md`
- `docs/executive_presentation_playbook.md`
- `docs/analytics_standards.md`
