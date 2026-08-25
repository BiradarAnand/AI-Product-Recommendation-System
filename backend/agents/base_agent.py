from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """Base interface for all agents in the MAS."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        
    @abstractmethod
    def process(self, message: str, context: dict, **kwargs) -> dict:
        """
        Process the user message given the context.
        Returns a dictionary with the results of the agent's work.
        """
        pass
