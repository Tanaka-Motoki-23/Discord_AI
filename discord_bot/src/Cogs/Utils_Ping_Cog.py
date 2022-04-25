from discord.ext import commands

"""
Bot接続を確認するためのシンプルなコマンド。

コマンド : <prefix>Ping

「pong!」と返信します。
"""


def setup(bot):
    bot.add_cog(Utils_Ping_Cog(bot))


class Utils_Ping_Cog(commands.Cog):
    # 接続時の初期設定
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Ping ready.")

    # Pingコマンド
    @commands.command(name="Ping")
    async def ping(self, ctx):
        await ctx.send("pong!")
