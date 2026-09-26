from fastapi import APIRouter

from app.api.v1.endpoints import auth, github, health, repositories, webhooks

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(github.router)
api_router.include_router(repositories.router)
api_router.include_router(webhooks.router)
