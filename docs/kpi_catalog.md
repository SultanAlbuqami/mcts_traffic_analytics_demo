# KPI Catalog

| KPI | Definition | Formula | Grain | Primary source(s) | Business use |
|---|---|---|---|---|---|
| Total Accidents | Count of accident incidents in the selected period | `COUNT(incident_id)` | Incident | Accident reports | Executive volume tracking |
| Fatalities | Total fatalities across selected incidents | `SUM(fatalities)` | Incident | Accident reports | Severity monitoring |
| Injuries | Total injuries across selected incidents | `SUM(injuries)` | Incident | Accident reports | Operational impact |
| Severe Accidents | Incidents classified as Severe or Fatal | `COUNTIF(severity in {"Severe","Fatal"})` | Incident | Accident reports | High-risk prioritization |
| Severe Rate | Share of severe incidents out of all incidents | `Severe Accidents / Total Accidents` | Incident | Accident reports | Comparison across regions/roads |
| Fatality Rate per Accident | Fatalities per incident | `Fatalities / Total Accidents` | Incident | Accident reports | Leadership KPI |
| Total Violations | Count of recorded violations | `COUNT(violation_id)` | Violation / Road-day | Violation system | Compliance and behavior signal |
| Violations per 1000 Volume | Violations normalized by traffic exposure | `(Total Violations * 1000) / Daily Volume` | Road-day | Violations + sensors | Fair comparison across roads |
| Daily Volume | Total measured vehicle volume by road-day | `SUM(volume)` | Road-day | Speed sensors | Exposure baseline |
| Avg Sensor Speed | Average observed speed by road-day | `AVG(avg_speed)` | Road-day | Speed sensors | Diagnostic signal |
| P95 Speed | 95th percentile speed by road-day | `P95(avg_speed)` | Road-day | Speed sensors | Speed risk monitoring |
| Hotspot Rank | Rank of road segments by severity-adjusted risk | Sort by `Severe Rate`, then `Fatalities` | Road | Accidents | Targeted intervention |
| Road-Day Fatality Flag Rate | Share of road-days with at least one fatality | `AVG(has_fatality)` | Road-day | Model dataset | Predictive monitoring |

## KPI Design Notes

- Executive KPIs should be paired with interpretation notes and limitations.
- Exposure-normalized KPIs are better than raw counts when comparing roads or regions.
- Every KPI in production should have an owner, refresh cadence, validation rule, and source lineage reference.
