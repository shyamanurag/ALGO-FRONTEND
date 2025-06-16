"""
Real TrueData Live Client using official library
Provides live market data for autonomous trading system
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Callable
from truedata import TD_live

logger = logging.getLogger(__name__)

class TrueDataLiveClient:
    """Real TrueData client using official library"""
    
    def __init__(self):
        self.username = "tdwsp697"
        self.password = "shyam@697"
        self.url = "push.truedata.in"
        self.port = 8084
        
        self.td_client = None
        self.connected = False
        self.subscribed_symbols = []
        self.live_data = {}
        self.data_callback = None
        
    def set_data_callback(self, callback: Callable):
        """Set callback function for receiving live data"""
        self.data_callback = callback
        
    def _on_trade_data(self, data):
        """Handle incoming trade data"""
        try:
            logger.info(f"📈 TrueData received: {data}")
            
            # Parse and store data
            if hasattr(data, 'symbol'):
                symbol = data.symbol
                self.live_data[symbol] = {
                    'symbol': symbol,
                    'ltp': getattr(data, 'ltp', 0),
                    'volume': getattr(data, 'volume', 0),
                    'high': getattr(data, 'high', 0),
                    'low': getattr(data, 'low', 0),
                    'timestamp': datetime.now().isoformat()
                }
                
                # Call external callback if set
                if self.data_callback:
                    self.data_callback(symbol, self.live_data[symbol])
                    
        except Exception as e:
            logger.error(f"Error processing TrueData: {e}")
    
    def connect(self) -> bool:
        """Connect to TrueData"""
        try:
            logger.info(f"🚀 Connecting to TrueData: {self.username}@{self.url}:{self.port}")
            
            self.td_client = TD_live(
                login_id=self.username,
                password=self.password,
                url=self.url,
                live_port=self.port,
                compression=False  # Disable compression
            )
            
            # Set up callback
            self.td_client.trade_callback = self._on_trade_data
            
            # Connect
            self.td_client.connect()
            self.connected = True
            
            logger.info("✅ TrueData connected successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ TrueData connection failed: {e}")
            self.connected = False
            return False
    
    def subscribe_symbols(self, symbols: List[str]) -> bool:
        """Subscribe to live data for symbols"""
        try:
            if not self.connected or not self.td_client:
                logger.warning("TrueData not connected")
                return False
                
            self.td_client.start_live_data(symbols)
            self.subscribed_symbols.extend(symbols)
            
            logger.info(f"📊 Subscribed to TrueData symbols: {symbols}")
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing to symbols: {e}")
            return False
    
    def unsubscribe_symbols(self, symbols: List[str]) -> bool:
        """Unsubscribe from symbols"""
        try:
            if not self.connected or not self.td_client:
                return False
                
            self.td_client.stop_live_data(symbols)
            
            # Remove from subscribed list
            for symbol in symbols:
                if symbol in self.subscribed_symbols:
                    self.subscribed_symbols.remove(symbol)
                    
            logger.info(f"📊 Unsubscribed from TrueData symbols: {symbols}")
            return True
            
        except Exception as e:
            logger.error(f"Error unsubscribing from symbols: {e}")
            return False
    
    def get_live_data(self, symbol: str) -> Optional[Dict]:
        """Get latest data for a symbol"""
        return self.live_data.get(symbol)
    
    def get_all_data(self) -> Dict:
        """Get all live data"""
        return self.live_data.copy()
    
    def is_connected(self) -> bool:
        """Check connection status"""
        return self.connected
    
    def get_status(self) -> Dict:
        """Get client status"""
        return {
            "connected": self.connected,
            "username": self.username,
            "server": f"{self.url}:{self.port}",
            "subscribed_symbols": self.subscribed_symbols,
            "data_count": len(self.live_data),
            "last_update": datetime.now().isoformat()
        }
    
    def disconnect(self):
        """Disconnect from TrueData"""
        try:
            if self.td_client and self.connected:
                # Stop all subscriptions
                if self.subscribed_symbols:
                    self.td_client.stop_live_data(self.subscribed_symbols)
                
                # Disconnect
                self.td_client.disconnect()
                
            self.connected = False
            self.subscribed_symbols = []
            logger.info("🔌 TrueData disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting from TrueData: {e}")

# Global instance
truedata_live_client = TrueDataLiveClient()