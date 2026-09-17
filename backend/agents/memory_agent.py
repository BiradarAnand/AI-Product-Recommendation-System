from .base_agent import BaseAgent
from tools.memory_tools import fetch_user_context, save_search


class MemoryAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Memory Agent",
            description="Manages short-term and long-term user context, including recent searches and wishlists."
        )

    def process(self, message: str, context: dict, **kwargs) -> dict:
        """
        The memory agent retrieves context for the user and optionally saves the new message.
        `context` should contain 'user_id' and 'action' (e.g., 'retrieve' or 'save').
        """
        user_id = context.get("user_id")
        action = kwargs.get("action", "retrieve")

        if action == "retrieve":
            return fetch_user_context(user_id)
        elif action == "save":
            save_search(user_id, message)
            return {"status": "saved"}

        return {}