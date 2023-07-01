from fastapi import APIRouter, Request, HTTPException
from bson import ObjectId
from .. import utils
from .. import webhooks
import traceback
from datetime import datetime

router = APIRouter(prefix="/api")
db = utils.get_db_client()
current_utc_time = datetime.utcnow()


@router.get("/update/issue/updatefields")
async def update_id_fields():
    update_fields = db.issues.find({"playerData.id": {"$exists": True}}, {"modlogs": 0})
    return utils.prepare_json(update_fields)


@router.get("/update/issue/putprojectonissues")
async def update_all_issues_to_include_project():
    db.issues.update_many(
        {}, {"$set": {"project_id": ObjectId("63fe47296edfc3b387628861")}}
    )
    return "done"


@router.get("/update/issue/idtodiscordid")
async def update_all_issues_to_discord_id():
    db.issues.updateMany({}, {"$rename": {"playerData.id": "playerData.discord_id"}})


@router.get("/update/addblacklistfield")
async def update_all_users_to_include_ban_field():
    db.users.update_many({}, {"$set": {"banned": False}})


@router.get("/update/updateallissuestonewdata")
async def update_all_issues_with_new_data():
    names_and_ids = []
    all_issues = utils.prepare_json(db.issues.find({}, {"modlogs": 0}))
    for issue in all_issues:
        if "playerData" in issue:
            dict_to_push = {
                "issue_id": issue["id"],
                "discord_id": issue["playerData"]["id"],
                "updatedAt": current_utc_time,
            }

            names_and_ids.append(dict_to_push)
        else:
            pass

    for object in names_and_ids:
        issue = utils.prepare_json(
            db.issues.find_one_and_update(
                {"_id": ObjectId(object["issue_id"])},
                {
                    "$unset": {"playerData": 1},
                    "$set": {
                        "discord_id": object["discord_id"],
                        "updatedAt": object["updatedAt"],
                    },
                },
            )
        )

    # return names_and_ids
