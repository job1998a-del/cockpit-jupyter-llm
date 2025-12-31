from agents.base_agent import BaseAgent
from assistants.virtual_assistant_resemble import HumanLikeAgent
from config.settings import settings
import asyncio
from typing import Dict, Any

class OllamaAgent(BaseAgent):
    """
    Wrapper for the custom 'Almost Human' Ollama Agent.
    Maintains the cognitive stack logic.
    """
    
    def __init__(self):
        super().__init__("Almost Human Ollama Agent", "2.0")
        # Reuse the existing sophisticated agent logic
        # We point it to the settings-based config
        self.internal_agent = HumanLikeAgent()
        
    async def chat(self, message: str, **kwargs) -> Dict[str, Any]:
        user_id = kwargs.get("user_id", "default_user")
        session_id = kwargs.get("session_id", "default_session")
        
        try:
            result = await self.internal_agent.process_conversation(
                user_id, session_id, message
            )
            
            response_text = result.get("text_response", "")
            self.add_to_memory("user", message)
            self.add_to_memory("assistant", response_text)
            
            return {
                "response": response_text,
                "agent": self.name,
                "model": settings.ollama_model,
                "tokens_used": len(response_text.split()),
                "meta": {
                    "goal": result.get("goal"),
                    "tool_used": result.get("tool_used"),
                    "emotional_state": result.get("emotional_state")
                }
            }
        except Exception as e:
            return {
                "error": str(e),
                "response": "My internal cognitive stack encountered an issue."
            }

    async def stream_chat(self, message: str, **kwargs):
        # HumanLikeAgent doesn't natively stream individual tokens yet
        yield await self.chat(message, **kwargs)
