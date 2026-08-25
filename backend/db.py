import mysql.connector
import os
import time

def get_db(retries=3, delay=2):
    for attempt in range(retries):
        try:
            conn = mysql.connector.connect(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
                port=int(os.getenv("DB_PORT", 4000)),
                ssl_disabled=False,
                connection_timeout=15,
                autocommit=False
            )
            return conn
        except Exception as e:
            print(f"[DB] Connection attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise

import sqlite3

def get_catalog_db():
    db_path = os.path.join(os.path.dirname(__file__), "amazon_catalog.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

print("DB ready — fresh connection per request")