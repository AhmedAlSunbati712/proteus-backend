from __future__ import annotations

from .catvton import CatVTONModel
from common.config import load_settings
from common.log_utils import get_logger, setup_logging
from .pipeline import run_jobs
from common.redis_client import RedisClient
from common.s3_client import S3ImageStore


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
        raw_jobs = redis_client.consume_job_weaver(settings.redis_queue, timeout_seconds=5)
        if raw_jobs is None:
            continue

        done_events = run_jobs(
            settings=settings,
            store=store,
            model=model,
            raw_jobs=raw_jobs,
            logger=logger,
        )

        for done_event in done_events:
            redis_client.publish_event(
                settings.redis_events_channel,
                done_event.model_dump(mode="json"),
            )


if __name__ == "__main__":
    main()
