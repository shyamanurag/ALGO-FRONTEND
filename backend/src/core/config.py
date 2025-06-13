"""
Trading System Configuration
"""
from pydantic import BaseModel
from typing import Dict, Any

class TradingSettings(BaseModel):
    """Trading system settings"""
    paper_trading: bool = True
    autonomous_trading_enabled: bool = True
    daily_stop_loss_percent: float = 2.0
    max_positions: int = 10
    
    class Config:
        env_prefix = "TRADING_"

# Global settings instance
settings = TradingSettings()
