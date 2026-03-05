from __future__ import annotations

import json
import logging
import traceback
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any, Iterator

from .utils import utc_now_iso


LOGGER_NAME = "traffic_analytics_demo"


def configure_logging(out_dir: Path, level: str = "INFO") -> logging.Logger:
    out_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(out_dir / "pipeline.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


@dataclass
class StepRecord:
    step: str
    started_at_utc: str
    ended_at_utc: str | None = None
    duration_seconds: float | None = None
    status: str = "RUNNING"
    details: dict[str, Any] = field(default_factory=dict)


class PipelineRunTracker:
    def __init__(self, output_dir: Path, pipeline_name: str, logger: logging.Logger | None = None) -> None:
        self.output_dir = output_dir
        self.pipeline_name = pipeline_name
        self.logger = logger or logging.getLogger(LOGGER_NAME)
        self.run_started_at = utc_now_iso()
        self.steps: list[StepRecord] = []
        self.metadata: dict[str, Any] = {}

    def set_metadata(self, **kwargs: Any) -> None:
        self.metadata.update(kwargs)

    @contextmanager
    def step(self, name: str, **details: Any) -> Iterator[None]:
        record = StepRecord(step=name, started_at_utc=utc_now_iso(), details=details)
        self.steps.append(record)
        started = perf_counter()
        self.logger.info("Starting step: %s", name)
        try:
            yield
        except Exception as exc:
            record.status = "FAILED"
            record.details = {**record.details, "error": str(exc), "traceback": traceback.format_exc(limit=8)}
            raise
        else:
            record.status = "SUCCESS"
        finally:
            record.ended_at_utc = utc_now_iso()
            record.duration_seconds = round(perf_counter() - started, 3)
            self.logger.info(
                "Finished step: %s | status=%s | duration=%.3fs",
                name,
                record.status,
                record.duration_seconds or 0.0,
            )

    def write_summary(self, status: str = "SUCCESS", error: str | None = None) -> Path:
        summary = {
            "pipeline_name": self.pipeline_name,
            "status": status,
            "run_started_at_utc": self.run_started_at,
            "run_finished_at_utc": utc_now_iso(),
            "metadata": self.metadata,
            "steps": [asdict(step) for step in self.steps],
        }
        if error:
            summary["error"] = error

        output_path = self.output_dir / "run_summary.json"
        output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return output_path
