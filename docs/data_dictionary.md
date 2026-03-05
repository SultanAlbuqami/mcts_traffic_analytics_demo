# Data Dictionary — Curated Layer

> **Generated:** 2026-03-05T16:52:57Z  
> **Source:** `data\curated`  
> **Data:** 100% synthetic (seed=42) — no real personal data.  
>
> **Sensitivity levels:**
> - `PUBLIC` — safe for external sharing; aggregated or anonymised.
> - `INTERNAL` — traceability / operational fields; share within team only.
> - `CONFIDENTIAL` — not present in this dataset (would require access controls).

## `accidents`

- **File:** `accidents.csv`
- **Rows:** 500
- **Columns:** 22

| Column | Type | Null % | Sensitivity | Sample Values |
|--------|------|--------|-------------|---------------|
| `incident_id` | object | 0.0% | INTERNAL | `A000000`, `A000001`, `A000002` |
| `date_time` | object | 0.0% | PUBLIC | `2026-02-28 15:10:29+00:00`, `2026-02-08 05:47:46+00:00`, `2026-02-10 10:26:56+00:00` |
| `road_id` | object | 0.0% | PUBLIC | `R0014`, `R0018`, `R0007` |
| `vehicles_involved` | int64 | 0.0% | PUBLIC | `3`, `2`, `6` |
| `injuries` | int64 | 0.0% | PUBLIC | `0`, `1`, `4` |
| `fatalities` | int64 | 0.0% | PUBLIC | `0`, `1`, `2` |
| `lighting` | object | 0.0% | PUBLIC | `Day`, `Night` |
| `severity` | object | 0.0% | PUBLIC | `Moderate`, `Fatal`, `Severe` |
| `source_system` | object | 0.0% | INTERNAL | `accident_reports` |
| `ingest_batch_id` | object | 0.0% | INTERNAL | `B20260305T000843Z` |
| `extracted_at_utc` | object | 0.0% | INTERNAL | `2026-03-05T00:08:43+00:00` |
| `record_hash` | object | 0.0% | INTERNAL | `c3efd059f908b01d`, `d78e6bc0e184deba`, `4924f0394240592e` |
| `date` | object | 0.0% | PUBLIC | `2026-02-28`, `2026-02-08`, `2026-02-10` |
| `region` | object | 0.0% | PUBLIC | `Riyadh`, `Qassim`, `Madinah` |
| `city` | object | 0.0% | PUBLIC | `Al Kharj`, `Buraidah`, `Madinah` |
| `road_type` | object | 0.0% | PUBLIC | `Highway`, `Rural`, `Urban` |
| `speed_limit` | int64 | 0.0% | PUBLIC | `100`, `80`, `60` |
| `lanes` | int64 | 0.0% | PUBLIC | `3`, `2`, `1` |
| `weather` | object | 0.0% | PUBLIC | `Dust`, `Clear`, `Rain` |
| `visibility_km` | float64 | 0.0% | PUBLIC | `3.8`, `4.7`, `10.5` |
| `precip_mm` | float64 | 0.0% | PUBLIC | `0.02`, `0.01`, `0.08` |
| `temp_c` | float64 | 0.0% | PUBLIC | `24.5`, `30.5`, `31.1` |

---

## `model_df`

- **File:** `model_df.csv`
- **Rows:** 720
- **Columns:** 30

| Column | Type | Null % | Sensitivity | Sample Values |
|--------|------|--------|-------------|---------------|
| `road_id` | object | 0.0% | PUBLIC | `R0000`, `R0001`, `R0002` |
| `date` | object | 0.0% | PUBLIC | `2026-02-03`, `2026-02-04`, `2026-02-05` |
| `daily_volume` | int64 | 0.0% | PUBLIC | `93`, `110`, `98` |
| `mean_speed` | float64 | 0.0% | PUBLIC | `84.89999999999999`, `78.3`, `91.95` |
| `p95_speed` | float64 | 0.0% | PUBLIC | `94.25`, `87.33999999999999`, `100.1` |
| `sensor_events` | int64 | 0.0% | PUBLIC | `6`, `7`, `5` |
| `PhoneUse` | float64 | 0.0% | PUBLIC | `0.0`, `2.0`, `1.0` |
| `RedLight` | float64 | 0.0% | PUBLIC | `0.0`, `1.0`, `2.0` |
| `Seatbelt` | float64 | 0.0% | PUBLIC | `1.0`, `0.0`, `2.0` |
| `Speeding` | float64 | 0.0% | PUBLIC | `1.0`, `0.0`, `2.0` |
| `UnsafeLaneChange` | float64 | 0.0% | PUBLIC | `0.0`, `1.0`, `2.0` |
| `total_violations` | float64 | 0.0% | PUBLIC | `2.0`, `3.0`, `0.0` |
| `accidents` | float64 | 0.0% | PUBLIC | `1.0`, `0.0`, `2.0` |
| `injuries` | float64 | 0.0% | PUBLIC | `2.0`, `0.0`, `1.0` |
| `fatalities` | float64 | 0.0% | PUBLIC | `0.0`, `1.0`, `2.0` |
| `severe` | float64 | 0.0% | PUBLIC | `1.0`, `0.0`, `2.0` |
| `region` | object | 0.0% | PUBLIC | `Eastern`, `Riyadh`, `Qassim` |
| `city` | object | 0.0% | PUBLIC | `Dammam`, `Riyadh`, `Buraidah` |
| `road_type` | object | 0.0% | PUBLIC | `Urban`, `Highway`, `Rural` |
| `speed_limit` | int64 | 0.0% | PUBLIC | `80`, `60`, `140` |
| `lanes` | int64 | 0.0% | PUBLIC | `2`, `5`, `3` |
| `weather_mode` | object | 0.0% | PUBLIC | `Clear`, `Dust` |
| `low_visibility_hours` | int64 | 0.0% | PUBLIC | `3`, `4`, `1` |
| `rain_hours` | int64 | 0.0% | PUBLIC | `3`, `1`, `0` |
| `fog_hours` | int64 | 0.0% | PUBLIC | `1`, `0`, `3` |
| `max_precip_mm` | float64 | 0.0% | PUBLIC | `3.99`, `2.98`, `3.4` |
| `avg_temp_c` | float64 | 0.0% | PUBLIC | `30.94347826086957`, `30.129166666666663`, `30.0875` |
| `has_fatality` | int64 | 0.0% | PUBLIC | `0`, `1` |
| `severe_rate` | float64 | 0.0% | PUBLIC | `1.0`, `0.0`, `0.5` |
| `violations_per_1000_volume` | float64 | 0.0% | PUBLIC | `21.50537634408602`, `27.272727272727277`, `0.0` |

