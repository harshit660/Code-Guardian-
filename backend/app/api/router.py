from fastapi import APIRouter

from app.api.routes import analyses, auth, repositories

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(repositories.router, prefix="/repositories", tags=["repositories"])
api_router.include_router(analyses.router, prefix="/analyses", tags=["analysis"])

