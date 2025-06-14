"""
Configuration settings for the trading system
"""
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os
from pathlib import Path
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings"""
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', case_sensitive=True)
    
    # API Settings
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    DEBUG: bool = Field(default=False)
    
    # Database Settings - Check for DigitalOcean DATABASE_URL first
    DATABASE_URL_OVERRIDE: Optional[str] = Field(default=None, env='DATABASE_URL')
    DB_HOST: str = Field(default="localhost", env='DB_HOST')
    DB_PORT: int = Field(default=5432, env='DB_PORT')
    DB_NAME: str = Field(default="trading", env='DB_NAME')
    DB_USER: str = Field(default="postgres", env='DB_USER')
    DB_PASSWORD: str = Field(default="", env='DB_PASSWORD')
    DB_SSL_MODE: str = Field(default="disable", env='DB_SSL_MODE')
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL with proper SSL configuration"""
        # If DigitalOcean provides DATABASE_URL, use it but fix SSL issues
        if self.DATABASE_URL_OVERRIDE:
            url = self.DATABASE_URL_OVERRIDE
            
            # Parse the URL
            parsed = urlparse(url)
            
            # Parse query parameters
            query_params = parse_qs(parsed.query)
            
            # Fix SSL parameters for SQLAlchemy
            if 'sslmode' in query_params:
                # Remove sslmode from query params as SQLAlchemy handles it differently
                del query_params['sslmode']
            
            # Reconstruct the URL without sslmode
            new_query = urlencode(query_params, doseq=True)
            new_parsed = parsed._replace(query=new_query)
            base_url = urlunparse(new_parsed)
            
            # For DigitalOcean managed databases, we need to use SSL
            # but handle it through connect_args in SQLAlchemy
            return base_url
        
        # Otherwise, construct from individual settings
        # Don't include sslmode in the URL for SQLAlchemy
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def DATABASE_CONNECT_ARGS(self) -> dict:
        """Get connection arguments for SQLAlchemy"""
        connect_args = {}
        
        # If using DigitalOcean or SSL is required
        if self.DATABASE_URL_OVERRIDE or self.DB_SSL_MODE != 'disable':
            connect_args['sslmode'] = self.DB_SSL_MODE or 'require'
            # DigitalOcean managed databases require SSL
            if 'ondigitalocean.com' in (self.DATABASE_URL_OVERRIDE or self.DB_HOST):
                connect_args['sslmode'] = 'require'
        
        return connect_args
    
    # Redis Settings - Check for DigitalOcean REDIS_URL first
    REDIS_URL_OVERRIDE: Optional[str] = Field(default=None, env='REDIS_URL')
    REDIS_HOST: str = Field(default="localhost", env='REDIS_HOST')
    REDIS_PORT: int = Field(default=6379, env='REDIS_PORT')
    REDIS_DB: int = Field(default=0, env='REDIS_DB')
    REDIS_PASSWORD: Optional[str] = Field(default=None, env='REDIS_PASSWORD')
    REDIS_SSL: bool = Field(default=False, env='REDIS_SSL')
    
    @property
    def REDIS_URL(self) -> str:
        """Construct Redis URL with proper SSL configuration"""
        # If DigitalOcean provides REDIS_URL, use it directly
        if self.REDIS_URL_OVERRIDE:
            return self.REDIS_URL_OVERRIDE
        
        # Otherwise, construct from individual settings
        protocol = "rediss" if self.REDIS_SSL else "redis"
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"{protocol}://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Trading Settings
    DEFAULT_TIMEFRAME: str = Field(default="1h")
    DEFAULT_SYMBOLS: List[str] = Field(default=["BTC/USD", "ETH/USD"])
    MAX_POSITION_SIZE: float = Field(default=1.0)
    RISK_PER_TRADE: float = Field(default=0.02)
    
    # Backtesting Settings
    BACKTEST_START_DATE: str = Field(default="2023-01-01")
    BACKTEST_END_DATE: str = Field(default="2023-12-31")
    INITIAL_CAPITAL: float = Field(default=100000.0)
    
    # Monitoring Settings
    METRICS_INTERVAL: int = Field(default=60)  # seconds
    
    # File Paths
    BASE_DIR: Path = Field(default=Path(__file__).parent.parent.parent)
    DATA_DIR: Path = Field(default=Path(__file__).parent.parent.parent / "data")
    LOGS_DIR: Path = Field(default=Path(__file__).parent.parent.parent / "logs")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    
    # Zerodha
    ZERODHA_API_KEY: Optional[str] = Field(None, description="Zerodha API key")
    ZERODHA_API_SECRET: Optional[str] = Field(None, description="Zerodha API secret")
    ZERODHA_USER_ID: Optional[str] = Field(None, description="Zerodha user ID")
    
    # TrueData
    TRUEDATA_USERNAME: Optional[str] = Field(None, description="TrueData username")
    TRUEDATA_PASSWORD: Optional[str] = Field(None, description="TrueData password")
    
    # Orchestrator
    ORCHESTRATOR_CONFIG: dict = Field(
        default={
            "max_positions": 5,
            "max_risk_per_trade": 0.02,  # 2% per trade
            "max_daily_loss": 0.05,      # 5% daily loss limit
            "default_timeframe": "1m",
            "default_provider": "zerodha"
        },
        description="Trading orchestrator configuration"
    )
    
    # WebSocket
    WS_PING_INTERVAL: int = Field(30, description="WebSocket ping interval in seconds")
    WS_PING_TIMEOUT: int = Field(10, description="WebSocket ping timeout in seconds")
    
    # Logging
    LOG_LEVEL: str = Field("INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Create settings instance
settings = get_settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(exist_ok=True)
settings.LOGS_DIR.mkdir(exist_ok=True) 