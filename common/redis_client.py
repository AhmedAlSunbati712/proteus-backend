from __future__ import annotations

import json
from typing import Any

import redis


class RedisClient:
    def __init__(self, redis_url: str) -> None:
        self._redis = redis.Redis.from_url(redis_url, decode_responses=True)

    def ping(self) -> bool:
        return bool(self._redis.ping())

    def _decode_job_payload(self, payload: str) -> dict[str, Any] | None:
        try:
            decoded = json.loads(payload)
            return decoded if isinstance(decoded, dict) else None
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _malformed_job_payload(payload: str) -> dict[str, Any]:
        return {
            "id": "unknown",
            "user_id": "unknown",
            "vton_id": "unknown",
            "raw_payload": payload,
            "malformed_payload": True,
        }

    def consume_job_weaver(
        self, queue_name: str = "queue:weaver_jobs", timeout_seconds: int = 5
    ) -> list[dict[str, Any]] | None:
        """
        Consume one or more weaver jobs.

        Behavior:
        - Block up to `timeout_seconds` waiting for the first job (BRPOP).
        - Read `config:batch_size` (default 1).
        - If batch size > 1, opportunistically pull additional jobs via non-blocking RPOP.
        """
        first_item = self._redis.brpop(queue_name, timeout=timeout_seconds)
        if first_item is None:
            return None

        _, first_payload = first_item
        first_job = self._decode_job_payload(first_payload)
        jobs: list[dict[str, Any]] = []
        if first_job is not None:
            jobs.append(first_job)
        else:
            jobs.append(self._malformed_job_payload(first_payload))

        batch_size = max(1, self.get_config_batch_size())
        remaining = batch_size - len(jobs)
        while remaining > 0:
            payload = self._redis.rpop(queue_name)
            if payload is None:
                break
            job = self._decode_job_payload(payload)
            if job is None:
                jobs.append(self._malformed_job_payload(payload))
            else:
                jobs.append(job)
            remaining -= 1

        return jobs if jobs else None
    def consume_job_tailor(self, queue_name: str = "queue:tailor_jobs", timeout_seconds: int = 5) -> dict[str, Any] | None:
        # BRPOP returns tuple: (queue_name, payload)
        item = self._redis.brpop(queue_name, timeout=timeout_seconds)
        if item is None:
            return None
        _, payload = item
        return json.loads(payload)

    def publish_event(self, channel_name: str, event: dict[str, Any]) -> int:
        return int(self._redis.publish(channel_name, json.dumps(event, default=str)))

    def get_config_batch_size(self) -> int:
        return int(self._redis.get("config:batch_size")) if self._redis.get("config:batch_size") is not None else 1

    def set_config_batch_size(self, batch_size: int) -> None:
        if batch_size < 1:
            return
        self._redis.set("config:batch_size", str(batch_size))

    def get_queue_depth(self, queue_name: str) -> int:
        return int(self._redis.llen(queue_name)) if self._redis.llen(queue_name) is not None else 0
