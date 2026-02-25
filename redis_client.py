import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

class RedisCache:
    def __init__(self):
        self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    
    def get(self, key: str):
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    def set(self, key: str, value, expire: int = 300):  # 5 minutes default
        try:
            self.redis_client.setex(key, expire, json.dumps(value, default=str))
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    def delete(self, key: str):
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str):
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            return True
        except Exception as e:
            print(f"Redis delete pattern error: {e}")
            return False

cache = RedisCache()