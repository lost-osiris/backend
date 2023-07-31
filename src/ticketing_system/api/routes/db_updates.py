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


@router.get("/update/updateallissuestonewdata")
async def update_all_issues_with_new_data():
    db.issues.update_many({}, {"$rename": {"updatedAt": "date"}})
    docs_without_dates = db.issues.find({"date": {"$exists": False}})
    for doc in docs_without_dates:
        db.issues.update_one({"_id": doc["_id"]}, {"$set": {"date": current_utc_time}})
