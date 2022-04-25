import asyncio
import os
import random

import cv2
import discord
import mojimoji
import numpy as np
import sympy
from discord.ext import commands

IMAGE_ARCHIVE_PATH = os.environ.get("IMAGE_ARCHIVE_PATH")

"""
料理画像でファインチューニングしたStyleGAN2-ADAによって生成した画像を送信する。
see:https://github.com/NVlabs/stylegan2-ada-pytorch

コマンド : <prefix>MESHI generate num

一度に複数枚送信する場合、長方形になるようにグリッド形状を計算して配置する。
numは64*64といった数式でも指定可能。
画像は8MB未満になるようにリサイズする。
"""


def setup(bot):
    bot.add_cog(MESHI_Cog(bot))


class MESHI_Cog(commands.Cog):
    # 接続時の初期設定
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.image_path_list = [IMAGE_ARCHIVE_PATH + i for i in os.listdir(IMAGE_ARCHIVE_PATH)]
        print("MESHI ready.")

    @commands.group()
    async def MESHI(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.channel.send(
                "`MESHI generate` を利用出来ます！\n" + "> `AriesMESHI generate`: AIが飯テロ画像を生成します。\n"
            )

    @MESHI.command(name="generate", aliases=["gen"])
    async def generate(self, ctx, num="1"):
        async with ctx.channel.typing():
            num = mojimoji.zen_to_han(num)
            # sanitize
            for ele in num:
                if (
                    ele == "("
                    or ele == ")"
                    or ele == "+"
                    or ele == "-"
                    or ele == "*"
                    or ele == "/"
                    or ele == " "
                    or ele.isdecimal()
                ):
                    continue
                else:
                    await ctx.channel.send(num + "は数値に変換できません。")
                    return

            try:
                num = int(sympy.simplify(num))
            except Exception:
                await ctx.channel.send(num + "は数値に変換できません。")
                return

            if int(num) <= 0:
                num = 1
            else:
                num = int(num)

            max_num = 512 * 512
            if num > max_num:
                ctx.channel.send("1度に生成出来る飯テロ画像は" + str(max_num) + "個までです。")
                return

            color = discord.Color.random()
            start_embed = discord.Embed(color=color)
            author = "Generating MESHI..."
            start_embed.set_author(name=author)
            start_message = await ctx.channel.send(embed=start_embed)

            await self.bot.change_presence(
                activity=discord.Activity(type=discord.ActivityType.watching, name="飯テロGenerator")
            )

            image_id = [x for x in range(len(self.image_path_list))]
            if num <= len(self.image_path_list):
                sample_id = random.sample(image_id, k=num)
            else:
                sample_id = random.choices(image_id, k=num)

            image_grid_size = self.calc_matrix_size(num)

            horizontal_images = list()
            _iter = 0
            for _row in range(image_grid_size[0]):
                left_image = None
                for _concat in range(image_grid_size[1]):
                    image = cv2.imread(self.image_path_list[sample_id[_iter]])
                    if num > (8000 / 300):
                        H, W, C = image.shape
                        scale = max(np.sqrt(8000 / (num * 350)), 32 / 512)

                        image = cv2.resize(image, (int(W * scale), int(H * scale)))
                    if left_image is None:
                        left_image = image
                    else:
                        left_image = cv2.hconcat([left_image, image])

                    _iter += 1
                    if _iter % 1000 == 0:
                        await asyncio.sleep(0.1)
                        await self.bot.change_presence(
                            activity=discord.Game(name="iter:" + str(_iter) + "/" + str(num))
                        )

                horizontal_images.append(left_image.copy())

            above_image = None
            for horizontal_image in horizontal_images:
                if above_image is None:
                    above_image = horizontal_image
                else:
                    above_image = cv2.vconcat([above_image, horizontal_image])

            send_image_path = "./latest.jpg"
            cv2.imwrite(send_image_path, above_image)

            while True:
                size = os.path.getsize(send_image_path) / (1e3)
                print(size)

                if size < 8000:
                    break

                H, W, C = above_image.shape
                scale = np.sqrt(7500 / size)
                above_image = cv2.resize(above_image, (int(W * scale), int(H * scale)))
                cv2.imwrite(send_image_path, above_image)
                print(os.path.getsize(send_image_path) / (1e3))

            await asyncio.sleep(0.1)
            await self.bot.change_presence(activity=None)

        try:
            await ctx.channel.send(file=discord.File(send_image_path))
        except discord.errors.HTTPException:
            await ctx.channel.send("画像の送信中にエラーが発生しました...")

        await start_message.delete()

    def calc_matrix_size(self, image_num):
        factor_dict = sympy.factorint(image_num)
        factor = [1]
        for base, power in factor_dict.items():
            for _ in range(power):
                factor.append(base)

        x = 1
        y = 1
        for ele in factor[::-1]:
            if x * ele >= y * ele:
                y = y * ele
            else:
                x = x * ele
        if x >= y:
            select = [y, x]
        else:
            select = [x, y]

        return select
