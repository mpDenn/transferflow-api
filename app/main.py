from fastapi import FastAPI
from app.routers.users import router as user_router

app = FastAPI()

@app.get("/health")
def get_health():
    return {"status": "ok"}

app.include_router(user_router)