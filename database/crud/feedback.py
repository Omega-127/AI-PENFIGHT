"""
AI Penfight - Feedback CRUD Operations
Manages personalized coaching recommendations linked to specific analyses.
"""

from typing import Any, Dict, List, Optional
from database.connection import get_db, transaction
from database.crud.base import row_to_dict, rows_to_list, dump_json, load_json


class FeedbackRepository:
    @staticmethod
    def create(
        analysis_id: int,
        user_id: int,
        title: str,
        content: str,
        recommendations: Optional[List[str]] = None,
        feedback_type: str = "adaptive",
        tone: str = "encouraging",
        db_path: Optional[str] = None,
    ) -> int:
        """Stores a personalized feedback item linked to an analysis."""
        rec_json = dump_json(recommendations or [])
        with transaction(db_path) as cursor:
            cursor.execute(
                """
                INSERT INTO feedbacks (
                    analysis_id, user_id, feedback_type,
                    title, content, recommendations, tone
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    analysis_id,
                    user_id,
                    feedback_type,
                    title,
                    content,
                    rec_json,
                    tone,
                ),
            )
            return cursor.lastrowid

    @staticmethod
    def get_by_id(feedback_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves a single feedback record by primary key."""
        with get_db(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM feedbacks WHERE id = ?;", (feedback_id,))
            feedback = row_to_dict(cursor.fetchone())
            if feedback:
                feedback["recommendations"] = load_json(feedback.get("recommendations"), [])
            return feedback

    @staticmethod
    def get_by_analysis_id(
        analysis_id: int, db_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves all feedback records generated for a specific analysis."""
        with get_db(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT f.*, a.analysis_summary, a.confidence_score
                FROM feedbacks f
                JOIN analyses a ON f.analysis_id = a.id
                WHERE f.analysis_id = ?
                ORDER BY f.created_at DESC;
                """,
                (analysis_id,),
            )
            items = rows_to_list(cursor.fetchall())
            for item in items:
                item["recommendations"] = load_json(item.get("recommendations"), [])
            return items

    @staticmethod
    def get_personalized_feedback_history(
        user_id: int,
        limit: int = 10,
        offset: int = 0,
        unapplied_only: bool = False,
        db_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves personalized feedback history for an isolated user.
        Supports filtering for active unapplied recommendations.
        """
        query = """
            SELECT f.id, f.analysis_id, f.user_id, f.feedback_type,
                   f.title, f.content, f.recommendations, f.tone,
                   f.is_applied, f.created_at,
                   a.analysis_summary, a.model_version
            FROM feedbacks f
            JOIN analyses a ON f.analysis_id = a.id
            WHERE f.user_id = ?
        """
        params: list = [user_id]

        if unapplied_only:
            query += " AND f.is_applied = 0"

        query += " ORDER BY f.created_at DESC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        with get_db(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            items = rows_to_list(cursor.fetchall())
            for item in items:
                item["recommendations"] = load_json(item.get("recommendations"), [])
            return items

    @staticmethod
    def mark_as_applied(
        feedback_id: int, is_applied: bool = True, db_path: Optional[str] = None
    ) -> bool:
        """Flags feedback as reviewed/applied by the user."""
        applied_val = 1 if is_applied else 0
        with transaction(db_path) as cursor:
            cursor.execute(
                "UPDATE feedbacks SET is_applied = ? WHERE id = ?;",
                (applied_val, feedback_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def delete(feedback_id: int, db_path: Optional[str] = None) -> bool:
        """Deletes a feedback record."""
        with transaction(db_path) as cursor:
            cursor.execute("DELETE FROM feedbacks WHERE id = ?;", (feedback_id,))
            return cursor.rowcount > 0
