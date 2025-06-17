"""
PROPER TrueData Provider Implementation
Based on official TrueData package specifications with compression support
Version 7.0.0+ with lz4 compression
"""

import logging
import asyncio
import threading
from datetime import datetime
from typing import Dict, Optional, List, Any, Callable
import os
import json
from dataclasses import dataclass, asdict

# TrueData imports (official package)
try:
    from truedata import TD_live, TD_hist
    TRUEDATA_AVAILABLE = True
except ImportError as e:
    logging.warning(f"TrueData package not available: {e}")
    TRUEDATA_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class MarketDataUpdate:
    """Market data update structure"""
    symbol: str
    ltp: float
    volume: int
    oi: int
    bid: float
    ask: float
    high: float
    low: float
    open: float
    change: float
    change_percent: float
    timestamp: str
    data_source: str = "TRUEDATA_LIVE"

class TrueDataProvider:
    """
    Official TrueData Provider with compression support
    Uses TrueData package v7.0.0+ with lz4 compression
    """
    
    def __init__(self):
        self.login_id = os.environ.get('TRUEDATA_USERNAME', '')
        self.password = os.environ.get('TRUEDATA_PASSWORD', '')
        self.live_port = int(os.environ.get('TRUEDATA_PORT', '8082'))
        
        # TrueData objects
        self.td_live = None
        self.td_hist = None
        
        # Connection status
        self.connected = False
        self.live_data = {}
        self.last_update = None
        
        # Data callback handlers
        self.data_callbacks: List[Callable] = []
        
        # Symbol mappings (TrueData format)
        self.symbols = {
            'NIFTY': 'NIFTY 50-I',
            'BANKNIFTY': 'NIFTY BANK-I', 
            'FINNIFTY': 'NIFTY FIN SERVICE-I'
        }
        
        logger.info(f"🔗 TrueData Provider initialized for {self.login_id}")
    
    async def initialize(self) -> bool:
        """Initialize TrueData connection with compression support"""
        if not TRUEDATA_AVAILABLE:
            logger.error("❌ TrueData package not installed")
            return False
            
        if not self.login_id or not self.password:
            logger.error("❌ TrueData credentials not configured")
            return False
        
        try:
            # Initialize live data connection with compression enabled
            self.td_live = TD_live(
                self.login_id, 
                self.password,
                live_port=self.live_port,
                log_level=logging.INFO
            )
            
            # Initialize historical data connection
            self.td_hist = TD_hist(self.login_id, self.password)
            
            # Set up data callback
            self.td_live.on_data_receive = self._on_data_receive
            self.td_live.on_error = self._on_error
            self.td_live.on_disconnect = self._on_disconnect
            
            # Connect to TrueData
            await self._connect_async()
            
            if self.connected:
                # Subscribe to symbols
                await self._subscribe_symbols()
                logger.info("✅ TrueData connected with compression enabled")
                return True
            else:
                logger.error("❌ TrueData connection failed")
                return False
                
        except Exception as e:
            logger.error(f"TrueData initialization error: {e}")
            return False
    
    async def _connect_async(self):
        """Connect to TrueData in async manner"""
        def connect_sync():
            try:
                self.td_live.start()
                self.connected = True
                logger.info("🚀 TrueData live connection established")
            except Exception as e:
                logger.error(f"TrueData connection error: {e}")
                self.connected = False
        
        # Run connection in thread to avoid blocking
        await asyncio.get_event_loop().run_in_executor(
            None, connect_sync
        )
    
    async def _subscribe_symbols(self):
        """Subscribe to market symbols"""
        try:
            for symbol_key, symbol_name in self.symbols.items():
                # Subscribe to real-time data
                self.td_live.subscribe(symbol_name)
                logger.info(f"📊 Subscribed to {symbol_name}")
                
        except Exception as e:
            logger.error(f"Error subscribing to symbols: {e}")
    
    def _on_data_receive(self, data):
        """Handle incoming market data (with decompression)"""
        try:
            # TrueData automatically handles lz4 decompression
            # Data comes as Python dict/object
            
            symbol_name = data.get('symbol', '')
            
            # Map back to our symbol format
            symbol_key = None
            for key, td_symbol in self.symbols.items():
                if td_symbol in symbol_name:
                    symbol_key = key
                    break
            
            if not symbol_key:
                return
            
            # Extract market data
            ltp = float(data.get('ltp', 0))
            volume = int(data.get('volume', 0))
            oi = int(data.get('oi', 0))
            
            # Calculate bid/ask from depth
            depth = data.get('depth', {})
            bid = float(depth.get('buy', [{}])[0].get('price', ltp * 0.999))
            ask = float(depth.get('sell', [{}])[0].get('price', ltp * 1.001))
            
            # OHLC data
            ohlc = data.get('ohlc', {})
            high = float(ohlc.get('high', ltp))
            low = float(ohlc.get('low', ltp))
            open_price = float(ohlc.get('open', ltp))
            
            # Calculate change
            change = ltp - open_price
            change_percent = (change / open_price * 100) if open_price > 0 else 0
            
            # Create market data update
            market_update = MarketDataUpdate(
                symbol=symbol_key,
                ltp=round(ltp, 2),
                volume=volume,
                oi=oi,
                bid=round(bid, 2),
                ask=round(ask, 2),
                high=round(high, 2),
                low=round(low, 2),
                open=round(open_price, 2),
                change=round(change, 2),
                change_percent=round(change_percent, 2),
                timestamp=datetime.now().isoformat(),
                data_source="TRUEDATA_LIVE_COMPRESSED"
            )
            
            # Store data
            self.live_data[symbol_key] = asdict(market_update)
            self.last_update = datetime.now()
            
            # Notify callbacks
            for callback in self.data_callbacks:
                try:
                    callback(market_update)
                except Exception as cb_error:
                    logger.error(f"Callback error: {cb_error}")
            
            logger.debug(f"📈 LIVE: {symbol_key} - LTP: {ltp}, Vol: {volume}")
            
        except Exception as e:
            logger.error(f"Error processing TrueData message: {e}")
    
    def _on_error(self, error):
        """Handle TrueData errors"""
        logger.error(f"TrueData error: {error}")
        self.connected = False
    
    def _on_disconnect(self):
        """Handle TrueData disconnection"""
        logger.warning("TrueData disconnected")
        self.connected = False
        
        # Auto-reconnect after delay
        asyncio.create_task(self._auto_reconnect())
    
    async def _auto_reconnect(self):
        """Auto-reconnect to TrueData"""
        await asyncio.sleep(5)
        logger.info("🔄 Attempting TrueData reconnection...")
        await self._connect_async()
        
        if self.connected:
            await self._subscribe_symbols()
    
    def add_data_callback(self, callback: Callable):
        """Add callback for market data updates"""
        self.data_callbacks.append(callback)
    
    def get_live_data(self, symbol: str = None) -> Optional[Dict]:
        """Get live market data"""
        if symbol:
            return self.live_data.get(symbol)
        return self.live_data.copy()
    
    def is_connected(self) -> bool:
        """Check connection status"""
        return self.connected and self.td_live is not None
    
    async def get_historical_data(self, symbol: str, start_date: str, end_date: str, interval: str = "1D") -> Optional[List[Dict]]:
        """Get historical market data"""
        try:
            if not self.td_hist:
                logger.error("Historical data client not initialized")
                return None
            
            symbol_name = self.symbols.get(symbol, symbol)
            
            # Get historical data
            data = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.td_hist.get_data(
                    symbol_name,
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval
                )
            )
            
            if data is not None and not data.empty:
                # Convert to list of dicts
                return data.to_dict('records')
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return None
    
    def get_status(self) -> Dict:
        """Get detailed connection status"""
        return {
            'connected': self.connected,
            'login_id': self.login_id,
            'port': self.live_port,
            'symbols_subscribed': list(self.symbols.keys()),
            'symbols_receiving_data': list(self.live_data.keys()),
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'compression_enabled': True,  # v7.0.0+ default
            'package_version': '7.0.0+',
            'data_source': 'TRUEDATA_LIVE_COMPRESSED'
        }
    
    async def disconnect(self):
        """Disconnect from TrueData"""
        try:
            if self.td_live:
                self.td_live.disconnect()
            
            self.connected = False
            self.live_data = {}
            
            logger.info("🔴 TrueData disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting TrueData: {e}")

# Global instance
truedata_provider = TrueDataProvider()

# Helper functions for backward compatibility
async def initialize_truedata() -> bool:
    """Initialize TrueData provider"""
    return await truedata_provider.initialize()

def get_live_data(symbol: str = None) -> Optional[Dict]:
    """Get live market data"""
    return truedata_provider.get_live_data(symbol)

def is_connected() -> bool:
    """Check connection status"""
    return truedata_provider.is_connected()

def get_connection_status() -> Dict:
    """Get detailed status"""
    return truedata_provider.get_status()

async def get_historical_data(symbol: str, start_date: str, end_date: str, interval: str = "1D") -> Optional[List[Dict]]:
    """Get historical data"""
    return await truedata_provider.get_historical_data(symbol, start_date, end_date, interval)

def add_data_callback(callback: Callable):
    """Add data callback"""
    truedata_provider.add_data_callback(callback)

logger.info("🚀 TrueData Provider v7.0.0+ with compression support loaded")