"""
AI Penfight - Base CRUD Repository
Provides common utility functions, connection management, and dict serialization for SQLite rows.
"""

import sqlite3
import json
from typing import Any, Dict, List, Optional
from database.connection import get_db, transaction


def row_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    """Converts a sqlite3.Row instance to a Python dictionary."""
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
    """Converts a sequence of sqlite3.Row instances to a list of dicts."""
    return [dict(r) for r in rows]


def dump_json(obj: Any) -> str:
    """Safely serializes Python object to JSON string."""
    if isinstance(obj, str):
        return obj
    return json.dumps(obj)


def load_json(json_str: Optional[str], default: Any = None) -> Any:
    """Safely deserializes JSON string to Python object."""
    if not json_str:
        return default
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default
