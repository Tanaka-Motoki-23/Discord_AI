import asyncio
import os

import discord
from discord.ext import commands

ANONYMOUS_CHANNEL_ID = int(os.environ.get("ANONYMOUS_CHANNEL_ID"))


def setup(bot):
    bot.add_cog(Anonymous_Cog(bot))


class Anonymous_Cog(commands.Cog):
    # 接続時の初期設定
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Anonymous talk ready.")

    """Anonymous post"""

    @commands.Cog.listener()
    async def on_message(self, ctx):
        if not type(ctx.channel) == discord.DMChannel or ctx.author.bot:
            return
        if ctx.author not in self.bot.guilds[0].members:
            return

        send_channel = self.bot.guilds[0].get_channel(ANONYMOUS_CHANNEL_ID)

        async with send_channel.typing():
            async with ctx.channel.typing():
                await asyncio.sleep(1)
                await send_channel.send(ctx.content)
            await ctx.channel.send(
                "メッセージを送信しました。\n"
                + "Guild : "
                + self.bot.guilds[0].name
                + "\n"
                + "Channel : "
                + send_channel.name
                + "\n"
                + "> "
                + ctx.content
            )
