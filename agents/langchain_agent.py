from langchain_community.llms import Ollama
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from agents.base_agent import BaseAgent
from agents.tools import get_available_tools
from config.settings import settings
import asyncio
import logging

logger = logging.getLogger(__name__)

class LangChainAgent(BaseAgent):
    """LangChain-powered agent with tool usage"""
    
    def __init__(self):
        super().__init__("LangChain Agent", "1.0")
        
        # Setup Ollama LLM
        # Note: Streaming is handled via callback manager in some versions
        self.llm = Ollama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.7
        )
        
        # Setup memory
        self.memory_manager = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Get available tools
        self.tools = get_available_tools()
        
        # Initialize agent
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory_manager,
            verbose=settings.debug,
            handle_parsing_errors=True
        )
    
    async def chat(self, message: str, **kwargs) -> Dict[str, Any]:
        """Process chat with LangChain agent"""
        try:
            # Run in thread pool since LangChain is sync
            loop = asyncio.get_event_loop()
            # The agent.run is sync in this version of LangChain
            response = await loop.run_in_executor(
                None, 
                lambda: self.agent.run(input=message)
            )
            
            self.add_to_memory("user", message)
            self.add_to_memory("assistant", response)
            
            return {
                "response": response,
                "agent": self.name,
                "model": settings.ollama_model,
                "tokens_used": len(response.split())  # Approximation
            }
        except Exception as e:
            logger.error(f"LangChain Agent Error: {e}")
            return {
                "error": str(e),
                "response": "I encountered an error while thinking. Please check my connection to Ollama."
            }
    
    async def stream_chat(self, message: str, **kwargs):
        """Stream response token by token (Placeholder for legacy version)"""
        # In legacy initialize_agent, streaming is complex. 
        # For now, we return as a single chunk for compatibility.
        yield await self.chat(message)
