import discord
import os
from discord import Color
from dotenv import load_dotenv
from pathlib import Path
from . import utils

load_dotenv()

IGNORED_UPDATE_EVENT_KEYS = ["modlogs", "description", "attachments", "project_id"]
# webhook = discord.SyncWebhook.from_url(os.getenv("WEBHOOK_URL"))
webhook = discord.SyncWebhook.from_url(
    "https://discordapp.com/api/webhooks/1075674946715525120/uHhuAUGWxX3-QfipUTapVmmHK0Ch9L31r0zkpqB7zj8xhTvH5y2kuAb7XZUtxmlEtg-3",
)


def create_embed(message, color, title):
    return discord.Embed(title=title, description=message, color=color)


def send_new_issue(issue):
    description = f"[click here to see issue in website](https://modforge.gg/issue/{issue['_id']})"
    discord_id = issue["playerData"]["discord_id"]
    discord_name = issue["playerData"]["name"]
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

    webhook.send(embed=embed)


def send_update_issue(diff, issue, user_info):
    summary_for_title = utils.to_title_case(issue["category"])
    description = f"[{issue['summary']}](https://modforge.gg/issue/{issue['_id']})"
    ignored_update_list = []
    message_list = []
    discord_id = user_info["discord_id"]
    discord_name = user_info["username"]
    author_name = issue["playerData"]["name"]
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

    for i in diff:
        if i["key"] in IGNORED_UPDATE_EVENT_KEYS:
            ignored_update_list.append(i["key"])
        else:
            message_list.append({f"{i['key']}": f"{i['old']} \u2b95 {i['new']}\n"})

    if len(ignored_update_list) > 0:
        for message in message_list:
            for k, v in message.items():
                if "%20" in v:
                    message[k] = v.replace("%20", " ")
                    v = message[k]

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
        embed.add_field(
            name="", value=f"{', '.join(ignored_update_list)} updated", inline=False
        )

        embed.set_footer(
            text="Description, Modlogs, and Attachments not shown, click above link to view"
        )
        webhook.send(embed=embed)

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
        webhook.send(embed=embed)


def send_deleted_issue(issue, user_info):
    discord_id = user_info["discord_id"]
    discord_name = user_info["username"]
    author_name = issue["playerData"]["name"]
    discord_avatar_id = user_info["avatar"]
    category = issue["category"]

    if "%20" in category:
        category = category.replace("%20", " ")

    color = Color.green()

    embed = discord.Embed(color=color, title=f"{author_name}'s Issue was Deleted!")

    embed.add_field(name="Summary", value=issue["summary"], inline=False)
    embed.add_field(name="Player", value=issue["playerData"]["name"], inline=True)
    embed.add_field(name="Type", value=issue["type"], inline=False)
    embed.add_field(name="Category", value=category, inline=True)
    embed.add_field(name="Version", value=issue["version"], inline=True)

    embed.set_author(
        name=discord_name,
        icon_url=f"https://cdn.discordapp.com/avatars/{discord_id}/{discord_avatar_id}.png",
    )
    webhook.send(embed=embed)


def send_join_waitlist(user_info):
    color = Color.blurple()
    discord_id = user_info["discord_id"]
    discord_name = user_info["username"]
    discord_avatar_id = user_info["avatar"]

    embed = discord.Embed(
        color=color, title=f"{discord_name} has requested to join Pale Court"
    )

    embed.set_author(
        name=discord_name,
        icon_url=f"https://cdn.discordapp.com/avatars/{discord_id}/{discord_avatar_id}.png",
    )
    webhook.send(embed=embed)


def send_accept_waitlist(user_info):
    color = Color.green()
    discord_id = user_info["discord_id"]
    discord_name = user_info["username"]
    discord_avatar_id = user_info["avatar"]

    embed = discord.Embed(
        color=color, title=f"{discord_name} has been accepted into Pale Court"
    )

    embed.set_author(
        name=discord_name,
        icon_url=f"https://cdn.discordapp.com/avatars/{discord_id}/{discord_avatar_id}.png",
    )
    webhook.send(embed=embed)


def send_reject_waitlist(user_info):
    color = Color.red()
    discord_id = user_info["discord_id"]
    discord_name = user_info["username"]
    discord_avatar_id = user_info["avatar"]

    embed = discord.Embed(
        color=color, title=f"{discord_name} was rejected from joining Pale Court"
    )

    embed.set_author(
        name=discord_name,
        icon_url=f"https://cdn.discordapp.com/avatars/{discord_id}/{discord_avatar_id}.png",
    )
    webhook.send(embed=embed)
