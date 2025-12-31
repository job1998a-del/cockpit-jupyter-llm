from fastapi import APIRouter
from agents.tools import get_available_tools

router = APIRouter(prefix="/api/tools")

@router.get("")
async def list_tools():
    """List all tools available to the agents"""
    tools = get_available_tools()
    return [
        {
            "name": t.name,
            "description": t.description
        } for t in tools
    ]
