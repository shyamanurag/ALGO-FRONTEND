"""
FIXED TrueData Integration
Replaces all buggy TrueData library implementations with our proper WebSocket client
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime
import os
import asyncio

logger = logging.getLogger(__name__)

# Import our proper TrueData client
from proper_truedata_client import (
    proper_truedata_client, 
    initialize_proper_truedata,
    get_live_data,
    is_connected,
    get_connection_status,
    add_data_callback
)

class FixedTrueDataManager:
    """
    Fixed TrueData manager that uses our proper WebSocket implementation
    Replaces all the buggy library calls with clean, working code
    """
    
    def __init__(self):
        self.client = proper_truedata_client
        self.connected = False
        self.last_status = {}
        
    async def initialize(self) -> bool:
        """Initialize TrueData connection"""
        try:
            logger.info("🚀 Initializing FIXED TrueData integration...")
            
            # Use our proper implementation
            success = initialize_proper_truedata()
            self.connected = success
            
            if success:
                logger.info("✅ Fixed TrueData connected successfully")
                
                # Set up data callback for logging
                def data_callback(market_update):
                    logger.info(f"📊 Market Data: {market_update.symbol} - LTP: {market_update.ltp}")
                
                add_data_callback(data_callback)
                
            else:
                logger.error("❌ Fixed TrueData connection failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Error initializing fixed TrueData: {e}")
            return False
    
    def get_market_data(self, symbol: str = None) -> Optional[Dict]:
        """Get live market data"""
        try:
            return get_live_data(symbol)
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return None
    
    def is_connected(self) -> bool:
        """Check connection status"""
        try:
            return is_connected()
        except Exception as e:
            logger.error(f"Error checking connection: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Get detailed status"""
        try:
            status = get_connection_status()
            self.last_status = status
            return status
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return self.last_status or {
                'connected': False,
                'error': str(e),
                'data_source': 'FIXED_TRUEDATA_ERROR'
            }
    
    async def disconnect(self):
        """Disconnect TrueData"""
        try:
            self.client.disconnect()
            self.connected = False
            logger.info("🔴 Fixed TrueData disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")

# Global instance
fixed_truedata_manager = FixedTrueDataManager()

# Replacement functions for the buggy implementations
async def connect_truedata_fixed():
    """
    FIXED version of TrueData connection
    Replaces all the buggy endpoint implementations
    """
    try:
        logger.info("🔄 Connecting TrueData using FIXED implementation...")
        
        success = await fixed_truedata_manager.initialize()
        
        if success:
            status = fixed_truedata_manager.get_status()
            
            return {
                "success": True,
                "message": "TrueData connected successfully using FIXED implementation",
                "status": status,
                "data_source": "FIXED_TRUEDATA_WEBSOCKET",
                "symbols": ["NIFTY", "BANKNIFTY", "FINNIFTY"],
                "websocket_url_format": "wss://{url}:{port}?user={username}&password={password}",
                "compression": "disabled (avoiding library bugs)",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": "TrueData connection failed",
                "error": "Connection timeout or authentication failure",
                "data_source": "FIXED_TRUEDATA_ERROR"
            }
            
    except Exception as e:
        logger.error(f"Fixed TrueData connection error: {e}")
        return {
            "success": False,
            "message": "TrueData connection error",
            "error": str(e),
            "data_source": "FIXED_TRUEDATA_ERROR"
        }

async def disconnect_truedata_fixed():
    """FIXED version of TrueData disconnection"""
    try:
        await fixed_truedata_manager.disconnect()
        
        return {
            "success": True,
            "message": "TrueData disconnected successfully using FIXED implementation",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Fixed TrueData disconnect error: {e}")
        return {
            "success": False,
            "message": "TrueData disconnect error",
            "error": str(e)
        }

def get_truedata_status_fixed():
    """FIXED version of TrueData status"""
    try:
        return {
            "success": True,
            "connected": fixed_truedata_manager.is_connected(),
            "status": fixed_truedata_manager.get_status(),
            "live_data": fixed_truedata_manager.get_market_data(),
            "implementation": "FIXED_TRUEDATA_WEBSOCKET",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Fixed TrueData status error: {e}")
        return {
            "success": False,
            "error": str(e),
            "connected": False,
            "implementation": "FIXED_TRUEDATA_ERROR"
        }

def get_live_market_data_fixed(symbol: str = None):
    """FIXED version of getting live market data - REAL DATA ONLY"""
    try:
        # ONLY use real TrueData client - NO FALLBACK TO MOCK DATA
        data = fixed_truedata_manager.get_market_data(symbol)
        
        if data and isinstance(data, dict) and len(data) > 0:
            return {
                "success": True,
                "data": data,
                "symbols": list(data.keys()) if isinstance(data, dict) else [symbol] if symbol else [],
                "data_source": "FIXED_TRUEDATA_WEBSOCKET",
                "timestamp": datetime.now().isoformat()
            }
        else:
            # NO FALLBACK - FAIL PROPERLY IF NO REAL DATA
            return {
                "success": False,
                "message": "No real market data available from TrueData",
                "data_source": "NO_REAL_DATA",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Fixed market data error: {e}")
        return {
            "success": False,
            "error": str(e),
            "data_source": "TRUEDATA_ERROR"
        }

logger.info("🚀 Fixed TrueData Integration loaded - no buggy library dependencies")