import discord
import time
import os
from discord import app_commands
from discord.ext import commands
from .issue_project.cog import IssueProject
from dotenv import load_dotenv


load_dotenv()

CHANNEL = "b"
CMD_CHANNEL = "b"
COMMAND_PREFIX = "!"
TOKEN = os.getenv("TOKEN")
SECRET = os.getenv("CLIENT_SECRET")
MY_GUILD = discord.Object(id=636623317180088321)
COOLDOWN_AMOUNT = 300.0  # seconds


intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)


last_executed = time.time()


def assert_cooldown():
    global last_executed
    if last_executed + COOLDOWN_AMOUNT < time.time():
        last_executed = time.time()
        return True
    return False


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    await bot.load_extension("src.ticketing_system.bot.issue_project.cog")


@bot.event
async def on_message(message):
    tram_list = ["tram", "trams"]
    risto_list = ["lord and savior", "supreme overlord", "fire emblem"]
    if message.mentions:
        whitelist_roles = [
            1117918920276463707,
            734974559761072169,
            1084931529991532619,
            1121841448363511874,
            1024504503388622848,
            693648003126263818,
        ]
        if message.author.bot:
            return
        for role in message.author.roles:
            if role.id in whitelist_roles:
                return
        user_mentioned = message.mentions[0]
        user_roles = user_mentioned.roles

        for role in user_roles:
            if role.id == 1121842647498227823:
                print("found don't ping!")
                await message.channel.send(
                    'Please do not ping people with the "don\'t ping" role \n https://media.discordapp.net/attachments/462200562620825600/919850262959640596/dontpingplz.png',
                    reference=message,
                    mention_author=True,
                )
                break

    if any(word in message.content.lower().split() for word in tram_list):
        print("saw tram")

        if not assert_cooldown():
            print("on cooldown")
            return

        if message.author.bot & assert_cooldown():
            return
        with open("src/ticketing_system/bot/tram_copypasta.md") as target:
            tram_reply = target.read()

            await message.channel.send(
                tram_reply, reference=message, mention_author=False
            )

    if any(word in message.content.lower() for word in risto_list):
        print("saw risto")

        if not assert_cooldown():
            print("on cooldown")
            return

        if message.author.bot & assert_cooldown():
            return
        await message.channel.send(
            "Bow down mortals \nhttps://cdn.discordapp.com/attachments/825530277694144542/1077734017790656583/image.png",
            reference=message,
            mention_author=False,
        )


def main():
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
