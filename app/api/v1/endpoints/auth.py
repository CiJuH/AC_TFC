from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token

router = APIRouter(prefix="/auth", tags=["auth"])

DISCORD_AUTH_URL = "https://discord.com/api/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_USER_URL = "https://discord.com/api/users/@me"

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


@router.get("/discord/login")
def discord_login():
    """Redirect user to Discord OAuth consent screen."""
    params = (
        f"client_id={settings.DISCORD_CLIENT_ID}"
        f"&redirect_uri={settings.DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify%20email"
    )
    return RedirectResponse(f"{DISCORD_AUTH_URL}?{params}")


@router.get("/discord/callback")
async def discord_callback(code: str, db: Session = Depends(get_db)):
    """
    Discord sends the user back here with a code.
    Exchange it for user info, create/update user, return JWT tokens.
    """
    import httpx

    # 1. Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(DISCORD_TOKEN_URL, data={
            "client_id": settings.DISCORD_CLIENT_ID,
            "client_secret": settings.DISCORD_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.DISCORD_REDIRECT_URI,
        })
        token_data = token_response.json()

        # 2. Fetch Discord user info
        user_response = await client.get(
            DISCORD_USER_URL,
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        discord_user = user_response.json()

    # 3. Upsert user in DB
    from app.models.user import User, OAuthProvider
    user = db.query(User).filter_by(
        oauth_provider=OAuthProvider.discord,
        oauth_id=discord_user["id"],
    ).first()

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

    db.commit()
    db.refresh(user)

    # 4. Return JWT tokens
    return {
        "access_token": create_access_token(str(user.id)),
        "refresh_token": create_refresh_token(str(user.id)),
        "token_type": "bearer",
    }


@router.get("/google/login")
def google_login():
    """Redirect user to Google OAuth consent screen."""
    params = (
        f"client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
    )
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{params}")


@router.get("/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    """Google OAuth callback — same flow as Discord."""
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

    from app.models.user import User, OAuthProvider
    user = db.query(User).filter_by(
        oauth_provider=OAuthProvider.google,
        oauth_id=google_user["sub"],
    ).first()

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

    db.commit()
    db.refresh(user)

    return {
        "access_token": create_access_token(str(user.id)),
        "refresh_token": create_refresh_token(str(user.id)),
        "token_type": "bearer",
    }
