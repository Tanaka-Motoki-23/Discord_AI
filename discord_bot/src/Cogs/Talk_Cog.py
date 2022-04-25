import asyncio
import json
import os
import random
import re
import traceback

import cv2
import discord
import mojimoji
import numpy as np
import sympy
from discord.ext import commands
from janome.tokenizer import Tokenizer
from transformers import AutoModelForCausalLM, T5Tokenizer

TWEET_ARCHIVE_PATH = os.environ.get("TWEET_ARCHIVE_PATH")
MODEL_PATH = os.environ.get("MODEL_PATH")
FREE_TALK_CHANNEL_ID = int(os.environ.get("FREE_TALK_CHANNEL_ID"))
IMAGE_ARCHIVE_PATH = os.environ.get("IMAGE_ARCHIVE_PATH")

"""
FREE_TALK_CHANNEL_IDにおいて、自然言語で対話を行う。

モデルはTwitterアーカイブでファインチューニングしたGPT-2を利用。
see:https://huggingface.co/rinna/japanese-gpt2-medium

会話中に届くメッセージは形態素解析を行い、飯テロをするという趣旨の内容であれば、GANで生成した料理画像を添付。
モデルはStyleGAN2-ADAを利用。画像は予め推論して保存しておく。
see:https://github.com/NVlabs/stylegan2-ada-pytorch
"""


def setup(bot):
    bot.add_cog(Talk_Cog(bot))


