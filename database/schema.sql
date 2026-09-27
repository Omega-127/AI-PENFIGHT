-- ====================================================================
-- AI Penfight - Database Schema Definition (SQLite & PostgreSQL Compatible)
-- ====================================================================
-- Description: Core schema for users, interactions, AI analyses,
--              personalized feedback, historical performance metrics,
--              and pre-calculated dashboard rollups.
-- ====================================================================

-- 1. Enforce SQLite Foreign Key constraints
PRAGMA foreign_keys = ON;

-- --------------------------------------------------------------------
-- Table 1: users
-- Stores user account info, authentication tokens, and user preferences.
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    preferences TEXT DEFAULT '{}', -- JSON string for user UI & AI tuning preferences
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- --------------------------------------------------------------------
-- Table 2: interactions
-- Records each user session/input event before or during AI processing.
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    mode TEXT NOT NULL DEFAULT 'analysis' CHECK (mode IN ('analysis', 'feedback', 'match', 'practice')),
    input_data TEXT NOT NULL,       -- Raw user input payload / parameters (e.g. angle, velocity, flick coordinate)
    status TEXT NOT NULL DEFAULT 'completed' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- --------------------------------------------------------------------
-- Table 3: analyses
-- Stores AI-generated analysis results, detected patterns, and model metadata.
-- User isolation is guaranteed via direct user_id reference.
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interaction_id INTEGER NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,       -- Explicit user reference for tenant isolation and index efficiency
    analysis_summary TEXT NOT NULL,
    detected_patterns TEXT DEFAULT '[]', -- JSON array of detected errors/strengths
    confidence_score REAL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    model_version TEXT NOT NULL DEFAULT 'penfight-ai-v1',
    prompt_version TEXT NOT NULL DEFAULT 'prompt-v1.0',
    latency_ms INTEGER DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (interaction_id) REFERENCES interactions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- --------------------------------------------------------------------
-- Table 4: feedbacks
-- Stores actionable, personalized suggestions and coaching tips linked
-- directly to specific analyses.
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS feedbacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,       -- User isolation reference
    feedback_type TEXT NOT NULL DEFAULT 'adaptive' CHECK (feedback_type IN ('adaptive', 'rule_based', 'ai_generated', 'tactical')),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    recommendations TEXT DEFAULT '[]', -- JSON array of actionable steps
    tone TEXT DEFAULT 'encouraging' CHECK (tone IN ('encouraging', 'analytical', 'critical', 'direct')),
    is_applied INTEGER NOT NULL DEFAULT 0 CHECK (is_applied IN (0, 1)),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- --------------------------------------------------------------------
-- Table 5: performances
-- Time-series log storing granular metrics, score trends, and skill progression.
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS performances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    interaction_id INTEGER,         -- Optional link to the specific trigger interaction
    metric_name TEXT NOT NULL,       -- e.g., 'accuracy', 'reaction_time_ms', 'flick_control', 'tactical_score'
    metric_value REAL NOT NULL,
    trend_direction TEXT DEFAULT 'stable' CHECK (trend_direction IN ('up', 'down', 'stable')),
    recorded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (interaction_id) REFERENCES interactions(id) ON DELETE SET NULL
);

-- --------------------------------------------------------------------
-- Table 6: performance_rollups
-- Pre-aggregated summary cache per user. Eliminates expensive full-table
-- aggregations on frequent dashboard requests.
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS performance_rollups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    total_interactions INTEGER NOT NULL DEFAULT 0,
    total_analyses INTEGER NOT NULL DEFAULT 0,
    total_feedbacks INTEGER NOT NULL DEFAULT 0,
    avg_accuracy_score REAL NOT NULL DEFAULT 0.0,
    avg_latency_ms REAL NOT NULL DEFAULT 0.0,
    overall_trend TEXT NOT NULL DEFAULT 'stable' CHECK (overall_trend IN ('improving', 'stable', 'declining')),
    recent_mistake_count INTEGER NOT NULL DEFAULT 0,
    last_interaction_at DATETIME,
    last_calculated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ====================================================================
-- INDEXES FOR HIGH-FREQUENCY QUERY OPTIMIZATION
-- ====================================================================

-- Users lookups
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Interactions: Fast retrieval of user history ordered chronologically
CREATE INDEX IF NOT EXISTS idx_interactions_user_created ON interactions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_interactions_session ON interactions(session_id);

-- Analyses: Fast retrieval of previous analyses by user and timestamp
CREATE INDEX IF NOT EXISTS idx_analyses_user_created ON analyses(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analyses_interaction ON analyses(interaction_id);

-- Feedback: Instant lookup by analysis and by user history
CREATE INDEX IF NOT EXISTS idx_feedbacks_analysis ON feedbacks(analysis_id);
CREATE INDEX IF NOT EXISTS idx_feedbacks_user_created ON feedbacks(user_id, created_at DESC);

-- Performance: Efficient time-series metric trend analysis per user
CREATE INDEX IF NOT EXISTS idx_performances_user_metric_time ON performances(user_id, metric_name, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_performances_user_recorded ON performances(user_id, recorded_at DESC);

-- Performance Rollup: Instant dashboard summary lookup
CREATE INDEX IF NOT EXISTS idx_rollups_user ON performance_rollups(user_id);

-- ====================================================================
-- AUTOMATIC TIMESTAMP TRIGGERS
-- ====================================================================

-- Auto-update updated_at on users table
CREATE TRIGGER IF NOT EXISTS trg_users_updated_at
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;
