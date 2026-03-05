# Traffic Safety Analytics — Story One-Pager

> **Data:** 100% synthetic (seed=42). No real personal data, no real government records.  
> **Purpose:** Demonstrate end-to-end governed analytics engineering for portfolio / interview.

---

## The Problem

Road safety authorities face a recurring challenge: they collect enormous volumes of traffic sensor data, violation records, and accident reports across dozens of road segments — but the data sits in silos. Analysts produce ad-hoc reports; executives see conflicting KPIs; interventions are funded on intuition rather than evidence.

**The business question:**  
*Which road segments, at which times, under which conditions, present the highest preventable risk — and what is the expected return on targeted intervention?*

---

## The Signal

This demo ingests and integrates four synthetic source streams:

| Source | Signal |
|--------|--------|
| Speed sensors (5-minute intervals) | Volume, velocity, P95 speed spikes |
| Violation records | Type, location, driver profile, fine amount |
| Accident reports | Severity, injuries, fatalities, weather context |
| Road segment metadata | Type, lanes, speed limit, region |

After ETL, quality checks, and a daily road-segment aggregation, the model learns that the combined signature of *high P95 speed + low-visibility hours + elevated phone-use violations* predicts next-day severe incidents with measurable lift over a naive baseline.

---

## The Decision Layer

The prescriptive scenario engine ranks interventions by **risk-reduction ROI**:

| Intervention | Mechanism | KPI Impact |
|-------------|-----------|------------|
| Dynamic speed advisory | Reduce P95 speed during fog/rain | –18% predicted severe rate |
| Targeted enforcement (phone use) | Deploy mobile units to hotspot segments | –12% violation density |
| Lighting upgrade | Reduce low-visibility hours factor | –9% severe rate on affected roads |

The Streamlit dashboard surfaces these rankings, the model's calibration curve, and an executive summary — all reproducible with one CLI command.

---

## The Impact (Demo Framing)

| Metric | Baseline | After top-2 interventions |
|--------|---------|--------------------------|
| Predicted severe accidents (30-day) | 124 | ~93 (synthetic) |
| High-risk road-days flagged | 210 | 147 |
| Violation density (top-10 segments) | 4.2 / 1000 vehicles | 3.1 / 1000 vehicles |

> These numbers are **illustrative outputs from the synthetic pipeline**, not real-world predictions. They change deterministically with `--seed 42`.

---

## What This Proves (Engineering Evidence)

| Capability | Artifact |
|-----------|---------|
| Multi-source integration + traceability | `data/processed/*.csv` with `ingest_batch_id`, `record_hash`, `source_system` |
| Reproducible ETL | `src/traffic_analytics_demo/cli.py` — one command rebuilds everything |
| Data quality enforcement | `out/quality_report.md` — rule-based + statistical checks |
| Predictive modeling | `out/model_report.md` — train/holdout split, group-level checks |
| Prescriptive planning | `out/scenario_report.md` — ranked intervention packages |
| Executive communication | `out/executive_report.md` + Streamlit dashboard |
| Power BI readiness | `out/powerbi/` — star schema CSVs + DAX measures |
| Governance & compliance | `docs/governance.md`, `docs/data_dictionary.md`, PDPL notes |
| Operational maturity | CI, Dockerfile (non-root), healthcheck, structured logging |

---

## Demo in 5 Minutes

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt && pip install -e .
python -m traffic_analytics_demo.cli all --days 30 --seed 42 --road-segments 24
streamlit run app/streamlit_app.py
```

Open `http://localhost:8501` → navigate the dashboard tabs → show `out/executive_report.md`.

---

## Assumptions & Limitations

1. All data is synthetic. Distributions are plausible but not calibrated to any real road network.
2. The predictive model is a demonstration artifact (gradient boosting on tabular features). Production would require real data, proper validation, and regulatory approval.
3. Intervention ROI estimates are illustrative scenario outputs, not causal analyses.
4. No PII is present. The design respects PDPL principles (see `docs/saudi_compliance_reference.md`).
