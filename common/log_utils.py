from __future__ import annotations

import logging as py_logging
from typing import Any


class JobContextAdapter(py_logging.LoggerAdapter):
    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        extra = kwargs.setdefault("extra", {})
        context = {
            "job_id": self.extra.get("job_id", "-"),
            "user_id": self.extra.get("user_id", "-"),
            "vton_id": self.extra.get("vton_id", "-"),
        }
        extra.update(context)
        return msg, kwargs


def setup_logging(level: str = "INFO") -> None:
    py_logging.basicConfig(
        level=getattr(py_logging, level.upper(), py_logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s job_id=%(job_id)s user_id=%(user_id)s vton_id=%(vton_id)s %(message)s",
    )


def get_logger(name: str) -> JobContextAdapter:
    logger = py_logging.getLogger(name)
    return JobContextAdapter(logger, {"job_id": "-", "user_id": "-", "vton_id": "-"})


def bind_job(logger: JobContextAdapter, job_id: str, user_id: str, vton_id: str) -> JobContextAdapter:
    return JobContextAdapter(logger.logger, {"job_id": job_id, "user_id": user_id, "vton_id": vton_id})
