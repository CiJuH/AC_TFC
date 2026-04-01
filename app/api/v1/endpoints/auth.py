from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from passlib.context import CryptContext
from app.db.session import get_db
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.models.user import User, OAuthProvider

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DISCORD_AUTH_URL = "https://discord.com/api/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_USER_URL = "https://discord.com/api/users/@me"

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


# --- Email / password ---

class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

    user = User(
        oauth_provider=OAuthProvider.email,
        username=body.username,
        password_hash=pwd_context.hash(body.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {
        "access_token": create_access_token(str(user.id)),
        "refresh_token": create_refresh_token(str(user.id)),
        "token_type": "bearer",
    }


@router.post("/login")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.username == body.username, User.oauth_provider == OAuthProvider.email)
    )
    user = result.scalar_one_or_none()

    if not user or not user.password_hash or not pwd_context.verify(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    return {
        "access_token": create_access_token(str(user.id)),
        "refresh_token": create_refresh_token(str(user.id)),
        "token_type": "bearer",
    }


@router.post("/refresh")
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    import uuid
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = await db.get(User, uuid.UUID(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return {
        "access_token": create_access_token(str(user.id)),
        "token_type": "bearer",
    }


# --- Discord OAuth ---

@router.get("/discord/login")
def discord_login():
    params = (
        f"client_id={settings.DISCORD_CLIENT_ID}"
        f"&redirect_uri={settings.DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify%20email"
    )
    return RedirectResponse(f"{DISCORD_AUTH_URL}?{params}")


@router.get("/discord/callback")
async def discord_callback(code: str, db: AsyncSession = Depends(get_db)):
    import httpx

    async with httpx.AsyncClient() as client:
        token_response = await client.post(DISCORD_TOKEN_URL, data={
            "client_id": settings.DISCORD_CLIENT_ID,
            "client_secret": settings.DISCORD_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.DISCORD_REDIRECT_URI,
        })
        token_data = token_response.json()

        user_response = await client.get(
            DISCORD_USER_URL,
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        discord_user = user_response.json()

    result = await db.execute(
        select(User).where(User.oauth_provider == OAuthProvider.discord, User.oauth_id == discord_user["id"])
    )
    user = result.scalar_one_or_none()

    avatar_url = None
    if discord_user.get("avatar"):
        avatar_url = f"https://cdn.discordapp.com/avatars/{discord_user['id']}/{discord_user['avatar']}.png"

    if not user:
        user = User(
            oauth_provider=OAuthProvider.discord,
            oauth_id=discord_user["id"],
            username=discord_user["username"],
            avatar_url=avatar_url,
        )
        db.add(user)
    else:
        user.username = discord_user["username"]
        user.avatar_url = avatar_url

    await db.commit()
    await db.refresh(user)

    return {
        "access_token": create_access_token(str(user.id)),
        "refresh_token": create_refresh_token(str(user.id)),
        "token_type": "bearer",
    }


# --- Google OAuth ---

@router.get("/google/login")
def google_login():
    params = (
        f"client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
    )
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{params}")


@router.get("/google/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    import httpx

    async with httpx.AsyncClient() as client:
        token_response = await client.post(GOOGLE_TOKEN_URL, data={
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        })
        token_data = token_response.json()

        user_response = await client.get(
            GOOGLE_USER_URL,
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        google_user = user_response.json()

    result = await db.execute(
        select(User).where(User.oauth_provider == OAuthProvider.google, User.oauth_id == google_user["sub"])
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            oauth_provider=OAuthProvider.google,
            oauth_id=google_user["sub"],
            username=google_user.get("name", google_user.get("email", "user")),
            avatar_url=google_user.get("picture"),
        )
        db.add(user)
    else:
        user.username = google_user.get("name", user.username)
        user.avatar_url = google_user.get("picture", user.avatar_url)

    await db.commit()
    await db.refresh(user)

    return {
        "access_token": create_access_token(str(user.id)),
        "refresh_token": create_refresh_token(str(user.id)),
        "token_type": "bearer",
    }