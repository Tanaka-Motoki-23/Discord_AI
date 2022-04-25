# lintをかける
.PHONY: lint
lint:
	docker exec -it discord_bot_00 make lint

# format違反をある程度自動修正する
.PHONY: format
format:
	docker exec -it discord_bot_00 make format

.PHONY: test
test:
	poetry run pytest -s -vv ./tests

# Docker imageのビルド
.PHONY: build_bot
build_bot:
	docker-compose -f ./docker-compose.yml build discord_bot_00

# Docker imageの起動
.PHONY: up_bot
up_bot:
	docker-compose -f ./docker-compose.yml up -d discord_bot_00

# Docker imageの実行
.PHONY: exec_bot
exec_bot:
	docker exec -it discord_bot_00 bash

# Docker imageの停止
.PHONY: down
down:
	docker-compose -f ./docker-compose.yml down

# Botクライアントの起動
.PHONY: start_bot
start_bot:
	docker exec -it discord_bot_00 make start_bot