-- =============================================================
-- LineWhiz — SQLite Database Schema
-- Version: 1.0
-- Database: SQLite (MVP) → PostgreSQL (scale at 1000+ users)
-- =============================================================

-- Enable WAL mode for better concurrent read performance
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- =============================================================
-- TABLE: api_keys
-- Stores hashed API keys with tier information.
-- API keys are shown to the user once at creation, then only
-- the SHA-256 hash is stored. Never store plaintext keys.
-- =============================================================

CREATE TABLE IF NOT EXISTS api_keys (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    key_hash    TEXT    NOT NULL UNIQUE,             -- SHA-256 hash of the API key
    tier        TEXT    NOT NULL DEFAULT 'free'      -- 'free', 'pro', 'business'
                        CHECK (tier IN ('free', 'pro', 'business')),
    label       TEXT,                                -- User-defined label, e.g. "My Shop OA"
    is_active   INTEGER NOT NULL DEFAULT 1           -- 1 = active, 0 = revoked
                        CHECK (is_active IN (0, 1)),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_api_keys_hash
    ON api_keys(key_hash);

CREATE INDEX IF NOT EXISTS idx_api_keys_active_tier
    ON api_keys(is_active, tier);


-- =============================================================
-- TABLE: usage_logs
-- Tracks every MCP tool call for rate limiting, analytics,
-- and billing purposes.
-- =============================================================

CREATE TABLE IF NOT EXISTS usage_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key_id  INTEGER NOT NULL REFERENCES api_keys(id) ON DELETE CASCADE,
    tool_name   TEXT    NOT NULL,                    -- e.g. 'send_broadcast', 'get_account_info'
    success     INTEGER NOT NULL DEFAULT 1           -- 1 = success, 0 = failure
                        CHECK (success IN (0, 1)),
    error_msg   TEXT,                                -- NULL if success, error description if failure
    called_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_usage_api_date
    ON usage_logs(api_key_id, called_at);

CREATE INDEX IF NOT EXISTS idx_usage_tool_name
    ON usage_logs(tool_name, called_at);


-- =============================================================
-- TABLE: auto_replies (FUTURE — v2.0)
-- Keyword-based auto-reply rules for incoming messages.
-- Requires webhook server to be running.
-- =============================================================

CREATE TABLE IF NOT EXISTS auto_replies (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key_id      INTEGER NOT NULL REFERENCES api_keys(id) ON DELETE CASCADE,
    keyword         TEXT    NOT NULL,                -- Trigger word/phrase
    match_type      TEXT    NOT NULL DEFAULT 'contains'
                            CHECK (match_type IN ('exact', 'contains', 'starts_with')),
    response        TEXT    NOT NULL,                -- Message text to reply with
    is_active       INTEGER NOT NULL DEFAULT 1
                            CHECK (is_active IN (0, 1)),
    priority        INTEGER NOT NULL DEFAULT 0,      -- Higher = checked first
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_auto_replies_api_key
    ON auto_replies(api_key_id, is_active);

CREATE INDEX IF NOT EXISTS idx_auto_replies_keyword
    ON auto_replies(keyword, match_type);


-- =============================================================
-- HELPER QUERIES — Rate Limiting
-- =============================================================

-- Count today's usage for a specific API key (rate limit check)
-- Usage: Replace ? with api_key_id
-- SELECT COUNT(*) FROM usage_logs
-- WHERE api_key_id = ? AND called_at >= date('now');

-- Count today's broadcasts for a specific API key
-- SELECT COUNT(*) FROM usage_logs
-- WHERE api_key_id = ?
--   AND tool_name = 'send_broadcast'
--   AND called_at >= date('now');


-- =============================================================
-- HELPER QUERIES — Analytics
-- =============================================================

-- Get usage stats for a key (last 30 days)
-- SELECT tool_name, COUNT(*) as calls, SUM(success) as ok, SUM(1 - success) as errors
-- FROM usage_logs
-- WHERE api_key_id = ? AND called_at >= date('now', '-30 days')
-- GROUP BY tool_name
-- ORDER BY calls DESC;

-- Most popular tools across all users (last 7 days)
-- SELECT tool_name, COUNT(*) as total_calls
-- FROM usage_logs
-- WHERE called_at >= date('now', '-7 days')
-- GROUP BY tool_name
-- ORDER BY total_calls DESC;

-- Daily active keys (last 30 days)
-- SELECT date(called_at) as day, COUNT(DISTINCT api_key_id) as active_keys
-- FROM usage_logs
-- WHERE called_at >= date('now', '-30 days')
-- GROUP BY day
-- ORDER BY day;

-- Error rate by tool (last 7 days)
-- SELECT tool_name,
--        COUNT(*) as total,
--        SUM(1 - success) as errors,
--        ROUND(100.0 * SUM(1 - success) / COUNT(*), 1) as error_pct
-- FROM usage_logs
-- WHERE called_at >= date('now', '-7 days')
-- GROUP BY tool_name
-- HAVING total >= 10
-- ORDER BY error_pct DESC;


-- =============================================================
-- HELPER QUERIES — Billing / Revenue
-- =============================================================

-- Count paying users by tier
-- SELECT tier, COUNT(*) as user_count
-- FROM api_keys
-- WHERE is_active = 1 AND tier != 'free'
-- GROUP BY tier;

-- Monthly usage per paying user (for billing validation)
-- SELECT ak.tier, ak.label,
--        COUNT(ul.id) as calls_this_month
-- FROM api_keys ak
-- JOIN usage_logs ul ON ak.id = ul.api_key_id
-- WHERE ak.is_active = 1
--   AND ul.called_at >= date('now', 'start of month')
-- GROUP BY ak.id
-- ORDER BY calls_this_month DESC;


-- =============================================================
-- MIGRATION NOTES
-- =============================================================

-- MVP Simplification:
-- For initial launch, skip DB-backed auth entirely.
-- Use environment variable tier:
--   LINEWHIZ_TIER = os.environ.get("LINEWHIZ_TIER", "pro")
-- Add DB-backed auth in v1.1 when differentiating free/paid users.

-- Future Migration to PostgreSQL:
-- 1. Replace INTEGER PRIMARY KEY AUTOINCREMENT → SERIAL PRIMARY KEY
-- 2. Replace TEXT datetime defaults → TIMESTAMP WITH TIME ZONE DEFAULT NOW()
-- 3. Replace CHECK constraints → Use ENUM types where appropriate
-- 4. Add connection pooling (asyncpg + pool)
-- 5. Add partitioning on usage_logs by month for performance

-- Future Tables (v2.0+):
-- subscriptions    — Stripe subscription tracking
-- webhook_events   — Incoming LINE webhook event log
-- flex_templates   — Saved Flex Message templates
-- scheduled_msgs   — Scheduled broadcast queue
-- accounts         — Multi-account management (enterprise)
