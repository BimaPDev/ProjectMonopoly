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

CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

CREATE TABLE upload_jobs (
    id TEXT PRIMARY KEY,               -- Unique job ID
    user_id INT NOT NULL,               -- User who uploaded the file
    video_path TEXT DEFAULT '',         -- Local file path (if stored locally)
    storage_type VARCHAR(50) DEFAULT 'local',  -- "local", "s3", "gcs"
    file_url TEXT DEFAULT '',           -- Full URL (if using S3/GCS)
    status TEXT DEFAULT 'pending',      -- "pending", "processing", "completed", "failed"
    created_at TIMESTAMP DEFAULT NOW(), -- Timestamp when job was created
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

ALTER TABLE "users" ADD COLUMN "oauth_provider" VARCHAR(50), ADD COLUMN "oauth_id" VARCHAR(255);

ALTER TABLE "groups" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "group_items" ADD FOREIGN KEY ("group_id") REFERENCES "groups" ("id");

ALTER TABLE "competitors" ADD FOREIGN KEY ("group_id") REFERENCES "groups" ("id");

ALTER TABLE "posts" ADD FOREIGN KEY ("group_id") REFERENCES "groups" ("id");
