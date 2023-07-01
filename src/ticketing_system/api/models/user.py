from pydantic import BaseModel
from bson import ObjectId
from fastapi import HTTPException

import traceback

from .. import utils

db = utils.get_db_client()


class User(BaseModel):
    discord_id: str
    # avatar: Union[str, None] = None
    # banner: Union[str, None] = None
    # banner_color: Union[str, None] = None
    # banned: bool


def create_or_get_user(discord_user):
    user_info = {
        "discord_id": discord_user["id"],
        "username": discord_user["username"],
        "avatar": discord_user["avatar"],
        "banner": discord_user["banner"],
        "banner_color": discord_user["banner_color"],
        "banned": False,
    }
    find_user = db.users.find_one({"discord_id": user_info["discord_id"]})

    if not find_user:
        try:
            db.users.insert_one(user_info)
            user = utils.prepare_json(user_info)
            user["projects"] = get_user_project_roles(user_info["discord_id"])
        except:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=503, detail="Unable write issue to database"
            )

    if find_user:
        try:
            user = utils.prepare_json(
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
            user["projects"] = get_user_project_roles(user_info["discord_id"])
        except:
            raise HTTPException(
                status_code=503, detail="Unable write issue to database"
            )

    return user


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
