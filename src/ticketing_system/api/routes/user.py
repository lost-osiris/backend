from fastapi import APIRouter, Request, HTTPException
from bson import ObjectId
from .. import utils
from .. import auth
from .. import webhooks
import os
import requests
import traceback
import time
from datetime import timedelta

SECRET = os.getenv("CLIENT_SECRET")
APP_ID = os.getenv("APPLICATION_ID")
PROD_AUTH_REDIRECT = "https://modforge.gg/"

router = APIRouter(prefix="/api")
db = utils.get_db_client()


@router.get("/user/{discord_id}")
async def get_user(discord_id):
    user = utils.prepare_json(db.users.find_one({"discord_id": discord_id}))
    if user:
        user["projects"] = get_user_project_roles(user["discord_id"])
        return user

    raise HTTPException(status_code=404, detail="User not found")


@router.post("/user/discord/{code}")
async def get_code_run_exchange(code):
    data = {
        "client_id": APP_ID,
        "client_secret": SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "http://localhost:3000/"
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

    r = requests.get(
        "https://discord.com/api/v8/users/@me",
        headers={"Authorization": f"Bearer {r.json()['access_token']}"},
    )

    user = create_or_get_user(r.json())

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user["id"]}, expires_delta=access_token_expires
    )
    user["token"] = {"access_token": access_token, "token_type": "bearer"}
    user["projects"] = get_user_project_roles(user["discord_id"])
    return user


def create_or_get_user(discord_user):
    user_info = {
        "discord_id": discord_user["id"],
        "username": discord_user["username"],
        "avatar": discord_user["avatar"],
        "banner": discord_user["banner"],
        "banner_color": discord_user["banner_color"],
        "banned": False,
        "projects": [],
    }
    find_user = db.users.find_one({"discord_id": user_info["discord_id"]})

    if not find_user:
        try:
            db.users.insert_one(user_info)
            return utils.prepare_json(user_info)
        except:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=503, detail="Unable write issue to database"
            )

    if find_user:
        try:
            return utils.prepare_json(
                db.users.find_one_and_update(
                    {"discord_id": user_info["discord_id"]},
                    {
                        "$set": {
                            "discord_id": user_info["discord_id"],
                            "username": user_info["username"],
                            "avatar": user_info["avatar"],
                            "banner": user_info["banner"],
                            "banner_color": user_info["banner_color"],
                        }
                    },
                )
            )
        except:
            raise HTTPException(
                status_code=503, detail="Unable write issue to database"
            )


def get_user_project_roles(discord_id, project_id=None):
    query_builder = {"members.discord_id": discord_id}

    if project_id:
        query_builder["_id"] = ObjectId(project_id)

    query = db.projects.find(
        query_builder,
        {"_id": 1, "members": 1, "name": 1, "version": 1},
    )

    if query:
        return utils.prepare_json(
            [
                {
                    "id": project["_id"],
                    "name": project["name"],
                    "version": project["version"],
                    "roles": [i["role"] for i in project["members"]],
                }
                for project in query
            ]
        )

    return []
