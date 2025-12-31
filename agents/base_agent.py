from abc import ABC, abstractmethod
from typing import Dict, Any, List
from config.settings import settings

class BaseAgent(ABC):
    """Abstract base class for all AI agents"""
    
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.memory = []
    
    @abstractmethod
    async def chat(self, message: str, **kwargs) -> Dict[str, Any]:
        """Process a chat message"""
        pass
    
    @abstractmethod
    async def stream_chat(self, message: str, **kwargs):
        """Stream chat response"""
        pass
    
    def add_to_memory(self, role: str, content: str):
        """Add to conversation memory"""
        self.memory.append({"role": role, "content": content})
        # Keep last 10 messages
        if len(self.memory) > 10:
            self.memory = self.memory[-10:]

class AgentFactory:
    """Factory to create agents based on configuration"""
    
    @staticmethod
    def create_agent(agent_type: str = None):
        if agent_type is None:
            agent_type = settings.llm_provider
        
        if agent_type == "langchain":
            from agents.langchain_agent import LangChainAgent
            return LangChainAgent()
        elif agent_type == "ollama":
            from agents.ollama_agent import OllamaAgent
            return OllamaAgent()
        else:
            # Default fallback to Ollama if unknown
            from agents.ollama_agent import OllamaAgent
            return OllamaAgent()
