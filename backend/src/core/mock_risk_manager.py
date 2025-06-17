# Mock Risk Manager for OrderManager fallback
"""
Simple mock risk manager when sophisticated one isn't available
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MockRiskManager:
    """Simple mock risk manager"""
    
    def __init__(self):
        self.enabled = True
        
    async def check_trade_allowed(self, signal) -> bool:
        """Always allow trades in mock mode"""
        return True
        
    async def check_order_risk(self, order) -> Dict[str, Any]:
        """Basic risk check"""
        return {"allowed": True, "reason": "Mock risk manager"}
        
    def validate_trade(self, symbol: str, quantity: int) -> bool:
        """Basic validation"""
        return True