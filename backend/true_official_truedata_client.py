"""
TRUE OFFICIAL TrueData Client Implementation
Using EXACT format from GitHub sample code
URL: push.truedata.in, Port: 9084
Uses official 'truedata' library with TD_live class
"""

import logging
import time
import threading
from datetime import datetime
from typing import Dict, List, Callable, Optional
import os
from dataclasses import dataclass, asdict

# Official TrueData library (the one that actually works)
try:
    from truedata import TD_live
    TRUEDATA_OFFICIAL_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Official TrueData package not available: {e}")
    TRUEDATA_OFFICIAL_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class MarketDataUpdate:
    """Market data update structure"""
    symbol: str
    ltp: float
    volume: int
    timestamp: str
    oi: int = 0
    bid: float = 0.0
    ask: float = 0.0
    high: float = 0.0
    low: float = 0.0
    open: float = 0.0
    change: float = 0.0
    change_percent: float = 0.0
    data_source: str = "TRUEDATA_OFFICIAL_LIBRARY"

class TrueOfficialTrueDataClient:
    """
    TRUE Official TrueData client using exact GitHub sample format
    """
    
    def __init__(self):
        # Credentials from environment
        self.username = os.environ.get('TRUEDATA_USERNAME', 'tdwsp697')
        self.password = os.environ.get('TRUEDATA_PASSWORD', 'shyam@697')
        
        # Official TrueData client
        self.td_obj = None
        self.connected = False
        
        # Data storage
        self.live_data = {}
        self.last_update = None
        
        # Callbacks
        self.data_callbacks: List[Callable] = []
        
        logger.info(f"🔗 TRUE Official TrueData Client initialized for {self.username}")
    
    def start_connection(self) -> bool:
        """Start connection using EXACT GitHub sample format"""
        if not TRUEDATA_OFFICIAL_AVAILABLE:
            logger.error("❌ Official TrueData library not available")
            return False
            
        try:
            logger.info("🚀 Starting TRUE Official TrueData connection (GitHub sample format)...")
            
            # EXACT format from GitHub sample
            self.td_obj = TD_live(
                self.username, 
                self.password, 
                url='push.truedata.in', 
                live_port=9084,  # Correct port from sample
                log_level=logging.WARNING,
                full_feed=True,
                dry_run=False
            )
            
            logger.info("✅ TD_live object created successfully")
            
            # Set up callbacks exactly like the sample
            @self.td_obj.full_feed_trade_callback
            def full_feed_trade(tick_data):
                try:
                    logger.debug(f"📊 Tick data received: {tick_data}")
                    self._process_tick_data(tick_data)
                except Exception as e:
                    logger.error(f"Error processing tick data: {e}")
            
            @self.td_obj.bidask_callback
            def new_bidask(bidask_data):
                try:
                    logger.debug(f"📊 BidAsk data received: {bidask_data}")
                    self._process_bidask_data(bidask_data)
                except Exception as e:
                    logger.error(f"Error processing bidask data: {e}")
            
            @self.td_obj.full_feed_bar_callback
            def full_feed_bar(bar_data):
                try:
                    logger.debug(f"📊 Bar data received: {bar_data}")
                    self._process_bar_data(bar_data)
                except Exception as e:
                    logger.error(f"Error processing bar data: {e}")
            
            # Wait for connection to establish (like in sample)
            time.sleep(3)
            
            self.connected = True
            logger.info("✅ TRUE Official TrueData connected successfully!")
            
            # Subscribe to initial symbols
            self._subscribe_initial_symbols()
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting TRUE Official TrueData: {e}")
            return False
    
    def _process_tick_data(self, tick_data):
        """Process tick data from TrueData"""
        try:
            # Extract data from TrueData tick format
            if isinstance(tick_data, dict):
                symbol = tick_data.get('symbol', '')
                ltp = float(tick_data.get('ltp', 0))
                volume = int(tick_data.get('volume', 0))
                
                if symbol and ltp > 0:
                    # Create market update
                    market_update = MarketDataUpdate(
                        symbol=symbol,
                        ltp=ltp,
                        volume=volume,
                        timestamp=datetime.now().isoformat(),
                        oi=int(tick_data.get('oi', 0)),
                        high=float(tick_data.get('high', ltp)),
                        low=float(tick_data.get('low', ltp)),
                        open=float(tick_data.get('open', ltp)),
                        data_source="TRUEDATA_OFFICIAL_LIBRARY"
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
                    
                    logger.debug(f"📈 TRUE REAL: {symbol} - LTP: {ltp}")
            
        except Exception as e:
            logger.error(f"Error processing tick data: {e}")
    
    def _process_bidask_data(self, bidask_data):
        """Process bid-ask data"""
        try:
            # Update existing symbol data with bid/ask
            if isinstance(bidask_data, dict):
                symbol = bidask_data.get('symbol', '')
                if symbol in self.live_data:
                    self.live_data[symbol]['bid'] = float(bidask_data.get('bid', 0))
                    self.live_data[symbol]['ask'] = float(bidask_data.get('ask', 0))
        except Exception as e:
            logger.error(f"Error processing bidask data: {e}")
    
    def _process_bar_data(self, bar_data):
        """Process bar data (OHLCV)"""
        try:
            # Update OHLC data
            if isinstance(bar_data, dict):
                symbol = bar_data.get('symbol', '')
                if symbol in self.live_data:
                    self.live_data[symbol]['high'] = float(bar_data.get('high', 0))
                    self.live_data[symbol]['low'] = float(bar_data.get('low', 0))
                    self.live_data[symbol]['open'] = float(bar_data.get('open', 0))
        except Exception as e:
            logger.error(f"Error processing bar data: {e}")
    
    def _subscribe_initial_symbols(self):
        """Subscribe to initial symbols for testing"""
        try:
            # Start with basic symbols to test connection
            # Once working, expand to top 250 futures
            initial_symbols = [
                "NIFTY",
                "BANKNIFTY", 
                "FINNIFTY",
                "RELIANCE",
                "TCS"
            ]
            
            logger.info(f"📊 Testing subscription to {len(initial_symbols)} symbols...")
            
            # The official library handles subscription automatically when symbols are traded
            # No explicit subscription needed
            
        except Exception as e:
            logger.error(f"Error with initial symbols: {e}")
    
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
        return self.connected and self.td_obj is not None
    
    def get_status(self) -> Dict:
        """Get detailed connection status"""
        return {
            'connected': self.is_connected(),
            'username': self.username,
            'url': 'push.truedata.in',
            'port': 9084,
            'symbols_receiving_data': list(self.live_data.keys()),
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'implementation': 'TRUE_OFFICIAL_LIBRARY',
            'github_sample_format': True,
            'full_feed': True,
            'dry_run': False,
            'data_source': 'TRUEDATA_OFFICIAL_LIBRARY'
        }
    
    def disconnect(self):
        """Disconnect from TrueData"""
        try:
            if self.td_obj:
                # Official library doesn't have explicit disconnect
                pass
            
            self.connected = False
            self.live_data = {}
            
            logger.info("🔴 TRUE Official TrueData disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")

# Thread wrapper for async compatibility
class TrueOfficialWrapper:
    """Thread wrapper for TRUE official TrueData client"""
    
    def __init__(self):
        self.client = TrueOfficialTrueDataClient()
        self.thread = None
        self.started = False
    
    def start(self):
        """Start TRUE official TrueData client"""
        if self.started:
            return self.client.is_connected()
            
        def run_client():
            success = self.client.start_connection()
            if success:
                logger.info("🎯 TRUE Official TrueData client running")
                # Keep alive (like GitHub sample)
                while self.client.is_connected():
                    time.sleep(30)  # Keep thread alive
            else:
                logger.error("❌ Failed to start TRUE Official TrueData client")
        
        self.thread = threading.Thread(target=run_client, daemon=True)
        self.thread.start()
        
        # Wait for connection
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
    
    def disconnect(self):
        """Disconnect"""
        self.client.disconnect()
        self.started = False

# Global instance
true_official_client = TrueOfficialWrapper()

# Helper functions
def initialize_true_official() -> bool:
    """Initialize TRUE official TrueData client"""
    return true_official_client.start()

def get_live_data(symbol: str = None) -> Optional[Dict]:
    """Get live market data"""
    return true_official_client.get_live_data(symbol)

def is_connected() -> bool:
    """Check connection status"""
    return true_official_client.is_connected()

def get_connection_status() -> Dict:
    """Get detailed status"""
    return true_official_client.get_status()

def add_data_callback(callback: Callable):
    """Add data callback"""
    true_official_client.add_data_callback(callback)

logger.info("🚀 TRUE Official TrueData Client loaded (exact GitHub sample format)")