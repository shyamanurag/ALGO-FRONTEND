"""
HYBRID REAL DATA PROVIDER
Primary: TrueData (fastest, real-time ticks)
Fallback: Zerodha (reliable, real market data)
NO SIMULATION EVER!
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, List
import os

logger = logging.getLogger(__name__)

class HybridDataProvider:
    """
    Hybrid real data provider - TrueData primary, Zerodha fallback
    NEVER uses simulation - only real market data
    """
    
    def __init__(self):
        self.truedata_client = None
        self.zerodha_client = None
        self.current_provider = None
        self.market_data = {}
        self.last_update = None
        
        # Symbols to track
        self.symbols = ["NIFTY", "BANKNIFTY", "FINNIFTY"]
        
        # Provider priority
        self.provider_priority = ["TRUEDATA", "ZERODHA"]
        
    async def initialize(self):
        """Initialize both data providers"""
        try:
            # Initialize TrueData
            await self._initialize_truedata()
            
            # Initialize Zerodha
            await self._initialize_zerodha()
            
            # Determine active provider
            await self._select_active_provider()
            
            logger.info(f"✅ Hybrid data provider initialized - Active: {self.current_provider}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize hybrid data provider: {e}")
            return False
    
    async def _initialize_truedata(self):
        """Initialize TrueData client"""
        try:
            from truedata_client import TrueDataClient
            
            self.truedata_client = TrueDataClient()
            self.truedata_client.start_connection()
            
            # Wait a moment for connection
            await asyncio.sleep(3)
            
            if self.truedata_client.connected:
                logger.info("✅ TrueData initialized and connected")
            else:
                logger.warning("⚠️ TrueData initialized but not connected")
                
        except Exception as e:
            logger.error(f"TrueData initialization failed: {e}")
            self.truedata_client = None
    
    async def _initialize_zerodha(self):
        """Initialize REAL Zerodha client for PAID subscription"""
        try:
            from real_zerodha_client import get_real_zerodha_client
            
            self.zerodha_client = get_real_zerodha_client()
            
            status = self.zerodha_client.get_status()
            
            if status['has_credentials']:
                if status['authenticated']:
                    logger.info("✅ Real Zerodha initialized and authenticated - PAID subscription")
                else:
                    logger.info("⚠️ Real Zerodha initialized but needs authentication - PAID subscription")
            else:
                logger.warning("⚠️ Zerodha credentials not configured - need real API keys for PAID subscription")
                
        except Exception as e:
            logger.error(f"Real Zerodha initialization failed: {e}")
            self.zerodha_client = None
    
    async def _select_active_provider(self):
        """Select the best available data provider"""
        # Try TrueData first
        if self.truedata_client and self.truedata_client.connected:
            self.current_provider = "TRUEDATA"
            logger.info("🚀 Using TrueData as primary data source")
            return
        
        # Fallback to Zerodha (PAID subscription)
        if self.zerodha_client:
            status = self.zerodha_client.get_status()
            if status['has_credentials']:
                self.current_provider = "ZERODHA"
                logger.info("🔄 Using PAID Zerodha subscription as data source")
                return
        
        # No providers available
        self.current_provider = None
        logger.error("❌ No data providers available - will return empty data")
    
    async def get_live_market_data(self) -> Optional[Dict]:
        """Get live market data from active provider"""
        try:
            # Refresh provider status
            await self._check_and_switch_provider()
            
            if self.current_provider == "TRUEDATA":
                return await self._get_truedata_data()
            elif self.current_provider == "ZERODHA":
                return await self._get_zerodha_data()
            else:
                logger.error("No active data provider available")
                return None
                
        except Exception as e:
            logger.error(f"Error getting live market data: {e}")
            return None
    
    async def _check_and_switch_provider(self):
        """Check provider health and switch if needed"""
        # If TrueData reconnected, switch back to it
        if (self.current_provider != "TRUEDATA" and 
            self.truedata_client and 
            self.truedata_client.connected):
            
            self.current_provider = "TRUEDATA"
            logger.info("🔄 Switched back to TrueData (primary)")
            
        # If current provider failed, try fallback
        elif (self.current_provider == "TRUEDATA" and 
              (not self.truedata_client or not self.truedata_client.connected)):
            
            if self.zerodha_client:
                self.current_provider = "ZERODHA"
                logger.warning("🔄 TrueData lost, switching to Zerodha fallback")
            else:
                self.current_provider = None
                logger.error("❌ All data providers failed")
    
    async def _get_truedata_data(self) -> Optional[Dict]:
        """Get data from TrueData"""
        try:
            if not self.truedata_client or not self.truedata_client.connected:
                return None
            
            # Get live data from TrueData
            live_data = self.truedata_client.live_data
            
            if not live_data:
                return None
            
            # Format data for API response
            formatted_data = {}
            for symbol in self.symbols:
                if symbol in live_data:
                    data = live_data[symbol]
                    formatted_data[symbol] = {
                        "symbol": symbol,
                        "ltp": data.get("ltp", 0),
                        "change": data.get("change", 0),
                        "change_percent": data.get("change_percent", 0),
                        "volume": data.get("volume", 0),
                        "high": data.get("high", 0),
                        "low": data.get("low", 0),
                        "open": data.get("open", 0),
                        "data_source": "REAL_TRUEDATA",
                        "market_status": "OPEN" if self._is_market_open() else "CLOSED",
                        "timestamp": datetime.now().isoformat(),
                        "connection_status": "TrueData live feed"
                    }
            
            if formatted_data:
                self.last_update = datetime.now()
                logger.debug(f"📊 TrueData: {len(formatted_data)} symbols updated")
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"Error getting TrueData data: {e}")
            return None
    
    async def _get_zerodha_data(self) -> Optional[Dict]:
        """Get REAL data from PAID Zerodha subscription"""
        try:
            if not self.zerodha_client:
                return None
            
            # Get REAL quotes from PAID Zerodha subscription
            quotes = await self.zerodha_client.get_live_quotes(self.symbols)
            
            if quotes:
                self.last_update = datetime.now()
                logger.debug(f"📊 PAID Zerodha: {len(quotes)} symbols updated")
            
            return quotes
            
        except Exception as e:
            logger.error(f"Error getting PAID Zerodha data: {e}")
            return None
    
    def _is_market_open(self) -> bool:
        """Check if market is open"""
        current_time = datetime.now().time()
        market_open = datetime.strptime("09:15", "%H:%M").time()
        market_close = datetime.strptime("15:30", "%H:%M").time()
        
        return market_open <= current_time <= market_close
    
    def get_provider_status(self) -> Dict:
        """Get status of all providers"""
        return {
            "current_provider": self.current_provider,
            "truedata_status": {
                "available": self.truedata_client is not None,
                "connected": self.truedata_client.connected if self.truedata_client else False
            },
            "zerodha_status": {
                "available": self.zerodha_client is not None,
                "connected": True if self.zerodha_client else False  # Zerodha uses HTTP API
            },
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "data_integrity": "REAL_DATA_ONLY"
        }
    
    async def start_monitoring(self):
        """Start continuous monitoring and provider switching"""
        while True:
            try:
                await self._check_and_switch_provider()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Provider monitoring error: {e}")
                await asyncio.sleep(60)

# Global instance
hybrid_data_provider = HybridDataProvider()

async def get_hybrid_data_provider():
    """Get the global hybrid data provider"""
    return hybrid_data_provider