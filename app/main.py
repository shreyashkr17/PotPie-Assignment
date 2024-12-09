from fastapi import FastAPI
from fastapi.responses import FileResponse
from app.api.endpoints import router
import os

app = FastAPI()

app.include_router(router)


INDEX_FILE_PATH = os.path.join(os.path.dirname(__file__), "static", "index.html")
@app.get("/")
async def root():
    return FileResponse(INDEX_FILE_PATH)