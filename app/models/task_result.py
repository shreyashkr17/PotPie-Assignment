from pydantic import BaseModel
from typing import List, Dict

class Issue(BaseModel):
    type: str
    line: int
    description: str
    suggestion: str

class FileResult(BaseModel):
    name: str
    issues: List[Issue]

class TaskResult(BaseModel):
    task_id: str
    status: str
    results: Dict