---

## `roads`

- **File:** `roads.csv`
- **Rows:** 24
- **Columns:** 10

| Column | Type | Null % | Sensitivity | Sample Values |
|--------|------|--------|-------------|---------------|
| `road_id` | object | 0.0% | PUBLIC | `R0000`, `R0001`, `R0002` |
| `region` | object | 0.0% | PUBLIC | `Eastern`, `Riyadh`, `Qassim` |
| `city` | object | 0.0% | PUBLIC | `Dammam`, `Riyadh`, `Buraidah` |
| `road_type` | object | 0.0% | PUBLIC | `Urban`, `Highway`, `Rural` |
| `speed_limit` | int64 | 0.0% | PUBLIC | `80`, `60`, `140` |
| `lanes` | int64 | 0.0% | PUBLIC | `2`, `5`, `3` |
| `source_system` | object | 0.0% | INTERNAL | `roads_registry` |
| `ingest_batch_id` | object | 0.0% | INTERNAL | `B20260305T000843Z` |
| `extracted_at_utc` | object | 0.0% | INTERNAL | `2026-03-05T00:08:43+00:00` |
| `record_hash` | object | 0.0% | INTERNAL | `83aebf41226026b1`, `279df14a5c0aead4`, `42fddcf7f3b72ffa` |

---

## `sensors`

- **File:** `sensors.csv`
- **Rows:** 5,000
- **Columns:** 10

| Column | Type | Null % | Sensitivity | Sample Values |
|--------|------|--------|-------------|---------------|
| `sensor_id` | int64 | 0.0% | INTERNAL | `305`, `324`, `202` |
| `date_time` | object | 0.0% | PUBLIC | `2026-02-03 18:08:27+00:00`, `2026-02-03 10:53:47+00:00`, `2026-02-03 15:20:32+00:00` |
| `road_id` | object | 0.0% | PUBLIC | `R0000`, `R0001`, `R0002` |
| `volume` | int64 | 0.0% | PUBLIC | `19`, `21`, `16` |
| `avg_speed` | float64 | 0.0% | PUBLIC | `77.2`, `78.1`, `94.7` |
| `source_system` | object | 0.0% | INTERNAL | `speed_sensors` |
| `ingest_batch_id` | object | 0.0% | INTERNAL | `B20260305T000843Z` |
| `extracted_at_utc` | object | 0.0% | INTERNAL | `2026-03-05T00:08:43+00:00` |
| `record_hash` | object | 0.0% | INTERNAL | `9cae17b982bae4e7`, `377ceee413d057db`, `f486f3b7627b1014` |
| `date` | object | 0.0% | PUBLIC | `2026-02-03`, `2026-02-04`, `2026-02-05` |

---

## `violations`

- **File:** `violations.csv`
- **Rows:** 1,600
- **Columns:** 11

| Column | Type | Null % | Sensitivity | Sample Values |
|--------|------|--------|-------------|---------------|
| `violation_id` | object | 0.0% | INTERNAL | `V0000000`, `V0000001`, `V0000002` |
| `date_time` | object | 0.0% | PUBLIC | `2026-03-02 22:10:42+00:00`, `2026-03-03 07:09:21+00:00`, `2026-02-18 18:05:53+00:00` |
| `road_id` | object | 0.0% | PUBLIC | `R0010`, `R0021`, `R0015` |
| `violation_type` | object | 0.0% | PUBLIC | `Speeding`, `UnsafeLaneChange`, `Seatbelt` |
| `fine_amount` | int64 | 0.0% | PUBLIC | `690`, `380`, `552` |
| `driver_age_band` | object | 0.0% | INTERNAL | `46-60`, `26-35`, `18-25` |
| `source_system` | object | 0.0% | INTERNAL | `violation_system` |
| `ingest_batch_id` | object | 0.0% | INTERNAL | `B20260305T000843Z` |
| `extracted_at_utc` | object | 0.0% | INTERNAL | `2026-03-05T00:08:43+00:00` |
| `record_hash` | object | 0.0% | INTERNAL | `2f9079b014d5e65e`, `30377da9f07a13e2`, `880eb7b094b1ef16` |
| `date` | object | 0.0% | PUBLIC | `2026-03-02`, `2026-03-03`, `2026-02-18` |

---
