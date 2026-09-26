import mysql.connector
from mysql.connector import pooling, errors
import os
import time

# ── Connection config ─────────────────────────────────────────────────────────
_DB_CONFIG = {
    "host":               os.getenv("DB_HOST", "localhost"),
    "user":               os.getenv("DB_USER", "root"),
    "password":           os.getenv("DB_PASSWORD"),
    "database":           os.getenv("DB_NAME", ""),
    "port":               int(os.getenv("DB_PORT", 3305)),
    "ssl_disabled":       True,          # local MySQL — no SSL needed
    "connection_timeout": 15,
    "autocommit":         True,          # avoids forgotten-commit leaks
    "use_pure":           True,          # pure Python driver — more stable on Windows
}

# ── Pool (created once at import time) ───────────────────────────────────────
_POOL_SIZE = 5

def _create_pool():
    try:
        pool = pooling.MySQLConnectionPool(
            pool_name="recovibe_pool",
            pool_size=_POOL_SIZE,
            pool_reset_session=True,     # clears session state on reuse
            **_DB_CONFIG,
        )
        print(f"[DB] Pool created — {_POOL_SIZE} connections on {_DB_CONFIG['host']}:{_DB_CONFIG['port']}")
        return pool
    except Exception as e:
        print(f"[DB] WARNING: Could not create pool at startup: {e}")
        return None

_pool = _create_pool()


# ── Public API ────────────────────────────────────────────────────────────────
def get_db(retries=3, delay=2):
    """
    Return a live database connection.

    Tries to get one from the pool first.  If the pool is exhausted or the
    connection is stale (Errno 10053 / 2055 / 2006), falls back to opening a
    fresh raw connection with exponential backoff.
    """
    global _pool

    # 1. Try the pool
    if _pool is not None:
        for attempt in range(retries):
            try:
                conn = _pool.get_connection()
                # Ping to detect and recover from a stale connection
                conn.ping(reconnect=True, attempts=2, delay=1)
                return conn
            except errors.PoolError:
                # Pool exhausted — fall through to raw connection below
                break
            except Exception as e:
                print(f"[DB] Pool connection attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(delay)

    # 2. Fall back to a fresh raw connection (also handles pool=None at startup)
    for attempt in range(retries):
        try:
            conn = mysql.connector.connect(**_DB_CONFIG)
            return conn
        except Exception as e:
            print(f"[DB] Connection attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))   # exponential back-off
            else:
                raise


def close_db(conn):
    """
    Safely return a connection to the pool (or close it if it came from the
    fallback path).  Always call this in a finally block.
    """
    if conn is None:
        return
    try:
        conn.close()   # returns to pool if pooled, closes if raw
    except Exception:
        pass


print("DB ready — pooled connections enabled")