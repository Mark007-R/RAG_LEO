"""
Production-grade configuration management.
Supports multiple environments (development, production, testing).
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # Application
    APP_NAME: str = "RAG_LEO"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    TESTING: bool = False
    ENV: str = "production"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    WORKERS: int = 4
    
    # Security
    SECRET_KEY: str
    API_KEY_ENABLED: bool = True
    API_KEYS: str = ""  # Comma-separated API keys
    CORS_ORIGINS: str = "*"
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS: str = "pdf"
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Database
    DATABASE_URL: str = "sqlite:///rag_leo.db"
    DATABASE_ECHO: bool = False
    
    # Storage
    BASE_DIR: Path = Path(__file__).parent
    UPLOAD_FOLDER: str = "uploads"
    INDEX_FOLDER: str = "indexes"
    METADATA_FOLDER: str = "metadata"
    LOGS_FOLDER: str = "logs"
    TEMP_FOLDER: str = "temp"
    
    # RAG Pipeline
    GROQ_API_KEY: str
    EMBED_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    GROQ_MODEL_NAME: str = "llama-3.1-8b-instant"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RETRIEVAL: int = 4
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 512
    LLM_TIMEOUT: int = 30
    LLM_MAX_RETRIES: int = 2
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_FILE_BACKUP_COUNT: int = 5
    
    # Redis Cache (optional)
    REDIS_URL: Optional[str] = None
    CACHE_TTL: int = 3600  # 1 hour
    
    # Celery (optional)
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    
    # Monitoring
    METRICS_ENABLED: bool = True
    HEALTH_CHECK_INTERVAL: int = 60
    
    # Data Retention
    CLEANUP_ENABLED: bool = True
    CLEANUP_INTERVAL_HOURS: int = 24
    FILE_RETENTION_DAYS: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def get_upload_path(self) -> Path:
        """Get absolute upload directory path."""
        return self.BASE_DIR / self.UPLOAD_FOLDER
    
    def get_index_path(self) -> Path:
        """Get absolute index directory path."""
        return self.BASE_DIR / self.INDEX_FOLDER
    
    def get_metadata_path(self) -> Path:
        """Get absolute metadata directory path."""
        return self.BASE_DIR / self.METADATA_FOLDER
    
    def get_logs_path(self) -> Path:
        """Get absolute logs directory path."""
        return self.BASE_DIR / self.LOGS_FOLDER
    
    def get_api_keys_list(self) -> list[str]:
        """Parse comma-separated API keys."""
        if not self.API_KEYS:
            return []
        return [key.strip() for key in self.API_KEYS.split(",") if key.strip()]
    
    def get_cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins."""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


class DevelopmentSettings(Settings):
    """Development environment settings."""
    DEBUG: bool = True
    ENV: str = "development"
    LOG_LEVEL: str = "DEBUG"
    DATABASE_ECHO: bool = True
    API_KEY_ENABLED: bool = False
    RATE_LIMIT_ENABLED: bool = False
    
    class Config:
        env_file = ".env.dev"


class ProductionSettings(Settings):
    """Production environment settings."""
    DEBUG: bool = False
    ENV: str = "production"
    LOG_LEVEL: str = "INFO"
    DATABASE_ECHO: bool = False
    API_KEY_ENABLED: bool = True
    RATE_LIMIT_ENABLED: bool = True
    
    class Config:
        env_file = ".env.prod"


class TestingSettings(Settings):
    """Testing environment settings."""
    TESTING: bool = True
    ENV: str = "testing"
    DATABASE_URL: str = "sqlite:///test_rag_leo.db"
    LOG_LEVEL: str = "WARNING"
    API_KEY_ENABLED: bool = False
    RATE_LIMIT_ENABLED: bool = False
    
    class Config:
        env_file = ".env.test"


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings based on environment.
    Uses caching to avoid repeated reads.
    """
    env = os.getenv("APP_ENV", "production").lower()
    
    settings_map = {
        "development": DevelopmentSettings,
        "production": ProductionSettings,
        "testing": TestingSettings,
    }
    
    settings_class = settings_map.get(env, ProductionSettings)
    return settings_class()


# Global settings instance
settings = get_settings()
