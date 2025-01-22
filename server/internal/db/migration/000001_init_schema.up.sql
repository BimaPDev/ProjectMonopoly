CREATE TABLE "users" (
  "id" SERIAL PRIMARY KEY,
  "username" VARCHAR(255) UNIQUE NOT NULL,
  "email" VARCHAR(255) UNIQUE NOT NULL,
  "password_hash" VARCHAR(255) NOT NULL,
  "created_at" TIMESTAMP
);

CREATE TABLE "groups" (
  "id" SERIAL PRIMARY KEY,
  "user_id" INT,
  "name" VARCHAR(255) NOT NULL,
  "description" TEXT,
  "social_media_link" VARCHAR(255) NOT NULL,
  "created_at" TIMESTAMP
);

CREATE TABLE "group_items" (
  "id" SERIAL PRIMARY KEY,
  "group_id" INT,
  "type" VARCHAR(50),
  "data" JSONB,
  "created_at" TIMESTAMP
);

CREATE TABLE "competitors" (
  "id" SERIAL PRIMARY KEY,
  "group_id" INT,
  "name" VARCHAR(255) NOT NULL,
  "social_media_link" VARCHAR(255) NOT NULL,
  "created_at" TIMESTAMP
);

CREATE TABLE "posts" (
  "id" SERIAL PRIMARY KEY,
  "group_id" INT,
  "title" VARCHAR(255) NOT NULL,
  "social_media_link" VARCHAR(255) NOT NULL,
  "created_at" TIMESTAMP
);

ALTER TABLE "groups" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "group_items" ADD FOREIGN KEY ("group_id") REFERENCES "groups" ("id");

ALTER TABLE "competitors" ADD FOREIGN KEY ("group_id") REFERENCES "groups" ("id");

ALTER TABLE "posts" ADD FOREIGN KEY ("group_id") REFERENCES "groups" ("id");
