# Botの起動
.PHONY: start_bot
start_bot:
	mkdir -p $(SAVE_WAV_PATH)
	python ./src/bot_client.py
	
# lintをかける
.PHONY: lint
lint:
	poetry run pysen run lint

# format違反をある程度自動修正する
.PHONY: format
format:
	poetry run pysen run format
