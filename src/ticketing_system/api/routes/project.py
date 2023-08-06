from fastapi import APIRouter, Request, HTTPException
from bson import ObjectId
import bson
from .. import utils
from .. import auth
from .. import webhooks
import traceback
import time
import urllib.parse

router = APIRouter(prefix="/api")
db = utils.get_db_client()


@router.put("/project")
async def create_project(user: auth.UserDep, request: Request):
    req_info = await request.json()

    find_project = db.projects.find_one({"name": req_info["name"]})

    if not find_project:
        try:
            project = db.projects.insert_one(req_info)
            return utils.json_ready(req_info["name"])

        except:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=503, detail="Unable write issue to database"
            )

    elif find_project:
        print(traceback.format_exc())
        raise HTTPException(
            status_code=400,
            detail="This project already exists, please enter a unique project name",
        )
    else:
        raise HTTPException(status_code=503, detail="Unable write issue to database")


@router.get("/project/{project_id}/getwebhooks")
async def get_project_webhooks(user_auth: auth.UserDep, project_id: str):
    return utils.prepare_json(
        db.projects.find_one({"_id": ObjectId(project_id)}, {"webhooks": 1})
    )


@router.get("/projects")
async def get_all_projects(user_auth: auth.UserDep):
    user = user_auth["token"].user
    projects = utils.prepare_json(
        db.projects.find(
            {
                "$or": [
                    {"is_public": True},
                    {"members": {"$elemMatch": {"discord_id": user["discord_id"]}}},
                ]
            },
            {"webhooks": 0},
        )
    )

    for project in projects:
        if any(
            member["discord_id"] == user["discord_id"] for member in project["members"]
        ):
            project["is_member"] = True
        else:
            project["is_member"] = False

    discord_ids = [j["discord_id"] for i in projects for j in i["members"]]
    users = utils.prepare_json(
        db.users.find(
            {"discord_id": {"$in": discord_ids}},
            {"projects": 0, "banner": 0, "banner_color": 0},
        )
    )

    output = {"public_projects": [], "user_projects": []}

    for project in projects:
        project_members = [i["discord_id"] for i in project["members"]]
        members = [i for i in users if i["discord_id"] in project_members]
        member_info_with_role = []

        for member in members:
            for m in project["members"]:
                if m["discord_id"] == member["discord_id"]:
                    member["role"] = m["role"]
                    break
            member_info_with_role.append(member)

        if project["is_member"] == True:
            output["user_projects"].append(
                {
                    **project,
                    "members": member_info_with_role,
                    "member_count": len(member_info_with_role),
                }
            )
        else:
            output["public_projects"].append(
                {
                    **project,
                    "members": member_info_with_role,
                    "member_count": len(member_info_with_role),
                }
            )

    return utils.prepare_json(output)


@router.get("/project/{project_id}")
async def get_project_members(project_id):
    project = utils.prepare_json(db.projects.find_one({"_id": ObjectId(project_id)}))

    discord_ids = [i["discord_id"] for i in project["members"]]
    users = utils.prepare_json(db.users.find({"discord_id": {"$in": discord_ids}}))

    return {
        **project,
        "members": users,
        "member_count": len(project["members"]),
    }


@router.get("/project/{project_id}/waitlist")
async def get_waitlist(project_id):
    return utils.prepare_json(
        db.projects.find_one({"_id": ObjectId(project_id)}, {"waitlist": 1, "_id": 0})
    )


@router.post("/project/{project_id}/members/joinwaitlist")
async def join_waitlist(user_auth: auth.UserDep, project_id: str, request: Request):
    req_info = await request.json()

    user = user_auth["token"].user
    find_member = db.projects.find(
        {"_id": ObjectId(project_id)},
        {
            "_id": 0,
            "members": {"$elemMatch": {"discord_id": user["discord_id"]}},
        },
    )
    find_project = utils.prepare_json(
        db.projects.find_one({"_id": ObjectId(project_id)}, {"name": 1, "webhooks": 1})
    )

    if find_member[0]:
        raise HTTPException(
            status_code=503,
            detail=f"User already a member of this project",
        )

    elif not find_member[0]:
        find_waitlist = db.projects.find(
            {"_id": ObjectId(project_id)},
            {
                "_id": 0,
                "waitlist": {"$elemMatch": {"discord_id": user["discord_id"]}},
            },
        )
        if find_waitlist[0]:
            raise HTTPException(
                status_code=503,
                detail=f"User already on the waitlist",
            )
        else:
            insert_info = {
                "discord_id": user["discord_id"],
                "username": user["username"],
                "avatar": user["avatar"],
            }
            db.projects.update_one(
                {"_id": ObjectId(project_id)},
                {"$push": {"waitlist": insert_info}},
            )

            if "webhooks" in find_project:
                webhooks.send_join_waitlist(
                    user, find_project["name"], find_project["webhooks"]
                )
            return req_info


### PUT ###


