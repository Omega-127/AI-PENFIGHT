"""
AI Penfight - Analysis CRUD Operations
Manages persistence and high-performance retrieval of AI analysis results.
"""

from typing import Any, Dict, List, Optional
from database.connection import get_db, transaction
from database.crud.base import row_to_dict, rows_to_list, dump_json, load_json


class AnalysisRepository:
    @staticmethod
    def create(
        interaction_id: int,
        user_id: int,
        analysis_summary: str,
        detected_patterns: Optional[List[str]] = None,
        confidence_score: Optional[float] = None,
        model_version: str = "penfight-ai-v1",
        prompt_version: str = "prompt-v1.0",
        latency_ms: int = 0,
        db_path: Optional[str] = None,
    ) -> int:
        """Stores the result of an AI analysis run."""
        patterns_json = dump_json(detected_patterns or [])
        with transaction(db_path) as cursor:
            cursor.execute(
                """
                INSERT INTO analyses (
                    interaction_id, user_id, analysis_summary,
                    detected_patterns, confidence_score, model_version,
                    prompt_version, latency_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    interaction_id,
                    user_id,
                    analysis_summary,
                    patterns_json,
                    confidence_score,
                    model_version,
                    prompt_version,
                    latency_ms,
                ),
            )
            return cursor.lastrowid

    @staticmethod
    def get_by_id(analysis_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves an analysis by its ID."""
        with get_db(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM analyses WHERE id = ?;", (analysis_id,))
            analysis = row_to_dict(cursor.fetchone())
            if analysis:
                analysis["detected_patterns"] = load_json(analysis.get("detected_patterns"), [])
            return analysis

    @staticmethod
    def get_by_interaction_id(
        interaction_id: int, db_path: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieves the analysis associated with a specific interaction."""
        with get_db(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM analyses WHERE interaction_id = ?;", (interaction_id,))
            analysis = row_to_dict(cursor.fetchone())
            if analysis:
                analysis["detected_patterns"] = load_json(analysis.get("detected_patterns"), [])
            return analysis

    @staticmethod
    def get_previous_analyses(
        user_id: int,
        limit: int = 10,
        offset: int = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        db_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves previous analyses filtered by user and timestamp window,
        optimized using composite index (user_id, created_at DESC).
        """
        query = """
            SELECT a.id, a.interaction_id, a.user_id, a.analysis_summary,
                   a.detected_patterns, a.confidence_score, a.model_version,
                   a.prompt_version, a.latency_ms, a.created_at,
                   i.mode AS interaction_mode, i.input_data AS interaction_input
            FROM analyses a
            JOIN interactions i ON a.interaction_id = i.id
            WHERE a.user_id = ?
        """
        params: list = [user_id]

        if start_date:
            query += " AND a.created_at >= ?"
            params.append(start_date)

        if end_date:
            query += " AND a.created_at <= ?"
            params.append(end_date)

        query += " ORDER BY a.created_at DESC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        with get_db(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            analyses = rows_to_list(cursor.fetchall())
            for item in analyses:
                item["detected_patterns"] = load_json(item.get("detected_patterns"), [])
                item["interaction_input"] = load_json(item.get("interaction_input"), item.get("interaction_input"))
            return analyses

    @staticmethod
    def delete(analysis_id: int, db_path: Optional[str] = None) -> bool:
        """Deletes an analysis record and cascades to feedback."""
        with transaction(db_path) as cursor:
            cursor.execute("DELETE FROM analyses WHERE id = ?;", (analysis_id,))
            return cursor.rowcount > 0
