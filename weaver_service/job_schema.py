from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class WeaverJob(BaseModel):
    id: str
    user_id: str
    vton_id: str
    user_snap_s3: str
    uncleaned_outfit_s3: str
    created_at: datetime | None = None


class WeaverJobDoneEvent(BaseModel):
    job_id: str
    job_type: Literal["try_on"] = "try_on"
    status: Literal["done", "failed"]
    user_id: str
    vton_id: str
    result_s3_key: str | None = None
    error: str | None = None
    finished_at: datetime = Field(default_factory=datetime.utcnow)