@router.put("/project/{project_id}/updatewebhooks")
async def update_project_webhooks(
    project_id: str, user_auth: auth.UserDep, request: Request
):
    req_info = await request.json()

    try:
        find_project_and_update = db.projects.find_one_and_update(
            {"_id": ObjectId(project_id)}, {"$set": {"webhooks": req_info}}
        )
    except:
        print(traceback.format_exc())
        raise HTTPException(status_code=503, detail="Unable write issue to database")


@router.put("/project/{project_id}/members/updatewaitlist")
async def update_waitlist(user: auth.UserDep, project_id: str, request: Request):
    req_info = await request.json()

    req_info = {
        "discord_id": req_info[0]["discord_id"],
        "username": req_info[0]["username"],
        "avatar": req_info[0]["avatar"],
        "role": req_info[1],
    }

    find_project = utils.prepare_json(
        db.projects.find_one({"_id": ObjectId(project_id)}, {"name": 1, "webhooks": 1})
    )

    get_user_info = utils.prepare_json(
        db.users.find_one(
            {"discord_id": req_info["discord_id"]},
            {"avatar": 1, "_id": 0},
        )
    )

    webhook_data = {
        "discord_id": req_info["discord_id"],
        "username": req_info["username"],
        "avatar": get_user_info["avatar"],
        "role": req_info["role"],
    }

    find_member = db.projects.find(
        {"_id": ObjectId(project_id)},
        {
            "_id": 0,
            "members": {"$elemMatch": {"discord_id": req_info["discord_id"]}},
        },
    )

    if find_member[0]:
        raise HTTPException(
            status_code=503,
            detail=f"User already a member of this project",
        )

    elif not find_member[0] and req_info["role"] == "remove":
        db.projects.update_one(
            {
                "_id": ObjectId(project_id),
            },
            {"$pull": {"waitlist": {"discord_id": req_info["discord_id"]}}},
        )
        if "webhooks" in find_project:
            webhooks.send_reject_waitlist(
                webhook_data, find_project["name"], find_project["webhooks"]
            )

    elif not find_member[0]:
        insert_info = {
            "discord_id": req_info["discord_id"],
            "role": req_info["role"],
        }
        db.projects.update_one(
            {"_id": ObjectId(project_id)},
            {"$push": {"members": insert_info}},
        )
        db.projects.update_one(
            {
                "_id": ObjectId(project_id),
            },
            {"$pull": {"waitlist": {"discord_id": req_info["discord_id"]}}},
        )
        if "webhooks" in find_project:
            webhooks.send_accept_waitlist(
                webhook_data, find_project["name"], find_project["webhooks"]
            )

    return req_info


@router.put("/project/{project_id}/updatemember")
async def update_members(user: auth.UserDep, project_id: str, request: Request):
    req_info = await request.json()
    req_info = {"discord_id": req_info[0]["discord_id"], "role": req_info[1]}

    if req_info["role"] == "remove":
        db.projects.find_one_and_update(
            {"_id": ObjectId(project_id)},
            {"$pull": {"members": {"discord_id": req_info["discord_id"]}}},
        )
    elif req_info["role"] != "remove":
        db.projects.find_one_and_update(
            {"_id": ObjectId(project_id), "members.discord_id": req_info["discord_id"]},
            {"$set": {"members.$.role": req_info["role"]}},
        )


@router.get("/project/{project_id}/category/{category}/issues")
async def get_all_by_category(user: auth.UserDep, project_id: str, category: str):
    issues = utils.prepare_json(
        db.issues.aggregate(
            [
                {
                    "$match": {
                        "project_id": ObjectId(project_id),
                        "category": urllib.parse.unquote(category),
                    }
                },
                {
                    "$project": {
                        "priority": 1,
                        "status": 1,
                        "category": 1,
                        "discord_id": 1,
                        "version": 1,
                        "archived": 1,
                        "project_id": 1,
                        "type": 1,
                        "summary": 1,
                        "description": 1,
                        "_id": 1,
                        "os": 1,
                        "weight": {
                            "$cond": [
                                {"$eq": ["$priority", "high"]},
                                1,
                                {
                                    "$cond": [{"$eq": ["$priority", "medium"]}, 2, 3],
                                },
                            ]
                        },
                        "issue_type": {
                            "$cond": [
                                {"$eq": ["$type", "bug"]},
                                1,
                                0,
                            ]
                        },
                    }
                },
                {"$sort": {"weight": 1, "issue_type": -1}},
            ]
        )
    )
    discord_ids = [i["discord_id"] for i in issues]

    users = {
        i["discord_id"]: i
        for i in utils.prepare_json(db.users.find({"discord_id": {"$in": discord_ids}}))
    }

    merged_issues = []
    for issue in issues:
        if issue["discord_id"] in users:
            issue["playerData"] = users[issue["discord_id"]]
        else:
            issue["playerData"] = {}

        merged_issues.append(issue)

    return utils.prepare_json(merged_issues)
