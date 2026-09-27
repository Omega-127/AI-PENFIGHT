# AI Penfight — Database Architecture & Specification

## 1. Executive Summary

This module implements the complete, production-grade relational database architecture for the **AI Penfight** platform using **SQLite** for zero-dependency local development and prototyping, while maintaining 100% architectural compatibility for migration to **PostgreSQL** in production.

### Core Architectural Guarantees:
- **Foreign Key Enforcement**: Strict referential integrity via SQLite `PRAGMA foreign_keys = ON;` activated on every database connection.
- **Tenant & User Data Isolation**: Every domain entity (`interactions`, `analyses`, `feedbacks`, `performances`, `performance_rollups`) contains a direct `user_id` foreign key. Queries never rely on fragile multi-table joins to filter tenant data.
- **High-Performance Lookups**: Targeted composite indexes ensure sub-millisecond lookups for previous analyses, chronologically sorted interaction histories, and time-series performance metrics.
- **Pre-Aggregated Dashboard Rollups**: A dedicated `performance_rollups` summary structure eliminates expensive multi-table aggregations on frequent dashboard requests.
- **Cascading Referential Integrity**: Complete lifecycle management where deleting a user or interaction cleanly cascades to all dependent records.

---

## 2. Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    USERS ||--o{ INTERACTIONS : "initiates (1:N)"
    USERS ||--o{ ANALYSES : "owns (1:N)"
    USERS ||--o{ FEEDBACKS : "receives (1:N)"
    USERS ||--o{ PERFORMANCES : "logs (1:N)"
    USERS ||--|| PERFORMANCE_ROLLUPS : "summarizes (1:1)"
    INTERACTIONS ||--o| ANALYSES : "generates (1:1)"
    INTERACTIONS ||--o{ PERFORMANCES : "triggers (1:N)"
    ANALYSES ||--o{ FEEDBACKS : "produces (1:N)"

    USERS {
        INTEGER id PK "AUTOINCREMENT"
        TEXT username UK "Unique username"
        TEXT email UK "Unique email"
        TEXT password_hash "Hashed credentials"
        TEXT preferences "JSON user preferences"
        DATETIME created_at "Registration timestamp"
        DATETIME updated_at "Auto-updated via trigger"
    }

    INTERACTIONS {
        INTEGER id PK "AUTOINCREMENT"
        INTEGER user_id FK "References USERS(id) ON DELETE CASCADE"
        TEXT session_id "Session / Game UUID"
        TEXT mode "analysis | feedback | match | practice"
        TEXT input_data "JSON payload of user input / strike vectors"
        TEXT status "pending | processing | completed | failed"
        DATETIME created_at "Event timestamp"
    }

    ANALYSES {
        INTEGER id PK "AUTOINCREMENT"
        INTEGER interaction_id FK,UK "References INTERACTIONS(id) ON DELETE CASCADE"
        INTEGER user_id FK "References USERS(id) ON DELETE CASCADE"
        TEXT analysis_summary "AI analysis narrative"
        TEXT detected_patterns "JSON array of detected errors/patterns"
        REAL confidence_score "Float between 0.0 and 1.0"
        TEXT model_version "AI model identifier"
        TEXT prompt_version "Prompt template identifier"
        INTEGER latency_ms "Execution time in milliseconds"
        DATETIME created_at "Timestamp of analysis"
    }

    FEEDBACKS {
        INTEGER id PK "AUTOINCREMENT"
        INTEGER analysis_id FK "References ANALYSES(id) ON DELETE CASCADE"
        INTEGER user_id FK "References USERS(id) ON DELETE CASCADE"
        TEXT feedback_type "adaptive | rule_based | ai_generated | tactical"
        TEXT title "Summary title"
        TEXT content "Detailed feedback narrative"
        TEXT recommendations "JSON array of actionable steps"
        TEXT tone "encouraging | analytical | critical | direct"
        INTEGER is_applied "0 or 1"
        DATETIME created_at "Timestamp of feedback"
    }

    PERFORMANCES {
        INTEGER id PK "AUTOINCREMENT"
        INTEGER user_id FK "References USERS(id) ON DELETE CASCADE"
        INTEGER interaction_id FK "Nullable: references INTERACTIONS(id) ON DELETE SET NULL"
        TEXT metric_name "e.g. accuracy, reaction_time_ms, flick_control"
        REAL metric_value "Metric measurement"
        TEXT trend_direction "up | down | stable"
        DATETIME recorded_at "Metric timestamp"
    }

    PERFORMANCE_ROLLUPS {
        INTEGER id PK "AUTOINCREMENT"
        INTEGER user_id FK,UK "References USERS(id) ON DELETE CASCADE"
        INTEGER total_interactions "Cached interaction count"
        INTEGER total_analyses "Cached analysis count"
        INTEGER total_feedbacks "Cached feedback count"
        REAL avg_accuracy_score "Rolling average accuracy"
        REAL avg_latency_ms "Rolling average AI latency"
        TEXT overall_trend "improving | stable | declining"
        INTEGER recent_mistake_count "Count of unapplied feedback / errors"
        DATETIME last_interaction_at "Timestamp of latest interaction"
        DATETIME last_calculated_at "Timestamp of rollup calculation"
    }
```

---

## 3. Database Schema Specification

### 3.1 `users`
Represents application accounts and personalization settings.
- `id` (`INTEGER PRIMARY KEY AUTOINCREMENT`): Unique identifier.
- `username` (`TEXT NOT NULL UNIQUE`): Unique handle.
- `email` (`TEXT NOT NULL UNIQUE`): Unique email.
- `password_hash` (`TEXT NOT NULL`): Secure password hash.
- `preferences` (`TEXT DEFAULT '{}'`): JSON payload storing user preferences (theme, notification levels, gameplay tuning).
- `created_at` (`DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP`): Creation time.
- `updated_at` (`DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP`): Updated automatically via SQLite trigger.

### 3.2 `interactions`
Logs each input submission, pen flick vector, or match round.
- `id` (`INTEGER PRIMARY KEY AUTOINCREMENT`): Unique interaction ID.
- `user_id` (`INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE`): Owning user.
- `session_id` (`TEXT NOT NULL`): Session identifier.
- `mode` (`TEXT NOT NULL CHECK(mode IN ('analysis', 'feedback', 'match', 'practice'))`): Operational mode.
- `input_data` (`TEXT NOT NULL`): JSON representation of angle, velocity, flick coordinates, and spin.
- `status` (`TEXT NOT NULL CHECK(status IN ('pending', 'processing', 'completed', 'failed'))`): Execution status.
- `created_at` (`DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP`): Event timestamp.

### 3.3 `analyses`
Captures output from the AI Engine pipeline.
- `id` (`INTEGER PRIMARY KEY AUTOINCREMENT`): Unique analysis ID.
- `interaction_id` (`INTEGER NOT NULL UNIQUE REFERENCES interactions(id) ON DELETE CASCADE`): 1-to-1 link to interaction.
- `user_id` (`INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE`): Direct user reference for isolated tenant lookups.
- `analysis_summary` (`TEXT NOT NULL`): Human-readable AI summary.
- `detected_patterns` (`TEXT DEFAULT '[]'`): JSON list of detected errors or gameplay patterns.
- `confidence_score` (`REAL CHECK(confidence_score >= 0.0 AND confidence_score <= 1.0)`): Model certainty.
- `model_version` (`TEXT NOT NULL DEFAULT 'penfight-ai-v1'`): AI model tracking.
- `prompt_version` (`TEXT NOT NULL DEFAULT 'prompt-v1.0'`): Prompt version tracking.
- `latency_ms` (`INTEGER DEFAULT 0`): Inference time in milliseconds.
- `created_at` (`DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP`): Analysis timestamp.

### 3.4 `feedbacks`
Stores personalized recommendations and coaching advice derived from an analysis.
- `id` (`INTEGER PRIMARY KEY AUTOINCREMENT`): Unique feedback ID.
- `analysis_id` (`INTEGER NOT NULL REFERENCES analyses(id) ON DELETE CASCADE`): Parent analysis.
- `user_id` (`INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE`): Owning user for direct lookups.
- `feedback_type` (`TEXT NOT NULL CHECK(feedback_type IN ('adaptive', 'rule_based', 'ai_generated', 'tactical'))`): Feedback classification.
- `title` (`TEXT NOT NULL`): Short title.
- `content` (`TEXT NOT NULL`): In-depth coaching suggestions.
- `recommendations` (`TEXT DEFAULT '[]'`): JSON list of discrete actionable steps.
- `tone` (`TEXT DEFAULT 'encouraging' CHECK(tone IN ('encouraging', 'analytical', 'critical', 'direct'))`): AI voice tone.
- `is_applied` (`INTEGER NOT NULL DEFAULT 0 CHECK(is_applied IN (0, 1))`): Tracking whether user reviewed/applied advice.
- `created_at` (`DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP`): Creation timestamp.

### 3.5 `performances`
Granular time-series log of user metrics over time.
- `id` (`INTEGER PRIMARY KEY AUTOINCREMENT`): Metric event ID.
- `user_id` (`INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE`): Owning user.
- `interaction_id` (`INTEGER REFERENCES interactions(id) ON DELETE SET NULL`): Associated interaction (optional).
- `metric_name` (`TEXT NOT NULL`): Metric name (e.g., `accuracy`, `reaction_time_ms`, `flick_control`, `tactical_score`).
- `metric_value` (`REAL NOT NULL`): Measured value.
- `trend_direction` (`TEXT DEFAULT 'stable' CHECK(trend_direction IN ('up', 'down', 'stable'))`): Directional movement.
- `recorded_at` (`DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP`): Metric timestamp.

### 3.6 `performance_rollups` (Dashboard Summary Structure)
Pre-aggregated summary cache per user. Prevents recalculating aggregates across hundreds of rows on every dashboard view.
- `id` (`INTEGER PRIMARY KEY AUTOINCREMENT`): Summary row ID.
- `user_id` (`INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE`): 1-to-1 link per user.
- `total_interactions` (`INTEGER NOT NULL DEFAULT 0`): Cached count of interactions.
- `total_analyses` (`INTEGER NOT NULL DEFAULT 0`): Cached count of analyses.
- `total_feedbacks` (`INTEGER NOT NULL DEFAULT 0`): Cached count of feedback entries.
- `avg_accuracy_score` (`REAL NOT NULL DEFAULT 0.0`): Pre-computed average accuracy.
- `avg_latency_ms` (`REAL NOT NULL DEFAULT 0.0`): Pre-computed average AI response time.
- `overall_trend` (`TEXT NOT NULL DEFAULT 'stable' CHECK(overall_trend IN ('improving', 'stable', 'declining'))`): High-level trend indicator.
- `recent_mistake_count` (`INTEGER NOT NULL DEFAULT 0`): Active unapplied errors.
- `last_interaction_at` (`DATETIME`): Timestamp of latest interaction.
- `last_calculated_at` (`DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP`): Rollup freshness timestamp.

---

## 4. Indexing Strategy

| Index Name | Table | Columns | Purpose |
|---|---|---|---|
| `idx_users_username` | `users` | `(username)` | O(1) user login lookup |
| `idx_users_email` | `users` | `(email)` | O(1) email authentication lookup |
| `idx_interactions_user_created` | `interactions` | `(user_id, created_at DESC)` | High-speed paginated user interaction history |
| `idx_interactions_session` | `interactions` | `(session_id)` | Fast lookup of interactions within a match session |
| `idx_analyses_user_created` | `analyses` | `(user_id, created_at DESC)` | Ultra-fast retrieval of historical analyses for adaptive prompts |
| `idx_analyses_interaction` | `analyses` | `(interaction_id)` | O(1) analysis lookup from interaction |
| `idx_feedbacks_analysis` | `feedbacks` | `(analysis_id)` | Instant feedback retrieval for a specific analysis |
| `idx_feedbacks_user_created` | `feedbacks` | `(user_id, created_at DESC)` | User feedback history and unapplied tips |
| `idx_performances_user_metric_time` | `performances` | `(user_id, metric_name, recorded_at DESC)` | Trend queries for charts (e.g. accuracy progression) |
| `idx_performances_user_recorded` | `performances` | `(user_id, recorded_at DESC)` | Chronological user metric timeline |
| `idx_rollups_user` | `performance_rollups` | `(user_id)` | Sub-millisecond single-row dashboard KPI fetch |

---

## 5. PostgreSQL Migration Guide

The schema is explicitly designed to minimize friction when upgrading from SQLite to PostgreSQL:

| Feature / Type | SQLite (Prototype) | PostgreSQL (Production) |
|---|---|---|
| Auto-increment PK | `INTEGER PRIMARY KEY AUTOINCREMENT` | `BIGSERIAL PRIMARY KEY` or `INT GENERATED ALWAYS AS IDENTITY` |
| Timestamps | `DATETIME DEFAULT CURRENT_TIMESTAMP` | `TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP` |
| JSON Fields | `TEXT` (stored as JSON string) | `JSONB` (binary JSON with index support) |
| Booleans | `INTEGER CHECK (col IN (0, 1))` | `BOOLEAN DEFAULT FALSE` |
| Floats | `REAL` | `DOUBLE PRECISION` or `NUMERIC(5,2)` |
| Foreign Key Check | Enabled via `PRAGMA foreign_keys = ON;` | Enforced natively by PostgreSQL engine |
| Upsert Syntax | `INSERT ... ON CONFLICT(col) DO UPDATE` | `INSERT ... ON CONFLICT(col) DO UPDATE` (fully identical) |

### Migration Steps:
1. Replace `INTEGER PRIMARY KEY AUTOINCREMENT` with `BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY`.
2. Change JSON `TEXT` columns to `JSONB`.
3. Change `DATETIME` columns to `TIMESTAMPTZ`.
4. Point `DATABASE_URL` to your PostgreSQL instance: `postgresql://user:password@host:5432/penfight`.
5. The repository and query design will function without changes to SQL business logic.

---

## 6. Directory Structure

```text
database/
├── __init__.py          # Package initialization with top-level exports
├── config.py            # Environment-aware database paths & SQLite pragmas
├── connection.py        # Connection factory, PRAGMA enforcement, transaction context managers
├── schema.sql           # DDL: Tables, foreign keys, constraints, indexes, triggers
├── seed.sql             # SQL seed script with multi-user sample datasets
├── seed.py              # Python utility to reset and seed the database
├── queries.sql          # Annotated SQL implementations of the 5 required queries
├── example_usage.py     # End-to-end verification script testing CRUD, FKs, and queries
├── README.md            # Architecture documentation (this file)
└── crud/                # Repository layer (Data Access Objects)
    ├── __init__.py      # Repository exports
    ├── base.py          # Row conversion, JSON serializers, context helpers
    ├── user.py          # UserRepository: Account creation, updates, isolation
    ├── interaction.py   # InteractionRepository: Input logging, paginated history
    ├── analysis.py      # AnalysisRepository: AI outputs, timestamp-range lookups
    ├── feedback.py      # FeedbackRepository: Coaching tips, applied flags
    ├── performance.py   # PerformanceRepository: Time-series metrics, trends
    └── rollup.py        # PerformanceRollupRepository: O(1) dashboard summaries
```

---

## 7. Quickstart & Verification

### Initialize and Seed Database:
```bash
python -m database.seed
```

### Run Full Test & Verification Suite:
```bash
python database/example_usage.py
```

This verification script runs:
1. Complete CRUD operations on all 6 entities.
2. Verification of SQLite Foreign Key enforcement (catches invalid IDs).
3. Verification of Cascading Deletes (purging a user removes all associated child data).
4. Execution of all 5 required business queries with live output.
