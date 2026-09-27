"""
AI Penfight - User CRUD Operations
Handles user registration, authentication lookups, profile updates, and isolation.
"""

from typing import Any, Dict, List, Optional
from database.connection import get_db, transaction
from database.crud.base import row_to_dict, rows_to_list, dump_json, load_json


class UserRepository:
    @staticmethod
    def create(
        username: str,
        email: str,
        password_hash: str,
        preferences: Optional[Dict[str, Any]] = None,
        db_path: Optional[str] = None,
    ) -> int:
        """
        Creates a new user account and initializes a performance rollup cache for them.
        """
        pref_json = dump_json(preferences or {})
        with transaction(db_path) as cursor:
            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash, preferences)
                VALUES (?, ?, ?, ?);
                """,
                (username, email, password_hash, pref_json),
            )
            user_id = cursor.lastrowid
            
            # Initialize empty performance rollup record for instant dashboard retrieval
            cursor.execute(
                """
                INSERT INTO performance_rollups (user_id)
                VALUES (?);
                """,
                (user_id,),
            )
            return user_id

    @staticmethod
    def get_by_id(user_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves a user by primary key ID."""
        with get_db(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?;", (user_id,))
            user = row_to_dict(cursor.fetchone())
            if user:
                user["preferences"] = load_json(user.get("preferences"), {})
            return user

    @staticmethod
    def get_by_username(username: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves a user by unique username."""
        with get_db(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?;", (username,))
            user = row_to_dict(cursor.fetchone())
            if user:
                user["preferences"] = load_json(user.get("preferences"), {})
            return user

    @staticmethod
    def get_by_email(email: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves a user by unique email."""
        with get_db(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?;", (email,))
            user = row_to_dict(cursor.fetchone())
            if user:
                user["preferences"] = load_json(user.get("preferences"), {})
            return user

    @staticmethod
    def update_preferences(
        user_id: int, preferences: Dict[str, Any], db_path: Optional[str] = None
    ) -> bool:
        """Updates user preferences JSON object."""
        pref_json = dump_json(preferences)
        with transaction(db_path) as cursor:
            cursor.execute(
                """
                UPDATE users
                SET preferences = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?;
                """,
                (pref_json, user_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def delete(user_id: int, db_path: Optional[str] = None) -> bool:
        """
        Deletes a user. Foreign-key cascading will automatically remove all
        associated interactions, analyses, feedback, and performance records.
        """
        with transaction(db_path) as cursor:
            cursor.execute("DELETE FROM users WHERE id = ?;", (user_id,))
            return cursor.rowcount > 0

    @staticmethod
    def list_all(limit: int = 50, offset: int = 0, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists users with pagination."""
        with get_db(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, username, email, preferences, created_at, updated_at
                FROM users
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?;
                """,
                (limit, offset),
            )
            users = rows_to_list(cursor.fetchall())
            for u in users:
                u["preferences"] = load_json(u.get("preferences"), {})
            return users
