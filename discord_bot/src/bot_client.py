import os
import traceback

import discord
from discord.ext import commands

# Bot Access Token
TOKEN = os.environ.get("TOKEN")
BOT_PREFIX = os.environ.get("BOT_PREFIX")

# ログの設定
# 読み込むコグ
INITIAL_EXTENSIONS = [
    "Cogs.Talk_Cog",
    "Cogs.MESHI_Cog",
    "Cogs.Utils_CleanUp_Cog",
    "Cogs.Utils_Ping_Cog",
    "Cogs.Anonymous_Cog",
    "Cogs.Wolfram_Cog",
    "Cogs.Story_Cog",
    "Cogs.TTS_Cog",
    "Cogs.Text2img_Cog",
    "Cogs.Morse_Code_Cog",
]


def bot_setup() -> discord.ext.commands.bot.Bot:
    intents = discord.Intents.default()
    intents.members = True
    client = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)
    for cog in INITIAL_EXTENSIONS:
        try:
            client.load_extension(cog)
        except Exception:
            traceback.print_exc()
    return client


def main() -> None:
    # Botの起動とDiscordサーバーへの接続
    bot = bot_setup()
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
