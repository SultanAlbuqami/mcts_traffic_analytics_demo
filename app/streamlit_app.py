from __future__ import annotations

import sys
from pathlib import Path

# Streamlit Cloud installs requirements.txt but does NOT run `pip install -e .`
# This ensures the local src/ package is importable in both environments.
_src_dir = Path(__file__).resolve().parents[1] / "src"
if _src_dir.exists() and str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

import json

import altair as alt
import pandas as pd
import streamlit as st

from traffic_analytics_demo.ai.service import build_snapshot, generate_analyst_insight
from traffic_analytics_demo.config import get_paths, get_settings

st.set_page_config(page_title="Traffic Safety Analytics", layout="wide")

repo_root = Path(__file__).resolve().parents[1]
paths = get_paths()
settings = get_settings()
processed_dir = (
    paths.data_curated if (paths.data_curated / "model_df.csv").exists() else paths.data_processed
)
out_dir = paths.out
powerbi_dir = paths.out_powerbi


@st.cache_data(show_spinner=False)
def load_csv(path: Path, **kwargs) -> pd.DataFrame:
    return pd.read_csv(path, **kwargs)


@st.cache_data(show_spinner=False)
def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


@st.cache_data(show_spinner=False)
def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def style_app() -> None:
    st.markdown(
        """
        <style>
        :root {
            --paper: #f4efe4;
            --ink: #13212c;
            --accent: #a5402d;
            --accent-2: #1f5c56;
            --panel: rgba(255, 252, 245, 0.88);
            --line: rgba(19, 33, 44, 0.14);
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(165, 64, 45, 0.12), transparent 32%),
                radial-gradient(circle at top right, rgba(31, 92, 86, 0.12), transparent 26%),
                linear-gradient(180deg, #f7f1e4 0%, #efe7d8 100%);
            color: var(--ink);
        }
        h1, h2, h3 {
            font-family: Georgia, "Times New Roman", serif;
            letter-spacing: 0.02em;
        }
        [data-testid="stMetric"] {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 14px 18px;
            box-shadow: 0 10px 28px rgba(19, 33, 44, 0.06);
        }
        [data-testid="stSidebar"] {
            background: rgba(248, 243, 233, 0.95);
        }
        .hero {
            padding: 1.2rem 1.4rem;
            border: 1px solid var(--line);
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(255,255,255,0.8), rgba(255,248,238,0.92));
            box-shadow: 0 18px 40px rgba(19, 33, 44, 0.08);
            margin-bottom: 1rem;
        }
        .hero p {
            margin-bottom: 0;
            font-size: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def build_weekly_trend(df: pd.DataFrame) -> pd.DataFrame:
    weekly = (
        df.assign(
            week=pd.to_datetime(df["date_time"], utc=True, errors="coerce")
            .dt.tz_convert(None)
            .dt.to_period("W")
            .astype(str)
        )
        .groupby("week", as_index=False)
        .agg(
            accidents=("incident_id", "count"),
            fatalities=("fatalities", "sum"),
            severe=("severity", lambda s: int(s.isin(["Severe", "Fatal"]).sum())),
        )
    )
    return weekly


def build_hotspots(df: pd.DataFrame) -> pd.DataFrame:
    hotspots = (
        df.groupby(["road_id", "region", "city", "road_type"], as_index=False)
        .agg(
            accidents=("incident_id", "count"),
            severe=("severity", lambda s: int(s.isin(["Severe", "Fatal"]).sum())),
            fatalities=("fatalities", "sum"),
        )
        .sort_values(["fatalities", "accidents"], ascending=False)
    )
    hotspots["severe_rate"] = (hotspots["severe"] / hotspots["accidents"]).fillna(0.0)
    return hotspots


style_app()

st.title("Traffic Safety Analytics")
st.markdown(
    """
    <div class="hero">
        <p><strong>Governed traffic safety analytics workflow.</strong> This app shows multi-source integration,
        traceability, data quality gates, predictive prioritization, and Power BI handoff from one pipeline.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

required_files = [
    processed_dir / "accidents.csv",
    processed_dir / "roads.csv",
    processed_dir / "model_df.csv",
    out_dir / "quality_report.md",
    out_dir / "model_report.md",
    out_dir / "executive_report.md",
    out_dir / "diagnostic_report.md",
    out_dir / "scenario_report.md",
    out_dir / "scenario_summary.csv",
    out_dir / "scenario_top_opportunities.csv",
    out_dir / "scenario_region_impact.csv",
    out_dir / "run_summary.json",
]
missing_files = [path for path in required_files if not path.exists()]
if missing_files:
    st.error("Required demo artifacts are missing.")
    st.code("python -m traffic_analytics_demo.cli all")
    st.stop()

accidents = load_csv(processed_dir / "accidents.csv", parse_dates=["date_time"])
roads = load_csv(processed_dir / "roads.csv")
model_df = load_csv(processed_dir / "model_df.csv")
holdout_path = out_dir / "model_holdout_predictions.csv"
holdout_predictions = (
    load_csv(holdout_path, parse_dates=["date"]) if holdout_path.exists() else pd.DataFrame()
)

quality_report = load_text(out_dir / "quality_report.md")
model_report = load_text(out_dir / "model_report.md")
executive_report = load_text(out_dir / "executive_report.md")
diagnostic_report = load_text(out_dir / "diagnostic_report.md")
scenario_report = load_text(out_dir / "scenario_report.md")
solution_overview = (
    load_text(out_dir / "solution_overview.md")
    if (out_dir / "solution_overview.md").exists()
    else ""
)
data_dictionary = (
    load_text(out_dir / "data_dictionary.md") if (out_dir / "data_dictionary.md").exists() else ""
)
powerbi_notes = (
    load_text(powerbi_dir / "model_notes.md") if (powerbi_dir / "model_notes.md").exists() else ""
)
powerbi_measures = (
    load_text(powerbi_dir / "measures.dax") if (powerbi_dir / "measures.dax").exists() else ""
)
governance_doc = load_text(repo_root / "docs" / "governance.md")
architecture_doc = load_text(repo_root / "docs" / "architecture_overview.md")
run_summary = load_json(out_dir / "run_summary.json")
scenario_summary = load_csv(out_dir / "scenario_summary.csv")
scenario_top_opportunities = load_csv(
    out_dir / "scenario_top_opportunities.csv", parse_dates=["date"]
)
scenario_region_impact = load_csv(out_dir / "scenario_region_impact.csv")

accidents["date"] = pd.to_datetime(accidents["date_time"], utc=True).dt.date
model_df["date"] = pd.to_datetime(model_df["date"], errors="coerce").dt.date
if not holdout_predictions.empty:
    holdout_predictions["date"] = pd.to_datetime(
        holdout_predictions["date"], errors="coerce"
    ).dt.date
if not scenario_top_opportunities.empty:
    scenario_top_opportunities["date"] = pd.to_datetime(
        scenario_top_opportunities["date"], errors="coerce"
    ).dt.date

with st.sidebar:
    st.subheader("Filters")
    st.caption(f"Pipeline status: {run_summary.get('status', 'unknown')}")
    regions = ["All"] + sorted(accidents["region"].dropna().unique().tolist())
    selected_region = st.selectbox("Region", regions)
    road_types = ["All"] + sorted(accidents["road_type"].dropna().unique().tolist())
    selected_road_type = st.selectbox("Road type", road_types)
    min_date = accidents["date"].min()
    max_date = accidents["date"].max()
    selected_dates = st.date_input(
        "Date window", value=(min_date, max_date), min_value=min_date, max_value=max_date
    )

filtered = accidents.copy()
if selected_region != "All":
    filtered = filtered[filtered["region"] == selected_region]
if selected_road_type != "All":
    filtered = filtered[filtered["road_type"] == selected_road_type]
if isinstance(selected_dates, tuple | list) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
    filtered = filtered[(filtered["date"] >= start_date) & (filtered["date"] <= end_date)]

filtered_model_df = model_df.copy()
if selected_region != "All" and "region" in filtered_model_df.columns:
    filtered_model_df = filtered_model_df[filtered_model_df["region"] == selected_region]
if selected_road_type != "All" and "road_type" in filtered_model_df.columns:
    filtered_model_df = filtered_model_df[filtered_model_df["road_type"] == selected_road_type]
if isinstance(selected_dates, tuple | list) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
    filtered_model_df = filtered_model_df[
        (filtered_model_df["date"] >= start_date) & (filtered_model_df["date"] <= end_date)
    ]

filtered_holdout = holdout_predictions.copy()
if not filtered_holdout.empty:
    if selected_region != "All":
        filtered_holdout = filtered_holdout[filtered_holdout["region"] == selected_region]
    if selected_road_type != "All":
        filtered_holdout = filtered_holdout[filtered_holdout["road_type"] == selected_road_type]
    if isinstance(selected_dates, tuple | list) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
        filtered_holdout = filtered_holdout[
            (filtered_holdout["date"] >= start_date) & (filtered_holdout["date"] <= end_date)
        ]

filtered_scenario_opportunities = scenario_top_opportunities.copy()
if not filtered_scenario_opportunities.empty:
    if selected_region != "All":
        filtered_scenario_opportunities = filtered_scenario_opportunities[
            filtered_scenario_opportunities["region"] == selected_region
        ]
    if selected_road_type != "All":
        filtered_scenario_opportunities = filtered_scenario_opportunities[
            filtered_scenario_opportunities["road_type"] == selected_road_type
        ]
    if isinstance(selected_dates, tuple | list) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
        filtered_scenario_opportunities = filtered_scenario_opportunities[
            (filtered_scenario_opportunities["date"] >= start_date)
            & (filtered_scenario_opportunities["date"] <= end_date)
        ]

filtered_scenario_region_impact = scenario_region_impact.copy()
if not filtered_scenario_region_impact.empty and selected_region != "All":
    filtered_scenario_region_impact = filtered_scenario_region_impact[
        filtered_scenario_region_impact["region"] == selected_region
    ]

hotspots = build_hotspots(filtered)
weekly = build_weekly_trend(filtered)

total_accidents = len(filtered)
fatalities = int(filtered["fatalities"].sum())
injuries = int(filtered["injuries"].sum())
severe_count = int(filtered["severity"].isin(["Severe", "Fatal"]).sum())
severe_rate = (severe_count / total_accidents) if total_accidents else 0.0

quality_gate_line = next(
    (line for line in quality_report.splitlines() if "Overall gate" in line),
    "- Overall gate: unknown",
)
dq_gate_value = quality_gate_line.split("**")[1] if "**" in quality_gate_line else "unknown"
best_scenario = scenario_summary.sort_values(
    ["avg_risk_reduction", "high_risk_road_days_reduced"],
    ascending=False,
).iloc[0]["scenario"]
successful_steps = sum(step.get("status") == "SUCCESS" for step in run_summary.get("steps", []))
latest_run_duration = sum(
    float(step.get("duration_seconds") or 0.0) for step in run_summary.get("steps", [])
)
top_region = (
    filtered.groupby("region", as_index=False)
    .agg(accidents=("incident_id", "count"))
    .sort_values("accidents", ascending=False)
    .iloc[0]["region"]
    if not filtered.empty
    else "n/a"
)
top_hotspot = hotspots.iloc[0]["road_id"] if not hotspots.empty else "n/a"

metric_cols = st.columns(6)
metric_cols[0].metric("Accidents", f"{total_accidents:,}")
metric_cols[1].metric("Fatalities", f"{fatalities:,}")
metric_cols[2].metric("Injuries", f"{injuries:,}")
metric_cols[3].metric("Severe Rate", f"{severe_rate:.1%}")
metric_cols[4].metric("DQ Gate", dq_gate_value)
metric_cols[5].metric("Best Action", best_scenario)

(
    tab_overview,
    tab_hotspots,
    tab_diagnostics,
    tab_actions,
    tab_quality,
    tab_model,
    tab_ai,
    tab_delivery,
) = st.tabs(
    [
        "Overview",
        "Hotspots",
        "Diagnostics",
        "Interventions",
        "Quality",
        "Model",
        "AI Analyst",
        "Power BI & Governance",
    ]
)

with tab_overview:
    if filtered.empty:
        st.warning("No incidents match the current filters.")
    else:
        left, right = st.columns([1.5, 1])

        with left:
            st.subheader("Weekly trend")
            trend_chart = (
                alt.Chart(weekly)
                .transform_fold(["accidents", "severe", "fatalities"], as_=["metric", "value"])
                .mark_line(point=True, strokeWidth=3)
                .encode(
                    x=alt.X("week:N", sort=None, title="Week"),
                    y=alt.Y("value:Q", title="Count"),
                    color=alt.Color(
                        "metric:N",
                        scale=alt.Scale(
                            domain=["accidents", "severe", "fatalities"],
                            range=["#1f5c56", "#a5402d", "#13212c"],
                        ),
                    ),
                    tooltip=[
                        alt.Tooltip("week:N", title="Week"),
                        alt.Tooltip("metric:N", title="Metric"),
                        alt.Tooltip("value:Q", title="Count"),
                    ],
                )
                .properties(height=360)
            )
            st.altair_chart(trend_chart, width="stretch")

        with right:
            st.subheader("Severity mix")
            severity_mix = (
                filtered["severity"]
                .value_counts()
                .rename_axis("severity")
                .reset_index(name="count")
            )
            severity_chart = (
                alt.Chart(severity_mix)
                .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
                .encode(
                    x=alt.X("severity:N", sort="-y", title="Severity"),
                    y=alt.Y("count:Q", title="Incidents"),
                    color=alt.Color(
                        "severity:N",
                        scale=alt.Scale(
                            domain=["Minor", "Moderate", "Severe", "Fatal"],
                            range=["#d9c9a0", "#c57d56", "#a5402d", "#5a1f1a"],
                        ),
                        legend=None,
                    ),
                    tooltip=[
                        alt.Tooltip("severity:N", title="Severity"),
                        alt.Tooltip("count:Q", title="Count"),
                    ],
                )
                .properties(height=360)
            )
            st.altair_chart(severity_chart, width="stretch")

        st.subheader("Region summary")
        region_summary = (
            filtered.groupby("region", as_index=False)
            .agg(
                accidents=("incident_id", "count"),
                severe=("severity", lambda s: int(s.isin(["Severe", "Fatal"]).sum())),
                fatalities=("fatalities", "sum"),
            )
            .sort_values(["fatalities", "accidents"], ascending=False)
        )
        region_summary["severe_rate"] = (
            region_summary["severe"] / region_summary["accidents"]
        ).fillna(0.0)
        st.dataframe(region_summary, width="stretch", hide_index=True)

        action_highlight = scenario_summary.sort_values(
            ["avg_risk_reduction", "high_risk_road_days_reduced"],
            ascending=False,
        ).iloc[0]
        st.info(
            f"Recommended package: {action_highlight['scenario']} | "
            f"avg predicted risk reduction {action_highlight['avg_risk_reduction']:.4f} | "
            f"high-risk road-days reduced {int(action_highlight['high_risk_road_days_reduced'])}"
        )
        st.caption(
            f"Latest pipeline run: {run_summary.get('status', 'unknown')} | "
            f"{successful_steps}/{len(run_summary.get('steps', []))} steps successful | "
            f"{latest_run_duration:.1f}s total runtime"
        )

    with st.expander("Executive narrative", expanded=False):
        st.markdown(executive_report)

with tab_hotspots:
    st.subheader("Operational hotspot ranking")
    hotspot_view = hotspots[hotspots["accidents"] >= 20].sort_values(
        ["severe_rate", "fatalities"], ascending=False
    )
    bubble = (
        alt.Chart(hotspot_view.head(25))
        .mark_circle(opacity=0.78, stroke="#13212c", strokeWidth=0.6)
        .encode(
            x=alt.X("accidents:Q", title="Accidents"),
            y=alt.Y("severe_rate:Q", title="Severe rate"),
            size=alt.Size("fatalities:Q", title="Fatalities"),
            color=alt.Color(
                "road_type:N", scale=alt.Scale(range=["#1f5c56", "#a5402d", "#d9c9a0"])
            ),
            tooltip=[
                alt.Tooltip("road_id:N", title="Road"),
                alt.Tooltip("region:N", title="Region"),
                alt.Tooltip("city:N", title="City"),
                alt.Tooltip("road_type:N", title="Road Type"),
                alt.Tooltip("accidents:Q", title="Accidents"),
                alt.Tooltip("severe:Q", title="Severe"),
                alt.Tooltip("fatalities:Q", title="Fatalities"),
                alt.Tooltip("severe_rate:Q", title="Severe Rate", format=".2%"),
            ],
        )
        .properties(height=420)
    )
    st.altair_chart(bubble, width="stretch")
    st.dataframe(hotspot_view.head(15), width="stretch", hide_index=True)

with tab_diagnostics:
    st.subheader("Diagnostic / root-cause style view")
    left, right = st.columns([1.1, 0.9])
    with left:
        if {"region", "violations_per_1000_volume", "severe_rate", "daily_volume"}.issubset(
            filtered_model_df.columns
        ):
            diag_region = (
                filtered_model_df.groupby("region", as_index=False)
                .agg(
                    road_days=("road_id", "count"),
                    avg_severe_rate=("severe_rate", "mean"),
                    avg_violations_per_1000_volume=("violations_per_1000_volume", "mean"),
                    avg_daily_volume=("daily_volume", "mean"),
                )
                .sort_values("avg_severe_rate", ascending=False)
            )
            diag_chart = (
                alt.Chart(diag_region)
                .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
                .encode(
                    x=alt.X("region:N", sort="-y", title="Region"),
                    y=alt.Y("avg_severe_rate:Q", title="Average severe rate"),
                    color=alt.Color(
                        "avg_violations_per_1000_volume:Q", scale=alt.Scale(scheme="oranges")
                    ),
                    tooltip=[
                        alt.Tooltip("region:N", title="Region"),
                        alt.Tooltip("road_days:Q", title="Road-days"),
                        alt.Tooltip("avg_severe_rate:Q", title="Avg Severe Rate", format=".2%"),
                        alt.Tooltip(
                            "avg_violations_per_1000_volume:Q",
                            title="Violations / 1000 Volume",
                            format=".2f",
                        ),
                        alt.Tooltip("avg_daily_volume:Q", title="Avg Daily Volume", format=".1f"),
                    ],
                )
                .properties(height=360)
            )
            st.altair_chart(diag_chart, width="stretch")
    with right:
        st.markdown(diagnostic_report)

with tab_actions:
    st.subheader("Intervention planning")
    top_row_left, top_row_right = st.columns([1.1, 0.9])
    with top_row_left:
        scenario_chart = (
            alt.Chart(scenario_summary)
            .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
            .encode(
                x=alt.X("scenario:N", sort="-y", title="Scenario"),
                y=alt.Y("avg_risk_reduction:Q", title="Average predicted risk reduction"),
                color=alt.Color("high_risk_road_days_reduced:Q", scale=alt.Scale(scheme="teals")),
                tooltip=[
                    alt.Tooltip("scenario:N", title="Scenario"),
                    alt.Tooltip("avg_risk_reduction:Q", title="Avg Risk Reduction", format=".4f"),
                    alt.Tooltip(
                        "high_risk_road_days_reduced:Q", title="High-Risk Road-Days Reduced"
                    ),
                    alt.Tooltip("high_risk_reduction_rate:Q", title="Reduction Rate", format=".2%"),
                ],
            )
            .properties(height=360)
        )
        st.altair_chart(scenario_chart, width="stretch")
    with top_row_right:
        scenario_options = scenario_summary["scenario"].tolist()
        selected_scenario = st.selectbox("Scenario package", scenario_options)
        scenario_card = scenario_summary[scenario_summary["scenario"] == selected_scenario].iloc[0]
        st.metric("Avg risk reduction", f"{scenario_card['avg_risk_reduction']:.4f}")
        st.metric(
            "High-risk road-days reduced", f"{int(scenario_card['high_risk_road_days_reduced'])}"
        )
        st.metric("Reduction rate", f"{scenario_card['high_risk_reduction_rate']:.2%}")
        st.markdown(
            "Use this view to explain what the analytics suggests as the highest-leverage action package, "
            "not just where the current hotspots are."
        )

    opportunity_view = filtered_scenario_opportunities.copy()
    if not opportunity_view.empty:
        opportunity_view = opportunity_view[opportunity_view["scenario"] == selected_scenario]
    region_impact_view = filtered_scenario_region_impact.copy()
    if not region_impact_view.empty:
        region_impact_view = region_impact_view[region_impact_view["scenario"] == selected_scenario]

    lower_left, lower_right = st.columns([1.15, 0.85])
    with lower_left:
        st.markdown("### Highest-leverage road-days")
        if opportunity_view.empty:
            st.info("No scenario opportunities match the current filters.")
        else:
            st.dataframe(
                opportunity_view.head(15),
                width="stretch",
                hide_index=True,
            )
    with lower_right:
        st.markdown("### Regional impact")
        if region_impact_view.empty:
            st.info("No regional impact rows match the current filters.")
        else:
            st.dataframe(region_impact_view, width="stretch", hide_index=True)

    with st.expander("Scenario analysis report", expanded=False):
        st.markdown(scenario_report)

with tab_quality:
    st.subheader("Governed analytics controls")
    q1, q2 = st.columns([1, 1])
    with q1:
        st.markdown(quality_report)
    with q2:
        st.markdown("### Traceability sample")
        traceability_cols = [
            col
            for col in ["incident_id", "road_id", "source_system", "ingest_batch_id", "record_hash"]
            if col in accidents.columns
        ]
        st.dataframe(accidents[traceability_cols].head(12), width="stretch", hide_index=True)
        st.markdown("### Source coverage")
        source_summary = pd.DataFrame(
            {
                "domain": ["Road registry", "Accident reports", "Road-day model dataset"],
                "row_count": [
                    roads["road_id"].nunique(),
                    accidents["incident_id"].nunique(),
                    model_df.shape[0],
                ],
            }
        )
        st.dataframe(source_summary, width="stretch", hide_index=True)
        if solution_overview:
            st.markdown("### Solution overview")
            st.markdown(solution_overview)

with tab_model:
    st.subheader("Predictive prioritization")
    if filtered_holdout.empty:
        st.info("Run the model step to generate holdout predictions.")
    else:
        top_risks = filtered_holdout.sort_values("predicted_risk", ascending=False).head(15)
        risk_distribution = (
            filtered_holdout.groupby("risk_band", as_index=False)
            .size()
            .rename(columns={"size": "road_days"})
            .sort_values("road_days", ascending=False)
        )
        left, right = st.columns([1.2, 1])
        with left:
            st.markdown("### Highest-risk road-days")
            st.dataframe(top_risks, width="stretch", hide_index=True)
        with right:
            risk_chart = (
                alt.Chart(risk_distribution)
                .mark_arc(innerRadius=60)
                .encode(
                    theta="road_days:Q",
                    color=alt.Color(
                        "risk_band:N",
                        scale=alt.Scale(
                            domain=["Critical", "High", "Medium", "Low"],
                            range=["#a5402d", "#c57d56", "#d9c9a0", "#1f5c56"],
                        ),
                    ),
                    tooltip=[
                        alt.Tooltip("risk_band:N", title="Risk Band"),
                        alt.Tooltip("road_days:Q", title="Road-days"),
                    ],
                )
                .properties(height=340)
            )
            st.altair_chart(risk_chart, width="stretch")
    with st.expander("Model report", expanded=False):
        st.markdown(model_report)

with tab_ai:
    st.subheader("AI Analyst")
    st.caption(
        "Fail-closed mode: if gateway is unavailable or disabled, deterministic offline insights are returned."
    )
    st.caption(f"Configured provider: {settings.llm_provider}")

    prompt = st.text_area(
        "Question to analyst",
        value="Provide the top 3 risks and the top 3 actions for the next 24 hours.",
        height=120,
    )
    if st.button("Generate Analyst Brief", type="primary"):
        snapshot = build_snapshot(
            top_region=str(top_region),
            severe_rate=float(severe_rate),
            top_hotspot=str(top_hotspot),
            accidents=int(total_accidents),
            fatalities=int(fatalities),
            injuries=int(injuries),
            dq_gate=str(dq_gate_value),
        )
        result = generate_analyst_insight(prompt=prompt, snapshot=snapshot, settings=settings)
        if result.warning:
            st.warning(result.warning)
        st.code(result.text)
        st.caption(f"Provider used: {result.provider} | fallback: {result.used_fallback}")

        with st.expander("Analyst snapshot input", expanded=False):
            st.json(snapshot)

with tab_delivery:
    left, right = st.columns([1.1, 0.9])
    with left:
        st.subheader("Power BI handoff")
        run_meta = pd.DataFrame(
            [
                {"attribute": "Pipeline status", "value": run_summary.get("status", "unknown")},
                {
                    "attribute": "Pipeline name",
                    "value": run_summary.get("pipeline_name", "unknown"),
                },
                {
                    "attribute": "Run started (UTC)",
                    "value": run_summary.get("run_started_at_utc", "unknown"),
                },
                {
                    "attribute": "Run finished (UTC)",
                    "value": run_summary.get("run_finished_at_utc", "unknown"),
                },
                {
                    "attribute": "Configured days",
                    "value": run_summary.get("metadata", {}).get("days", "unknown"),
                },
                {
                    "attribute": "Configured seed",
                    "value": run_summary.get("metadata", {}).get("seed", "unknown"),
                },
            ]
        )
        run_meta["value"] = run_meta["value"].astype(str)
        st.dataframe(run_meta, width="stretch", hide_index=True)
        powerbi_files = (
            sorted(path.name for path in powerbi_dir.iterdir()) if powerbi_dir.exists() else []
        )
        st.dataframe(pd.DataFrame({"asset": powerbi_files}), width="stretch", hide_index=True)
        if powerbi_notes:
            st.markdown(powerbi_notes)
        if powerbi_measures:
            st.markdown("### Suggested DAX measures")
            st.code(powerbi_measures, language="sql")
    with right:
        st.subheader("Governance notes")
        st.markdown(governance_doc)
        with st.expander("Architecture overview", expanded=False):
            st.markdown(architecture_doc)
        if data_dictionary:
            with st.expander("Data dictionary", expanded=False):
                st.markdown(data_dictionary)
