from fastapi import APIRouter, Request
from .. import auth
from .. import utils
from bson import ObjectId

from datetime import datetime

router = APIRouter(prefix="/api")
db = utils.get_db_client()


@router.get("/blogs")
async def get_all_blogs():
    all_blogs = utils.prepare_json(db.blogs.find({}))
    send_info = []

    for blog in all_blogs:
        get_discord_info = utils.prepare_json(
            db.users.find_one(
                {"discord_id": blog["discord_id"]},
                {"avatar": 1, "username": 1, "discord_id": 1},
            )
        )
        send_info.append({"blog_info": blog, "user_info": get_discord_info})

    return send_info


@router.post("/blogs/createblog")
async def create_blog(user: auth.UserDep, request: Request):
    current_time = datetime.utcnow()
    req_info = await request.json()
    user = user["token"].user

    db.blogs.insert_one(
        {
            "date": current_time,
            "discord_id": user["discord_id"],
            "post": req_info["post"],
            "tags": req_info["tags"],
            "title": req_info["title"],
        }
    )
    # somewhere in here pass


@router.put("/blogs/updateblog")
async def update_blog(blog_id, user: auth.UserDep, request: Request):
    user = user["token"].user
    req_info = await request.json()

    get_blog = db.blogs.find_one_and_update({"_id": ObjectId(blog_id)}, {req_info})

    return user


@router.delete("/blogs/deleteblog")
async def delete_blog(blog_id, user: auth.UserDep):
    user = user["token"].user
    get_blog = db.blogs.find_one_and_delete({"_id": ObjectId(blog_id)})

    return user
