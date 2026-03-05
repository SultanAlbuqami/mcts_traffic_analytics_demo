# Job Role Coverage Matrix (Advanced Analytics + Governance)

This matrix maps the target role expectations to concrete repository evidence.

## Key Responsibilities Coverage

| Responsibility | Current Evidence in Repo | Coverage |
|---|---|---|
| Collect, consolidate, document multi-source data with traceability | `src/traffic_analytics_demo/data_gen.py`, `ingest.py`, `transform.py`, trace fields (`source_system`, `ingest_batch_id`, `record_hash`) | High |
| Integrate and validate data accuracy/completeness/consistency | `quality.py`, `out/quality_report.md`, `tests/test_quality.py` | High |
| Build reusable cleaning/transformation pipelines | CLI commands + `transform.py` + governed outputs | High |
| Advanced analytics (descriptive/diagnostic/predictive/prescriptive) | `report.py`, `diagnostics.py`, `model.py`, `scenario.py` | High |
| Model validation, testing, and quality checks | `model_report.md`, group checks in model, pytest suite | Medium-High |
| ML pattern detection with bias/limitations awareness | model group metrics + documented limitations in reports | Medium |
| Executive dashboards and KPI drilldowns in Power BI | `out/powerbi/*`, `docs/how_to_show_in_powerbi.md`, Streamlit app tabs | High |
| Executive-level reports for multiple stakeholder levels | `out/executive_report.md` + `out/stakeholder_pack.md` | High |
| Governance/security/privacy compliance in Saudi context | `docs/governance.md`, `docs/saudi_compliance_reference.md`, root PDPL notes | Medium-High |
| Multi-entity data-sharing context | lineage + governance docs + manifest artifacts | Medium |
| Executive communication and methodology transparency | reports include assumptions/limitations; presentation docs included | High |
| Knowledge sharing, standards, templates | root docs/runbook/ADR/evidence + standards section below | Medium-High |

## Required Skills Coverage

| Skill | Evidence |
|---|---|
| Python analytics proficiency | End-to-end package under `src/traffic_analytics_demo` |
| Power BI proficiency (modeling/KPIs) | `out/powerbi/fact_*.csv`, `dim_*.csv`, `measures.dax`, modeling notes |
| Data quality mindset | Quality gates + tests + lineage manifest |
| Senior communication | Executive report + stakeholder pack + governance docs |
| Big-data awareness | Scalable layered architecture documented (`raw -> staged -> curated`) |

## Remaining Gaps to Reach Interview-Strong Position

1. Add external-source simulation pack (government/regulator-style contracts and SLAs).
2. Add explicit role-based access simulation for sensitive columns (classification/access policy demo).
3. Add drift monitoring and scheduled quality trend dashboard for operational maturity story.
4. Add Arabic executive summary variant for leadership communication in local context.

## Recommended Next Sprint (1-2 days)

1. Add `data_contracts/` for each source (schema, owner, refresh cadence, validation rules).
2. Add `classification_policy.md` with field-level classes (Public/Internal/Restricted).
3. Add `out/quality_trend.csv` generation and Streamlit trend visual.
4. Add `out/executive_report_ar.md` generation from existing metrics.
