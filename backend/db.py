# db.py
# ─────────────────────────────────────────────────────────────────────
# Single shared connection pool for the entire app.
# Import get_db() from here in every file that needs a DB connection.
#
# Math: pool_size × gunicorn_workers ≤ max_user_connections (5)
#       pool_size=2, workers=2  →  4 total  ✅
# ─────────────────────────────────────────────────────────────────────

import os
from mysql.connector import pooling

db_pool = pooling.MySQLConnectionPool(
    pool_name="app_pool",
    pool_size=2,
    pool_reset_session=True,
    host=os.environ.get("DB_HOST"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    database=os.environ.get("DB_NAME"),
    port=int(os.environ.get("DB_PORT", 3306))
)

def get_db():
    """Borrow a connection from the shared pool.
    Always call conn.close() in a finally block to return it."""
    return db_pool.get_connection()