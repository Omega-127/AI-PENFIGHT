"""
AI Penfight - Database Seeder Utility
Initializes schema and seeds realistic test data.
Run using: python -m database.seed
"""

import sys
from pathlib import Path
from database.connection import init_db, get_db, transaction
from database.config import DATABASE_PATH

BASE_DIR = Path(__file__).resolve().parent
SCHEMA_FILE = BASE_DIR / "schema.sql"
SEED_FILE = BASE_DIR / "seed.sql"


def run_seed(db_path: str = None) -> None:
    path = db_path or DATABASE_PATH
    print(f"[*] Initializing database at: {path}")
    
    # 1. Initialize schema
    init_db(schema_file=str(SCHEMA_FILE), db_path=path)
    print("    [OK] Schema initialized successfully.")
    
    # 2. Execute seed data
    if not SEED_FILE.exists():
        raise FileNotFoundError(f"Seed script not found at {SEED_FILE}")
        
    with open(SEED_FILE, "r", encoding="utf-8") as f:
        seed_sql = f.read()
        
    with get_db(path) as conn:
        conn.executescript(seed_sql)
        print("    [OK] Seed data applied successfully.")
        
    # Verify counts
    with get_db(path) as conn:
        cursor = conn.cursor()
        for table in ["users", "interactions", "analyses", "feedbacks", "performances", "performance_rollups"]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            cnt = cursor.fetchone()[0]
            print(f"        - {table}: {cnt} rows")
            
    print("[*] Database seeding completed successfully!")


if __name__ == "__main__":
    db_target = sys.argv[1] if len(sys.argv) > 1 else None
    run_seed(db_target)
