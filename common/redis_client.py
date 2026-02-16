from __future__ import annotations

import json
from typing import Any

import redis


class RedisClient:
    def __init__(self, redis_url: str) -> None:
        self._redis = redis.Redis.from_url(redis_url, decode_responses=True)

    def ping(self) -> bool:
        return bool(self._redis.ping())

    def consume_job_weaver(self, queue_name: str = "queue:weaver_jobs", timeout_seconds: int = 5) -> dict[str, Any] | None:
        # BRPOP returns tuple: (queue_name, payload)
        """
        Pseudocode for consuming jobs appropriately for the weaver:
        get the value of the key config:batch_size from the redis client
        i <- 0
        jobs = []
        while i < batch_size:
            item = self._redis.brpop(queue_name, timeout=timeout_seconds)
            if item is None:
                break
            _, payload = item
            jobs.append(json.loads(payload))
            i += 1
        return jobs
        (or None if jobs is empty)
        """
        item = self._redis.brpop(queue_name, timeout=timeout_seconds)
        if item is None:
            return None
        _, payload = item
        return json.loads(payload)
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
