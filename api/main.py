from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from agents.base_agent import AgentFactory
from config.settings import settings
import logging

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("api.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown events"""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"LLM Provider: {settings.llm_provider} | Model: {settings.ollama_model}")
    
    # Initialize a test agent to warm up/verify config
    try:
        test_agent = AgentFactory.create_agent(settings.llm_provider)
        logger.info(f"Initial agent check successful: {test_agent.name}")
    except Exception as e:
        logger.error(f"Failed to verify initial agent: {e}")
    
    yield
    
    # Shutdown
    logger.info("Gracefully shutting down Trinity Core API...")

# Initialize FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from api.routes import chat, health, tools

app.include_router(health.router, tags=["System"])
app.include_router(chat.router, tags=["Intelligence"])
app.include_router(tools.router, tags=["Tools"])

@app.get("/", tags=["System"])
async def root():
    """Root metadata endpoint"""
    return {
        "status": "online",
        "app": settings.app_name,
        "version": settings.app_version,
        "provider": settings.llm_provider,
        "capabilities": ["chat", "streaming", "tools"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app", 
        host=settings.host, 
        port=settings.port, 
        reload=settings.debug
    )
