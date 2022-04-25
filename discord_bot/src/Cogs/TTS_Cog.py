import os
import re
import traceback

import discord
import google.cloud.texttospeech as tts
from discord.ext import commands, tasks

"""
テキストチャンネル(TTS_CHANNEL_ID)に送信したメッセージを自動的にボイスチャンネル(DEFAULT_VOICE_CHANNEL_ID)で音声として再生する。

音声合成はGCPのwavenetを利用している。
see : https://cloud.google.com/text-to-speech?hl=ja/96

Discordコマンド
Botをボイスチャンネルに手動接続:<prefix>connect
(テキストチャンネル(TTS_CHANNEL_ID)にメッセージが送信されることでも自動的に接続する。)

Botをボイスチャンネルから手動切断:<prefix>disconnect
(ボイスチャンネルにBot以外にクライアントがいなくなることでも自動的に切断する。)
"""

API_KEY_PATH = os.environ.get("API_KEY_PATH")

DEFAULT_VOICE_CHANNEL_ID = int(os.environ.get("DEFAULT_VOICE_CHANNEL_ID"))
TTS_CHANNEL_ID = int(os.environ.get("TTS_CHANNEL_ID"))
SAVE_WAV_PATH = os.environ.get("SAVE_WAV_PATH")


def setup(bot):
    bot.add_cog(TTS_Cog(bot))


class TTS_Cog(commands.Cog):
    # 接続時の初期設定
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = self.bot.voice_clients
        self.tts_client = tts.TextToSpeechClient.from_service_account_json(API_KEY_PATH)
        self.wav_id = 0

    @commands.Cog.listener()
    async def on_ready(self):
        self.check_disconnect.start()
        print("TTS ready.")

    # TTS
    @commands.Cog.listener()
    async def on_message(self, ctx):
        if not (ctx.channel.id == TTS_CHANNEL_ID) or (ctx.author == self.bot.user):
            return
        if (
            ctx.content == self.bot.command_prefix + "dis"
            or ctx.content == self.bot.command_prefix + "connect"
            or ctx.content == self.bot.command_prefix + "disconnect"
        ):
            return

        # ボイスチャンネルに接続確認
        if len(self.bot.voice_clients) == 0:
            if ctx.author.voice is None:
                voice_channel = self.bot.guilds[0].get_channel(DEFAULT_VOICE_CHANNEL_ID)
                await voice_channel.connect()
            else:
                await ctx.author.voice.channel.connect()

        # 入力
        _input = ctx.content
        _input = self.remove_emoji(_input)
        if len(_input) >= 100:
            await ctx.reply("再生されるのは最大100文字までです。")
            _input = "ttsチャンネルで発言がありました。"

        # wav生成
        voice_file = self.text_to_wav(self.tts_client, voice_name="ja-JP-Wavenet-B", text=_input)
        try:
            audio_source = discord.FFmpegPCMAudio(voice_file)
            self.bot.voice_clients[0].play(audio_source)
        except Exception:
            traceback.print_exc()
            await ctx.reply("この文章を再生できませんでした。別のチャットを再生中の可能性があります。")

    def remove_emoji(self, text):
        text = re.sub(r"<.*>", "", text)
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
        text = emoji_pattern.sub(r"", text)
        return text

    def text_to_wav(self, client, voice_name: str, text: str):
        language_code = "-".join(voice_name.split("-")[:2])
        text_input = tts.SynthesisInput(text=text)
        voice_params = tts.VoiceSelectionParams(language_code=language_code, name=voice_name)
        audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.LINEAR16)

        response = client.synthesize_speech(
            input=text_input, voice=voice_params, audio_config=audio_config
        )

        filename = SAVE_WAV_PATH + f"{language_code}" + str(self.wav_id).zfill(4) + ".wav"
        self.wav_id += 1

        with open(filename, "wb") as out:
            out.write(response.audio_content)
            # print(f'Generated speech saved to "{filename}"')
        return filename

    # voice channel connection
    @commands.command(name="connect")
    async def connect(self, ctx):
        if ctx.message.author.voice is None:
            voice_channel = self.bot.guilds[0].get_channel(DEFAULT_VOICE_CHANNEL_ID)
            await voice_channel.connect()
        else:
            await ctx.message.author.voice.channel.connect()

    @commands.command(name="disconnect", aliases=["dis"])
    async def disconnect(self, ctx=None):
        try:
            await self.bot.voice_clients[0].disconnect()
        except Exception:
            pass

    @tasks.loop(seconds=60)
    async def check_disconnect(self):
        if len(self.bot.voice_clients) == 0:
            return
        if len(self.bot.voice_clients[0].channel.members) == 1:
            await self.disconnect()
