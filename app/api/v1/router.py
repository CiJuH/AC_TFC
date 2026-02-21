from fastapi import APIRouter
from app.api.v1.endpoints import auth

api_router = APIRouter()
api_router.include_router(auth.router)

# Future routers — uncomment as you build them:
# from app.api.v1.endpoints import users, queues, dodo_codes, reviews, chat, admin
# api_router.include_router(users.router)
# api_router.include_router(queues.router)
# api_router.include_router(dodo_codes.router)
# api_router.include_router(reviews.router)
# api_router.include_router(chat.router)
# api_router.include_router(admin.router)
