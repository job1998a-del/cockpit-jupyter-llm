from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    app_name: str = "Cockpit AI Agent"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # LLM Settings
    llm_provider: str = "ollama"  # "ollama", "openai", "anthropic"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    
    # LangChain Settings
    enable_langchain: bool = True
    enable_tools: bool = True
    enable_memory: bool = True
    
    # Resemble.AI
    resemble_api_key: Optional[str] = None
    resemble_default_voice: Optional[str] = None
    
    # Render Settings
    port: int = 8000
    host: str = "0.0.0.0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "ignore"

settings = Settings()
