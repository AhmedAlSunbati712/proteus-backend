from __future__ import annotations

from pydantic import ValidationError

from .catvton import CatVTONModel
from .config import load_settings
from .job_schema import WeaverJobDoneEvent
from .log_utils import get_logger, setup_logging
from .pipeline import run_job
from .redis_client import RedisClient
from .s3_client import S3ImageStore


def main() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)
    logger = get_logger("weaver.main")

    redis_client = RedisClient(settings.redis_url)
    if not redis_client.ping():
        raise RuntimeError("Redis ping failed")

    store = S3ImageStore(settings)
    model = CatVTONModel(settings)
    model.load()

    logger.info(
        "Weaver worker started: queue=%s channel=%s backend=%s",
        settings.redis_queue,
        settings.redis_events_channel,
        settings.inference_backend,
    )

    while True:
        raw_job = redis_client.consume_job(settings.redis_queue, timeout_seconds=5)
        if raw_job is None:
            continue

        try:
            done_event = run_job(
                settings=settings,
                store=store,
                model=model,
                raw_job=raw_job,
                logger=logger,
            )
        except ValidationError as exc:
            done_event = WeaverJobDoneEvent(
                job_id=raw_job.get("id", "unknown"),
                status="failed",
                user_id=raw_job.get("user_id", "unknown"),
                vton_id=raw_job.get("vton_id", "unknown"),
                error=f"invalid_job_payload: {exc.errors()}",
            )
            logger.exception("Invalid weaver job payload")
        except Exception as exc:  # noqa: BLE001
            done_event = WeaverJobDoneEvent(
                job_id=raw_job.get("id", "unknown"),
                status="failed",
                user_id=raw_job.get("user_id", "unknown"),
                vton_id=raw_job.get("vton_id", "unknown"),
                error=str(exc),
            )
            logger.exception("Weaver job failed")

        redis_client.publish_event(
            settings.redis_events_channel,
            done_event.model_dump(mode="json"),
        )


if __name__ == "__main__":
    main()
