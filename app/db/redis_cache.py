import os
import json
import redis
from dotenv import load_dotenv

load_dotenv()

# Get Redis connection details from environment variables
# REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
# REDIS_PORT = os.getenv("REDIS_PORT", "6379")
# REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
# REDIS_DB = os.getenv("REDIS_DB", "0")
# print(REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB)

redis_client = redis.StrictRedis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    password=os.getenv("REDIS_PASSWORD"),
    db=int(os.getenv("REDIS_DB", "0")),
    decode_responses=True,
)

def save_task_status(task_id: str, status: str):
    redis_client.set(f"task_status:{task_id}", status)

def get_task_status(task_id: str):
    return redis_client.get(f"task_status:{task_id}")

def save_task_result(task_id: str, result: dict):
    redis_client.set(f"task_result:{task_id}", json.dumps(result))

def get_task_result(task_id: str):
    result = redis_client.get(f"task_result:{task_id}")
    return json.loads(result) if result else None