from fastapi import APIRouter, Request, HTTPException, Depends
from bson import ObjectId
from .. import utils
from .. import webhooks
import traceback
from typing import Annotated
from .. import auth
from ..models import user as user_models

router = APIRouter(prefix="/api")
db = utils.get_db_client()


### GET ###


@router.get("/issue/{issue_id}")
async def get_one(issue_id, user: auth.UserDep):
    issue = utils.prepare_json(db.issues.find_one({"_id": ObjectId(issue_id)}))
    if issue:
        user = utils.prepare_json(
            db.users.find_one(
                {"discord_id": issue["discord_id"]},
            )
        )
        issue["playerData"] = user or {}

    return issue


@router.get("/issue/{issue_id}/modlogs")
async def get_one(user: auth.UserDep, issue_id):
    return utils.prepare_json(
        db.issues.find_one({"_id": ObjectId(issue_id)}, {"modlogs": 1})
    )


### POST ###


@router.post("/issue")
async def create_issue(user_auth: auth.UserDep, request: Request):
    req_info = await request.json()
    print(req_info)
    req_info["category"] = req_info["category"].lower()
    req_info["project_id"] = ObjectId(req_info["project_id"])

    # TODO: check to see if user_id is allowed to create this issue on the project_name

    try:
        issue = db.issues.insert_one(req_info)
    except:
        print(traceback.format_exc())
        raise HTTPException(status_code=503, detail="Unable write issue to database")

    req_info["playerData"] = user_auth["token"].user

    webhooks.send_new_issue(req_info)
    return utils.prepare_json(issue.inserted_id)


### PUT ###


@router.put("/issue/{issue_id}")
async def update_issue(user: auth.UserDep, issue_id, request: Request):
    req_info = await request.json()
    print(req_info)
    issue_id = ObjectId(issue_id)
    issue = utils.prepare_json(db.issues.find_one({"_id": issue_id}))

    user_projects = [
        i for i in user["token"].user["projects"] if i["id"] == issue["project_id"]
    ]

    has_contributor = [i for i in user_projects if "contributor" in i["roles"]]

    if user["discord_id"] != issue["discord_id"] or not has_contributor:
        raise HTTPException(
            status_code=403,
            detail="User does not have permissions to perform update on issue.",
        )

    issue_info = req_info["issue"]
    issue_info["project_id"] = ObjectId(issue_info["project_id"])
    issue_info["category"] = issue_info["category"].lower()
    user_info = req_info["userInfo"]

    issue_info = {
        k: v for k, v in issue_info.items() if k != "playerData" and k != "weight"
    }
    user_info = {k: user_info[k] for k in ["discord_id", "avatar", "username"]}

    issue_info.pop("id")

    issue = db.issues.find_one_and_update(
        {"_id": issue_id}, {"$set": issue_info}, upsert=False
    )

    diff = []

    for key, value in issue_info.items():
        if value == issue[key]:
            continue

        diff.append({"new": value, "old": issue[key], "key": key})

    issue["playerData"] = utils.prepare_json(
        db.users.find_one({"discord_id": issue["discord_id"]})
    )

    webhooks.send_update_issue(diff, issue, user_info)

    return utils.prepare_json(issue)


@router.delete("/issue/{issue_id}")
async def delete_issue(user_auth: auth.UserDep, issue_id, request: Request):
    user = user_auth["token"].user

    req_info = await request.json()
    user_info = {k: req_info[k] for k in ["discord_id", "avatar", "username"]}

    issue = db.issues.find_one({"_id": ObjectId(issue_id)})
    issue["playerData"] = utils.prepare_json(
        db.users.find_one({"discord_id": issue["discord_id"]})
    )

    has_contributor = [i for i in user["projects"] if "contributor" in i["roles"]]

    if user["discord_id"] != issue["discord_id"] or not has_contributor:
        raise HTTPException(
            status_code=403,
            detail="User does not have permissions to perform update on issue.",
        )

    db.issues.find_one_and_delete({"_id": ObjectId(issue_id)})

    webhooks.send_deleted_issue(issue, user_info)
