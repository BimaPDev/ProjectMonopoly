CREATE TABLE "users" (
  "id" SERIAL PRIMARY KEY,
  "username" VARCHAR(255) UNIQUE NOT NULL,
  "email" VARCHAR(255) UNIQUE NOT NULL,
  "password_hash" VARCHAR(255) NOT NULL,
  "oauth_provider" VARCHAR(50),
  "oauth_id" VARCHAR(255),
  "created_at" TIMESTAMP DEFAULT NOW(),
  "updated_at" TIMESTAMP DEFAULT NOW()
);

CREATE TABLE "groups" (
  "id" SERIAL PRIMARY KEY,
  "user_id" INT NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "description" TEXT,
  "created_at" TIMESTAMP DEFAULT NOW(),
  "updated_at" TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE CASCADE
);

CREATE TABLE "group_items" (
  "id" SERIAL PRIMARY KEY,
  "group_id" INT NOT NULL,
  "type" VARCHAR(50),
  "data" JSONB,
  "created_at" TIMESTAMP DEFAULT NOW(),
  "updated_at" TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY ("group_id") REFERENCES "groups" ("id") ON DELETE CASCADE
);

CREATE TABLE competitors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  group_id INT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
  platform VARCHAR(50) NOT NULL,
  username VARCHAR(100) NOT NULL,
  profile_url TEXT NOT NULL,
  last_checked TIMESTAMP DEFAULT NOW(),
  UNIQUE (group_id, platform, username)
);


CREATE TABLE "posts" (
  "id" SERIAL PRIMARY KEY,
  "group_id" INT NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "social_media_link" VARCHAR(255) NOT NULL,
  "created_at" TIMESTAMP DEFAULT NOW(),
  "updated_at" TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY ("group_id") REFERENCES "groups" ("id") ON DELETE CASCADE
);

CREATE TABLE "sessions" (
  "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "user_id" INT NOT NULL,
  "created_at" TIMESTAMP DEFAULT NOW(),
  "expires_at" TIMESTAMP NOT NULL,
  FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE CASCADE
);

CREATE TABLE "upload_jobs" (
  "id" TEXT PRIMARY KEY,
  "user_id" INT NOT NULL,
  "platform" VARCHAR(50),
  "video_path" TEXT DEFAULT '',
  "storage_type" VARCHAR(50) DEFAULT 'local',
  "file_url" TEXT DEFAULT '',
  "status" TEXT DEFAULT 'pending',
  "caption" TEXT DEFAULT '',
  "created_at" TIMESTAMP DEFAULT NOW(),
  "updated_at" TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE CASCADE
);

CREATE TABLE competitor_posts (
  id SERIAL PRIMARY KEY,
  competitor_id UUID REFERENCES competitors(id) ON DELETE CASCADE,
  platform VARCHAR(50) NOT NULL,
  post_id VARCHAR(100) NOT NULL,
  content TEXT,
  media JSONB DEFAULT '{}'::jsonb,
  posted_at TIMESTAMP,
  engagement JSONB DEFAULT '{}'::jsonb,
  hashtags TEXT[] DEFAULT '{}',
  scraped_at TIMESTAMP DEFAULT NOW(),
  UNIQUE (platform, post_id)
);

ALTER TABLE group_items
ADD CONSTRAINT group_items_group_id_type_key UNIQUE (group_id, type);
