-- ====================================================================
-- AI Penfight - Sample Seed Data
-- ====================================================================
-- Populates the database with realistic sample users, interaction logs,
-- AI analysis results, coaching feedback, performance time-series,
-- and dashboard rollups.
-- ====================================================================

PRAGMA foreign_keys = ON;

-- --------------------------------------------------------------------
-- 1. SEED USERS
-- --------------------------------------------------------------------
INSERT OR IGNORE INTO users (id, username, email, password_hash, preferences, created_at)
VALUES
(1, 'alex_striker', 'alex@penfight.ai', 'pbkdf2:sha256:600000$alex$hash123', '{"theme": "dark", "feedback_verbosity": "detailed", "difficulty": "hard"}', '2026-09-01 08:00:00'),
(2, 'maya_tactics', 'maya@penfight.ai', 'pbkdf2:sha256:600000$maya$hash456', '{"theme": "light", "feedback_verbosity": "concise", "difficulty": "medium"}', '2026-09-10 09:30:00'),
(3, 'sam_rookie', 'sam@penfight.ai', 'pbkdf2:sha256:600000$sam$hash789', '{"theme": "system", "feedback_verbosity": "coaching", "difficulty": "easy"}', '2026-09-20 14:15:00');

-- --------------------------------------------------------------------
-- 2. SEED INTERACTIONS
-- --------------------------------------------------------------------
INSERT OR IGNORE INTO interactions (id, user_id, session_id, mode, input_data, status, created_at)
VALUES
-- Alex Striker Interactions (Match & Analysis)
(1, 1, 'sess_alex_001', 'analysis', '{"angle_deg": 38.5, "velocity_mps": 4.2, "flick_origin": [120, 340], "target_pen_id": "pen_bot_01", "spin": "clockwise"}', 'completed', '2026-09-25 10:10:00'),
(2, 1, 'sess_alex_001', 'feedback', '{"requested_focus": "defensive_rebound", "last_shot_id": 1}', 'completed', '2026-09-25 10:12:00'),
(3, 1, 'sess_alex_002', 'match', '{"round": 1, "flick_power": 85, "contact_point": "cap", "table_friction": 0.18}', 'completed', '2026-09-26 15:45:00'),
(4, 1, 'sess_alex_003', 'analysis', '{"angle_deg": 42.0, "velocity_mps": 5.1, "flick_origin": [140, 310], "target_pen_id": "pen_boss_02", "spin": "counter-clockwise"}', 'completed', '2026-09-27 11:20:00'),

-- Maya Tactics Interactions (Practice & Analysis)
(5, 2, 'sess_maya_001', 'practice', '{"drill": "edge_stop", "angle_deg": 15.0, "velocity_mps": 2.1, "boundary_distance_mm": 12}', 'completed', '2026-09-26 14:00:00'),
(6, 2, 'sess_maya_002', 'analysis', '{"drill": "ricochet_angle", "angle_deg": 65.2, "velocity_mps": 3.8, "table_edge_hit": true}', 'completed', '2026-09-27 08:30:00'),

-- Sam Rookie Interactions
(7, 3, 'sess_sam_001', 'analysis', '{"angle_deg": 80.0, "velocity_mps": 7.5, "flick_origin": [50, 500], "target_pen_id": "pen_target_01"}', 'completed', '2026-09-27 12:00:00');

-- --------------------------------------------------------------------
-- 3. SEED ANALYSES
-- --------------------------------------------------------------------
INSERT OR IGNORE INTO analyses (id, interaction_id, user_id, analysis_summary, detected_patterns, confidence_score, model_version, prompt_version, latency_ms, created_at)
VALUES
(1, 1, 1, 'High-velocity offensive strike. Excellent trajectory alignment with 38.5 degree attack angle.', '["optimal strike angle", "solid center-of-mass contact", "controlled follow-through"]', 0.94, 'penfight-ai-v1.2', 'feedback_prompt_v2', 320, '2026-09-25 10:10:05'),
(2, 2, 1, 'Defensive positioning analysis: Pen landed 8mm from boundary with stable friction decay.', '["minimal overshoot", "effective boundary dampening"]', 0.91, 'penfight-ai-v1.2', 'feedback_prompt_v2', 290, '2026-09-25 10:12:04'),
(3, 4, 1, 'Aggressive power strike. Velocity 5.1 m/s slightly over target threshold, causing mild table skid.', '["excessive velocity", "minor lateral drift", "high impact force"]', 0.89, 'penfight-ai-v1.2', 'feedback_prompt_v2', 310, '2026-09-27 11:20:06'),
(4, 6, 2, 'Ricochet strike successful. Angle conversion efficiency calculated at 88.4%.', '["clean rebound", "moderate spin retention"]', 0.92, 'penfight-ai-v1.2', 'feedback_prompt_v2', 350, '2026-09-27 08:30:05'),
(5, 7, 3, 'Severe over-strike detected. High risk of self-elimination over table edge.', '["excessive initial power", "over-rotation", "erratic trajectory"]', 0.97, 'penfight-ai-v1.2', 'feedback_prompt_v2', 280, '2026-09-27 12:00:04');

