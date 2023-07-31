import discord
import os
from discord import Color
from dotenv import load_dotenv
from pathlib import Path
from . import utils

load_dotenv()

IGNORED_UPDATE_EVENT_KEYS = [
    "modlogs",
    "description",
    "attachments",
    "project_id",
    "summary",
    "date",
]
webhook_issues = discord.SyncWebhook.from_url(os.getenv("WEBHOOK_ISSUES"))
webhook_waitlist = discord.SyncWebhook.from_url(os.getenv("WEBHOOK_WAITLIST"))
webhook_comments = discord.SyncWebhook.from_url(os.getenv("WEBHOOK_COMMENTS"))

# webhook = discord.SyncWebhook.from_url(
#     "https://discordapp.com/api/webhooks/1075674946715525120/uHhuAUGWxX3-QfipUTapVmmHK0Ch9L31r0zkpqB7zj8xhTvH5y2kuAb7XZUtxmlEtg-3",
# )


def discord_button_view(style, label, url):
    view = discord.ui.View()
    button = discord.ui.Button(style=style, label=label, url=url)
    view.add_item(item=button)
    return view


def create_embed(message, color, title):
    return discord.Embed(title=title, description=message, color=color)


def send_new_issue(issue):
    description = f"[click here to see issue in website](https://modforge.gg/issue/{issue['_id']})"
    discord_id = issue["playerData"]["discord_id"]
    discord_name = issue["playerData"]["username"]
    discord_avatar_id = issue["playerData"]["avatar"]
    category = issue["category"]

    if "%20" in category:
        category = category.replace("%20", " ")

    if issue["type"] == "bug":
        color = Color.red()
    else:
        color = Color.yellow()

    embed = discord.Embed(title="Issue Created", color=color, description=description)

    embed.add_field(name="Summary", value=issue["summary"], inline=False)
    embed.add_field(name="Type", value=issue["type"], inline=False)
    embed.add_field(name="Category", value=category, inline=True)
    embed.add_field(name="Version", value=issue["version"], inline=True)

    embed.set_author(
        name=discord_name,
        icon_url=f"https://cdn.discordapp.com/avatars/{discord_id}/{discord_avatar_id}.png",
    )

    if not os.getenv("WEBHOOK_DISABLED"):
        webhook_issues.send(embed=embed)


def send_update_issue(diff, issue, user_info):
    summary_for_title = utils.to_title_case(issue["category"])
    description = f"[{issue['summary']}](https://modforge.gg/issue/{issue['_id']})"
    ignored_update_list = []
    message_list = []
    discord_id = user_info["discord_id"]
    discord_name = user_info["username"]
    author_name = issue["playerData"]["username"]
    discord_avatar_id = user_info["avatar"]

    embed = discord.Embed(
        title=f"{author_name}'s Issue on {summary_for_title} was Updated!",
        description=description,
        color=Color.blurple(),
    )
    embed.set_author(
        name=discord_name,
        icon_url=f"https://cdn.discordapp.com/avatars/{discord_id}/{discord_avatar_id}.png",
    )

    for i in [item for item in diff if item["key"] != "date"]:
        if i["key"] in IGNORED_UPDATE_EVENT_KEYS:
            ignored_update_list.append(i["key"])
        elif i["key"] == "os":
            new_values_as_string = ", ".join(str(value) for value in i.get("new", []))
            message_list.append({f"{i['key']}": f"{new_values_as_string}\n"})
        else:
            message_list.append({f"{i['key']}": f"{i['old']} \u2b95 {i['new']}\n"})

    if len(ignored_update_list) > 0:
        for message in message_list:
            for k, v in message.items():
                if "%20" in v:
                    message[k] = v.replace("%20", " ")
                    v = message[k]

                else:
                    embed.add_field(
                        name=k,
                        value=v,
                        inline=True,
                    )
        embed.add_field(
            name="", value=f"{', '.join(ignored_update_list)} updated", inline=False
        )

        embed.set_footer(
            text="Description, and Modlogs not shown, click above link to view"
        )
        if not os.getenv("WEBHOOK_DISABLED"):
            webhook_issues.send(embed=embed)

    elif len(ignored_update_list) == 0:
        for message in message_list:
            for k, v in message.items():
                if "%20" in v:
                    v = v.replace("%20", " ")
                if k == "summary":
                    embed.add_field(
                        name=k,
                        value=v,
                        inline=False,
                    )
                else:
                    embed.add_field(
                        name=k,
                        value=v,
                        inline=True,
                    )
        embed.set_footer(
            text="Description, Modlogs, and Attachments not shown, click above link to view"
        )

        if not os.getenv("WEBHOOK_DISABLED"):
            webhook_issues.send(embed=embed)


def send_deleted_issue(issue, user_info):
    discord_id = user_info["discord_id"]
    discord_name = user_info["username"]
    author_name = issue["playerData"]["username"]
    discord_avatar_id = user_info["avatar"]
    category = issue["category"]

    if "%20" in category:
        category = category.replace("%20", " ")

    color = Color.green()

    embed = discord.Embed(color=color, title=f"{author_name}'s Issue was Deleted!")

    embed.add_field(name="Summary", value=issue["summary"], inline=False)
    embed.add_field(name="Player", value=issue["playerData"]["username"], inline=True)
    embed.add_field(name="Type", value=issue["type"], inline=False)
    embed.add_field(name="Category", value=category, inline=True)
    embed.add_field(name="Version", value=issue["version"], inline=True)

    embed.set_author(
        name=discord_name,
        icon_url=f"https://cdn.discordapp.com/avatars/{discord_id}/{discord_avatar_id}.png",
    )
    if not os.getenv("WEBHOOK_DISABLED"):
        webhook_issues.send(embed=embed)


