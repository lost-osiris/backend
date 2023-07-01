import requests

from fastapi import APIRouter, Request, HTTPException
from bson import ObjectId

from ..models import user as user_models
from .. import utils
from .. import auth

router = APIRouter(prefix="/api")
db = utils.get_db_client()


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


@router.put("/user/addtoproject")
async def add_user_to_project(user_auth: auth.UserDep, request: Request):
    req_info = await request.json()
    print(req_info)

    # elif find_user and not db.users.find_one(
    #     {"user_id": req_info["user_id"], "projects": req_info["projects"]}
    # ):
    #     db.projects.update_one(
    #         {"user_id": req_info["user_id"]},
    #         {"$push": {"projects": req_info["projects"]}},
    #     )
    #     print("found user but didn't find the project, so we update with the project")

    # elif find_user and db.users.find_one(
    #     {"user_id": req_info["user_id"], "projects": req_info["projects"]}
    # ):
    #     print(
    #         "found the user and it's a part of the project we are looking for, so we reject"
    #     )
