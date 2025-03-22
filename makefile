# Makefile

.PHONY: rebuild build down

rebuild:
	docker compose down -v --remove-orphans
	docker compose build --no-cache
	docker compose up -d

build:
	docker compose build --no-cache
	docker compose up -d

down:
	docker compose down -v --remove-orphans

