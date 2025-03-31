# memory/redis_memory.py

import redis
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def save_to_memory(key: str, value: str):
    """Save a string value to Redis"""
    r.set(key, value)


def read_from_memory(key: str) -> str:
    """Read a value from Redis"""
    return r.get(key)


def append_to_list(key: str, value: str):
    """Append a value to a Redis list"""
    r.rpush(key, value)


def get_list(key: str, limit: int = 10) -> list:
    """Read a Redis list (most recent N)"""
    return r.lrange(key, -limit, -1)
