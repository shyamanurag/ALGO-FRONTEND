"""
Official TrueData Client Implementation
Using the official truedata-ws library v5.0.11
Credentials: tdwsp697/shyam@697, Port: 8084
Supports: NSE Equity, NSE F&O, Indices (250 symbols limit)
"""

import logging
import asyncio
import threading
from datetime import datetime
from typing import Dict, List, Callable, Optional
import os
from dataclasses import dataclass, asdict

# Official TrueData library
try:
    from truedata_ws import TrueDataWS
    TRUEDATA_WS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"TrueData WS package not available: {e}")
    TRUEDATA_WS_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class MarketDataUpdate:
    """Market data update structure for 250 symbols"""
    symbol: str
    symbol_id: str
    timestamp: str
    ltp: float
    volume: int
    oi: int = 0
    bid: float = 0.0
    ask: float = 0.0
    high: float = 0.0
    low: float = 0.0
    open: float = 0.0
    change: float = 0.0
    change_percent: float = 0.0
    segment: str = "NSE"
    data_source: str = "TRUEDATA_OFFICIAL"

class OfficialTrueDataClient:
    """
    Official TrueData client using truedata-ws library
    Supports NSE Equity, NSE F&O, Indices with 250 symbols limit
    """
    
    def __init__(self):
        # Official TrueData credentials
        self.username = os.environ.get('TRUEDATA_USERNAME', 'tdwsp697')
        self.password = os.environ.get('TRUEDATA_PASSWORD', 'shyam@697')
        self.port = int(os.environ.get('TRUEDATA_PORT', '8084'))
        
        # TrueData client
        self.td_client = None
        self.connected = False
        
        # Data storage
        self.live_data = {}
        self.last_update = None
        
        # Callbacks
        self.data_callbacks: List[Callable] = []
        
        # Top symbols for futures trading (will be populated dynamically)
        self.subscribed_symbols = []
        
        logger.info(f"🔗 Official TrueData Client initialized for {self.username} on port {self.port}")
    
    def start_connection(self) -> bool:
        """Start connection using official TrueData library"""
        if not TRUEDATA_WS_AVAILABLE:
            logger.error("❌ TrueData WS library not available")
            return False
            
        try:
            logger.info(f"🚀 Starting official TrueData connection...")
            
            # Initialize official TrueData client
            self.td_client = TrueDataWS(
                username=self.username,
                password=self.password,
                live_port=self.port
            )
            
            # Set up data callback
            self.td_client.on_message = self._on_message_received
            self.td_client.on_open = self._on_connection_open
            self.td_client.on_close = self._on_connection_close
            self.td_client.on_error = self._on_connection_error
            
            # Start connection
            self.td_client.start()
            
            # Wait for connection to establish
            import time
            time.sleep(3)
            
            if self.td_client.is_connected():
                self.connected = True
                logger.info("✅ Official TrueData connected successfully")
                
                # Subscribe to initial symbols
                self._subscribe_initial_symbols()
                return True
            else:
                logger.error("❌ TrueData connection failed")
                return False
                
        except Exception as e:
            logger.error(f"Error starting TrueData connection: {e}")
            return False
    
    def _on_connection_open(self):
        """Handle connection open"""
        logger.info("✅ TrueData WebSocket connection opened")
        self.connected = True
    
    def _on_connection_close(self):
        """Handle connection close"""
        logger.warning("🔴 TrueData WebSocket connection closed")
        self.connected = False
    
    def _on_connection_error(self, error):
        """Handle connection error"""
        logger.error(f"TrueData connection error: {error}")
        self.connected = False
    
    def _on_message_received(self, message):
        """Handle incoming market data messages"""
        try:
            logger.debug(f"📊 TrueData message: {message}")
            
            # Parse TrueData message format
            if isinstance(message, dict):
                # Extract symbol and price data
                symbol = message.get('symbol', '')
                
                if symbol and 'ltp' in message:
                    # Create market data update
                    market_update = MarketDataUpdate(
                        symbol=symbol,
                        symbol_id=str(message.get('token', '')),
                        timestamp=datetime.now().isoformat(),
                        ltp=float(message.get('ltp', 0)),
                        volume=int(message.get('volume', 0)),
                        oi=int(message.get('oi', 0)),
                        bid=float(message.get('bid', 0)),
                        ask=float(message.get('ask', 0)),
                        high=float(message.get('high', 0)),
                        low=float(message.get('low', 0)),
                        open=float(message.get('open', 0)),
                        change=float(message.get('change', 0)),
                        change_percent=float(message.get('change_percent', 0)),
                        segment=message.get('segment', 'NSE'),
                        data_source="TRUEDATA_OFFICIAL"
                    )
                    
                    # Store data
                    self.live_data[symbol] = asdict(market_update)
                    self.last_update = datetime.now()
                    
                    # Notify callbacks
                    for callback in self.data_callbacks:
                        try:
                            callback(market_update)
                        except Exception as cb_error:
                            logger.error(f"Callback error: {cb_error}")
                    
                    logger.debug(f"📈 REAL: {symbol} - LTP: {market_update.ltp}")
            
        except Exception as e:
            logger.error(f"Error processing TrueData message: {e}")
    
    def _subscribe_initial_symbols(self):
        """Subscribe to initial set of symbols"""
        try:
            # Start with major indices and top futures
            initial_symbols = [
                # Major Indices
                "NIFTY 50",
                "NIFTY BANK", 
                "NIFTY FIN SERVICE",
                "SENSEX",
                "NIFTY IT",
                
                # Top liquid futures (examples - should be dynamic)
                "RELIANCE",
                "TCS", 
                "HDFCBANK",
                "INFY",
                "ITC"
            ]
            
            logger.info(f"📊 Subscribing to {len(initial_symbols)} initial symbols...")
            
            # Subscribe using official library
            for symbol in initial_symbols:
                try:
                    self.td_client.subscribe(symbol, live_data=True)
                    self.subscribed_symbols.append(symbol)
                    logger.debug(f"✅ Subscribed to {symbol}")
                except Exception as sub_error:
                    logger.error(f"Error subscribing to {symbol}: {sub_error}")
            
            logger.info(f"✅ Subscribed to {len(self.subscribed_symbols)} symbols")
            
        except Exception as e:
            logger.error(f"Error subscribing to initial symbols: {e}")
    
    def subscribe_to_top_futures(self, symbols: List[str]):
        """Subscribe to top 250 futures dynamically"""
        try:
            logger.info(f"📊 Subscribing to {len(symbols)} top futures...")
            
            for symbol in symbols[:250]:  # Respect 250 symbol limit
                try:
                    if symbol not in self.subscribed_symbols:
                        self.td_client.subscribe(symbol, live_data=True)
                        self.subscribed_symbols.append(symbol)
                        logger.debug(f"✅ Added subscription: {symbol}")
                except Exception as sub_error:
                    logger.error(f"Error subscribing to {symbol}: {sub_error}")
            
            logger.info(f"✅ Total subscribed symbols: {len(self.subscribed_symbols)}")
            
        except Exception as e:
            logger.error(f"Error subscribing to top futures: {e}")
    
    def add_data_callback(self, callback: Callable):
        """Add callback for market data updates"""
        self.data_callbacks.append(callback)
        logger.info(f"📊 Added data callback: {len(self.data_callbacks)} total")
    
    def get_live_data(self, symbol: str = None) -> Optional[Dict]:
        """Get live market data"""
        if symbol:
            return self.live_data.get(symbol)
        return self.live_data.copy()
    
    def is_connected(self) -> bool:
        """Check connection status"""
        return self.connected and self.td_client and self.td_client.is_connected()
    
    def get_status(self) -> Dict:
        """Get detailed connection status"""
        return {
            'connected': self.is_connected(),
            'username': self.username,
            'port': self.port,
            'symbols_subscribed': self.subscribed_symbols,
            'symbols_receiving_data': list(self.live_data.keys()),
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'subscription_limit': 250,
            'current_subscriptions': len(self.subscribed_symbols),
            'segments': ['NSE Equity', 'NSE F&O', 'Indices'],
            'data_source': 'TRUEDATA_OFFICIAL_LIBRARY'
        }
    
    def disconnect(self):
        """Disconnect from TrueData"""
        try:
            if self.td_client:
                self.td_client.close()
            
            self.connected = False
            self.live_data = {}
            self.subscribed_symbols = []
            
            logger.info("🔴 Official TrueData disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting TrueData: {e}")

