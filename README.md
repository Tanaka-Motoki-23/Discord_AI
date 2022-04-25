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
# Discrord Botのアクセストークン see:https://discordpy.readthedocs.io/ja/latest/discord.html
export TOKEN = '***********************************************************************'

# GPT-2の学習に利用したtwitterアーカイブ
export TWEET_ARCHIVE_PATH ='../resources/GPT-2/tweet_archive/tweet.js'

# 推論に利用するGPT-2のモデルパラメータ
export MODEL_PATH = '../resources/GPT-2/model_param/checkpoint-150000/'

# StyleGAN2-ADAで生成した料理画像の保存先
export IMAGE_ARCHIVE_PATH = '../resources/StyleGAN2_ADA/generated_images/'

