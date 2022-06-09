import asyncio
import os
import random

import cv2
import discord
import numpy as np

import torch as th
from discord.ext import commands
from PIL import Image
from glide_text2im.download import load_checkpoint
from glide_text2im.model_creation import (
    create_model_and_diffusion,
    model_and_diffusion_defaults,
    model_and_diffusion_defaults_upsampler
)


GLIDE3_MODEL_PATH = os.environ.get("GLIDE3_MODEL_PATH")
GLIDE3_MODEL_UP_PATH = os.environ.get("GLIDE3_MODEL_UP_PATH")
TMP_PATH = os.environ.get("TMP_PATH")

"""
GLIDE-3によって生成した画像を送信する。
see:https://github.com/openai/glide-text2im

コマンド : <prefix>text2img generate "prompt"

promptとして与えられた画像を送信します。　
画像は８MB未満になるようにリサイズする。
"""

def setup(bot):
    bot.add_cog(Text2img_Cog(bot))


class Text2img_Cog(commands.Cog):
    # 接続時の初期設定
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.has_cuda = th.cuda.is_available()
        self.device = th.device('cpu' if not self.has_cuda else 'cuda')

        self.options = model_and_diffusion_defaults()
        self.options['use_fp16'] = self.has_cuda
        self.options['timestep_respacing'] = '100' # 高速サンプリングに100の拡散ステップを使用

        self.model, self.diffusion = create_model_and_diffusion(**self.options)
        self.model.eval()
        if self.has_cuda:
            self.model.convert_to_fp16()
        self.model.to(self.device)
        self.model.load_state_dict(th.load(GLIDE3_MODEL_PATH, map_location=self.device))

                # アップサンプラーモデルの生成
        self.options_up = model_and_diffusion_defaults_upsampler()
        self.options_up['use_fp16'] = self.has_cuda
        self.options_up['timestep_respacing'] = 'fast27' # 高速サンプリングに27の拡散ステップを使用
        self.model_up, self.diffusion_up = create_model_and_diffusion(**self.options_up)
        
        self.model_up.eval()
        if self.has_cuda:
            self.model_up.convert_to_fp16()
        self.model_up.to(self.device)
        self.model_up.load_state_dict(th.load(GLIDE3_MODEL_UP_PATH, map_location=self.device))
        print("GLIDE-3 ready.")

    @commands.group()
    async def Text2img(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.channel.send(
                '`Text2img generate` を利用出来ます！\n' + '> `AriesText2img generate "文章"`: AIが文章から画像を生成します。\n'
            )

    @Text2img.command(name="generate", aliases=["t2i"])
    async def generate(self, ctx, prompt):
        async with ctx.channel.typing():
            color = discord.Color.random()
            start_embed = discord.Embed(color=color)
            author = "Generating Image..."
            start_embed.set_author(name=author)
            start_message = await ctx.channel.send(embed=start_embed)

            generated_image = await self.predict(prompt)

            send_image_path = TMP_PATH + "./latest.jpg"
            generated_image.save(send_image_path)

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


    async def predict(self, prompt):
        batch_size = 1
        guidance_scale = 3.0

        # このパラメータを調整して、256x256画像の鮮明度を調整。
        # 1.0の方がシャープだが、アーティファクトが粗くなることがある。
        upsample_temp = 0.997

        ###########################
        # ベースモデルからのサンプリング #
        ###########################

        # モデルにフィードするテキストトークンを作成
        tokens = self.model.tokenizer.encode(prompt)
        tokens, mask = self.model.tokenizer.padded_tokens_and_mask(
            tokens, self.options['text_ctx']
        )

        # 分類子なしのガイダンストークン(空)を作成
        full_batch_size = batch_size * 2
        uncond_tokens, uncond_mask = self.model.tokenizer.padded_tokens_and_mask(
            [], self.options['text_ctx']
        )

        # トークンを一緒にモデルのkwargsにパック
        model_kwargs = dict(
            tokens=th.tensor(
                [tokens] * batch_size + [uncond_tokens] * batch_size, device=self.device
            ),
            mask=th.tensor(
                [mask] * batch_size + [uncond_mask] * batch_size,
                dtype=th.bool,
                device=self.device,
            ),
        )

        # 分類器のないガイダンスサンプリング関数の作成
        def model_fn(x_t, ts, **kwargs):
            half = x_t[: len(x_t) // 2]
            combined = th.cat([half, half], dim=0)
            model_out = self.model(combined, ts, **kwargs)
            eps, rest = model_out[:, :3], model_out[:, 3:]
            cond_eps, uncond_eps = th.split(eps, len(eps) // 2, dim=0)
            half_eps = uncond_eps + guidance_scale * (cond_eps - uncond_eps)
            eps = th.cat([half_eps, half_eps], dim=0)
            return th.cat([eps, rest], dim=1)

        # ベースモデルからのサンプル
        self.model.del_cache()
        samples = self.diffusion.p_sample_loop(
            model_fn,
            (full_batch_size, 3, self.options["image_size"], self.options["image_size"]),
            device=self.device,
            clip_denoised=True,
            progress=True,
            model_kwargs=model_kwargs,
            cond_fn=None,
        )[:batch_size]
        self.model.del_cache()

        ############################
        # 64x64の画像をアップサンプリング #
        ############################

        tokens = self.model_up.tokenizer.encode(prompt)
        tokens, mask = self.model_up.tokenizer.padded_tokens_and_mask(
            tokens, self.options_up['text_ctx']
        )

        # モデル条件付け辞書の作成
        model_kwargs = dict(
            # Low-res image to upsample.
            low_res=((samples+1)*127.5).round()/127.5 - 1,

            # テキストトークン
            tokens=th.tensor(
                [tokens] * batch_size, device=self.device
            ),
            mask=th.tensor(
                [mask] * batch_size,
                dtype=th.bool,
                device=self.device,
            ),
        )

        # ベースモデルからのサンプル
        self.model_up.del_cache()
        up_shape = (batch_size, 3, self.options_up["image_size"], self.options_up["image_size"])
        up_samples = self.diffusion_up.ddim_sample_loop(
            self.model_up,
            up_shape,
            noise=th.randn(up_shape, device=self.device) * upsample_temp,
            device=self.device,
            clip_denoised=True,
            progress=True,
            model_kwargs=model_kwargs,
            cond_fn=None,
        )[:batch_size]
        self.model_up.del_cache()

        scaled = ((up_samples + 1)*127.5).round().clamp(0,255).to(th.uint8).cpu()
        reshaped = scaled.permute(2, 0, 3, 1).reshape([up_samples.shape[2], -1, 3])
        image = Image.fromarray(reshaped.numpy())

        return image