"""
Real TrueData Integration using Official TrueData Library
This replaces the custom implementation with proper TrueData API integration
"""
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

# Global data storage
live_market_data = {}
truedata_connection_status = {
    'connected': False,
    'login_id': '',
    'last_update': None,
    'error': None
}

class RealTrueDataClient:
    def __init__(self):
        self.login_id = os.environ.get('TRUEDATA_USERNAME', 'tdwsp697')
        self.password = os.environ.get('TRUEDATA_PASSWORD', 'shyam@697')
        
        self.td_live = None
        self.connected = False
        self.live_data = {}
        self.connection_thread = None
        self.running = False
        
        logger.info(f"🔗 Real TrueData Client initialized for {self.login_id}")

    def start_connection(self):
        """Start REAL TrueData connection using official library"""
        global truedata_connection_status
        
        try:
            # Import the official TrueData library
            from truedata import TD_live
            
            logger.info(f"🚀 Connecting to TrueData with credentials: {self.login_id}")
            
            # Initialize TrueData connection
            self.td_live = TD_live(self.login_id, self.password)
            
            # Test connection by getting some data
            test_data = self.td_live.get_ltp(['NIFTY'])
            
            if test_data and 'NIFTY' in test_data:
                self.connected = True
                truedata_connection_status['connected'] = True
                truedata_connection_status['login_id'] = self.login_id
                truedata_connection_status['last_update'] = datetime.now().isoformat()
                truedata_connection_status['error'] = None
                
                logger.info("✅ REAL TrueData connection established successfully!")
                logger.info(f"📊 Test Data Received: {test_data}")
                
                # Start real-time data streaming
                self._start_live_streaming()
                
                return True
            else:
                raise Exception("Failed to get test data from TrueData")
                
        except Exception as e:
            error_msg = f"TrueData connection failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            truedata_connection_status['connected'] = False
            truedata_connection_status['error'] = error_msg
            truedata_connection_status['last_update'] = datetime.now().isoformat()
            
            return False

    def _start_live_streaming(self):
        """Start live data streaming thread"""
        if self.running:
            logger.warning("⚠️ Live streaming already running")
            return
            
        try:
            self.running = True
            self.connection_thread = threading.Thread(target=self._live_data_worker, daemon=True)
            self.connection_thread.start()
            
            logger.info("🔴 LIVE: Real-time TrueData streaming started")
            
        except Exception as e:
            logger.error(f"❌ Failed to start live streaming: {e}")

    def _live_data_worker(self):
        """Real-time data worker using TrueData streaming"""
        global live_market_data
        
        logger.info("🔗 Starting REAL TrueData live streaming...")
        
        # Symbols to track
        symbols = ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
        
        while self.running and self.connected:
            try:
                # Get live data from TrueData
                live_data = self.td_live.get_ltp(symbols)
                
                if live_data:
                    current_time = datetime.now()
                    
                    for symbol, price in live_data.items():
                        if price and price > 0:
                            # Get additional market data
                            ohlc_data = self.td_live.get_ohlc([symbol])
                            
                            market_data = {
                                'ltp': float(price),
                                'symbol': symbol,
                                'timestamp': current_time.isoformat(),
                                'data_source': 'REAL_TRUEDATA',
                                'status': 'LIVE'
                            }
                            
                            # Add OHLC data if available
                            if ohlc_data and symbol in ohlc_data:
                                ohlc = ohlc_data[symbol]
                                market_data.update({
                                    'open': float(ohlc.get('open', price)),
                                    'high': float(ohlc.get('high', price)),
                                    'low': float(ohlc.get('low', price)),
                                    'close': float(ohlc.get('close', price)),
                                    'volume': int(ohlc.get('volume', 0))
                                })
                            
                            # Calculate change percent
                            if 'open' in market_data and market_data['open'] > 0:
                                change = price - market_data['open']
                                market_data['change_percent'] = round((change / market_data['open']) * 100, 2)
                            
                            # Store in global data
                            live_market_data[symbol] = market_data
                            self.live_data[symbol] = market_data
                    
                    # Update connection status
                    truedata_connection_status['last_update'] = current_time.isoformat()
                    
                    # Log status every 30 seconds
                    if int(time.time()) % 30 == 0:
                        prices_str = ", ".join([f"{sym}={data['ltp']:.2f}" for sym, data in live_market_data.items()])
                        logger.info(f"📊 REAL LIVE DATA: {prices_str}")
                
                # Update every 2 seconds for real-time data
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Error in live data streaming: {e}")
                truedata_connection_status['error'] = str(e)
                time.sleep(10)  # Wait before retrying

    def get_all_data(self):
        """Get all live market data"""
        return self.live_data.copy()

    def get_symbol_data(self, symbol):
        """Get data for specific symbol"""
        return self.live_data.get(symbol)

    def is_connected(self):
        """Check if connected and receiving data"""
        return self.connected and len(self.live_data) > 0

    def get_status(self):
        """Get detailed connection status"""
        return {
            'connected': self.connected,
            'login_id': self.login_id,
            'data_source': 'REAL_TRUEDATA_OFFICIAL',
            'symbols_receiving_data': list(self.live_data.keys()),
            'data_count': len(self.live_data),
            'last_update': truedata_connection_status.get('last_update', 'Never'),
            'status': 'CONNECTED' if self.connected else 'DISCONNECTED',
            'library_status': 'OFFICIAL_TRUEDATA_LIBRARY',
            'error': truedata_connection_status.get('error')
        }

    def stop_connection(self):
        """Stop data feed"""
        global truedata_connection_status
        
        try:
            self.running = False
            self.connected = False
            
            truedata_connection_status['connected'] = False
            truedata_connection_status['last_update'] = datetime.now().isoformat()
            
            if self.connection_thread:
                self.connection_thread.join(timeout=5)
                
            logger.info("🔴 REAL TrueData connection stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping TrueData connection: {e}")

# Global instance
truedata_client = RealTrueDataClient()

# Helper functions for backward compatibility
def initialize_truedata():
    """Initialize REAL TrueData connection"""
    return truedata_client.start_connection()

def get_live_data(symbol=None):
    """Get live market data"""
    if symbol:
        return truedata_client.get_symbol_data(symbol)
    return truedata_client.get_all_data()

def is_connected():
    """Check connection status"""
    return truedata_client.is_connected()

def get_connection_status():
    """Get detailed status"""
    return truedata_client.get_status()

def test_market_data():
    """Test market data functionality"""
    return truedata_client.is_connected() and len(truedata_client.get_all_data()) > 0

logger.info("🚀 REAL TrueData Client ready - Using OFFICIAL TrueData Library")
print("✅ REAL TrueData implementation loaded successfully")