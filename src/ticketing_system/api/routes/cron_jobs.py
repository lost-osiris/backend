from fastapi import APIRouter

from .. import utils
from .. import webhooks

from datetime import datetime, timedelta
import math

router = APIRouter(prefix="/api")
db = utils.get_db_client()


def discord_timestamp_converter(datetime):
    return math.floor(datetime.timestamp())


@router.get("/cron/delete-warning")
async def warning_of_deletion():
    current_time = datetime.now()
    one_month_ago = current_time - timedelta(days=30)
    in_two_days = current_time + timedelta(days=2)

    get_eligible_issues = utils.prepare_json(
        db.issues.find(
            {"date": {"$lt": one_month_ago}, "archived": True},
            {"project_id": 1, "discord_id": 1, "id": 1, "category": 1},
        )
    )
    webhook_info = []
    unique_categories = set()
    for issue in get_eligible_issues:
        discord_info = utils.prepare_json(
            db.users.find_one(
                {"discord_id": issue["discord_id"]},
                {"username": 1},
            )
        )
        if discord_info is None:
            continue
        webhook_info.append(
            {
                "issue_link": f"http://localhost:3000/project/{issue['project_id']}/issue/{issue['id']}",
                "discord_name": discord_info["username"],
                "category": issue["category"],
            }
        )
        unique_categories.add(issue["category"])

    unique_categories_list = list(unique_categories)
    if len(webhook_info) > 0:
        return webhooks.send_cron_delete_warning(
            webhook_info,
            discord_timestamp_converter(in_two_days),
            unique_categories_list,
        )


@router.delete("/cron/delete-expired")
async def delete_expired_issues():
    current_time = datetime.now()
    one_month_ago = current_time - timedelta(days=30)

    get_eligible_issues = utils.prepare_json(
        db.issues.find_one_and_delete(
            {"date": {"$lt": one_month_ago}, "archived": True},
            {"project_id": 1, "discord_id": 1, "id": 1, "category": 1},
        )
    )

    return webhooks.send_cron_delete_success(len(get_eligible_issues))
