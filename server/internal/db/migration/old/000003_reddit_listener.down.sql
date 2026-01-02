-- Reddit Listener Pipeline
-- Migration: 000003_reddit_listener.down.sql
-- Rollback: Drop all Reddit-related tables

DROP TABLE IF EXISTS reddit_alerts CASCADE;
DROP TABLE IF EXISTS listener_state CASCADE;
DROP TABLE IF EXISTS strategy_cards CASCADE;
DROP TABLE IF EXISTS reddit_chunks CASCADE;
DROP TABLE IF EXISTS reddit_comments CASCADE;
DROP TABLE IF EXISTS reddit_items CASCADE;
DROP TABLE IF EXISTS reddit_sources CASCADE;
