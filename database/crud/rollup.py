"""
AI Penfight - Performance Rollup CRUD Operations
Maintains pre-aggregated performance cache for high-speed dashboard queries.
Avoids repetitive multi-table joins and aggregations on every dashboard load.
"""

from typing import Any, Dict, Optional
from database.connection import get_db, transaction
from database.crud.base import row_to_dict


class PerformanceRollupRepository:
    @staticmethod
    def get_summary(user_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        O(1) instant retrieval of pre-aggregated dashboard metrics for a user.
        """
        with get_db(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, user_id, total_interactions, total_analyses,
                       total_feedbacks, avg_accuracy_score, avg_latency_ms,
                       overall_trend, recent_mistake_count, last_interaction_at,
                       last_calculated_at
                FROM performance_rollups
                WHERE user_id = ?;
                """,
                (user_id,),
            )
            return row_to_dict(cursor.fetchone())

    @staticmethod
    def refresh_user_summary(user_id: int, db_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Recalculates aggregate metrics from raw tables and writes to the rollup cache.
        Can be triggered asynchronously or on critical milestone events.
        """
        with transaction(db_path) as cursor:
            # 1. Total interactions & last interaction timestamp
            cursor.execute(
                "SELECT COUNT(*), MAX(created_at) FROM interactions WHERE user_id = ?;",
                (user_id,),
            )
            inter_row = cursor.fetchone()
            total_interactions = inter_row[0] if inter_row else 0
            last_interaction_at = inter_row[1] if inter_row else None

            # 2. Total analyses and average latency
            cursor.execute(
                "SELECT COUNT(*), COALESCE(AVG(latency_ms), 0.0) FROM analyses WHERE user_id = ?;",
                (user_id,),
            )
            ana_row = cursor.fetchone()
            total_analyses = ana_row[0] if ana_row else 0
            avg_latency = round(float(ana_row[1]), 2) if ana_row else 0.0

            # 3. Total feedbacks
            cursor.execute(
                "SELECT COUNT(*) FROM feedbacks WHERE user_id = ?;",
                (user_id,),
            )
            fb_row = cursor.fetchone()
            total_feedbacks = fb_row[0] if fb_row else 0

            # 4. Average accuracy and trend from performance log
            cursor.execute(
                """
                SELECT COALESCE(AVG(metric_value), 0.0)
                FROM performances
                WHERE user_id = ? AND metric_name = 'accuracy';
                """,
                (user_id,),
            )
            acc_row = cursor.fetchone()
            avg_accuracy = round(float(acc_row[0]), 2) if acc_row else 0.0

            # 5. Determine overall trend from recent performance logs
            cursor.execute(
                """
                SELECT trend_direction, COUNT(*) as cnt
                FROM performances
                WHERE user_id = ?
                GROUP BY trend_direction
                ORDER BY cnt DESC
                LIMIT 1;
                """,
                (user_id,),
            )
            trend_row = cursor.fetchone()
            raw_trend = trend_row[0] if trend_row and trend_row[0] else "stable"
            trend_map = {
                "up": "improving",
                "improving": "improving",
                "down": "declining",
                "declining": "declining",
                "stable": "stable",
            }
            overall_trend = trend_map.get(raw_trend, "stable")

            # 6. Count recent mistakes / unapplied suggestions
            cursor.execute(
                "SELECT COUNT(*) FROM feedbacks WHERE user_id = ? AND is_applied = 0;",
                (user_id,),
            )
            mistake_row = cursor.fetchone()
            recent_mistakes = mistake_row[0] if mistake_row else 0

            # Upsert into performance_rollups
            cursor.execute(
                """
                INSERT INTO performance_rollups (
                    user_id, total_interactions, total_analyses, total_feedbacks,
                    avg_accuracy_score, avg_latency_ms, overall_trend,
                    recent_mistake_count, last_interaction_at, last_calculated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
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
                """,
                (
                    user_id,
                    total_interactions,
                    total_analyses,
                    total_feedbacks,
                    avg_accuracy,
                    avg_latency,
                    overall_trend,
                    recent_mistakes,
                    last_interaction_at,
                ),
            )

        return PerformanceRollupRepository.get_summary(user_id, db_path) or {}
