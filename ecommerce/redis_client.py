# mysite/redis_client.py
import redis
from django.conf import settings

# Create the connection pool once
# ConnectionPool is safer for multi-threaded apps (like production Django)
pool = redis.ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)

# Create the Redis instance using that pool
r = redis.Redis(connection_pool=pool)