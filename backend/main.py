from fastapi import FastAPI
from backend.api.poll import router as poll_router

app = FastAPI(title="Options Polling API", version="1.0.0")

app.include_router(poll_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}