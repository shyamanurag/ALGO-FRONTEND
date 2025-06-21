"""
TrueData Client using the official TD_live class
Based on the working implementation pattern provided
"""

import logging
import time
from typing import Dict, Optional, Callable, List, Any
import threading
from datetime import datetime

# Import the official TrueData library
from truedata import TD_live

# Import settings from the application's config module
from src.config import settings

# --- Global Variables for Singleton State ---
live_market_data: Dict[str, Dict[str, Any]] = {}
truedata_connection_status: Dict[str, Any] = {
    "connected": False,
    "last_update": None,
    "error_message": None,
    "active_symbols": []
}
# --- End Global Variables ---

# --- Logger Setup ---
logger = logging.getLogger(__name__)
if not logger.hasHandlers() and not logging.getLogger().hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# --- End Logger Setup ---


class TrueDataSingletonClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TrueDataSingletonClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.td_obj: Optional[TD_live] = None
        self.is_connected: bool = False
        self.connection_thread: Optional[threading.Thread] = None
        self.should_stop: bool = False
        
        # Configuration from settings
        self.username = getattr(settings, 'TRUEDATA_USERNAME', '')
        self.password = getattr(settings, 'TRUEDATA_PASSWORD', '')
        self.url = getattr(settings, 'TRUEDATA_URL', 'push.truedata.in')
        self.port = int(getattr(settings, 'TRUEDATA_PORT', 8084))
        
        logger.info(f"TrueData client initialized with URL: {self.url}:{self.port}")
    
    def connect(self) -> bool:
        """Connect to TrueData using the official TD_live class"""
        try:
            if self.is_connected and self.td_obj:
                logger.info("TrueData already connected")
                return True
                
            logger.info(f"Connecting to TrueData at {self.url}:{self.port}")
            
            # Initialize TD_live object
            self.td_obj = TD_live(
                username=self.username,
                password=self.password,
                live_port=self.port,
                log_level=logging.WARNING,
                url=self.url,
                compression=False
            )
            
            # Set up callbacks
            self._setup_callbacks()
            
            # Start with default symbols
            default_symbols = ['NIFTY', 'BANKNIFTY']
            if hasattr(settings, 'TRUEDATA_DEFAULT_SYMBOLS'):
                try:
                    import json
                    default_symbols = json.loads(settings.TRUEDATA_DEFAULT_SYMBOLS.replace("'", '"'))
                except:
                    default_symbols = ['NIFTY', 'BANKNIFTY']
            
            # Start live data for default symbols
            req_ids = self.td_obj.start_live_data(default_symbols)
            time.sleep(1)  # Give it a moment to establish connection
            
            self.is_connected = True
            truedata_connection_status["connected"] = True
            truedata_connection_status["last_update"] = datetime.utcnow()
            truedata_connection_status["active_symbols"] = default_symbols
            truedata_connection_status["error_message"] = None
            
            logger.info(f"TrueData connected successfully. Request IDs: {req_ids}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to TrueData: {e}")
            self.is_connected = False
            truedata_connection_status["connected"] = False
            truedata_connection_status["error_message"] = str(e)
            return False
    
    def _setup_callbacks(self):
        """Set up TrueData callbacks for receiving data"""
        if not self.td_obj:
            return
            
        @self.td_obj.trade_callback
        def handle_tick_data(tick_data):
            """Handle incoming tick data"""
            try:
                symbol = tick_data.get('symbol', 'UNKNOWN')
                live_market_data[symbol] = {
                    'symbol': symbol,
                    'price': tick_data.get('price', 0),
                    'volume': tick_data.get('volume', 0),
                    'timestamp': datetime.utcnow().isoformat(),
                    'raw_data': tick_data
                }
                truedata_connection_status["last_update"] = datetime.utcnow()
                logger.debug(f"Tick data received for {symbol}: {tick_data}")
            except Exception as e:
                logger.error(f"Error processing tick data: {e}")
        
        @self.td_obj.greek_callback  
        def handle_greek_data(greek_data):
            """Handle incoming Greek data for options"""
            try:
                symbol = greek_data.get('symbol', 'UNKNOWN')
                if symbol in live_market_data:
                    live_market_data[symbol]['greeks'] = greek_data
                else:
                    live_market_data[symbol] = {
                        'symbol': symbol,
                        'greeks': greek_data,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                logger.debug(f"Greek data received for {symbol}: {greek_data}")
            except Exception as e:
                logger.error(f"Error processing Greek data: {e}")
    
    def disconnect(self) -> bool:
        """Disconnect from TrueData"""
        try:
            if self.td_obj:
                # Stop the TD_live object
                self.should_stop = True
                self.is_connected = False
                self.td_obj = None
                
                truedata_connection_status["connected"] = False
                truedata_connection_status["last_update"] = datetime.utcnow()
                truedata_connection_status["error_message"] = None
                
                logger.info("TrueData disconnected successfully")
                return True
        except Exception as e:
            logger.error(f"Error disconnecting from TrueData: {e}")
            return False
    
    def subscribe_symbol(self, symbol: str) -> bool:
        """Subscribe to a new symbol"""
        try:
            if not self.is_connected or not self.td_obj:
                logger.warning("TrueData not connected. Cannot subscribe to symbol.")
                return False
                
            req_ids = self.td_obj.start_live_data([symbol])
            truedata_connection_status["active_symbols"].append(symbol)
            logger.info(f"Subscribed to symbol {symbol}. Request ID: {req_ids}")
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing to symbol {symbol}: {e}")
            return False
    
    def get_live_data(self) -> Dict[str, Any]:
        """Get current live market data"""
        return live_market_data.copy()
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status"""
        return truedata_connection_status.copy()


# --- Singleton Instance ---
client_instance = TrueDataSingletonClient()

# --- Public Functions (API) ---
def connect_truedata() -> bool:
    """Connect to TrueData - Public API function"""
    return client_instance.connect()

def disconnect_truedata() -> bool:
    """Disconnect from TrueData - Public API function"""
    return client_instance.disconnect()

def subscribe_to_symbol(symbol: str) -> bool:
    """Subscribe to a symbol - Public API function"""
    return client_instance.subscribe_symbol(symbol)

def get_live_market_data() -> Dict[str, Any]:
    """Get live market data - Public API function"""
    return client_instance.get_live_data()

def get_truedata_status() -> Dict[str, Any]:
    """Get TrueData connection status - Public API function"""
    return client_instance.get_connection_status()

# --- Backwards Compatibility ---
def is_connected() -> bool:
    """Check if TrueData is connected"""
    return client_instance.is_connected

def get_subscription_status() -> Dict[str, Any]:
    """Get subscription status"""
    return get_truedata_status()