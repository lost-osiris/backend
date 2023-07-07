from fastapi import APIRouter, HTTPException
from bson import ObjectId
from .. import utils
from .. import auth
from ..models.issue_comment import IssueComment
from datetime import datetime

import traceback

router = APIRouter(prefix="/api")
db = utils.get_db_client()


@router.get("/issue/{issue_id}/comments")
async def get_issue_comments(issue_id, user: auth.UserDep):
    return utils.prepare_json(db.comments.find({"issue_id": ObjectId(issue_id)}))


@router.post("/issue/{issue_id}/comment")
async def put_issue_comments(issue_id, comment: IssueComment, user_auth: auth.UserDep):
    user = user_auth["token"].user

    try:
        r = db.issue_comments.insert_one(
            {
                **comment.dict(),
                "issue_id": ObjectId(issue_id),
                "created_at": datetime.utcnow(),
                "discord_id": user["discord_id"],
            }
        )
        return utils.prepare_json(r.inserted_id)
    except:
        print(traceback.format_exc())
        raise HTTPException(status_code=503, detail="Unable write issue to database")

    # TODO: Send webhook on new comment created


@router.delete("/comment/{comment_id}")
async def put_issue_comments(comment_id, user_auth: auth.UserDep):
    user = user_auth["token"].user

    comment = db.issue_comments.find_one({"_id": ObjectId(comment_id)})
    issue = db.issues.find_one({"_id": ObjectId(comment["issue_id"])})

    user_projects = [i for i in user["projects"] if i["id"] == issue["project_id"]]

    has_permissions = [
        i for i in user_projects if "maintainer" in i["roles"] in i["roles"]
    ]

    if has_permissions or comment["discord_id"] == user["discord_id"]:
        db.issue_comments.delete_one({"_id": ObjectId(comment_id)})
    else:
        raise HTTPException(
            status_code=403,
            detail="User does not have permissions delete comment.",
        )
