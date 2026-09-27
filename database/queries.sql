-- ====================================================================
-- AI Penfight - Production Query Portfolio
-- ====================================================================
-- Optimized queries leveraging composite indexes for high throughput.
-- Parameter placeholders '?' represent runtime bound parameters.
-- ====================================================================

-- --------------------------------------------------------------------
-- 1. USER INTERACTION HISTORY
-- Purpose: Retrieve paginated history of interactions for a user,
--          ordered chronologically descending (most recent first).
-- Index Utilized: idx_interactions_user_created (user_id, created_at DESC)
-- --------------------------------------------------------------------
-- Example Parameters: user_id = 1, limit = 10, offset = 0
SELECT 
    i.id AS interaction_id,
    i.session_id,
    i.mode,
    i.input_data,
    i.status,
    i.created_at,
    a.id AS linked_analysis_id,
    a.confidence_score
FROM interactions i
LEFT JOIN analyses a ON i.id = a.interaction_id
WHERE i.user_id = 1
ORDER BY i.created_at DESC
LIMIT 10 OFFSET 0;


-- --------------------------------------------------------------------
-- 2. PREVIOUS ANALYSES BY USER AND TIMESTAMP RANGE
-- Purpose: Efficiently fetch historical AI analyses within a bounded
--          timeframe for adaptive feedback context without unbounded token costs.
-- Index Utilized: idx_analyses_user_created (user_id, created_at DESC)
-- --------------------------------------------------------------------
-- Example Parameters: user_id = 1, start_time = '2026-09-01 00:00:00', end_time = '2026-09-27 23:59:59'
SELECT 
    a.id AS analysis_id,
    a.interaction_id,
    a.analysis_summary,
    a.detected_patterns,
    a.confidence_score,
    a.model_version,
    a.prompt_version,
    a.latency_ms,
    a.created_at,
    i.mode AS interaction_mode
FROM analyses a
JOIN interactions i ON a.interaction_id = i.id
WHERE a.user_id = 1
  AND a.created_at >= '2026-09-01 00:00:00'
  AND a.created_at <= '2026-09-27 23:59:59'
ORDER BY a.created_at DESC
LIMIT 10 OFFSET 0;


-- --------------------------------------------------------------------
-- 3. PERSONALIZED FEEDBACK FOR A SPECIFIC ANALYSIS
-- Purpose: Retrieve coaching suggestions and actionable tips linked to an
--          analysis, along with the analysis context.
-- Index Utilized: idx_feedbacks_analysis (analysis_id)
-- --------------------------------------------------------------------
-- Example Parameters: analysis_id = 1
SELECT 
    f.id AS feedback_id,
    f.analysis_id,
    f.feedback_type,
    f.title,
    f.content,
    f.recommendations,
    f.tone,
    f.is_applied,
    f.created_at AS feedback_time,
    a.analysis_summary,
    a.confidence_score,
    u.username
FROM feedbacks f
JOIN analyses a ON f.analysis_id = a.id
JOIN users u ON f.user_id = u.id
WHERE f.analysis_id = 1;


-- --------------------------------------------------------------------
-- 4. PERFORMANCE TRENDS OVER TIME
-- Purpose: Retrieve chronologically ordered progression points for a specific
--          metric (e.g. 'accuracy') to render charts on the dashboard.
-- Index Utilized: idx_performances_user_metric_time (user_id, metric_name, recorded_at DESC)
-- --------------------------------------------------------------------
-- Example Parameters: user_id = 1, metric_name = 'accuracy', limit = 20
SELECT 
    p.id AS performance_id,
    p.metric_name,
    p.metric_value,
    p.trend_direction,
    p.recorded_at,
    i.session_id,
    i.mode AS interaction_mode
FROM performances p
LEFT JOIN interactions i ON p.interaction_id = i.id
WHERE p.user_id = 1 
  AND p.metric_name = 'accuracy'
ORDER BY p.recorded_at ASC
LIMIT 20;


-- --------------------------------------------------------------------
-- 5. DASHBOARD SUMMARY (INSTANT ROLLUP CACHE)
-- Purpose: Fetch high-level summary KPIs in sub-millisecond O(1) time
--          without running heavy multi-table aggregations.
-- Index Utilized: idx_rollups_user (user_id) [Unique Index]
-- --------------------------------------------------------------------
-- Example Parameters: user_id = 1
SELECT 
    u.id AS user_id,
    u.username,
    u.email,
    r.total_interactions,
    r.total_analyses,
    r.total_feedbacks,
    r.avg_accuracy_score,
    r.avg_latency_ms,
    r.overall_trend,
    r.recent_mistake_count,
    r.last_interaction_at,
    r.last_calculated_at
FROM users u
JOIN performance_rollups r ON u.id = r.user_id
WHERE u.id = 1;


-- --------------------------------------------------------------------
-- BONUS: ON-DEMAND ROLLUP REFRESH QUERY
-- Purpose: Atomically recomputes the user summary from source records.
-- --------------------------------------------------------------------
-- Example Parameters: user_id = 1
INSERT INTO performance_rollups (
    user_id,
    total_interactions,
    total_analyses,
    total_feedbacks,
    avg_accuracy_score,
    avg_latency_ms,
    overall_trend,
    recent_mistake_count,
    last_interaction_at,
    last_calculated_at
)
VALUES (
    1,
    (SELECT COUNT(*) FROM interactions WHERE user_id = 1),
    (SELECT COUNT(*) FROM analyses WHERE user_id = 1),
    (SELECT COUNT(*) FROM feedbacks WHERE user_id = 1),
    (SELECT COALESCE(AVG(metric_value), 0.0) FROM performances WHERE user_id = 1 AND metric_name = 'accuracy'),
    (SELECT COALESCE(AVG(latency_ms), 0.0) FROM analyses WHERE user_id = 1),
    (
        SELECT CASE COALESCE(
            (SELECT trend_direction FROM performances WHERE user_id = 1 GROUP BY trend_direction ORDER BY COUNT(*) DESC LIMIT 1),
            'stable'
        )
        WHEN 'up' THEN 'improving'
        WHEN 'down' THEN 'declining'
        ELSE 'stable' END
    ),
    (SELECT COUNT(*) FROM feedbacks WHERE user_id = 1 AND is_applied = 0),
    (SELECT MAX(created_at) FROM interactions WHERE user_id = 1),
    CURRENT_TIMESTAMP
)
ON CONFLICT(user_id) DO UPDATE SET
    total_interactions = excluded.total_interactions,
    total_analyses = excluded.total_analyses,
    total_feedbacks = excluded.total_feedbacks,
    avg_accuracy_score = excluded.avg_accuracy_score,
    avg_latency_ms = excluded.avg_latency_ms,
    overall_trend = excluded.overall_trend,
    recent_mistake_count = excluded.recent_mistake_count,
    last_interaction_at = excluded.last_interaction_at,
    last_calculated_at = CURRENT_TIMESTAMP;
