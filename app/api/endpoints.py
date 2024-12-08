from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult
from app.services.celery_tasks import analyze_pr_task
from app.db.redis_cache import get_task_status, get_task_result
from pydantic import BaseModel
router = APIRouter()

class AnalyzePRRequest(BaseModel):
    repo_url: str
    pr_number: int
    github_token: str

@router.post("/analyze-pr")
async def analyze_pr(request: AnalyzePRRequest):
    try:
        task = analyze_pr_task.delay(
                repo_url=request.repo_url,
                pr_number=request.pr_number,
                github_token=request.github_token,
            )
        return {"task_id": task.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{task_id}")
async def get_status(task_id: str):
    status = get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "status": status}

@router.get("/results/{task_id}")
async def get_results(task_id: str):
    result = get_task_result(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Results not available")
    return {"results": result}