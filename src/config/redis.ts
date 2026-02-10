import Redis from "ioredis";
import { REDIS_URL } from "../utils/env";

function createRedisClient(name: string): Redis {
  const isDev = process.env.NODE_ENV === "development";
  const maxRetriesEnv = process.env.REDIS_MAX_RETRIES;
  const maxRetries = maxRetriesEnv ? Number(maxRetriesEnv) : isDev ? 5 : 50;

  const client = new Redis(REDIS_URL, {
    lazyConnect: true,
    connectTimeout: 3000,
    maxRetriesPerRequest: null,
    retryStrategy: (times) => {
      if (Number.isFinite(maxRetries) && times >= maxRetries) return null;
      return Math.min(2000, 200 * times);
    },
  });

  let lastLoggedAt = 0;
  client.on("error", (err) => {
    const now = Date.now();
    if (now - lastLoggedAt < 5000) return;
    lastLoggedAt = now;
    console.error(`[redis:${name}]`, err?.message ?? err);
  });

  return client;
}

export const redis = createRedisClient("default");
export const subscriber = createRedisClient("subscriber");

