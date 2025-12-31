from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from agents.base_agent import AgentFactory
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat")

class ChatRequest(BaseModel):
    message: str
    stream: bool = False
    agent_type: Optional[str] = None
    user_id: str = "default_user"
    session_id: str = "web_session"

class ChatResponse(BaseModel):
    response: str
    agent: str
    model: str
    tokens_used: int
    meta: Optional[Dict[str, Any]] = None

@router.post("", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Chat with the designated AI agent"""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        # Create agent via factory
        agent = AgentFactory.create_agent(request.agent_type)
        
        if request.stream:
            async def stream_generator():
                async for chunk in agent.stream_chat(
                    request.message, 
                    user_id=request.user_id, 
                    session_id=request.session_id
                ):
                    import json
                    yield f"data: {json.dumps(chunk)}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream"
            )
        else:
            # Regular response
            response = await agent.chat(
                request.message, 
                user_id=request.user_id, 
                session_id=request.session_id
            )
            
            if "error" in response:
                raise HTTPException(status_code=500, detail=response["error"])
                
            return ChatResponse(**response)
            
    except Exception as e:
        logger.error(f"Chat Endpoint Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
