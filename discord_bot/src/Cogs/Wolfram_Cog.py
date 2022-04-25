import asyncio
import os
import traceback

import discord
import wolframalpha
from discord.ext import commands

WOLFRAM_APPID = os.environ.get("WOLFRAM_APPID")

"""
WolframAlpha APIを利用して、入力に対する計算結果を返します。
see : https://products.wolframalpha.com/api/documentation/

コマンド wolframalpha "target"

"""


def setup(bot):
    bot.add_cog(WolframCog(bot))


class WolframClient(object):
    def __init__(self, key):
        self.key = key
        self.client = wolframalpha.Client(key)

    # Processes a user query.
    def ask(self, queryText):
        res = self.client.query(queryText)
        src_list = list()

        for pod in res.pods:
            for sub in pod.subpods:
                src_list.append((pod.title, sub["img"]["@src"]))

        return src_list


class WolframCog(commands.Cog):
    # 接続時の初期設定
    def __init__(self, bot):
        self.bot = bot
        self.wolfram_client = WolframClient(WOLFRAM_APPID)

    @commands.Cog.listener()
    async def on_ready(self):
        print("Wolfram ready.")

    @commands.command(name="wolframalpha", aliases=["ASK"])
    async def request(self, ctx, target=None):
        if target is None:
            await ctx.send("targetが入力されていません。")
            return

        async with ctx.channel.typing():
            try:

                response = self.wolfram_client.ask(target)
            except Exception:
                await ctx.send("結果が見つかりませんでした。")
                traceback.print_exc()
                return

            color = discord.Color.random()
            max_num = 3
            for i in range(1, max_num + 1):
                try:
                    title, src = response[i]
                except Exception:
                    break
                embed = discord.Embed(color=color)
                embed.set_author(name=title)
                embed.set_image(url=src)
                await ctx.channel.send(embed=embed)
            await asyncio.sleep(0.1)