-- --------------------------------------------------------------------
-- 4. SEED FEEDBACKS
-- --------------------------------------------------------------------
INSERT OR IGNORE INTO feedbacks (id, analysis_id, user_id, feedback_type, title, content, recommendations, tone, is_applied, created_at)
VALUES
(1, 1, 1, 'tactical', 'Mastery in Offensive Angle', 'Your 38.5° strike vector delivered maximum momentum transfer without risking an off-table slide.', '["Maintain this thumb flick release point for medium-range targets", "Practice slight reverse spin for closer opponents"]', 'encouraging', 1, '2026-09-25 10:10:08'),
(2, 3, 1, 'adaptive', 'Power Regulation Required', 'Strike velocity exceeded safe limits by 15%. Dial back the release tension to prevent rebound penalties.', '["Reduce index finger preload tension by 10-15%", "Focus on center-of-gravity contact rather than top-cap clipping"]', 'analytical', 0, '2026-09-27 11:20:10'),
(3, 4, 2, 'adaptive', 'Precision Rebound Execution', 'Excellent trajectory calculation on the edge ricochet. Rebound angle matched simulation within 2.3 degrees.', '["Incorporate table seam friction variations into your practice routine", "Try pairing this shot with defensive edge guarding"]', 'encouraging', 1, '2026-09-27 08:30:08'),
(4, 5, 3, 'ai_generated', 'Fundamental Strike Control', 'Your shot velocity of 7.5 m/s is too aggressive for an opening move. Focus on table preservation.', '["Keep velocity under 4.0 m/s during opening rounds", "Position your pivot finger closer to the pen mid-body for stability", "Review Tutorial Drill #2: Table Edge Awareness"]', 'direct', 0, '2026-09-27 12:00:08');

-- --------------------------------------------------------------------
-- 5. SEED PERFORMANCES (TIME-SERIES METRICS)
-- --------------------------------------------------------------------
INSERT OR IGNORE INTO performances (id, user_id, interaction_id, metric_name, metric_value, trend_direction, recorded_at)
VALUES
-- Alex metrics progression
(1, 1, 1, 'accuracy', 92.5, 'up', '2026-09-25 10:10:10'),
(2, 1, 1, 'reaction_time_ms', 240.0, 'up', '2026-09-25 10:10:10'),
(3, 1, 3, 'accuracy', 89.0, 'down', '2026-09-26 15:45:10'),
(4, 1, 4, 'accuracy', 94.0, 'up', '2026-09-27 11:20:15'),
(5, 1, 4, 'flick_control', 87.5, 'stable', '2026-09-27 11:20:15'),

-- Maya metrics progression
(6, 2, 5, 'accuracy', 85.0, 'up', '2026-09-26 14:00:10'),
(7, 2, 6, 'accuracy', 88.5, 'up', '2026-09-27 08:30:10'),
(8, 2, 6, 'tactical_score', 91.0, 'up', '2026-09-27 08:30:10'),

-- Sam metrics
(9, 3, 7, 'accuracy', 62.0, 'down', '2026-09-27 12:00:10'),
(10, 3, 7, 'flick_control', 54.0, 'down', '2026-09-27 12:00:10');

-- --------------------------------------------------------------------
-- 6. SEED PERFORMANCE ROLLUPS (DASHBOARD SUMMARY CACHE)
-- --------------------------------------------------------------------
INSERT OR IGNORE INTO performance_rollups (id, user_id, total_interactions, total_analyses, total_feedbacks, avg_accuracy_score, avg_latency_ms, overall_trend, recent_mistake_count, last_interaction_at, last_calculated_at)
VALUES
(1, 1, 4, 3, 2, 91.83, 306.67, 'improving', 1, '2026-09-27 11:20:00', '2026-09-27 11:20:20'),
(2, 2, 2, 1, 1, 86.75, 350.00, 'improving', 0, '2026-09-27 08:30:00', '2026-09-27 08:30:15'),
(3, 3, 1, 1, 1, 62.00, 280.00, 'declining', 1, '2026-09-27 12:00:00', '2026-09-27 12:00:15');
