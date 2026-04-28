import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.mdns import start_mdns, stop_mdns
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.is_dev:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, start_mdns)
    yield
    if settings.is_dev:
        stop_mdns()


app = FastAPI(
    title=settings.APP_NAME,
    docs_url="/docs" if settings.is_dev else None,
    redoc_url="/redoc" if settings.is_dev else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}
