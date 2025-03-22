# Makefile

.PHONY: rebuild build down nuke frontend

rebuild:
	docker compose down -v --remove-orphans
	docker compose build --no-cache
	docker compose up -d

build:
	docker compose build --no-cache
	docker compose up -d

down:
	docker compose down -v --remove-orphans

nuke:
	docker system prune -a --volumes

frontend:
	docker compose build frontend
	docker compose up -d frontend


