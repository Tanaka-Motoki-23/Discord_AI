# Discord_AI
Discord_AI 開発用プロジェクトレポジトリ

## レポジトリのクローン

```bash
git clone https://github.com/Tanaka-Motoki-23/Discord_AI.git
```

## Requirements

docker-compose

### install docker-compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
```

```bash
sudo chmod +x /usr/local/bin/docker-compose
```

```bash
docker-compose -v
```

### 環境構築手順
#### 環境変数の設定
.envrcの作成
```bash
touch .envrc
```

環境変数を.envrcに設定

記載してあるパスやIDは例なので適宜変更してください
```bash
# GPT-2の学習に利用したtwitterアーカイブ
export TWEET_ARCHIVE_PATH ='../resources/GPT-2/tweet_archive/tweet.js'

# 推論に利用するGPT-2のモデルパラメータ
export MODEL_PATH = '../resources/GPT-2/model_param/checkpoint-150000/'

# StyleGAN2-ADAで生成した料理画像群
export IMAGE_ARCHIVE_PATH = '../resources/StyleGAN2_ADA/generated_images/'

#GCPのTTSを利用するためのAPI key
#see : https://cloud.google.com/text-to-speech?hl=ja/96
export API_KEY_PATH = 'src/GCP/key/ai-tts-abcdefghijk.json'

#TTSで合成した音声データの保存先
export SAVE_WAV_PATH  = '../resources/GCP/generated_speech/'

#OpneAI APIをを利用するためAPI keyとOrganization ID
#see : https://openai.com/api/
export OPENAI_API_KEY = '***********************************************************************'
export OPENAI_ORGANIZATION  = "***************************"

#Botを利用するサーバーの設定
# Discrord Botのアクセストークン see:https://discordpy.readthedocs.io/ja/latest/discord.html
export TOKEN = '***********************************************************************'

#自然言語対話Botを利用するチャンネルID
export FREE_TALK_CHANNEL_ID = 11111111111111111

#TTSを利用するメインのボイスチャンネルID
export DEFAULT_VOICE_CHANNEL_ID = 11111111111111112

#TTSで発言させるテキストチャンネルID
export TTS_CHANNEL_ID = 11111111111111113

#匿名機能を利用して会話するテキストチャンネルID
export ANONYMOUS_CHANNEL_ID = 11111111111111114
```
#### dockerの設定
dockerコンテナのビルド
```
make build_bot
```
ビルドされたコンテナを立ち上げる
```
make up_bot
```
コンテナに入る
```
make exec_bot
```
コンテナを停止させる
```
make down
```
- - -

### 実行方法
#### 実行に必要なデータ
 - GPT-2の学習済みモデル
 - 学習に利用したTwitterアーカイブ
 - StyleGAN2-ADAで生成した料理画像群
 - TTSを利用するためのCGPのAPI key
 - GPT-3を利用するためのOpenAI APIのAPI key

#### 実行コマンド
##### コンテナを立ち上げた状態で以下のコマンドを実行する
Botクライアントの起動
```
make start_bot
```
- - -

# Botの機能詳細
## GPT-2を利用した自然言語対話AI
Discordサーバー内のチャンネルに送信された内容を自動で取得し、対話文を生成して返信します。
メッセージに飯テロをするという趣旨の内容があれば、GANで生成した料理画像を添付します。

## GPT-3を利用した小説生成AI
小説のタイトルと主人公と長さを入力すると、入力に合った小説を生成します。
コマンド
```
<prefix>STORY "タイトル" "主人公名" "長さ(short,middle,long,verylong)"
```


