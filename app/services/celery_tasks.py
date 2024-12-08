from celery import Celery
from app.db.redis_cache import save_task_status, save_task_result
from app.services.ai_agent import analyze_code
import os
import asyncio
from dotenv import load_dotenv 

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_DB_BROKER = os.getenv("REDIS_DB_BROKER", "0")
REDIS_DB_BACKEND = os.getenv("REDIS_DB_BACKEND", "1")

celery = Celery(
    "tasks", 
    broker=f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_BROKER}",
    backend=f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_BACKEND}"
)

@celery.task(bind=True)
def analyze_pr_task(self, repo_url: str, pr_number: int, github_token: str):
    task_id = self.request.id
    save_task_status(task_id, "processing")

    try:
        result = asyncio.run(analyze_code(repo_url, pr_number, github_token, task_id))
        save_task_status(task_id, "completed")
        save_task_result(task_id, result)
    except Exception as e:
        save_task_status(task_id, "failed")
        raise e