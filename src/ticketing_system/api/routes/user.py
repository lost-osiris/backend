import requests

from fastapi import APIRouter, Request, HTTPException
from bson import ObjectId

from ..models import user as user_models
from .. import utils
from .. import auth

router = APIRouter(prefix="/api")
db = utils.get_db_client()


@router.get("/user/finduser/{discord_id}")
async def find_user(user_auth: auth.UserDep, discord_id):
    user = utils.prepare_json(db.users.find_one({"discord_id": discord_id}))
    if user:
        return user

    raise HTTPException(status_code=404, detail="user not found")


@router.get("/user/discord/{discord_id}")
async def get_user(user_auth: auth.UserDep, discord_id):
    user = utils.prepare_json(db.users.find_one({"discord_id": discord_id}))
    if user:
        user["projects"] = user_models.get_user_project_roles(user["discord_id"])
        r = requests.get(
            "https://discord.com/api/v8/users/@me",
            headers={
                "Authorization": f"Bearer {user_auth['token'].discord_access_token}"
            },
        )
        return {"user": user, "discord": r.json()}

    raise HTTPException(status_code=404, detail="User not found")


@router.get("/user/{user_id}")
async def get_user(user_auth: auth.UserDep, user_id):
    user = utils.prepare_json(db.users.find_one({"_id": ObjectId(user_id)}))
    if user:
        user["projects"] = user_models.get_user_project_roles(user["discord_id"])
        r = requests.get(
            "https://discord.com/api/v8/users/@me",
            headers={
                "Authorization": f"Bearer {user_auth['token'].discord_access_token}"
            },
        )
        return {"user": user, "discord": r.json()}

    raise HTTPException(status_code=404, detail="User not found")


@router.get("/user/findall/")
async def find_all_users():
    all_users = db.users.find(
        {}, {"discord_id": 1, "avatar": 1, "username": 1, "_id": 0}
    )
    return utils.prepare_json(all_users)
