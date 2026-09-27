"""
AI Penfight - Interaction CRUD Operations
Manages recording and retrieval of user inputs, match sessions, and modes.
"""

from typing import Any, Dict, List, Optional
from database.connection import get_db, transaction
from database.crud.base import row_to_dict, rows_to_list, dump_json, load_json


class InteractionRepository:
    @staticmethod
    def create(
        user_id: int,
        session_id: str,
        input_data: Any,
        mode: str = "analysis",
        status: str = "completed",
        db_path: Optional[str] = None,
    ) -> int:
        """Records a new interaction event for a user."""
        formatted_input = dump_json(input_data)
        with transaction(db_path) as cursor:
            cursor.execute(
                """
                INSERT INTO interactions (user_id, session_id, mode, input_data, status)
                VALUES (?, ?, ?, ?, ?);
                """,
                (user_id, session_id, mode, formatted_input, status),
            )
            return cursor.lastrowid

    @staticmethod
    def get_by_id(interaction_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves an interaction by its ID."""
        with get_db(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM interactions WHERE id = ?;", (interaction_id,))
            interaction = row_to_dict(cursor.fetchone())
            if interaction:
                interaction["input_data"] = load_json(interaction.get("input_data"), interaction.get("input_data"))
            return interaction

    @staticmethod
    def get_user_history(
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        mode: Optional[str] = None,
        db_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves paginated interaction history for an isolated user,
        ordered by most recent first using the (user_id, created_at) index.
        """
        query = """
            SELECT id, user_id, session_id, mode, input_data, status, created_at
            FROM interactions
            WHERE user_id = ?
        """
        params: list = [user_id]
        
        if mode:
            query += " AND mode = ?"
            params.append(mode)
            
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])
        
        with get_db(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            interactions = rows_to_list(cursor.fetchall())
            for item in interactions:
                item["input_data"] = load_json(item.get("input_data"), item.get("input_data"))
            return interactions

    @staticmethod
    def update_status(
        interaction_id: int, status: str, db_path: Optional[str] = None
    ) -> bool:
        """Updates the processing status of an interaction."""
        with transaction(db_path) as cursor:
            cursor.execute(
                "UPDATE interactions SET status = ? WHERE id = ?;",
                (status, interaction_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def delete(interaction_id: int, db_path: Optional[str] = None) -> bool:
        """Deletes an interaction and cascades to analysis and feedback."""
        with transaction(db_path) as cursor:
            cursor.execute("DELETE FROM interactions WHERE id = ?;", (interaction_id,))
            return cursor.rowcount > 0
