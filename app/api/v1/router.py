from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, users, islands, queues, queue_users,
    visits, reviews, queue_messages, chats,
    friendships, reports, admin,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(islands.router)
api_router.include_router(queues.router)
api_router.include_router(queue_users.router)
api_router.include_router(queue_messages.router)
api_router.include_router(visits.router)
api_router.include_router(reviews.router)
api_router.include_router(chats.router)
api_router.include_router(friendships.router)
api_router.include_router(reports.router)
api_router.include_router(admin.router)
