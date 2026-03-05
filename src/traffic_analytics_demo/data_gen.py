from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from .utils import utc_now_iso

REGIONS = ["Riyadh", "Makkah", "Eastern", "Madinah", "Qassim", "Asir"]
CITIES = {
    "Riyadh": ["Riyadh", "Al Kharj"],
    "Makkah": ["Jeddah", "Makkah"],
    "Eastern": ["Dammam", "Khobar"],
    "Madinah": ["Madinah"],
    "Qassim": ["Buraidah"],
    "Asir": ["Abha"],
}
ROAD_TYPES = ["Highway", "Urban", "Rural"]
VIOLATION_TYPES = ["Speeding", "RedLight", "Seatbelt", "PhoneUse", "UnsafeLaneChange"]
WEATHER = ["Clear", "Dust", "Rain", "Fog"]
WEATHER_PROBABILITIES = {
    "Riyadh": [0.74, 0.15, 0.06, 0.05],
    "Makkah": [0.76, 0.10, 0.08, 0.06],
    "Eastern": [0.70, 0.17, 0.08, 0.05],
    "Madinah": [0.75, 0.12, 0.07, 0.06],
    "Qassim": [0.72, 0.16, 0.06, 0.06],
    "Asir": [0.60, 0.08, 0.20, 0.12],
}
ROAD_TYPE_BASE_VOLUME = {"Highway": 150, "Urban": 88, "Rural": 42}
ROAD_TYPE_SPEED_MARGIN = {"Highway": 11.0, "Urban": 3.0, "Rural": 6.0}
REGION_VOLUME_FACTOR = {"Riyadh": 1.18, "Makkah": 1.12, "Eastern": 1.06, "Madinah": 0.95, "Qassim": 0.82, "Asir": 0.78}
SENSOR_HOUR_WEIGHTS = np.array(
    [
        0.012,
        0.010,
        0.009,
        0.008,
        0.010,
        0.018,
        0.040,
        0.070,
        0.078,
        0.058,
        0.044,
        0.040,
        0.042,
        0.044,
        0.048,
        0.058,
        0.074,
        0.082,
        0.074,
        0.060,
        0.046,
        0.034,
        0.022,
        0.017,
    ]
)
ACCIDENT_HOUR_WEIGHTS = np.array(
    [
        0.028,
        0.024,
        0.020,
        0.018,
        0.018,
        0.022,
        0.030,
        0.040,
        0.046,
        0.044,
        0.040,
        0.040,
        0.044,
        0.046,
        0.048,
        0.052,
        0.058,
        0.064,
        0.070,
        0.078,
        0.072,
        0.056,
        0.040,
        0.032,
    ]
)
DAY_HOURS = np.array([6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17])
NIGHT_HOURS = np.array([18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5])


@dataclass(frozen=True)
class GenConfig:
    days: int = 120
    seed: int = 42
    road_segments: int = 120
    accidents: int = 4000
    violations: int = 15000
    sensors_rows: int = 60000
def _scaled_integer_counts(raw_values: np.ndarray, target_total: int, min_value: int = 1) -> np.ndarray:
    values = np.asarray(raw_values, dtype=float)
    if values.size == 0:
        return np.array([], dtype=int)

    if target_total < min_value * values.size:
        min_value = 0

    clipped = np.clip(values, 1e-6, None)
    weighted = clipped / clipped.sum() * target_total
    counts = np.floor(weighted).astype(int)
    counts = np.maximum(counts, min_value)

    diff = int(target_total - counts.sum())
    if diff > 0:
        remainders = weighted - np.floor(weighted)
        order = np.argsort(-remainders)
        for idx in order[:diff]:
            counts[idx] += 1
    elif diff < 0:
        order = np.argsort(-counts)
        remaining = -diff
        for idx in order:
            if remaining <= 0:
                break
            reducible = counts[idx] - min_value
            if reducible <= 0:
                continue
            step = min(reducible, remaining)
            counts[idx] -= step
            remaining -= step

    return counts


