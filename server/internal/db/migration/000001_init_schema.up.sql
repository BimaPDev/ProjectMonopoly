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
  "platform" VARCHAR(50) NOT NULL,  -- e.g., 'tiktok', 'youtube'
  "data" JSONB,
  "created_at" TIMESTAMP DEFAULT NOW(),
  "updated_at" TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY ("group_id") REFERENCES "groups" ("id") ON DELETE CASCADE
);
ALTER TABLE group_items
ADD CONSTRAINT group_items_group_id_type_key UNIQUE (group_id);

CREATE TABLE competitors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  group_id INT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
  platform VARCHAR(50) NOT NULL,
  username VARCHAR(100) NOT NULL,
  profile_url TEXT NOT NULL,
  last_checked TIMESTAMP DEFAULT NOW(),
  followers BIGINT DEFAULT 0,
  engagement_rate NUMERIC(4,2) DEFAULT 0.0,
  growth_rate NUMERIC(4,2) DEFAULT 0.0,
  posting_frequency NUMERIC(5,2) DEFAULT 0.0,
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
  "group_id" INT,  -- Nullable, but can be linked to groups table
  "platform" VARCHAR(50) NOT NULL,  -- e.g., 'tiktok', 'youtube'
  "video_path" TEXT NOT NULL,
  "storage_type" VARCHAR(50) NOT NULL DEFAULT 'local',
  "file_url" TEXT DEFAULT '',
  "status" TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'uploading', 'done', 'failed')),
  "caption" TEXT DEFAULT '',
  "user_title" TEXT DEFAULT '',
  "user_hashtags" TEXT[] DEFAULT '{}',
  "ai_title" TEXT DEFAULT '',
  "ai_hashtags" TEXT[] DEFAULT '{}',
  "ai_post_time" TIMESTAMP,
  "created_at" TIMESTAMP DEFAULT NOW(),
  "updated_at" TIMESTAMP DEFAULT NOW(),
  "scheduled_date" date DEFAULT NOW(),

  FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE CASCADE,
  FOREIGN KEY ("group_id") REFERENCES "groups" ("id") ON DELETE SET NULL
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


--socialmeiad data, id PK, groupsid FK, type, data, created, upadted
CREATE TABLE socialmedia_data (
  id SERIAL PRIMARY KEY,
  group_id   INT NOT NULL
    REFERENCES groups(id)
    ON DELETE CASCADE,
  platform   VARCHAR(50)   NOT NULL,    -- e.g. 'twitter', 'instagram'
  type       VARCHAR(50)   NOT NULL,    -- e.g. 'followers', 'posts', 'engagement'
  data       JSONB         NOT NULL,    -- any details you want to store
  created_at TIMESTAMP     NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP     NOT NULL DEFAULT NOW()
);


-- Daily followers table to track follower counts per day
CREATE TABLE daily_followers (
  id              SERIAL      PRIMARY KEY,
  record_date     DATE        NOT NULL DEFAULT CURRENT_DATE,
  follower_count  BIGINT      NOT NULL
);
