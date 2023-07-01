from fastapi import APIRouter, Request, HTTPException
from bson import ObjectId
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


@router.get("/projects")
async def get_all_projects(user: auth.UserDep):
    projects = list(db.projects.find())
    return utils.prepare_json(projects)


@router.get("/project/{project_id}")
async def get_project(user: auth.UserDep, project_id):
    project = db.projects.find_one({"_id": ObjectId(project_id)})

    if project:
        return utils.prepare_json(
            {
                **project,
                # TODO: use project id for fetching discord bot
                # "webhooks": [i for i in db.webhooks.find({"name": project["name"]})],
            }
        )


@router.put("/project/webhooks")
async def create_project_webhook(user: auth.UserDep, request: Request):
    req_info = await request.json()
    proj_name = req_info["project_name"]
    time.sleep(0.5)

    find_project = db.projects.find_one({"name": proj_name})

    if find_project and db.webhooks.find_one({"url": req_info}):
        raise HTTPException(status_code=403, detail="webhook already exists")
    elif find_project and not db.webhooks.find_one({"url": req_info}):
        try:
            new_webhook = db.webhooks.insert_one(req_info)
        except:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=503, detail="Unable write issue to database"
            )

    elif not find_project:
        raise HTTPException(
            status_code=404,
            detail=f"Project not found, cannot write to database",
        )

    else:
        raise HTTPException(
            status_code=503,
            detail=f"Unable write webhook for channel to database",
        )


@router.get("/project/{project_id}/waitlist")
async def get_waitlist(project_id):
    return utils.prepare_json(
        db.projects.find_one({"_id": ObjectId(project_id)}, {"waitlist": 1, "_id": 0})
    )


@router.post("/project/{project_id}/members/joinwaitlist")
async def join_waitlist(project_id: str, request: Request):
    req_info = await request.json()
    find_member = db.projects.find(
        {"_id": ObjectId(project_id)},
        {"_id": 0, "members": {"$elemMatch": {"discord_id": req_info["discord_id"]}}},
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
                "waitlist": {"$elemMatch": {"discord_id": req_info["discord_id"]}},
            },
        )
        if find_waitlist[0]:
            raise HTTPException(
                status_code=503,
                detail=f"User already on the waitlist",
            )
        else:
            insert_info = {
                "discord_id": req_info["discord_id"],
                "username": req_info["username"],
                "avatar": req_info["avatar"],
            }
            db.projects.update_one(
                {"_id": ObjectId(project_id)},
                {"$push": {"waitlist": insert_info}},
            )
            webhooks.send_join_waitlist(req_info)
            return req_info


### PUT ###


@router.put("/project/webhooks")
async def create_project_webhook(request: Request):
    req_info = await request.json()
    proj_name = req_info["project_name"]
    time.sleep(0.5)

    find_project = db.projects.find_one({"name": proj_name})

    if find_project and db.webhooks.find_one({"url": req_info}):
        raise HTTPException(status_code=403, detail="webhook already exists")
    elif find_project and not db.webhooks.find_one({"url": req_info}):
        try:
            new_webhook = db.webhooks.insert_one(req_info)
        except:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=503, detail="Unable write issue to database"
            )

    elif not find_project:
        raise HTTPException(
            status_code=404,
            detail=f"Project not found, cannot write to database",
        )

    else:
        raise HTTPException(
            status_code=503,
            detail=f"Unable write webhook for channel to database",
        )


@router.put("/project/{project_id}/members/updatewaitlist")
async def update_waitlist(project_id: str, request: Request):
    req_info = await request.json()

    get_user_info = utils.prepare_json(
        db.users.find_one(
            {"discord_id": req_info["member"]["discord_id"]},
            {"avatar": 1, "_id": 0},
        )
    )

    webhook_data = {
        "discord_id": req_info["member"]["discord_id"],
        "username": req_info["member"]["username"],
        "avatar": get_user_info["avatar"],
        "role": req_info["role"],
    }

    find_member = db.projects.find(
        {"_id": ObjectId(project_id)},
        {
            "_id": 0,
            "members": {"$elemMatch": {"discord_id": req_info["member"]["discord_id"]}},
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
            {"$pull": {"waitlist": {"discord_id": req_info["member"]["discord_id"]}}},
        )
        webhooks.send_reject_waitlist(webhook_data)

    elif not find_member[0]:
        insert_info = {
            "discord_id": req_info["member"]["discord_id"],
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
            {"$pull": {"waitlist": {"discord_id": req_info["member"]["discord_id"]}}},
        )
        webhooks.send_accept_waitlist(webhook_data)

    return req_info


@router.get("/project/{project_id}/member/{discord_id}", status_code=204)
async def find_member(user: auth.UserDep, project_id: str, discord_id: str):
    find_member = db.projects.find(
        {"_id": ObjectId(project_id)},
        {"_id": 0, "members": {"$elemMatch": {"discord_id": discord_id}}},
    )

    if find_member[0]:
        return

    if not find_member[0]:
        raise HTTPException(
            status_code=503,
            detail=f"User not found in project",
        )


@router.get("/project/{project_id}/categories")
async def create_categories(user: auth.UserDep, project_id: str):
    project = db.projects.find_one({"_id": ObjectId(project_id)})

    if not project:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to retrieve categories from database",
        )

    return utils.prepare_json(project["categories"])


@router.put("/project/{project_id}}/categories")
async def create_categories(user: auth.UserDep, request: Request, project_id: str):
    req_info = await request.json()

    project = db.project.find({"_id": ObjectId(project_id)})
    if project:
        for category in req_info:
            db.projects.update_one(
                {"_id": ObjectId(project_id)},
                {"$push": {"categories": category.strip()}},
            )
    else:
        raise HTTPException(
            status_code=503,
            detail=f"Unable write to database",
        )


### DELETE ###


@router.get("/project/{project_id}/category/{category}/issues")
async def get_all_by_category(user: auth.UserDep, project_id: str, category: str):
    issues = utils.prepare_json(
        db.issues.aggregate(
            [
                {
                    "$match": {
                        "project_id": ObjectId(project_id),
                        "category": category,
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
                        "weight": {
                            "$cond": [
                                {"$eq": ["$priority", "high"]},
                                1,
                                {
                                    "$cond": [{"$eq": ["$priority", "medium"]}, 2, 3],
                                },
                            ]
                        },
                    }
                },
                {"$sort": {"weight": 1}},
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
