from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/ai_observability")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "ai_observability")
    DB_USER: str = os.getenv("DB_USER", "username")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")
    
    # Ollama Configuration
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")
    
    # ChromaDB Configuration
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501").split(",")
    
    # Alert Correlation Settings
    CORRELATION_THRESHOLD: float = 0.7
    CORRELATION_TIME_WINDOW: int = 300  # seconds
    
    # RCA Settings
    RCA_GENERATION_TIMEOUT: int = 120  # seconds
    MAX_HISTORICAL_CONTEXT: int = 10
    
    class Config:
        env_file = ".env"

settings = Settings()