# Thread-based wrapper for async compatibility
class OfficialTrueDataWrapper:
    """Thread wrapper for official TrueData client"""
    
    def __init__(self):
        self.client = OfficialTrueDataClient()
        self.thread = None
        self.started = False
    
    def start(self):
        """Start TrueData client in separate thread"""
        if self.started:
            return self.client.is_connected()
            
        def run_client():
            success = self.client.start_connection()
            if success:
                logger.info("🎯 Official TrueData client running in background")
            else:
                logger.error("❌ Failed to start official TrueData client")
        
        self.thread = threading.Thread(target=run_client, daemon=True)
        self.thread.start()
        
        # Wait for connection
        import time
        time.sleep(5)
        self.started = True
        
        return self.client.is_connected()
    
    def add_data_callback(self, callback):
        """Add data callback"""
        self.client.add_data_callback(callback)
    
    def get_live_data(self, symbol=None):
        """Get live data"""
        return self.client.get_live_data(symbol)
    
    def is_connected(self):
        """Check connection"""
        return self.client.is_connected()
    
    def get_status(self):
        """Get status"""
        return self.client.get_status()
    
    def subscribe_top_futures(self, symbols):
        """Subscribe to top futures"""
        self.client.subscribe_to_top_futures(symbols)
    
    def disconnect(self):
        """Disconnect"""
        self.client.disconnect()
        self.started = False

# Global instance
official_truedata_client = OfficialTrueDataWrapper()

# Helper functions for compatibility
def initialize_official_truedata() -> bool:
    """Initialize official TrueData client"""
    return official_truedata_client.start()

def get_live_data(symbol: str = None) -> Optional[Dict]:
    """Get live market data"""
    return official_truedata_client.get_live_data(symbol)

def is_connected() -> bool:
    """Check connection status"""
    return official_truedata_client.is_connected()

def get_connection_status() -> Dict:
    """Get detailed status"""
    return official_truedata_client.get_status()

def add_data_callback(callback: Callable):
    """Add data callback"""
    official_truedata_client.add_data_callback(callback)

def subscribe_to_top_futures(symbols: List[str]):
    """Subscribe to top 250 futures"""
    official_truedata_client.subscribe_top_futures(symbols)

logger.info("🚀 Official TrueData Client loaded (using truedata-ws v5.0.11)")