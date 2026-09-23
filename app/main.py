from fastapi import FastAPI
from app.routers.users import router as users_router
from app.routers.auth import router as auth_router
from app.routers.accounts import router as accounts_router

app = FastAPI()

@app.get("/health")
def get_health():
    return {"status": "ok"}

app.include_router(users_router)
app.include_router(auth_router)
app.include_router(accounts_router)