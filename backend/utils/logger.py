import os

def log_interaction(user_id: str, role: str, content: str, agent_name: str) -> None:
    """Insert a log entry into the interaction_logs.
    Args:
        user_id: Identifier of the user (or "guest").
        role: "user" or "assistant".
        content: Message content.
        agent_name: Name of the agent handling the interaction.
    """
    if not user_id:
        user_id = "guest"
    print(f"[logger] Log skipped: DB not configured")
