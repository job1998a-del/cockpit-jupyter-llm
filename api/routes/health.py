from fastapi import APIRouter
from config.settings import settings
import time

router = APIRouter(prefix="/health")

@router.get("")
async def health_check():
    """Service health status"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "app": settings.app_name,
        "version": settings.app_version
    }
