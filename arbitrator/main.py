from common.config import load_settings
from common.redis_client import RedisClient
from common.log_utils import get_logger, setup_logging
import time

def main() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)
    logger = get_logger("arbitrator.main")

    redis_client = RedisClient(settings.redis_url)
    if not redis_client.ping():
        raise RuntimeError("Redis ping failed")

    logger.info("Arbitrator worker started")
    batch_size = redis_client.get_config_batch_size()
    redis_client.set_config_batch_size(batch_size)
    logger.info("Batch size set to %s", batch_size)
    cooldown_time = 1 # 1 second
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


if __name__ == "__main__":
    main()
