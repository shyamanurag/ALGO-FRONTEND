"""
REAL TrueData WebSocket Client
Connects to actual TrueData push.truedata.in servers with Trial106 credentials
"""
import asyncio
import websockets
import json
import threading
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class TrueDataClient:
    def __init__(self):
        self.username = os.environ.get('TRUEDATA_USERNAME', 'Trial106')
        self.password = os.environ.get('TRUEDATA_PASSWORD', 'shyam106')
        self.url = os.environ.get('TRUEDATA_URL', 'push.truedata.in')
        self.port = int(os.environ.get('TRUEDATA_PORT', '8086'))
        
        self.websocket = None
        self.connected = False
        self.live_data = {}
        self.connection_thread = None
        self.running = False
        
        # Symbol mapping for major indices
        self.symbols = {
            'NIFTY': {'token': '26000', 'exchange': 'NSE'},
            'BANKNIFTY': {'token': '26009', 'exchange': 'NSE'}, 
            'FINNIFTY': {'token': '26037', 'exchange': 'NSE'}
        }
        
    def start_connection(self):
        """Start the WebSocket connection in a separate thread"""
        if self.running:
            return
            
        self.running = True
        self.connection_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.connection_thread.start()
        logger.info(f"🔄 Starting TrueData connection to {self.url}:{self.port}")
        
    def _run_async_loop(self):
        """Run the async event loop in the thread"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._connect_and_listen())
        except Exception as e:
            logger.error(f"TrueData async loop error: {e}")
        finally:
            self.connected = False
            
    async def _connect_and_listen(self):
        """Main connection and listening logic"""
        uri = f"ws://{self.url}:{self.port}"
        
        while self.running:
            try:
                logger.info(f"🔗 Attempting TrueData connection to {uri}")
                
                # Remove timeout parameter that's causing the issue
                async with websockets.connect(uri) as websocket:
                    self.websocket = websocket
                    self.connected = True
                    logger.info("✅ TrueData WebSocket connected successfully")
                    
                    # Send authentication
                    await self._authenticate()
                    
                    # Subscribe to symbols
                    await self._subscribe_to_symbols()
                    
                    # Listen for messages
                    await self._listen_for_messages()
                    
            except websockets.exceptions.ConnectionClosed:
                logger.warning("TrueData connection closed, attempting reconnect...")
                self.connected = False
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"TrueData connection error: {e}")
                self.connected = False
                await asyncio.sleep(10)
                
    async def _authenticate(self):
        """Send authentication message to TrueData"""
        try:
            auth_message = {
                "type": "login",
                "userid": self.username,
                "password": self.password
            }
            
            await self.websocket.send(json.dumps(auth_message))
            logger.info(f"📤 Authentication sent for user: {self.username}")
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            
    async def _subscribe_to_symbols(self):
        """Subscribe to NIFTY, BANKNIFTY, FINNIFTY"""
        try:
            for symbol, details in self.symbols.items():
                subscribe_message = {
                    "type": "subscribe",
                    "symbol": symbol,
                    "token": details['token'],
                    "exchange": details['exchange']
                }
                
                await self.websocket.send(json.dumps(subscribe_message))
                logger.info(f"📊 Subscribed to {symbol}")
                
        except Exception as e:
            logger.error(f"Subscription error: {e}")
            
    async def _listen_for_messages(self):
        """Listen for incoming market data messages"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._process_market_data(data)
                    
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {message}")
                    
        except Exception as e:
            logger.error(f"Message listening error: {e}")
            
    async def _process_market_data(self, data):
        """Process incoming market data"""
        try:
            # TrueData message format (adapt based on actual format)
            if 'symbol' in data and 'ltp' in data:
                symbol = data['symbol']
                
                self.live_data[symbol] = {
                    'symbol': symbol,
                    'ltp': float(data.get('ltp', 0)),
                    'change': float(data.get('change', 0)),
                    'change_percent': float(data.get('change_percent', 0)),
                    'volume': int(data.get('volume', 0)),
                    'high': float(data.get('high', 0)),
                    'low': float(data.get('low', 0)),
                    'open': float(data.get('open', 0)),
                    'timestamp': datetime.utcnow().isoformat(),
                    'data_source': 'TRUEDATA_LIVE',
                    'market_status': 'OPEN'
                }
                
                logger.info(f"📈 REAL DATA: {symbol} - LTP: {data.get('ltp')}, Volume: {data.get('volume')}")
                
        except Exception as e:
            logger.error(f"Data processing error: {e}")
            
    def get_symbol_data(self, symbol):
        """Get live data for a specific symbol"""
        return self.live_data.get(symbol)
        
    def get_all_data(self):
        """Get all live data"""
        return self.live_data.copy()
        
    def is_connected(self):
        """Check if connected to TrueData"""
        return self.connected
        
    def get_status(self):
        """Get connection status"""
        return {
            'connected': self.connected,
            'username': self.username,
            'url': f"{self.url}:{self.port}",
            'symbols_count': len(self.live_data),
            'symbols': list(self.live_data.keys()),
            'last_update': max([data.get('timestamp', '') for data in self.live_data.values()]) if self.live_data else None
        }
        
    def stop(self):
        """Stop the connection"""
        self.running = False
        if self.websocket:
            asyncio.create_task(self.websocket.close())

# Global instance
truedata_client = TrueDataClient()

def initialize_truedata():
    """Initialize TrueData connection"""
    try:
        truedata_client.start_connection()
        return True
    except Exception as e:
        logger.error(f"Failed to initialize TrueData: {e}")
        return False

def get_live_data(symbol=None):
    """Get live market data"""
    if symbol:
        return truedata_client.get_symbol_data(symbol)
    return truedata_client.get_all_data()

def is_connected():
    """Check if TrueData is connected"""
    return truedata_client.is_connected()

def get_connection_status():
    """Get detailed connection status"""
    return truedata_client.get_status()