"""
AI Penfight - Database Configuration Module
Provides centralized configuration and path resolution for database connections.
"""

import os
from pathlib import Path

# Base directory for the database module
BASE_DIR = Path(__file__).resolve().parent

# Default SQLite database path
DEFAULT_DB_PATH = BASE_DIR / "penfight.db"

# Allow overriding via environment variables for testing or production
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")
DATABASE_PATH = os.getenv("DATABASE_PATH", str(DEFAULT_DB_PATH))

# SQLite connection pragmas & pool configuration
SQLITE_TIMEOUT = float(os.getenv("SQLITE_TIMEOUT", "30.0"))
SQLITE_ENABLE_WAL = os.getenv("SQLITE_ENABLE_WAL", "true").lower() in ("true", "1", "yes")
SQLITE_ENABLE_FOREIGN_KEYS = True
