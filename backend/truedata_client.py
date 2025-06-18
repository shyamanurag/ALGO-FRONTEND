"""
Real TrueData Integration using TrueData-WS Library (More Stable)
This uses the truedata-ws library which has better connection handling
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
        
        self.td_obj = None
        self.connected = False
        self.live_data = {}
        self.connection_thread = None
        self.running = False
        self.symbols = ['NIFTY-I', 'BANKNIFTY-I', 'FINNIFTY-I']  # Index format for TrueData
        
        logger.info(f"🔗 Real TrueData-WS Client initialized for {self.login_id}")

    def start_connection(self):
        """Start REAL TrueData connection using truedata-ws library"""
        global truedata_connection_status
        
        try:
            # Import the truedata-ws library
            from truedata_ws.websocket.TD import TD
            
            logger.info(f"🚀 Connecting to TrueData-WS with credentials: {self.login_id}")
            
            # Initialize TrueData-WS connection
            self.td_obj = TD(self.login_id, self.password)
            
            # Give it a moment to establish connection
            time.sleep(3)
            
            # Start live data streaming for symbols
            logger.info(f"📊 Starting live data for: {self.symbols}")
            req_ids = self.td_obj.start_live_data(self.symbols)
            
            if req_ids:
                logger.info(f"✅ TrueData-WS live data started with request IDs: {req_ids}")
                
                self.connected = True
                truedata_connection_status['connected'] = True
                truedata_connection_status['login_id'] = self.login_id
                truedata_connection_status['last_update'] = datetime.now().isoformat()
                truedata_connection_status['error'] = None
                
                # Start data monitoring thread
                self._start_data_monitoring(req_ids)
                
                return True
            else:
                raise Exception("Failed to start live data streaming")
                
        except Exception as e:
            error_msg = f"TrueData-WS connection failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            truedata_connection_status['connected'] = False
            truedata_connection_status['error'] = error_msg
            truedata_connection_status['last_update'] = datetime.now().isoformat()
            
            return False

    def _start_data_monitoring(self, req_ids):
        """Start monitoring live data in a separate thread"""
        if self.running:
            logger.warning("⚠️ Data monitoring already running")
            return
            
        try:
            self.running = True
            self.connection_thread = threading.Thread(
                target=self._data_monitoring_worker, 
                args=(req_ids,), 
                daemon=True
            )
            self.connection_thread.start()
            
            logger.info("🔴 LIVE: TrueData-WS data monitoring started")
            
        except Exception as e:
            logger.error(f"❌ Failed to start data monitoring: {e}")

    def _data_monitoring_worker(self, req_ids):
        """Monitor live data from TrueData-WS"""
        global live_market_data
        
        logger.info("🔗 Starting TrueData-WS data monitoring...")
        
        while self.running and self.connected:
            try:
                current_time = datetime.now()
                updated_any = False
                
                for req_id in req_ids:
                    try:
                        # Get live data for this request ID
                        live_obj = self.td_obj.live_data.get(req_id)
                        
                        if live_obj and hasattr(live_obj, 'ltp') and live_obj.ltp:
                            # Extract symbol name (remove -I suffix for internal use)
                            symbol_name = live_obj.symbol.replace('-I', '') if hasattr(live_obj, 'symbol') else f'SYMBOL_{req_id}'
                            
                            # Create market data object
                            market_data = {
                                'ltp': float(live_obj.ltp),
                                'symbol': symbol_name,
                                'timestamp': current_time.isoformat(),
                                'data_source': 'REAL_TRUEDATA_WS',
                                'status': 'LIVE',
                                'req_id': req_id
                            }
                            
                            # Add additional data if available
                            if hasattr(live_obj, 'bid') and live_obj.bid:
                                market_data['bid'] = float(live_obj.bid)
                            if hasattr(live_obj, 'ask') and live_obj.ask:
                                market_data['ask'] = float(live_obj.ask)
                            if hasattr(live_obj, 'volume') and live_obj.volume:
                                market_data['volume'] = int(live_obj.volume)
                            if hasattr(live_obj, 'open') and live_obj.open:
                                market_data['open'] = float(live_obj.open)
                            if hasattr(live_obj, 'high') and live_obj.high:
                                market_data['high'] = float(live_obj.high)
                            if hasattr(live_obj, 'low') and live_obj.low:
                                market_data['low'] = float(live_obj.low)
                            
                            # Calculate change percent if open is available
                            if 'open' in market_data and market_data['open'] > 0:
                                change = market_data['ltp'] - market_data['open']
                                market_data['change_percent'] = round((change / market_data['open']) * 100, 2)
                            
                            # Store in global data
                            live_market_data[symbol_name] = market_data
                            self.live_data[symbol_name] = market_data
                            updated_any = True
                            
                    except Exception as e:
                        logger.debug(f"Error processing req_id {req_id}: {e}")
                
                if updated_any:
                    # Update connection status
                    truedata_connection_status['last_update'] = current_time.isoformat()
                    
                    # Log status every 30 seconds
                    if int(time.time()) % 30 == 0:
                        prices_str = ", ".join([f"{sym}={data['ltp']:.2f}" for sym, data in live_market_data.items()])
                        logger.info(f"📊 REAL LIVE DATA (TrueData-WS): {prices_str}")
                
                # Check data every 2 seconds
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Error in TrueData-WS monitoring: {e}")
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
            'data_source': 'REAL_TRUEDATA_WS',
            'symbols_receiving_data': list(self.live_data.keys()),
            'data_count': len(self.live_data),
            'last_update': truedata_connection_status.get('last_update', 'Never'),
            'status': 'CONNECTED' if self.connected else 'DISCONNECTED',
            'library_status': 'OFFICIAL_TRUEDATA_WS_LIBRARY',
            'error': truedata_connection_status.get('error')
        }

    def stop_connection(self):
        """Stop data feed"""
        global truedata_connection_status
        
        try:
            self.running = False
            self.connected = False
            
            if self.td_obj:
                # Stop live data streaming
                self.td_obj.stop_live_data()
            
            truedata_connection_status['connected'] = False
            truedata_connection_status['last_update'] = datetime.now().isoformat()
            
            if self.connection_thread:
                self.connection_thread.join(timeout=5)
                
            logger.info("🔴 TrueData-WS connection stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping TrueData-WS connection: {e}")

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

logger.info("🚀 TrueData-WS Client ready - Using OFFICIAL TrueData-WS Library")
print("✅ TrueData-WS implementation loaded successfully")