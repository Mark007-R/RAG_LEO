import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    
    APP_NAME: str = "RAG_LEO"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    TESTING: bool = False
    ENV: str = "production"
    
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    WORKERS: int = 4
    
    SECRET_KEY: str
    API_KEY_ENABLED: bool = True
    API_KEYS: str = ""
    CORS_ORIGINS: str = "*"
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS: str = "pdf"
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    
    DATABASE_URL: str = "sqlite:///rag_leo.db"
    DATABASE_ECHO: bool = False
    
    BASE_DIR: Path = Path(__file__).parent
    UPLOAD_FOLDER: str = "uploads"
    INDEX_FOLDER: str = "indexes"
    METADATA_FOLDER: str = "metadata"
    LOGS_FOLDER: str = "logs"
    TEMP_FOLDER: str = "temp"
    
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
    
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE_MAX_BYTES: int = 10 * 1024 * 1024
    LOG_FILE_BACKUP_COUNT: int = 5
    
    REDIS_URL: Optional[str] = None
    CACHE_TTL: int = 3600
    
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    
    METRICS_ENABLED: bool = True
    HEALTH_CHECK_INTERVAL: int = 60
    
    CLEANUP_ENABLED: bool = True
    CLEANUP_INTERVAL_HOURS: int = 24
    FILE_RETENTION_DAYS: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def get_upload_path(self):
        return self.BASE_DIR / self.UPLOAD_FOLDER
    
    def get_index_path(self):
        return self.BASE_DIR / self.INDEX_FOLDER
    
    def get_metadata_path(self):
        return self.BASE_DIR / self.METADATA_FOLDER
    
    def get_logs_path(self):
        return self.BASE_DIR / self.LOGS_FOLDER
    
    def get_api_keys_list(self):
        if not self.API_KEYS:
            return []
        return [key.strip() for key in self.API_KEYS.split(",") if key.strip()]
    
    def get_cors_origins_list(self):
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

class DevelopmentSettings(Settings):
    DEBUG: bool = True
    ENV: str = "development"
    LOG_LEVEL: str = "DEBUG"
    DATABASE_ECHO: bool = True
    API_KEY_ENABLED: bool = False
    RATE_LIMIT_ENABLED: bool = False
    
    class Config:
        env_file = ".env.dev"

class ProductionSettings(Settings):
    DEBUG: bool = False
    ENV: str = "production"
    LOG_LEVEL: str = "INFO"
    DATABASE_ECHO: bool = False
    API_KEY_ENABLED: bool = True
    RATE_LIMIT_ENABLED: bool = True
    
    class Config:
        env_file = ".env.prod"

class TestingSettings(Settings):
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
    env = os.getenv("APP_ENV", "production").lower()
    
    settings_map = {
        "development": DevelopmentSettings,
        "production": ProductionSettings,
        "testing": TestingSettings,
    }
    
    settings_class = settings_map.get(env, ProductionSettings)
    return settings_class()

settings = get_settings()
