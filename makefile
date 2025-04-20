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

buildfrontend:
	docker compose build frontend
	docker compose up -d frontend

buildbackend:
	docker compose build backend
	docker compose up -d backend

backendlogs:
	docker logs projectmonopoly-backend-1