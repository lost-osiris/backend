from fastapi import APIRouter, Request, HTTPException
from bson import ObjectId
from .. import utils
from .. import webhooks
import traceback
from datetime import datetime


router = APIRouter(prefix="/api")
db = utils.get_db_client()
current_utc_time = datetime.utcnow()


@router.get("/blogs")
async def get_all_blogs():
    all_blogs = db.blogs.find({})
    return utils.prepare_json(all_blogs)
