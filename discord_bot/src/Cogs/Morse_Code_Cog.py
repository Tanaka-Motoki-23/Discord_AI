import asyncio
import os

import re
import discord
import pykakasi
import numpy as np
from discord.ext import commands

from modules import make_gif

Light_IMAGE_PATH = os.environ.get("Light_IMAGE_PATH")
TMP_PATH = os.environ.get("TMP_PATH")

"""
入力された文字列からモールス信号のGifアニメーションを生成して返信する。

コマンド : <prefix>Morse "" size

sizeは256とすると256kB以下になり、絵文字としてそのまま使える。
80000以下の任意のサイズを指定可能。
"""


def setup(bot):
    bot.add_cog(Morse_Code_Cog(bot))


class Morse_Code_Cog(commands.Cog):
    # 接続時の初期設定
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.morse_dict = self.make_morse_dict()
        print("Morse_Code ready.")

    @commands.command(name="Morse")
    async def Mosre(self, ctx, input_, size=8000):
        async with ctx.channel.typing():

            color = discord.Color.random()
            start_embed = discord.Embed(color=color)
            author = "Generating Morse Code..."
            start_embed.set_author(name=author)
            start_message = await ctx.channel.send(embed=start_embed)
            await self.bot.change_presence(
                activity=discord.Activity(type=discord.ActivityType.watching, name="Morse Code Generator")
            )

            limit_size = 8000
            try:
                if 0 < size <= limit_size:
                    size = int(size)
                else:
                    size = limit_size
            except Exception:
                size = limit_size

            text = self.convert_to_hepburn(input_)
            text = re.sub(r"\s+", " ", text)
            
            if len(text) >= 100:
                await ctx.channel.send(f"生成元[{text}] \n Error:文字数制限[100]を超えています。")
                await start_message.delete()
                return

            generate_embed = discord.Embed(color=color)
            author = text
            generate_embed.set_author(name=author)
            await ctx.channel.send(embed=generate_embed)
            
            print(text)
            dulation = self.text_to_morse(text)
            print(dulation)
            dulation = list(np.array(dulation, dtype='int32')*200)

            images_path = [Light_IMAGE_PATH+i for i in os.listdir(Light_IMAGE_PATH)]
            images_path = images_path * int((len(dulation)-1)/2)
            
            images_path.append(images_path[0])

            save_path = TMP_PATH + 'morse_latest.gif'
            make_gif.Generate_Adaptive_size_Gif(images_path,
                           is_transparency=True,
                           max_size=size,
                           save_path=save_path,
                           duration=dulation,
                           is_loop = False)

            await asyncio.sleep(0.1)
            await self.bot.change_presence(activity=None)

        try:
            await ctx.channel.send(file=discord.File(save_path))
        except discord.errors.HTTPException:
            await ctx.channel.send("画像の送信中にエラーが発生しました...")

        await start_message.delete()

    def text_to_morse(self, text):
        ele_spase = 1
        char_spase = 3
        word_spase = 7
        morse = list()

        word_start = False
        char_start = True
        for char in text:
            try:
                if char != ' ':
                    morse_code = self.morse_dict[char]
                    print(char, self.morse_dict[char])
            except Exception:
                print(f'{char} is not in morse_dict')
                continue

            if char == ' ':
                word_start = True
            else:
                char_start = True
                for code in morse_code:
                    if word_start == True:
                        morse.append(word_spase)
                        word_start = False
                        char_start = False
                    elif char_start == True:
                        morse.append(char_spase)
                        word_start = False
                        char_start = False
                    else:
                        morse.append(ele_spase)
                    morse.append(code)
        morse.append(word_spase)
        return morse
            

    def convert_to_hepburn(self, text):
        kakasi = pykakasi.kakasi()
        print(kakasi.convert(text))

        result = ''
        for word in kakasi.convert(text):
            result = result + word['hepburn'].lower() + ' '
        return result


            
    def make_morse_dict(self):
        morse_english = dict()
        morse_english['a'] = [1, 3] 
        morse_english['b'] = [3, 1, 1, 1]
        morse_english['c'] = [3, 1, 3, 1]
        morse_english['d'] = [3, 1 ,1]
        morse_english['e'] = [1]
        morse_english['f'] = [1, 1, 3, 1]
        morse_english['g'] = [3, 3, 1]
        morse_english['h'] = [1, 1, 1, 1]
        morse_english['i'] = [1, 1]
        morse_english['j'] = [1, 3, 3, 3]
        morse_english['k'] = [3, 1, 3]
        morse_english['l'] = [1, 3, 1, 1]
        morse_english['m'] = [3, 3]
        morse_english['n'] = [3, 1]
        morse_english['o'] = [3, 3, 3]
        morse_english['p'] = [1, 3, 3, 1]
        morse_english['q'] = [3, 3, 1, 3]
        morse_english['r'] = [1, 3, 1]
        morse_english['s'] = [1, 1, 1]
        morse_english['t'] = [3]
        morse_english['u'] = [1, 1, 3]
        morse_english['v'] = [1, 1, 1, 3]
        morse_english['w'] = [1, 3, 3]
        morse_english['x'] = [3, 1, 1, 3]
        morse_english['y'] = [3, 1, 3, 3]
        morse_english['z'] = [3, 3, 1, 1]

        morse_english['1'] = [1, 3, 3, 3, 3]
        morse_english['2'] = [1, 1, 3, 3, 3]
        morse_english['3'] = [1, 1, 1, 3, 3]
        morse_english['4'] = [1, 1, 1, 1, 3]
        morse_english['5'] = [1, 1, 1, 1, 1]
        morse_english['6'] = [3, 1, 1, 1, 1]
        morse_english['7'] = [3, 3, 1, 1, 1]
        morse_english['8'] = [3, 3, 3, 1, 1]
        morse_english['9'] = [3, 3, 3, 3, 1]
        morse_english['0'] = [3, 3, 3, 3, 3]

        morse_english['.'] = [1, 3, 1, 3, 1, 3]
        morse_english[','] = [3, 3, 1, 1, 3, 3]
        morse_english[':'] = [3, 3, 3, 1, 1, 1]
        morse_english['?'] = [1, 1, 3, 3, 1, 1]
        morse_english['-'] = [3, 1, 1, 1, 1, 3]
        morse_english['('] = [3, 1, 3, 3, 1]
        morse_english[')'] = [3, 1, 3, 3, 1, 3]
        morse_english['/'] = [3, 1, 1, 3, 1]
        morse_english['='] = [3, 1, 1, 1, 3]
        morse_english['+'] = [1, 3, 1, 3, 1]
        morse_english['"'] = [1, 3, 1, 1, 3, 1]
        morse_english['*'] = [3, 1, 1, 3]
        morse_english['@'] = [1, 3, 3, 1, 3, 1]

        return morse_english

    