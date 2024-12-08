from fastapi import FastAPI
from app.api.endpoints import router

app = FastAPI()

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Backend is running on port 8080"}