from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import SessionLocal
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.offers import router as offers_router
from app.routers.applications import router as applications_router
from app.services.seed_service import seed_if_empty

app = FastAPI(title="Goatly Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(offers_router)
app.include_router(applications_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def startup_seed():
    if not settings.SEED_ON_STARTUP:
        return
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
