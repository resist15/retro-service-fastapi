from redis.asyncio import Redis

from app.observability.logging import get_logger

logger = get_logger(__name__)


class RedisSessionManager:
    def __init__(self) -> None:
        self.client: Redis | None = None

    async def init(self, host, port, passw) -> None:
        self.client = Redis(host=host, port=port, password=passw, decode_responses=True)
        try:
            await self.client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.error("Redis connection failed")
            logger.exception(e)
            raise

    async def close(self) -> None:
        if self.client:
            await self.client.aclose()
            self.client = None


redismanager = RedisSessionManager()


async def get_redis() -> Redis:
    if redismanager.client is None:
        raise RuntimeError("Redis is not initialized")
    return redismanager.client