def _sample_datetimes_for_date(
    date_value: object,
    n: int,
    rng: np.random.Generator,
    hour_weights: np.ndarray,
) -> list[pd.Timestamp]:
    base = pd.Timestamp(date_value).tz_localize("UTC")
    hours = rng.choice(np.arange(24), size=n, p=hour_weights / hour_weights.sum())
    minutes = rng.integers(0, 60, size=n)
    seconds = rng.integers(0, 60, size=n)
    return [
        base + pd.Timedelta(hours=int(hour), minutes=int(minute), seconds=int(second))
        for hour, minute, second in zip(hours, minutes, seconds)
    ]


def _sample_accident_timestamp(
    date_value: object,
    rng: np.random.Generator,
    night_bias: float,
) -> pd.Timestamp:
    bias = float(np.clip(night_bias, 0.0, 0.85))
    if rng.random() < (0.32 + bias):
        hour = int(rng.choice(NIGHT_HOURS))
    else:
        hour = int(rng.choice(DAY_HOURS))
    minute = int(rng.integers(0, 60))
    second = int(rng.integers(0, 60))
    return pd.Timestamp(date_value).tz_localize("UTC") + pd.Timedelta(hours=hour, minutes=minute, seconds=second)


def _weather_visibility(weather: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    base_visibility = np.select(
        [weather == "Dust", weather == "Rain", weather == "Fog"],
        [rng.normal(4.2, 1.0, size=weather.size), rng.normal(6.8, 1.1, size=weather.size), rng.normal(2.4, 0.7, size=weather.size)],
        default=rng.normal(10.0, 1.0, size=weather.size),
    )
    return np.clip(base_visibility, 0.5, 12).round(1)


def _weather_precip(weather: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    base_precip = np.select(
        [weather == "Rain", weather == "Fog"],
        [rng.gamma(1.8, 1.8, size=weather.size), rng.gamma(0.7, 0.5, size=weather.size)],
        default=rng.gamma(0.5, 0.15, size=weather.size),
    )
    return np.clip(base_precip, 0, 25).round(2)


def _weather_temperature(region: str, weather: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    regional_base = 31 if region in ["Riyadh", "Makkah", "Eastern"] else 24
    cooling = np.select([weather == "Rain", weather == "Fog"], [3.5, 2.5], default=0.0)
    temps = rng.normal(regional_base, 5.5, size=weather.size) - cooling
    return np.clip(temps, 5, 48).round(1)


def _aggregate_weather_daily(df_weather: pd.DataFrame) -> pd.DataFrame:
    return (
        df_weather.assign(date=df_weather["date_time"].dt.date)
        .groupby(["region", "city", "date"], as_index=False)
        .agg(
            weather_mode=("weather", lambda s: s.mode(dropna=True).iloc[0] if not s.mode(dropna=True).empty else "Clear"),
            low_visibility_hours=("visibility_km", lambda s: int((s < 4).sum())),
            rain_hours=("weather", lambda s: int((s == "Rain").sum())),
            fog_hours=("weather", lambda s: int((s == "Fog").sum())),
            max_precip_mm=("precip_mm", "max"),
            avg_temp_c=("temp_c", "mean"),
        )
    )


def generate_all(out_dir: Path, cfg: GenConfig = GenConfig()) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(cfg.seed)
    random.seed(cfg.seed)

    now = datetime.now(UTC)
    start = now - timedelta(days=cfg.days)
    end = now

    roads = []
    for i in range(cfg.road_segments):
        region = random.choice(REGIONS)
        city = random.choice(CITIES[region])
        road_type = random.choice(ROAD_TYPES)
        speed_limit = random.choice([60, 80, 100, 120, 140]) if road_type == "Highway" else random.choice([40, 60, 80])
        lanes = random.choice([2, 3, 4, 5]) if road_type != "Rural" else random.choice([1, 2])
        roads.append(
            {
                "road_id": f"R{i:04d}",
                "region": region,
                "city": city,
                "road_type": road_type,
                "speed_limit": speed_limit,
                "lanes": lanes,
            }
        )
    df_roads = pd.DataFrame(roads)
    road_profiles = df_roads[["road_id"]].copy()
    road_profiles["behavior_factor"] = rng.normal(0, 1, size=len(df_roads))
    road_profiles["exposure_factor"] = np.clip(rng.normal(1.0, 0.14, size=len(df_roads)), 0.70, 1.35)

    weather_rows = []
    hours = int(cfg.days * 24)
    base_times = pd.date_range(end=pd.Timestamp.now(tz="UTC"), periods=hours, freq="h", tz="UTC")
    for region in REGIONS:
        for city in CITIES[region]:
            w = rng.choice(WEATHER, size=hours, p=WEATHER_PROBABILITIES[region])
            visibility = _weather_visibility(w, rng)
            precip = _weather_precip(w, rng)
            temp = _weather_temperature(region, w, rng)
            weather_rows.append(
                pd.DataFrame(
                    {
                        "date_time": base_times,
                        "region": region,
                        "city": city,
                        "weather": w,
                        "visibility_km": visibility.round(1),
                        "precip_mm": precip.round(2),
                        "temp_c": temp.round(1),
                    }
                )
            )
    df_weather = pd.concat(weather_rows, ignore_index=True)
    weather_daily = _aggregate_weather_daily(df_weather)

    road_dates = pd.DataFrame(
        {
            "date": pd.date_range(
                start=pd.Timestamp(start.date(), tz="UTC"),
                periods=cfg.days,
                freq="D",
                tz="UTC",
            ).date
        }
    )
    road_days = df_roads.assign(_join_key=1).merge(road_dates.assign(_join_key=1), on="_join_key").drop(columns="_join_key")
    road_days = road_days.merge(road_profiles, on="road_id", how="left").merge(
        weather_daily,
        on=["region", "city", "date"],
        how="left",
    )
    road_days["weather_mode"] = road_days["weather_mode"].fillna("Clear")
    for col in ["low_visibility_hours", "rain_hours", "fog_hours", "max_precip_mm"]:
        road_days[col] = road_days[col].fillna(0)
    road_days["avg_temp_c"] = road_days["avg_temp_c"].fillna(28.0)

    day_index = pd.to_datetime(road_days["date"])
    weekend_factor = np.where(day_index.dt.dayofweek.isin([4, 5]), 0.90, 1.00)
    weather_volume_factor = road_days["weather_mode"].map({"Clear": 1.00, "Dust": 0.94, "Rain": 0.88, "Fog": 0.84}).fillna(1.0)
    weather_speed_penalty = road_days["weather_mode"].map({"Clear": 0.0, "Dust": 4.0, "Rain": 8.0, "Fog": 12.0}).fillna(0.0)
    road_type_risk = road_days["road_type"].map({"Highway": 0.30, "Urban": 0.18, "Rural": 0.24}).fillna(0.18)

    base_volume = road_days["road_type"].map(ROAD_TYPE_BASE_VOLUME) * road_days["region"].map(REGION_VOLUME_FACTOR)
    lanes_factor = 1 + ((road_days["lanes"].astype(float) - 2) * 0.07)
    volume_noise = np.clip(rng.normal(1.0, 0.12, size=len(road_days)), 0.75, 1.30)
    daily_volume_target = base_volume * lanes_factor * road_days["exposure_factor"] * weekend_factor * weather_volume_factor * volume_noise
    road_days["daily_volume_target"] = np.clip(daily_volume_target.round(), 18, 240)

    congestion_penalty = np.clip((road_days["daily_volume_target"] - road_days["daily_volume_target"].median()) / 28, 0, 10)
    speed_margin = road_days["road_type"].map(ROAD_TYPE_SPEED_MARGIN) + (road_days["behavior_factor"] * 4.0)
    mean_speed_target = road_days["speed_limit"].astype(float) + speed_margin - weather_speed_penalty - congestion_penalty + rng.normal(0, 5.5, size=len(road_days))
    road_days["mean_speed_target"] = np.clip(mean_speed_target, 18, 170)
    speed_tail = np.clip(10 + (road_days["behavior_factor"] * 2.0) + rng.normal(0, 3.0, size=len(road_days)), 5, 22)
    road_days["p95_speed_target"] = np.clip(road_days["mean_speed_target"] + speed_tail, road_days["mean_speed_target"] + 2, 185)

    raw_sensor_counts = road_days["daily_volume_target"] * road_days["road_type"].map({"Highway": 0.62, "Urban": 0.48, "Rural": 0.36})
    road_days["sensor_events_target"] = _scaled_integer_counts(raw_sensor_counts.to_numpy(), cfg.sensors_rows, min_value=1)

    sensor_rows: list[dict[str, object]] = []
    for row in road_days.itertuples(index=False):
        sensor_events = int(row.sensor_events_target)
        total_volume = max(sensor_events, int(round(float(row.daily_volume_target))))
        event_volumes = rng.multinomial(total_volume, np.repeat(1 / sensor_events, sensor_events))
        event_speeds = np.clip(
            rng.normal(
                float(row.mean_speed_target),
                max(5.5, float(row.p95_speed_target - row.mean_speed_target) / 1.2),
                size=sensor_events,
            ),
            10,
            185,
        ).round(1)
        event_times = _sample_datetimes_for_date(row.date, sensor_events, rng, SENSOR_HOUR_WEIGHTS)
        for event_idx in range(sensor_events):
            sensor_rows.append(
                {
                    "sensor_id": int(rng.integers(1, 350)),
                    "date_time": event_times[event_idx],
                    "road_id": row.road_id,
                    "volume": int(event_volumes[event_idx]),
                    "avg_speed": float(event_speeds[event_idx]),
                }
            )
    df_sensors = pd.DataFrame(sensor_rows)

    overspeed_excess = np.clip(road_days["p95_speed_target"] - road_days["speed_limit"].astype(float), 0, None)
    violation_pressure = (
        0.10
        + (overspeed_excess / 20.0)
        + (road_days["daily_volume_target"] / road_days["daily_volume_target"].median()) * 0.28
        + road_days["behavior_factor"].clip(-1.0, 1.5) * 0.10
        + (road_days["road_type"].eq("Urban").astype(float) * 0.12)
    )
    violation_weights = np.clip(violation_pressure.to_numpy(dtype=float), 0.01, None)
    violation_weights = violation_weights / violation_weights.sum()
    selected_violation_rows = rng.choice(road_days.index.to_numpy(), size=cfg.violations, replace=True, p=violation_weights)

    violation_count_by_idx = pd.Series(selected_violation_rows).value_counts().to_dict()
    road_days["simulated_violation_count"] = road_days.index.map(lambda idx: int(violation_count_by_idx.get(idx, 0)))
    road_days["simulated_violations_per_1000_volume"] = (
        road_days["simulated_violation_count"] * 1000 / road_days["daily_volume_target"].replace(0, np.nan)
    ).fillna(0.0)

    violation_rows: list[dict[str, object]] = []
    fine_base = {"Speeding": 600, "RedLight": 900, "Seatbelt": 220, "PhoneUse": 320, "UnsafeLaneChange": 450}
    age_bands = ["<18", "18-25", "26-35", "36-45", "46-60", "60+"]
    age_probs = [0.02, 0.24, 0.30, 0.20, 0.18, 0.06]
    for i, idx in enumerate(selected_violation_rows):
        row = road_days.iloc[int(idx)]
        overspeed_ratio = float(np.clip((row["p95_speed_target"] - row["speed_limit"]) / max(row["speed_limit"], 1), 0, 0.7))
        violation_probs = np.array(
            [
                0.35 + (0.55 * overspeed_ratio),
                0.08 + (0.08 if row["road_type"] == "Urban" else 0.02),
                0.14,
                0.17,
                0.10 + (0.04 if row["road_type"] != "Rural" else 0.01),
            ]
        )
        violation_probs = violation_probs / violation_probs.sum()
        violation_type = str(rng.choice(VIOLATION_TYPES, p=violation_probs))
        violation_rows.append(
            {
                "violation_id": f"V{i:07d}",
                "date_time": _sample_datetimes_for_date(row["date"], 1, rng, SENSOR_HOUR_WEIGHTS)[0],
                "road_id": row["road_id"],
                "violation_type": violation_type,
                "fine_amount": int(np.clip(rng.normal(fine_base[violation_type], fine_base[violation_type] * 0.18), 100, 2200)),
                "driver_age_band": str(rng.choice(age_bands, p=age_probs)),
            }
        )
    df_vio = pd.DataFrame(violation_rows)

    weather_risk = road_days["weather_mode"].map({"Clear": 0.00, "Dust": 0.20, "Rain": 0.38, "Fog": 0.52}).fillna(0.0)
    overspeed_norm = np.clip(overspeed_excess / 35.0, 0, 1.4)
    volume_norm = road_days["daily_volume_target"] / road_days["daily_volume_target"].quantile(0.95)
    violation_norm = road_days["simulated_violations_per_1000_volume"] / max(
        float(road_days["simulated_violations_per_1000_volume"].quantile(0.95)),
        1.0,
    )
    visibility_norm = np.clip(road_days["low_visibility_hours"] / 4.0, 0, 1.5)
    lane_risk = np.where(road_days["lanes"].astype(int) <= 2, 0.11, 0.04)
    behavior_norm = np.clip((road_days["behavior_factor"] + 2.0) / 4.0, 0, 1.0)

    accident_pressure = (
        0.10
        + (overspeed_norm * 0.23)
        + (violation_norm * 0.18)
        + (weather_risk * 0.16)
        + (road_type_risk * 0.14)
        + (volume_norm.clip(0, 1.6) * 0.10)
        + (visibility_norm * 0.09)
        + (lane_risk * 0.08)
        + (behavior_norm * 0.12)
        + rng.normal(0, 0.025, size=len(road_days))
    )
    accident_weights = np.clip(accident_pressure.to_numpy(dtype=float), 0.01, None)
    accident_weights = accident_weights / accident_weights.sum()
    selected_accident_rows = rng.choice(road_days.index.to_numpy(), size=cfg.accidents, replace=True, p=accident_weights)

    accident_rows: list[dict[str, object]] = []
    severity_scores: list[float] = []
    for i, idx in enumerate(selected_accident_rows):
        row = road_days.iloc[int(idx)]
        row_risk = float(accident_pressure[int(idx)])
        night_bias = float(np.clip((weather_risk.iloc[int(idx)] * 0.45) + (road_type_risk.iloc[int(idx)] * 0.18), 0.0, 0.42))
        date_time = _sample_accident_timestamp(row["date"], rng, night_bias=night_bias)
        lighting = "Night" if (date_time.hour >= 18 or date_time.hour < 6) else "Day"
        vehicles_involved = int(np.clip(rng.poisson(1.3 + (row_risk * 2.2)) + 1, 1, 8))
        injuries = int(np.clip(rng.poisson(0.15 + (row_risk * 1.25) + (0.18 if lighting == "Night" else 0.0)), 0, 6))
        fatality_prob = float(
            np.clip(
                0.005
                + (row_risk * 0.08)
                + (0.020 if lighting == "Night" else 0.0)
                + (0.012 if row["road_type"] in {"Highway", "Rural"} else 0.0),
                0,
                0.35,
            )
        )
        fatalities = int(np.clip(rng.binomial(1, fatality_prob) + rng.binomial(1, fatality_prob * 0.35), 0, 2))
        severity_score = (
            (row_risk * 1.35)
            + (injuries * 0.20)
            + (fatalities * 0.95)
            + (0.22 if lighting == "Night" else 0.0)
            + (vehicles_involved * 0.05)
            + rng.normal(0, 0.10)
        )
        severity_scores.append(severity_score)
        accident_rows.append(
            {
                "incident_id": f"A{i:06d}",
                "date_time": date_time,
                "road_id": row["road_id"],
                "vehicles_involved": vehicles_involved,
                "injuries": injuries,
                "fatalities": fatalities,
                "lighting": lighting,
            }
        )

    df_acc = pd.DataFrame(accident_rows)
    df_acc["severity"] = pd.cut(
        severity_scores,
        bins=[-10, 0.48, 0.98, 1.55, 10],
        labels=["Minor", "Moderate", "Severe", "Fatal"],
    ).astype(str)
    meta = {
        "generated_at_utc": utc_now_iso(),
        "generator_version": "2.0",
        "cfg": cfg.__dict__,
        "notes": "Synthetic datasets with correlated exposure, behavior, weather, violation, and accident patterns.",
    }
    (out_dir / "meta.json").write_text(pd.Series(meta).to_json(), encoding="utf-8")

    df_roads.to_csv(out_dir / "road_segments.csv", index=False)
    df_weather.to_csv(out_dir / "weather_hourly.csv", index=False)
    df_sensors.to_csv(out_dir / "speed_sensors.csv", index=False)
    df_acc.to_csv(out_dir / "accidents.csv", index=False)
    df_vio.to_csv(out_dir / "violations.csv", index=False)
