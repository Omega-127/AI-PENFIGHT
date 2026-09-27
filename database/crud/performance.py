"""
AI Penfight - Performance CRUD Operations
Records historical performance events and queries progression trends.
"""

from typing import Any, Dict, List, Optional
from database.connection import get_db, transaction
from database.crud.base import row_to_dict, rows_to_list


class PerformanceRepository:
    @staticmethod
    def record_metric(
        user_id: int,
        metric_name: str,
        metric_value: float,
        interaction_id: Optional[int] = None,
        trend_direction: str = "stable",
        db_path: Optional[str] = None,
    ) -> int:
        """Logs a single performance metric event for a user."""
        with transaction(db_path) as cursor:
            cursor.execute(
                """
                INSERT INTO performances (
                    user_id, interaction_id, metric_name, metric_value, trend_direction
                ) VALUES (?, ?, ?, ?, ?);
                """,
                (user_id, interaction_id, metric_name, metric_value, trend_direction),
            )
            return cursor.lastrowid

    @staticmethod
    def get_history(
        user_id: int,
        metric_name: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        db_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves raw performance records for a user, sorted chronologically."""
        query = """
            SELECT id, user_id, interaction_id, metric_name, metric_value,
                   trend_direction, recorded_at
            FROM performances
            WHERE user_id = ?
        """
        params: list = [user_id]

        if metric_name:
            query += " AND metric_name = ?"
            params.append(metric_name)

        query += " ORDER BY recorded_at DESC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        with get_db(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return rows_to_list(cursor.fetchall())

    @staticmethod
    def get_performance_trends(
        user_id: int,
        metric_name: str = "accuracy",
        limit: int = 20,
        db_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves recent progression trend data points for a specific metric.
        Indexed by (user_id, metric_name, recorded_at DESC).
        """
        with get_db(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, metric_name, metric_value, trend_direction, recorded_at
                FROM performances
                WHERE user_id = ? AND metric_name = ?
                ORDER BY recorded_at ASC
                LIMIT ?;
                """,
                (user_id, metric_name, limit),
            )
            return rows_to_list(cursor.fetchall())

    @staticmethod
    def calculate_overall_aggregates(
        user_id: int, db_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates raw aggregate performance statistics across the user's history.
        Used to recalculate or seed the performance rollup table.
        """
        with get_db(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    COUNT(DISTINCT i.id) AS total_interactions,
                    COUNT(DISTINCT a.id) AS total_analyses,
                    COUNT(DISTINCT f.id) AS total_feedbacks,
                    COALESCE(AVG(CASE WHEN p.metric_name = 'accuracy' THEN p.metric_value END), 0.0) AS avg_accuracy,
                    COALESCE(AVG(a.latency_ms), 0.0) AS avg_latency,
                    MAX(i.created_at) AS last_interaction
                FROM users u
                LEFT JOIN interactions i ON u.id = i.user_id
                LEFT JOIN analyses a ON u.id = a.user_id
                LEFT JOIN feedbacks f ON u.id = f.user_id
                LEFT JOIN performances p ON u.id = p.user_id
                WHERE u.id = ?
                GROUP BY u.id;
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return {
                    "total_interactions": 0,
                    "total_analyses": 0,
                    "total_feedbacks": 0,
                    "avg_accuracy": 0.0,
                    "avg_latency": 0.0,
                    "last_interaction": None,
                }
            return dict(row)
