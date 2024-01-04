import os
import os
import requests
import urllib
import datetime
from typing import Annotated, Union
from fastapi import Request, HTTPException, status, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from fastapi import APIRouter, Request, HTTPException
from . import utils

from fastapi.security import (
    OAuth2AuthorizationCodeBearer,
    HTTPBearer,
    OAuth2PasswordBearer,
)
from bson import ObjectId
from datetime import datetime, timedelta
from jose import JWTError, jwt
from .models.token import TokenData
from .models import user as user_models

SECRET_KEY = os.getenv("CLIENT_SECRET")
APP_ID = os.getenv("APPLICATION_ID")

PROD_AUTH_REDIRECT = (
    "https://modforge.gg/api/auth/discord?redirect_uri=https://modforge.gg"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 7200

oauth2_scheme = HTTPBearer()

router = APIRouter(prefix="/api")


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearer, self
        ).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=403, detail="Invalid authentication scheme."
                )
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(
                    status_code=403, detail="Invalid token or expired token."
                )
            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")

    def verify_jwt(self, token: str) -> bool:
        isTokenValid: bool = False

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except:
            payload = None

        if payload:
            isTokenValid = True

        return isTokenValid


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(JWTBearer())]):
    db = utils.get_db_client()

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(
            user_id=user_id,
            user=payload.get("user"),
        )
    except JWTError:
        raise credentials_exception

    user = db.users.find_one({"_id": ObjectId(token_data.user_id)})
    if user is None:
        raise credentials_exception

    user["token"] = token_data
    if user["banned"]:
        raise HTTPException(status_code=400, detail="Banned user")

    return utils.prepare_json(user)


@router.get("/auth/discord")
async def get_code_run_exchange(code: str, redirect_uri: str, request: Request):
    redirect_url = urllib.parse.unquote(redirect_uri)

    data = {
        "client_id": APP_ID,
        "client_secret": SECRET_KEY,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": f"{redirect_uri}/api/auth/discord?redirect_uri={redirect_uri}"
        if os.getenv("IS_DEV")
        else PROD_AUTH_REDIRECT,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(
        "https://discord.com/api/v8/oauth2/token",
        data=data,
        headers=headers,
    )
    r.raise_for_status()
    response_data = r.json()

    r = requests.get(
        "https://discord.com/api/v8/users/@me",
        headers={"Authorization": f"Bearer {response_data['access_token']}"},
    )

    user = user_models.create_or_get_user(r.json())

    access_token = create_access_token(
        data={
            "user": user,
            "sub": user["id"],
        }
    )

    return RedirectResponse(
        f"{redirect_url}?token={access_token}",
        status_code=303,
    )


@router.post("/auth/token/refresh")
async def token_refresh():
    ...


UserDep = Annotated[str, Depends(get_current_user)]
