postgres:
	docker run --name felix -p 5432:5432 -e POSTGRES_USER=root -e POSTGRES_PASSWORD=secret -d postgres

createdb:
	docker exec -it felix createdb --username=root --owner=root project_monopoly

dropdb:
	docker exec -it felix dropdb project_monopoly

migrateup:
	migrate -path internal/db/migration -database "postgresql://root:secret@localhost:5432/project_monopoly?sslmode=disable" -verbose up

migratedown:
	migrate -path internal/db/migration -database "postgresql://root:secret@localhost:5432/project_monopoly?sslmode=disable" -verbose down

sqlc:
	sqlc generate

rungo:
	go run cmd/api/main.go

runpy:
	python3 python/manager.py

server:
	$(MAKE) -j2 rungo runpy

redis:
	redis-server

celery:
	celery -A python.celery boss --loglevel=info
	celery -A python.celery task --loglevel=info
	celery -A tasks worker --loglevel=info -Q boss_queue --concurrency=1
	celery -A tasks worker --loglevel=info -Q manager_queue --concurrency=4
	celery -A tasks beat --loglevel=info




.PHONY: createdb dropdb postgres migrateup migratedown sqlc rungo runpy