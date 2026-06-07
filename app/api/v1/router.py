from fastapi import APIRouter

from app.api.v1.routes import auth, files, stats

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
