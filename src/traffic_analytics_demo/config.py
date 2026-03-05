from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Paths:
    root: Path
    data_raw: Path
    data_staged: Path
    data_curated: Path
    data_processed: Path
    out: Path
    out_powerbi: Path


@dataclass(frozen=True)
class RuntimeSettings:
    pipeline_name: str
    default_days: int
    default_seed: int
    log_level: str
    streamlit_port: int
    llm_provider: str
    llm_model: str
    llm_gateway_url: str | None
    llm_timeout_seconds: int


def _env_path(name: str, default: Path) -> Path:
    value = os.getenv(name)
    return Path(value).expanduser().resolve() if value else default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer.") from exc


def _env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    return value.strip() if value is not None else default


def get_paths() -> Paths:
    repo_root = Path(__file__).resolve().parents[2]
    data_root = _env_path("TRAFFIC_ANALYTICS_DATA_DIR", repo_root / "data")
    out_root = _env_path("TRAFFIC_ANALYTICS_OUT_DIR", repo_root / "out")
    data_raw = _env_path("TRAFFIC_ANALYTICS_RAW_DIR", data_root / "raw")
    data_staged = _env_path("TRAFFIC_ANALYTICS_STAGED_DIR", data_root / "staged")
    data_curated = _env_path("TRAFFIC_ANALYTICS_CURATED_DIR", data_root / "curated")
    data_processed = _env_path("TRAFFIC_ANALYTICS_PROCESSED_DIR", data_root / "processed")
    out_powerbi = _env_path("TRAFFIC_ANALYTICS_POWERBI_DIR", out_root / "powerbi")

    data_raw.mkdir(parents=True, exist_ok=True)
    data_staged.mkdir(parents=True, exist_ok=True)
    data_curated.mkdir(parents=True, exist_ok=True)
    data_processed.mkdir(parents=True, exist_ok=True)
    out_root.mkdir(parents=True, exist_ok=True)
    out_powerbi.mkdir(parents=True, exist_ok=True)

    return Paths(
        root=repo_root,
        data_raw=data_raw,
        data_staged=data_staged,
        data_curated=data_curated,
        data_processed=data_processed,
        out=out_root,
        out_powerbi=out_powerbi,
    )


def get_settings() -> RuntimeSettings:
    log_level = _env_str("TRAFFIC_ANALYTICS_LOG_LEVEL", "INFO").upper()
    if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError(
            "TRAFFIC_ANALYTICS_LOG_LEVEL must be one of DEBUG/INFO/WARNING/ERROR/CRITICAL."
        )

    default_days = _env_int("TRAFFIC_ANALYTICS_DEFAULT_DAYS", 120)
    if default_days <= 0:
        raise ValueError("TRAFFIC_ANALYTICS_DEFAULT_DAYS must be > 0.")

    default_seed = _env_int("TRAFFIC_ANALYTICS_DEFAULT_SEED", 42)
    if default_seed < 0:
        raise ValueError("TRAFFIC_ANALYTICS_DEFAULT_SEED must be >= 0.")

    streamlit_port = _env_int("TRAFFIC_ANALYTICS_STREAMLIT_PORT", 8501)
    if streamlit_port < 1 or streamlit_port > 65535:
        raise ValueError("TRAFFIC_ANALYTICS_STREAMLIT_PORT must be between 1 and 65535.")

    llm_provider = _env_str("TRAFFIC_ANALYTICS_LLM_PROVIDER", "mock").lower()
    if llm_provider not in {"mock", "local_gateway", "disabled"}:
        raise ValueError(
            "TRAFFIC_ANALYTICS_LLM_PROVIDER must be one of: mock, local_gateway, disabled."
        )

    llm_timeout_seconds = _env_int("TRAFFIC_ANALYTICS_LLM_TIMEOUT_SECONDS", 20)
    if llm_timeout_seconds <= 0:
        raise ValueError("TRAFFIC_ANALYTICS_LLM_TIMEOUT_SECONDS must be > 0.")

    llm_gateway_url_raw = _env_str("TRAFFIC_ANALYTICS_LLM_GATEWAY_URL", "")
    llm_gateway_url = llm_gateway_url_raw or None

    return RuntimeSettings(
        pipeline_name=_env_str("TRAFFIC_ANALYTICS_PIPELINE_NAME", "traffic_safety_analytics"),
        default_days=default_days,
        default_seed=default_seed,
        log_level=log_level,
        streamlit_port=streamlit_port,
        llm_provider=llm_provider,
        llm_model=_env_str("TRAFFIC_ANALYTICS_LLM_MODEL", "local-analyst-v1"),
        llm_gateway_url=llm_gateway_url,
        llm_timeout_seconds=llm_timeout_seconds,
    )
