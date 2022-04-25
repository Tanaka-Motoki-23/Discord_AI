import asyncio

from discord.ext import commands

"""
コマンドを送信したチャンネルにおける最新"num"件のメッセージを削除する。

Discordコマンド : <prefix>Clean "num"
"""


def setup(bot):
    bot.add_cog(Utils_CleanUp_Cog(bot))


class Utils_CleanUp_Cog(commands.Cog):
    # 接続時の初期設定
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Utils CleanUp ready.")

    # Cleanコマンド
    @commands.command(name="Clean")
    @commands.has_permissions(manage_guild=True)
    async def clean(self, ctx, limit: int):
        await ctx.message.channel.purge(limit=limit)
        message = await ctx.channel.send("start new session...")
        await asyncio.sleep(3)
        await message.delete()

    @clean.error
    async def clean_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.channel.send('`AriesClean "num"` を利用出来ます！')
