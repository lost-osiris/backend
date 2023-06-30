from fastapi import APIRouter, Request, HTTPException
from bson import ObjectId
from .. import utils
from .. import webhooks
import traceback


router = APIRouter(prefix="/api")
db = utils.get_db_client()


@router.get("/issue/{issue_id}")
async def get_one(issue_id):
    issue = utils.prepare_json(db.issues.find_one({"_id": ObjectId(issue_id)}))
    if issue:
        avatar_id = db.users.find_one(
            {"discord_id": issue["playerData"]["discord_id"]}, {"avatar": 1}
        )
        if avatar_id:
            issue["playerData"]["avatar"] = avatar_id["avatar"]

    return issue


@router.get("/issue/{issue_id}/modlogs")
async def get_one(issue_id):
    return utils.prepare_json(
        db.issues.find_one({"_id": ObjectId(issue_id)}, {"modlogs": 1})
    )


@router.post("/issue/findexact")
async def get_exact(request: Request):
    req_info = await request.json()
    if req_info.get("_id"):
        del req_info["_id"]

    return utils.prepare_json(db.issues.find_one(req_info))


@router.put("/issue/{issue_id}")
async def update_issue(issue_id, request: Request):
    req_info = await request.json()

    issue_info = req_info["issue"]
    issue_info["category"] = issue_info["category"].lower()
    user_info = req_info["userInfo"]["data"]

    issue_info = {k: v for k, v in issue_info.items() if k != "playerData"}
    user_info = {k: user_info[k] for k in ["discord_id", "avatar", "username"]}

    issue_id = ObjectId(issue_id)
    issue_info.pop("id")

    issue = db.issues.find_one_and_update(
        {"_id": issue_id}, {"$set": issue_info}, upsert=False
    )

    diff = []

    for key, value in issue_info.items():
        if value == issue[key]:
            continue

        diff.append({"new": value, "old": issue[key], "key": key})

    webhooks.send_update_issue(diff, issue, user_info)

    return utils.prepare_json(issue)


@router.post("/issue")
async def create_issue(request: Request):
    req_info = await request.json()
    req_info["category"] = req_info["category"].lower()

    # TODO: check to see if user_id is allowed to create this issue on the project_name

    try:
        issue = db.issues.insert_one(req_info)
    except:
        print(traceback.format_exc())
        raise HTTPException(status_code=503, detail="Unable write issue to database")

    webhooks.send_new_issue(req_info)
    return utils.prepare_json(issue.inserted_id)


@router.delete("/issue/{issue_id}")
async def delete_issue(issue_id, request: Request):
    req_info = await request.json()
    user_info = {k: req_info[k] for k in ["discord_id", "avatar", "username"]}

    issue = db.issues.find_one({"_id": ObjectId(issue_id)})
    db.issues.find_one_and_delete({"_id": ObjectId(issue_id)})

    webhooks.send_deleted_issue(issue, user_info)
