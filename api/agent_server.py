from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from assistants.virtual_assistant_resemble import HumanLikeAgent
import logging
import time
import asyncio

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgentAPI")

app = FastAPI(title="Trinity Core Agent API")

# Initialize the Agent
# Note: In a production env, you might want to manage this via a lifespan handler
agent = HumanLikeAgent()

@app.on_event("startup")
async def startup_event():
    await agent.initialize()
    logger.info("Trinity Core Agent initialized and ready for API requests.")

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    OpenAI-compatible endpoint for chat completions.
    Maps messages to the HumanLikeAgent's process loop.
    """
    data = await request.json()
    messages = data.get("messages", [])
    
    if not messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    # Extract the last user message
    user_input = messages[-1]["content"]
    user_id = data.get("user", "default_user")
    session_id = data.get("session_id", "web_ui_session")

    logger.info(f"Received request from user {user_id}: {user_input[:50]}...")

    try:
        # Process via our cognitive stack
        result = await agent.process_conversation(user_id, session_id, user_input)
        
        reply_content = result.get("text_response", "I'm sorry, I couldn't process that.")
        
        # Format response to match OpenAI spec
        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "trinity-core-agent",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": reply_content
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }
    except Exception as e:
        logger.error(f"Error processing agent request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/models")
async def list_models():
    """Returns the agent as a model option."""
    return {
        "object": "list",
        "data": [
            {
                "id": "trinity-core-agent",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "trinity-core"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
