import os
from .db import get_catalog_db

def log_interaction(user_id: str, role: str, content: str, agent_name: str) -> None:
    """Insert a log entry into the interaction_logs SQLite table.
    Args:
        user_id: Identifier of the user (or "guest").
        role: "user" or "assistant".
        content: Message content.
        agent_name: Name of the agent handling the interaction.
    """
    if not user_id:
        user_id = "guest"
    try:
        conn = get_catalog_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO interaction_logs (user_id, role, content, agent) VALUES (?, ?, ?, ?)",
            (user_id, role, content, agent_name)
        )
        conn.commit()
    except Exception as e:
        print(f"[logger] Failed to log interaction: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
