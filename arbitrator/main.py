from common.config import load_settings
from common.job_schema import WeaverJobDoneEvent
from common.redis_client import RedisClient
from common.s3_client import S3ImageStore
from common.log_utils import get_logger, setup_logging
import time

def main() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)
    logger = get_logger("arbitrator.main")

    redis_client = RedisClient(settings.redis_url)
    if not redis_client.ping():
        raise RuntimeError("Redis ping failed")

    logger.info("Arbitrator worker started: queue=%s channel=%s", settings.redis_queue, settings.redis_events_channel)
    batch_size = redis_client.get_config_batch_size()
    if batch_size is None:
        batch_size = 1
        redis_client.set_config_batch_size(batch_size)
    else:
        batch_size = int(batch_size)
    cooldown_time = 500 # 500ms
    last_adjustment = time.time()
    while True:
        queue_depth = redis_client.get_queue_depth(settings.redis_queue)
        if queue_depth is None:
            queue_depth = 0
        else:
            queue_depth = int(queue_depth)
        if time.time() - last_adjustment > cooldown_time:
            if queue_depth <= 10:
                batch_size = 1
            if queue_depth > 10:
                batch_size = 4
            if queue_depth > 50:
                batch_size = 8
            if queue_depth > 100:
                batch_size = 16
            last_adjustment = time.time()
            redis_client.set_config_batch_size(batch_size)
        time.sleep(0.1)

    
    