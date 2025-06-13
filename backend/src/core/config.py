"""
Simple Configuration Settings for Trading System
No Pydantic validation - just environment variable loading
"""
import os
from pathlib import Path

class SimpleSettings:
    """Simple settings class without Pydantic validation"""
    
    def __init__(self):
        # API Settings
        self.API_HOST = os.getenv("API_HOST", "0.0.0.0")
        self.API_PORT = int(os.getenv("API_PORT", "8000"))
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"
        
        # Database Settings
        self.DATABASE_URL = os.getenv("DATABASE_URL", "")
        self.DB_HOST = os.getenv("DATABASE_HOST", "localhost")
        self.DB_PORT = int(os.getenv("DATABASE_PORT", "5432"))
        self.DB_NAME = os.getenv("DATABASE_NAME", "trading")
        self.DB_USER = os.getenv("DATABASE_USER", "postgres")
        self.DB_PASSWORD = os.getenv("DATABASE_PASSWORD", "")
        
        # Redis Settings
        self.REDIS_URL = os.getenv("REDIS_URL", "")
        self.REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
        self.REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
        self.REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
        
        # Trading Settings
        self.PAPER_TRADING = os.getenv("PAPER_TRADING", "true").lower() == "true"
        self.AUTONOMOUS_TRADING_ENABLED = os.getenv("AUTONOMOUS_TRADING_ENABLED", "true").lower() == "true"
        
        # Zerodha Settings
        self.ZERODHA_API_KEY = os.getenv("ZERODHA_API_KEY", "")
        self.ZERODHA_API_SECRET = os.getenv("ZERODHA_API_SECRET", "")
        self.ZERODHA_CLIENT_ID = os.getenv("ZERODHA_CLIENT_ID", "")
        
        # Security Settings
        self.JWT_SECRET = os.getenv("JWT_SECRET", "default-secret-key")
        self.ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
        
        # CORS Settings
        self.ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
        
        # Log Settings
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    def get_database_url(self) -> str:
        """Get properly formatted database URL"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        # Construct from components
        if self.DB_PASSWORD:
            return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        else:
            return f"postgresql://{self.DB_USER}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    def get_redis_url(self) -> str:
        """Get properly formatted Redis URL"""
        if self.REDIS_URL:
            return self.REDIS_URL
        
        # Construct from components
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}"
        else:
            return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

# Create global settings instance
settings = SimpleSettings()
