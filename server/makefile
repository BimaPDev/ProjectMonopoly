postgres:
	docker run --name felix -p 5432:5432 -e POSTGRES_USER=root -e POSTGRES_PASSWORD=secret -d postgres

pgvector:
	docker run --name felix -p 5432:5432 \
	-e POSTGRES_USER=root -e POSTGRES_PASSWORD=secret -e POSTGRES_DB=project_monopoly \
	-d pgvector/pgvector:pg15

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

redis:
	redis-server --save "" --appendonly no

celery-worker:
	CELERY_BROKER_URL=redis://localhost:6379/0 CELERY_RESULT_BACKEND=redis://localhost:6379/0 \
	celery -A worker.celery_app worker -l info -Q celery --concurrency=4

dispatcher:
	python3 -m worker.auto_dispatch

flower:
	CELERY_BROKER_URL=redis://localhost:6379/0 celery -A worker.celery_app flower --port 5555

runpy: redis
	$(MAKE) -j2 celery-worker dispatcher

docker-migrateup:
	docker exec postgres psql -U root -d project_monopoly -f /migration/000001_init_schema.up.sql