class Talk_Cog(commands.Cog):
    # 接続時の初期設定
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.tweets = list()
        self.tokenizer = T5Tokenizer.from_pretrained("rinna/japanese-gpt2-medium")
        self.model = AutoModelForCausalLM.from_pretrained(MODEL_PATH)
        self.image_path_list = [IMAGE_ARCHIVE_PATH + i for i in os.listdir(IMAGE_ARCHIVE_PATH)]

        memory_conversation = 3
        self.conversation = list()
        for _ in range(memory_conversation):
            self.conversation.append("")

        with open(TWEET_ARCHIVE_PATH, "r", encoding="utf-8") as f:
            data = f.read()
        all_tweets = json.loads(data[data.find("[") :])
        for tweet in all_tweets:
            if not tweet["tweet"]["full_text"][:2] == "RT":
                self.tweets.append(tweet)
        print("free talk AI ready.")

    """free talk"""

    @commands.Cog.listener()
    async def on_message(self, ctx):
        if not (ctx.channel.id == FREE_TALK_CHANNEL_ID) or (ctx.author == self.bot.user):
            return

        _input = ctx.content
        _input = _input.lower()
        _input = self.remove_emoji(_input)
        _input = mojimoji.zen_to_han(_input)

        if await self.easter_egg(ctx, _input):
            return
        if await self.meshitero_check(ctx, _input):
            return

        async with ctx.channel.typing():
            self.conversation = [_input] + self.conversation[:-1]
            now_conversation = ""
            for pre_input in self.conversation:
                now_conversation = pre_input + "\n" + now_conversation
            text = self.generate_text(
                now_conversation, max_length=len(now_conversation) + 50, min_length=5
            )
            self.conversation = [text] + self.conversation[:-1]
        await ctx.channel.send(text)

    def remove_emoji(self, text):
        text = re.sub(r"<.*>", "(嬉)", text)
        # 正規表現パターンを構築
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "🥺"
            "]+",
            flags=re.UNICODE,
        )
        text = emoji_pattern.sub(r"(泣)", text)
        return text

    async def meshitero_check(self, ctx, _input):
        janome_tokenizer = Tokenizer()
        token_list = list()
        for token in janome_tokenizer.tokenize(_input):
            token_list.extend(str(token).split("\t")[1].split(","))

        if (
            "メシ" in token_list
            or "ﾒｼ" in token_list
            or "meshi" in token_list
            or "meshitero" in token_list
            or "テロ" in token_list
            or "ﾃﾛ" in token_list
        ) and (
            "やる" in token_list
            or "する" in token_list
            or "ダシ" in token_list
            or "ヨロ" in token_list
            or "よろしい" in token_list
            or "デキ" in token_list
            or "くださる" in token_list
        ):

            async with ctx.channel.typing():
                is_meshitero = True
                num = 1
                for ele in token_list:
                    if ele.isdigit():
                        num = int(ele)
                        break
                await ctx.channel.send(
                    self.generate_text(_input=_input, max_length=len(_input) + 50)
                )

                max_num = 1000
                if num > max_num:
                    num = max_num
                await self.generate_meshitero(ctx=ctx, num=int(num))

        else:
            is_meshitero = False
        return is_meshitero

    async def easter_egg(self, ctx, _input):
        if _input == "めしてろ":
            async with ctx.channel.typing():
                is_easter = True
                eggs = [
                    "「Please recommend」(飯テロはあらゆる人に勧める)",
                    "「That's possible」(飯テロの可能性は無限)",
                    "「keep an eye on it」(された飯テロは無視したら目潰しの刑)",
                ]
                egg = random.choice(eggs)
                await ctx.channel.send(egg)
        else:
            is_easter = False
        return is_easter

    def generate_text(self, _input, do_sample=True, max_length=40, min_length=1, top_k=10):
        model_input = self.tokenizer.encode(_input, return_tensors="pt")
        output = self.model.generate(
            input_ids=model_input,
            do_sample=do_sample,
            max_length=max_length,
            min_length=min_length,
            top_k=top_k,
            num_return_sequences=1,
        )
        out_list = self.tokenizer.batch_decode(output)
        text = out_list[0]
        print(text)

        try:
            text = text.split("</s>", maxsplit=1)[1]
            text = re.sub(r"</s>", "", text)
            if random.random() < 0.2:
                text = re.sub(r"<unk>", "😡", text)
            else:
                text = re.sub(r"<unk>", "😭", text)
            text = re.sub(r"@.\S+\s*", "", text)
            text = re.sub(r"#.\S+\s*", "", text)
            text = re.sub(r"(pic)\S+\s*", "", text)
            text = re.sub(r"(twitter.com)\S+\s*", "", text)
            text = re.sub(r"(https?|ftp)(:\/\/[-_\.!~*\'()a-zA-Z0-9;\/?:\@&=\+$,%#]+)", "", text)
            text = re.sub(r"\(\s*\S\s*\)", "😭", text)

            end_figs = ["😭", "😡", ")", "。", "」", "?", "!", ".", "♪"]
            text = self.cut_end(text, end_figs)

            sep_figs = ["😭", "😡", "。", "?", "!"]
            text = self.cut_first_sep(text, sep_figs)

            if bool(re.sub(r"\s*", "", text)) is False:
                text = "うーん...😭"

        except Exception:
            traceback.print_exc()
            text = "...😭"
        return text

    def cut_first_sep(self, text, sep_figs=None):
        if sep_figs is None:
            sep_figs = ["。"]
        fig_index = list()
        for sep_fig in sep_figs:
            fig_index.append(text.find(sep_fig))

        fig_index = [len(text) if index == -1 else index for index in fig_index]

        text = text[: min(fig_index) + 1]
        return text

    def cut_end(self, text, end_figs="。"):
        fig_index = list()
        for end_fig in end_figs:
            fig_index.append(text.rfind(end_fig))

        if max(fig_index) == -1:
            pass
        else:
            text = text[: max(fig_index) + 1]
        return text

    async def generate_meshitero(self, ctx, num=1):
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

    @commands.group()
    async def AI(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.channel.send(
                '`AI excavation` または `AI generate "質問文"` を利用出来ます！\n'
                + "> `AI excavation`: 学習に用いたデータをサンプリングします。\n"
                + '> `AI generate "質問文"`: 新たなテキストを生成します。'
            )

    @AI.command(name="excavation", aliases=["exc"])
    async def excavation(self, ctx, num=1):
        if int(num) < 0:
            num = 1

        max_num = 10
        if num > max_num:
            await ctx.channel.send("1度にサンプリングできるデータは" + str(max_num) + "個までです。")
            return

        color = discord.Color.random()
        start_embed = discord.Embed(color=color)
        author = "サンプリング中..."
        start_embed.set_author(name=author)
        start_message = await ctx.channel.send(embed=start_embed)
        blacks = random.sample(self.tweets, num)
        for black in blacks:
            try:
                media = black["tweet"]["entities"]["media"][0]
                await ctx.channel.send(media["expanded_url"])
            except KeyError:
                color = discord.Color.random()
                black_embed = discord.Embed(color=color)
                author = "AI"
                black_embed.set_author(name=author)
                value = self.adjust_text_tweet(black)
                black_embed.add_field(name=black["tweet"]["created_at"], value=value, inline=False)
                await ctx.channel.send(embed=black_embed)

        await start_message.delete()

    def adjust_text_tweet(self, tweet):
        text = tweet["tweet"]["full_text"]
        text = re.sub(r"@.\S+\s*", "@someone\n", text)
        return text

    @excavation.error
    async def excavation_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.channel.send(
                "`AI excavation`を利用出来ます！\n" + '> `AI excavation`には"質問文"は必要ありません。'
            )

    @AI.command(name="generate", aliases=["gen"])
    async def generate(self, ctx, _input: str, num=1):

        if int(num) < 0:
            num = 1

        max_num = 10
        if num > max_num:
            await ctx.channel.send("1度に生成できるテキストは" + str(max_num) + "個までです。")
            return

        color = discord.Color.random()
        start_embed = discord.Embed(color=color)
        author = "生成中..."
        start_embed.set_author(name=author)
        start_message = await ctx.channel.send(embed=start_embed)

        model_input = self.tokenizer.encode(_input, return_tensors="pt")
        output = self.model.generate(
            input_ids=model_input,
            do_sample=True,
            max_length=100,
            min_length=10,
            top_k=40,
            num_return_sequences=int(num),
        )

        color = discord.Color.random()
        black_embed = discord.Embed(color=color)
        author = "AI"
        black_embed.set_author(name=author)

        out_list = self.tokenizer.batch_decode(output)
        for text in out_list:
            try:
                text = text.split("</s>", maxsplit=1)[1]
                text = re.sub(r"</s>", "", text)
                text = re.sub(r"<unk>", "", text)
            except IndexError:
                text = "..."
            black_embed.add_field(name=_input, value=text, inline=False)

        await ctx.channel.send(embed=black_embed)
        await start_message.delete()

    @generate.error
    async def generate_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.channel.send(
                '`AI generate "質問文"` を利用出来ます！\n' + '> 質問文はダブルクオーテーション(")で括ってください。'
            )
