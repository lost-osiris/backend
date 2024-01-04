from fastapi import APIRouter, HTTPException
from bson import ObjectId
from .. import utils
from .. import auth
from .. import webhooks
from ..models.issue_comment import IssueComment
from datetime import datetime

import traceback

router = APIRouter(prefix="/api")
db = utils.get_db_client()


@router.get("/issue/{issue_id}/comments")
async def get_issue_comments(issue_id, user: auth.UserDep):
    return utils.prepare_json(db.comments.find({"issue_id": ObjectId(issue_id)}))


@router.post("/issue/{issue_id}/comment")
async def create_issue_comments(
    issue_id, comment: IssueComment, user_auth: auth.UserDep
):
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
        get_issue = utils.prepare_json(
            db.issues.find_one(
                {"_id": ObjectId(issue_id)},
                {"category": 1, "summary": 1, "project_id": 1},
            )
        )
        project = utils.prepare_json(
            db.projects.find_one({"_id": ObjectId(get_issue["project_id"])})
        )

        passing_info = {
            "issue_id": issue_id,
            "category": get_issue["category"],
            "summary": get_issue["summary"],
            "discord_id": user_auth["discord_id"],
            "avatar": user_auth["avatar"],
            "username": user_auth["username"],
        }

        webhooks.send_created_comment(passing_info, project["webhooks"]["comment"])

    except:
        print(traceback.format_exc())
        raise HTTPException(status_code=503, detail="Unable write comment to database")


@router.put("/comment/{comment_id}")
async def update_issue_comments(
    comment_id, comment: IssueComment, user_auth: auth.UserDep
):
    user = user_auth["token"].user
    old_comment = utils.prepare_json(
        db.issue_comments.find_one({"_id": ObjectId(comment_id)})
    )

    if not comment:
        raise HTTPException(
            status_code=404,
            detail="Comment not found",
        )

    if user["discord_id"] == old_comment["discord_id"]:
        try:
            db.issue_comments.find_one_and_update(
                {"_id": ObjectId(comment_id)},
                {
                    "$set": {
                        **comment.dict(),
                        "updated_at": datetime.utcnow(),
                    }
                },
                upsert=False,
            )
            return comment_id
        except:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=503, detail="Unable write comment to database"
            )
    else:
        raise HTTPException(
            status_code=403,
            detail="User does not have permissions edit comment.",
        )


@router.delete("/comment/{comment_id}")
async def delete_issue_comments(comment_id, user_auth: auth.UserDep):
    user = user_auth["token"].user

    comment = db.issue_comments.find_one({"_id": ObjectId(comment_id)})
    issue = db.issues.find_one({"_id": ObjectId(comment["issue_id"])})

    user_projects = [i for i in user["projects"] if i["id"] == str(issue["project_id"])]
    has_permissions = [i for i in user_projects if "maintainer" in i["roles"]]

    if has_permissions or comment["discord_id"] == user["discord_id"]:
        db.issue_comments.delete_one({"_id": ObjectId(comment_id)})
    else:
        raise HTTPException(
            status_code=403,
            detail="User does not have permissions delete comment.",
        )
