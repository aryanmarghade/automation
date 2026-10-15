import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "NexusFlow AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Host and port
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    WORKSPACE_DIR: Path = BASE_DIR / "workspace"
    DATA_DIR: Path = BASE_DIR / "backend" / "data"
    
    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DATA_DIR}/nexusflow.db"
    
    # Security
    SECRET_KEY: str = "nexusflow-insecure-secret-key-change-in-prod"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # AI Engine Defaults
    DEFAULT_AI_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    DEFAULT_OLLAMA_MODEL: str = "llama3.2:latest"
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    OPENAI_API_KEY: str = ""
    
    # Execution Sandbox Limits
    MAX_WORKFLOW_TIMEOUT_SEC: int = 300
    MAX_STEP_TIMEOUT_SEC: int = 60
    MAX_AGENT_ITERATIONS: int = 15
    MAX_CONCURRENT_STEPS: int = 4
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure critical directories exist
settings.WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
