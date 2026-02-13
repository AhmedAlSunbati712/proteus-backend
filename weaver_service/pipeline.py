from __future__ import annotations

from datetime import datetime

from .catvton import CatVTONModel
from .config import Settings
from .job_schema import WeaverJob, WeaverJobDoneEvent
from .log_utils import JobContextAdapter, bind_job
from .s3_client import S3ImageStore


def _result_key(settings: Settings, job: WeaverJob) -> str:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return f"{settings.s3_result_prefix}/{job.user_id}/{job.vton_id}/{job.id}_{ts}.png"


def run_job(
    *,
    settings: Settings,
    store: S3ImageStore,
    model: CatVTONModel,
    raw_job: dict,
    logger: JobContextAdapter,
) -> WeaverJobDoneEvent:
    job = WeaverJob.model_validate(raw_job)
    job_logger = bind_job(logger, job.id, job.user_id, job.vton_id)
    job_logger.info("Processing weaver job")

    person_img = store.download_image(job.user_snap_s3)
    outfit_img = store.download_image(job.uncleaned_outfit_s3)

    output = model.infer(person_img, outfit_img)
    output_key = _result_key(settings, job)
    store.upload_png(output_key, output)

    job_logger.info("Completed weaver job")
    return WeaverJobDoneEvent(
        job_id=job.id,
        status="done",
        user_id=job.user_id,
        vton_id=job.vton_id,
        result_s3_key=output_key,
    )
