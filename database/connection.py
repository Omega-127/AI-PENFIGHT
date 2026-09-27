"""
AI Penfight - Database Connection & Lifecycle Management
Provides robust SQLite connection handling, foreign key enforcement,
WAL mode activation, context managers for transactions, and initialization routines.
"""

import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional
from database.config import (
    DATABASE_PATH,
    SQLITE_TIMEOUT,
    SQLITE_ENABLE_WAL,
    SQLITE_ENABLE_FOREIGN_KEYS,
)

logger = logging.getLogger("penfight.database")


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Creates and configures an active SQLite connection.
    
    CRITICAL:
    1. Foreign key enforcement is turned ON for every connection.
    2. Row factory is configured to sqlite3.Row for dict-like access.
    3. WAL mode is enabled for concurrent reads and resilient writes.
    """
    path = db_path or DATABASE_PATH
    
    # Ensure directory exists
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(
        database=path,
        timeout=SQLITE_TIMEOUT,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
    )
    
    # Enable dict-like row access
    conn.row_factory = sqlite3.Row
    
    cursor = conn.cursor()
    
    # Enforce foreign key constraints
    if SQLITE_ENABLE_FOREIGN_KEYS:
        cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Enable WAL mode for high concurrency if configured
    if SQLITE_ENABLE_WAL:
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        
    cursor.close()
    return conn


@contextmanager
def get_db(db_path: Optional[str] = None) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager providing a managed connection that automatically closes upon exit.
    """
    conn = get_db_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def transaction(db_path: Optional[str] = None) -> Generator[sqlite3.Cursor, None, None]:
    """
    Context manager providing atomic transaction management.
    Commits on success, rolls back on any exception, and closes the connection.
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception as exc:
        conn.rollback()
        logger.error(f"Transaction aborted and rolled back: {exc}", exc_info=True)
        raise exc
    finally:
        conn.close()


def init_db(schema_file: Optional[str] = None, db_path: Optional[str] = None) -> None:
    """
    Initializes the database schema by executing schema.sql.
    """
    if schema_file is None:
        schema_file = str(Path(__file__).resolve().parent / "schema.sql")
        
    schema_path = Path(schema_file)
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema definition not found at: {schema_path}")
        
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
        
    with get_db(db_path) as conn:
        conn.executescript(schema_sql)
        logger.info(f"Database successfully initialized using schema from {schema_path}")