def send_join_waitlist(user_info):
    color = Color.blurple()
    discord_id = user_info["discord_id"]
    discord_name = user_info["username"]
    discord_avatar_id = user_info["avatar"]

    embed = discord.Embed(
        color=color,
        title=f"{discord_name} has requested to join Pale Court",
    )

    embed.set_thumbnail(
        url=f"https://cdn.discordapp.com/avatars/{discord_id}/{discord_avatar_id}.png",
    )
    if not os.getenv("WEBHOOK_DISABLED"):
        webhook_waitlist.send(
            embed=embed,
            view=discord_button_view(
                discord.ButtonStyle.green, "asdfasd", "google.com"
            ),
        )


def send_accept_waitlist(user_info):
    color = Color.green()
    discord_id = user_info["discord_id"]
    discord_name = user_info["username"]
    discord_avatar_id = user_info["avatar"]

    embed = discord.Embed(
        color=color,
        title=f"{discord_name} has been accepted into Pale Court as a {user_info['role']}",
    )

    embed.set_thumbnail(
        url=f"https://cdn.discordapp.com/avatars/{discord_id}/{discord_avatar_id}.png",
    )

    if not os.getenv("WEBHOOK_DISABLED"):
        webhook_waitlist.send(embed=embed)


def send_reject_waitlist(user_info):
    color = Color.red()
    discord_id = user_info["discord_id"]
    discord_name = user_info["username"]
    discord_avatar_id = user_info["avatar"]

    embed = discord.Embed(
        color=color, title=f"{discord_name} was rejected from joining Pale Court"
    )
    embed.set_thumbnail(
        url=f"https://cdn.discordapp.com/avatars/{discord_id}/{discord_avatar_id}.png",
    )

    if not os.getenv("WEBHOOK_DISABLED"):
        webhook_waitlist.send(embed=embed)


def send_created_comment(info):
    color = Color.green()
    discord_id = info["discord_id"]
    discord_name = info["username"]
    discord_avatar_id = info["avatar"]
    category = info["category"]
    issue_id = info["issue_id"]
    description = f"[{info['summary']}](https://modforge.gg/issue/{issue_id})"

    embed = discord.Embed(
        color=color,
        title=f"{discord_name} commented on an issue involving {category}",
        description=description,
    )
    embed.set_thumbnail(
        url=f"https://cdn.discordapp.com/avatars/{discord_id}/{discord_avatar_id}.png",
    )
    if not os.getenv("WEBHOOK_DISABLED"):
        webhook_comments.send(embed=embed)


def send_cron_delete_warning(info, discord_timestamp, category_list):
    color = Color.red()
    total_length_limit = 6000
    field_value_limit = 1024

    unique_categories = set(item["category"] for item in info)
    current_embed = discord.Embed(
        color=color,
        title=f"{len(info)} Issues will be deleted on <t:{discord_timestamp}:F>, <t:{discord_timestamp}:R>!",
        description="The following issues have been Archived over 30 days and are now marked for deletion. \nPlease review these issues to make sure anything you want to keep won't be deleted.",
    )

    def add_category_field(embed, category, field_value):
        if len(embed) + len(field_value) + len(f"{category}") <= total_length_limit:
            embed.add_field(name=f"{category}", value=field_value, inline=True)
            return True
        return False

    for category in category_list:
        if category in unique_categories:
            category_items = []
            current_value = ""
            for item in info:
                if item["category"] == category:
                    field_value = (
                        f"[{item['discord_name']}'s issue]({item['issue_link']})\n"
                    )
                    if len(current_value) + len(field_value) <= field_value_limit:
                        current_value += field_value
                    else:
                        category_items.append(current_value)
                        current_value = field_value

            # Add the remaining category items as a field to the current_embed
            if current_value:
                category_items.append(current_value)

            # Distribute category items across multiple embeds if needed
            for idx, item in enumerate(category_items):
                if not add_category_field(
                    current_embed,
                    category if idx == 0 else f"{category} ({idx + 1})",
                    item,
                ):
                    # Current embed is full, send it and create a new one
                    if not os.getenv("WEBHOOK_DISABLED"):
                        webhook_issues.send(embed=current_embed)
                    current_embed = discord.Embed(color=color)
                    add_category_field(
                        current_embed,
                        category if idx == 0 else f"{category} ({idx + 1})",
                        item,
                    )

    # Send the last embed (if any)
    if len(current_embed.fields) > 0:
        if not os.getenv("WEBHOOK_DISABLED"):
            webhook_issues.send(embed=current_embed)


def send_cron_delete_success(amount):
    color = Color.green()

    embed = discord.Embed(
        color=color,
        title=f"Successfully deleted {amount} issues",
        description=f"{amount} issues were Archived over 30 days, and have been deleted as a result.",
    )
    if not os.getenv("WEBHOOK_DISABLED"):
        webhook_comments.send(embed=embed)
