from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, islands, queues, queue_users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(islands.router)
api_router.include_router(queues.router)
api_router.include_router(queue_users.router)
