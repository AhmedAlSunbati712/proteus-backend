from __future__ import annotations

import json
from typing import Any

import redis


class RedisClient:
    def __init__(self, redis_url: str) -> None:
        self._redis = redis.Redis.from_url(redis_url, decode_responses=True)

    def ping(self) -> bool:
        return bool(self._redis.ping())

    def consume_job(self, queue_name: str, timeout_seconds: int = 5) -> dict[str, Any] | None:
        # BRPOP returns tuple: (queue_name, payload)
        item = self._redis.brpop(queue_name, timeout=timeout_seconds)
        if item is None:
            return None
        _, payload = item
        return json.loads(payload)

    def publish_event(self, channel_name: str, event: dict[str, Any]) -> int:
        return int(self._redis.publish(channel_name, json.dumps(event, default=str)))
