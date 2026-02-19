from __future__ import annotations

from datetime import datetime

from .catvton import CatVTONModel
from common.config import Settings
from common.job_schema import WeaverJob, WeaverJobDoneEvent
from common.log_utils import JobContextAdapter, bind_job
from common.s3_client import S3ImageStore


def _result_key(settings: Settings, job: WeaverJob) -> str:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return f"{settings.s3_result_prefix}/{job.user_id}/{job.vton_id}/{job.id}_{ts}.png"


def _failed_event(raw_job: dict, error: str) -> WeaverJobDoneEvent:
    return WeaverJobDoneEvent(
        job_id=raw_job.get("id", "unknown"),
        status="failed",
        user_id=raw_job.get("user_id", "unknown"),
        vton_id=raw_job.get("vton_id", "unknown"),
        error=error,
    )


def run_jobs(
    *,
    settings: Settings,
    store: S3ImageStore,
    model: CatVTONModel,
    raw_jobs: list[dict],
    logger: JobContextAdapter,
) -> list[WeaverJobDoneEvent]:
    events: list[WeaverJobDoneEvent] = []
    valid_jobs: list[WeaverJob] = []
    person_imgs = []
    outfit_imgs = []

    for raw_job in raw_jobs:
        try:
            job = WeaverJob.model_validate(raw_job)
        except Exception as exc:  # noqa: BLE001
            events.append(_failed_event(raw_job, f"invalid_job_payload: {exc}"))
            logger.exception("Invalid weaver job payload")
            continue

        job_logger = bind_job(logger, job.id, job.user_id, job.vton_id)
        job_logger.info("Preparing weaver job")
        try:
            person_imgs.append(store.download_image(job.user_snap_s3))
            outfit_imgs.append(store.download_image(job.uncleaned_outfit_s3))
            valid_jobs.append(job)
        except Exception as exc:  # noqa: BLE001
            events.append(
                WeaverJobDoneEvent(
                    job_id=job.id,
                    status="failed",
                    user_id=job.user_id,
                    vton_id=job.vton_id,
                    error=f"image_download_failed: {exc}",
                )
            )
            job_logger.exception("Failed to download job inputs")

    if not valid_jobs:
        return events

    try:
        outputs = model.infer_batch(person_imgs, outfit_imgs)
    except Exception as exc:  # noqa: BLE001
        for job in valid_jobs:
            events.append(
                WeaverJobDoneEvent(
                    job_id=job.id,
                    status="failed",
                    user_id=job.user_id,
                    vton_id=job.vton_id,
                    error=f"batch_inference_failed: {exc}",
                )
            )
        logger.exception("Batch inference failed")
        return events
    if len(outputs) != len(valid_jobs):
        err = f"batch_output_mismatch: expected {len(valid_jobs)} got {len(outputs)}"
        logger.error(err)
        for job in valid_jobs:
            events.append(
                WeaverJobDoneEvent(
                    job_id=job.id,
                    status="failed",
                    user_id=job.user_id,
                    vton_id=job.vton_id,
                    error=err,
                )
            )
        return events

    for job, output in zip(valid_jobs, outputs):
        job_logger = bind_job(logger, job.id, job.user_id, job.vton_id)
        try:
            output_key = _result_key(settings, job)
            store.upload_png(output_key, output)
            events.append(
                WeaverJobDoneEvent(
                    job_id=job.id,
                    status="done",
                    user_id=job.user_id,
                    vton_id=job.vton_id,
                    result_s3_key=output_key,
                )
            )
            job_logger.info("Completed weaver job")
        except Exception as exc:  # noqa: BLE001
            events.append(
                WeaverJobDoneEvent(
                    job_id=job.id,
                    status="failed",
                    user_id=job.user_id,
                    vton_id=job.vton_id,
                    error=f"upload_failed: {exc}",
                )
            )
            job_logger.exception("Failed to upload output image")

    return events
