import os
import sqlite3

def get_logger():
    """Simple logger utility that writes interaction logs to the SQLite DB."""
    from .logger import log_interaction  # noqa: F401
    return None
