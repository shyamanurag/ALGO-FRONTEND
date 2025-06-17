"""
CORRECT TrueData Integration using Official API
Based on official documentation: https://pypi.org/project/truedata/
"""
import threading
import logging
import time
from datetime import datetime
import os
from typing import Dict, Any, Optional

# Import official TrueData library
try:
    from truedata import TD_live
    print("✅ TrueData library imported successfully")
except ImportError as e:
    TD_live = None
    print(f"❌ TrueData library import failed: {e}")

logger = logging.getLogger(__name__)

class TrueDataClient:
    def __init__(self):
        self.login_id = os.environ.get('TRUEDATA_USERNAME', 'tdwsp697')
        self.password = os.environ.get('TRUEDATA_PASSWORD', 'shyam@697')
        
        self.td_obj = None
        self.connected = False
        self.live_data = {}
        self.connection_thread = None
        self.running = False
        
        # Symbols to subscribe (TrueData format)
        self.symbols = ['NIFTY 50', 'NIFTY BANK', 'NIFTY FIN SERVICE']
        
        # Initialize TrueData connection
        self._initialize_truedata()

    def _initialize_truedata(self):
        """Initialize TrueData using correct API"""
        try:
            if TD_live is None:
                logger.error("❌ TrueData library not available")
                return
                
            # Correct initialization as per documentation
            self.td_obj = TD_live(self.login_id, self.password)
            
            # Set up callback functions
            self._setup_callbacks()
            
            logger.info(f"✅ TrueData TD_live initialized for user: {self.login_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize TrueData: {e}")
            self.td_obj = None

    def _setup_callbacks(self):
        """Setup TrueData callback functions"""
        if not self.td_obj:
            return
            
        try:
            # Trade callback for tick data
            @self.td_obj.trade_callback
            def my_tick_data(tick_data):
                """Handle tick data from TrueData"""
                try:
                    symbol = tick_data.get('symbol', '')
                    
                    # Map TrueData symbols to our format
                    if 'NIFTY 50' in symbol or 'NIFTY' in symbol:
                        our_symbol = 'NIFTY'
                    elif 'NIFTY BANK' in symbol or 'BANKNIFTY' in symbol:
                        our_symbol = 'BANKNIFTY'
                    elif 'NIFTY FIN' in symbol or 'FINNIFTY' in symbol:
                        our_symbol = 'FINNIFTY'
                    else:
                        our_symbol = symbol
                    
                    # Update live data with tick information
                    self.live_data[our_symbol] = {
                        'ltp': tick_data.get('price', tick_data.get('ltp', 0)),
                        'volume': tick_data.get('volume', 0),
                        'timestamp': datetime.now().isoformat(),
                        'data_source': 'TRUEDATA_TICK',
                        'raw_data': tick_data
                    }
                    
                    logger.debug(f"📊 Tick data for {our_symbol}: {tick_data.get('price', 0)}")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing tick data: {e}")

            # Bid-Ask callback for spread data  
            @self.td_obj.bidask_callback
            def my_bidask_data(bidask_data):
                """Handle bid-ask data from TrueData"""
                try:
                    symbol = bidask_data.get('symbol', '')
                    
                    # Map symbol
                    if 'NIFTY 50' in symbol:
                        our_symbol = 'NIFTY'
                    elif 'NIFTY BANK' in symbol:
                        our_symbol = 'BANKNIFTY'
                    elif 'NIFTY FIN' in symbol:
                        our_symbol = 'FINNIFTY'
                    else:
                        our_symbol = symbol
                    
                    # Update with bid-ask data
                    if our_symbol in self.live_data:
                        self.live_data[our_symbol].update({
                            'bid': bidask_data.get('bid_price', 0),
                            'ask': bidask_data.get('ask_price', 0),
                            'bid_qty': bidask_data.get('bid_qty', 0),
                            'ask_qty': bidask_data.get('ask_qty', 0)
                        })
                    else:
                        self.live_data[our_symbol] = {
                            'bid': bidask_data.get('bid_price', 0),
                            'ask': bidask_data.get('ask_price', 0),
                            'bid_qty': bidask_data.get('bid_qty', 0),
                            'ask_qty': bidask_data.get('ask_qty', 0),
                            'timestamp': datetime.now().isoformat(),
                            'data_source': 'TRUEDATA_BIDASK'
                        }
                    
                    logger.debug(f"📈 Bid-Ask for {our_symbol}: {bidask_data.get('bid_price', 0)}-{bidask_data.get('ask_price', 0)}")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing bid-ask data: {e}")

            logger.info("✅ TrueData callbacks configured")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup TrueData callbacks: {e}")

    def start_connection(self):
        """Start TrueData connection using correct API"""
        if not self.td_obj:
            logger.error("❌ TrueData TD_live not initialized")
            return False
            
        if self.running:
            logger.warning("⚠️ TrueData connection already running")
            return True
            
        try:
            self.running = True
            
            # Start live data subscription using correct method
            logger.info(f"🔗 Starting TrueData live data for symbols: {self.symbols}")
            
            # Use correct method as per documentation
            self.td_obj.start_live_data(self.symbols)
            
            # Mark as connected
            self.connected = True
            logger.info("✅ TrueData live data started successfully!")
            
            # Start monitoring thread
            self.connection_thread = threading.Thread(target=self._monitor_connection, daemon=True)
            self.connection_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start TrueData live data: {e}")
            self.connected = False
            self.running = False
            return False

    def _monitor_connection(self):
        """Monitor TrueData connection"""
        while self.running:
            try:
                # Check if we're still getting data
                if self.live_data:
                    # Update connection status based on recent data
                    latest_timestamp = max([
                        datetime.fromisoformat(data.get('timestamp', '1970-01-01T00:00:00'))
                        for data in self.live_data.values()
                        if data.get('timestamp')
                    ], default=datetime.min)
                    
                    # If no data in last 60 seconds, mark as disconnected
                    if (datetime.now() - latest_timestamp).total_seconds() > 60:
                        logger.warning("⚠️ No TrueData updates in 60 seconds")
                        
                # Log status every 30 seconds
                logger.info(f"📊 TrueData Status: Connected={self.connected}, Symbols={len(self.live_data)}")
                for symbol, data in self.live_data.items():
                    ltp = data.get('ltp', 0)
                    if ltp > 0:
                        logger.info(f"   {symbol}: {ltp}")
                
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"❌ Error in TrueData monitoring: {e}")
                time.sleep(10)

    def stop_connection(self):
        """Stop TrueData connection using correct API"""
        try:
            self.running = False
            
            if self.td_obj and self.connected:
                # Stop live data using correct method
                self.td_obj.stop_live_data(self.symbols)
                
                # Disconnect
                self.td_obj.disconnect()
                
            self.connected = False
            
            if self.connection_thread:
                self.connection_thread.join(timeout=5)
                
            logger.info("🔴 TrueData connection stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping TrueData: {e}")

    def get_all_data(self):
        """Get all live market data"""
        return self.live_data.copy()

    def get_symbol_data(self, symbol):
        """Get data for specific symbol"""
        return self.live_data.get(symbol)

    def is_connected(self):
        """Check if connected and receiving data"""
        if not self.connected:
            return False
            
        # Check if we have recent data
        if not self.live_data:
            return False
            
        # Check for recent updates (within last 5 minutes)
        try:
            latest_timestamp = max([
                datetime.fromisoformat(data.get('timestamp', '1970-01-01T00:00:00'))
                for data in self.live_data.values()
                if data.get('timestamp')
            ], default=datetime.min)
            
            return (datetime.now() - latest_timestamp).total_seconds() < 300
            
        except:
            return self.connected

    def get_status(self):
        """Get detailed connection status"""
        return {
            'connected': self.connected,
            'login_id': self.login_id,
            'symbols_subscribed': self.symbols,
            'symbols_receiving_data': list(self.live_data.keys()),
            'data_count': len(self.live_data),
            'last_update': max([
                data.get('timestamp', '') for data in self.live_data.values()
            ], default='Never') if self.live_data else 'Never',
            'data_source': 'TRUEDATA_OFFICIAL_API'
        }

# Global instance
truedata_client = TrueDataClient()

# Helper functions for backward compatibility
def initialize_truedata():
    """Initialize and start TrueData connection"""
    return truedata_client.start_connection()

def get_live_data(symbol=None):
    """Get live data"""
    if symbol:
        return truedata_client.get_symbol_data(symbol)
    return truedata_client.get_all_data()

def is_connected():
    """Check connection status"""
    return truedata_client.is_connected()

def get_connection_status():
    """Get detailed status"""
    return truedata_client.get_status()

# Auto-start connection
logger.info("🚀 TrueData Official API Client initialized")
print("🚀 TrueData Official API Client ready to start")