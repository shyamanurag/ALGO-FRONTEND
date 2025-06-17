"""
TrueData Native WebSocket Client
Implements the correct TrueData WebSocket protocol as documented
"""
import asyncio
import websockets
import json
import threading
import logging
from datetime import datetime
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TrueDataWebSocketClient:
    def __init__(self):
        self.username = os.environ.get('TRUEDATA_USERNAME', 'tdwsp697')
        self.password = os.environ.get('TRUEDATA_PASSWORD', 'shyam@697')
        self.url = os.environ.get('TRUEDATA_URL', 'push.truedata.in')
        self.port = int(os.environ.get('TRUEDATA_PORT', '8084'))
        
        # WebSocket connection
        self.websocket = None
        self.connected = False
        self.live_data = {}
        self.connection_thread = None
        self.running = False
        
        # Symbol mapping (TrueData symbol IDs)
        self.symbols = {
            'NIFTY 50': {'id': '26000', 'our_name': 'NIFTY'},
            'NIFTY BANK': {'id': '26009', 'our_name': 'BANKNIFTY'},
            'NIFTY FIN SERVICE': {'id': '26037', 'our_name': 'FINNIFTY'}
        }
        
        logger.info(f"🔗 TrueData WebSocket Client initialized for {self.username}")

    def start_connection(self):
        """Start TrueData WebSocket connection"""
        if self.running:
            logger.warning("⚠️ TrueData WebSocket already running")
            return True
            
        try:
            self.running = True
            self.connection_thread = threading.Thread(target=self._run_async_connection, daemon=True)
            self.connection_thread.start()
            
            logger.info("🔗 Starting TrueData WebSocket connection thread")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start TrueData WebSocket: {e}")
            return False

    def _run_async_connection(self):
        """Run async WebSocket connection in thread"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the connection
            loop.run_until_complete(self._websocket_connection())
            
        except Exception as e:
            logger.error(f"❌ Error in WebSocket thread: {e}")
        finally:
            try:
                loop.close()
            except:
                pass

    async def _websocket_connection(self):
        """Main WebSocket connection logic"""
        while self.running:
            try:
                # Build WebSocket URL with authentication
                ws_url = f"wss://{self.url}:{self.port}?user={self.username}&password={self.password}"
                
                logger.info(f"🔗 Connecting to TrueData WebSocket: {ws_url}")
                
                # Connect to WebSocket
                async with websockets.connect(
                    ws_url,
                    ping_interval=30,
                    ping_timeout=10,
                    close_timeout=10
                ) as websocket:
                    self.websocket = websocket
                    self.connected = True
                    
                    logger.info("✅ TrueData WebSocket connected successfully!")
                    
                    # Subscribe to symbols
                    await self._subscribe_symbols()
                    
                    # Listen for messages
                    async for message in websocket:
                        try:
                            await self._handle_message(message)
                        except Exception as e:
                            logger.error(f"❌ Error handling message: {e}")
                            
            except websockets.exceptions.ConnectionClosed:
                logger.warning("⚠️ TrueData WebSocket connection closed, reconnecting...")
                self.connected = False
                
            except Exception as e:
                logger.error(f"❌ TrueData WebSocket error: {e}")
                self.connected = False
                
            # Reconnection delay
            if self.running:
                logger.info("⏰ Reconnecting in 10 seconds...")
                await asyncio.sleep(10)

    async def _subscribe_symbols(self):
        """Subscribe to required symbols"""
        try:
            if not self.websocket:
                return
                
            # Subscribe to symbols using TrueData protocol
            symbol_ids = [info['id'] for info in self.symbols.values()]
            
            subscribe_message = {
                "action": "subscribe",
                "symbols": symbol_ids
            }
            
            await self.websocket.send(json.dumps(subscribe_message))
            logger.info(f"📊 Subscribed to symbols: {symbol_ids}")
            
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to symbols: {e}")

    async def _handle_message(self, message):
        """Handle incoming WebSocket messages"""
        try:
            # Parse JSON message
            data = json.loads(message)
            
            # Handle different message types
            if 'message' in data:
                await self._handle_system_message(data['message'])
                
            if 'trade' in data:
                await self._handle_trade_data(data['trade'])
                
            if 'bidask' in data:
                await self._handle_bidask_data(data['bidask'])
                
            if 'min' in data:
                await self._handle_bar_data(data['min'])
                
        except json.JSONDecodeError:
            logger.error(f"❌ Invalid JSON message: {message}")
        except Exception as e:
            logger.error(f"❌ Error parsing message: {e}")

    async def _handle_system_message(self, message_data):
        """Handle system messages"""
        try:
            message_text = message_data.get('message', '')
            
            if message_text == "HeartBeat":
                logger.debug("💓 TrueData heartbeat received")
                
            elif message_text == "TrueData Real Time Data Service":
                logger.info("✅ TrueData service connected")
                
            elif "symbols added" in message_text:
                logger.info(f"📊 {message_text}")
                
            elif "symbols removed" in message_text:
                logger.info(f"📊 {message_text}")
                
            else:
                logger.info(f"📨 TrueData message: {message_text}")
                
        except Exception as e:
            logger.error(f"❌ Error handling system message: {e}")

    async def _handle_trade_data(self, trade_data):
        """Handle trade data: [symbol_id, timestamp, ltp, volume, atp, oi, ttq, special_tag, tick_seq]"""
        try:
            if len(trade_data) < 9:
                return
                
            symbol_id, timestamp, ltp, volume, atp, oi, ttq, special_tag, tick_seq = trade_data
            
            # Find our symbol name
            our_symbol = None
            for symbol_name, symbol_info in self.symbols.items():
                if symbol_info['id'] == str(symbol_id):
                    our_symbol = symbol_info['our_name']
                    break
                    
            if not our_symbol:
                return
                
            # Update live data
            self.live_data[our_symbol] = {
                'ltp': float(ltp),
                'volume': int(volume),
                'atp': float(atp) if atp else 0.0,  # Average Trade Price
                'oi': int(oi) if oi else 0,  # Open Interest
                'timestamp': datetime.now().isoformat(),
                'data_source': 'TRUEDATA_WEBSOCKET',
                'symbol': our_symbol,
                'raw_data': {
                    'symbol_id': symbol_id,
                    'tick_timestamp': timestamp,
                    'ttq': ttq,
                    'special_tag': special_tag,
                    'tick_seq': tick_seq
                }
            }
            
            logger.debug(f"📊 {our_symbol}: ₹{ltp} (Vol: {volume:,})")
            
        except Exception as e:
            logger.error(f"❌ Error handling trade data: {e}")

    async def _handle_bidask_data(self, bidask_data):
        """Handle bid-ask data"""
        try:
            # Update existing data with bid-ask information
            symbol_id = bidask_data.get('symbol_id')
            
            # Find our symbol
            our_symbol = None
            for symbol_name, symbol_info in self.symbols.items():
                if symbol_info['id'] == str(symbol_id):
                    our_symbol = symbol_info['our_name']
                    break
                    
            if our_symbol and our_symbol in self.live_data:
                self.live_data[our_symbol].update({
                    'bid': float(bidask_data.get('bid', 0)),
                    'bid_qty': int(bidask_data.get('bid_qty', 0)),
                    'ask': float(bidask_data.get('ask', 0)),
                    'ask_qty': int(bidask_data.get('ask_qty', 0))
                })
                
        except Exception as e:
            logger.error(f"❌ Error handling bid-ask data: {e}")

    async def _handle_bar_data(self, bar_data):
        """Handle bar/OHLC data"""
        try:
            # Extract OHLC data
            symbol_id = bar_data.get('symbol_id')
            
            # Find our symbol
            our_symbol = None
            for symbol_name, symbol_info in self.symbols.items():
                if symbol_info['id'] == str(symbol_id):
                    our_symbol = symbol_info['our_name']
                    break
                    
            if our_symbol and our_symbol in self.live_data:
                self.live_data[our_symbol].update({
                    'open': float(bar_data.get('o', 0)),
                    'high': float(bar_data.get('h', 0)),
                    'low': float(bar_data.get('l', 0)),
                    'close': float(bar_data.get('c', 0)),
                    'bar_volume': int(bar_data.get('v', 0)),
                    'bar_oi': int(bar_data.get('oi', 0))
                })
                
        except Exception as e:
            logger.error(f"❌ Error handling bar data: {e}")

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
            'username': self.username,
            'url': f"{self.url}:{self.port}",
            'symbols_subscribed': list(self.symbols.keys()),
            'symbols_receiving_data': list(self.live_data.keys()),
            'data_count': len(self.live_data),
            'last_update': max([
                data.get('timestamp', '') for data in self.live_data.values()
            ], default='Never') if self.live_data else 'Never',
            'data_source': 'TRUEDATA_WEBSOCKET_NATIVE',
            'protocol': 'WebSocket with proper TrueData format'
        }

    def stop_connection(self):
        """Stop WebSocket connection"""
        try:
            self.running = False
            self.connected = False
            
            if self.websocket:
                asyncio.create_task(self.websocket.close())
                
            if self.connection_thread:
                self.connection_thread.join(timeout=5)
                
            logger.info("🔴 TrueData WebSocket connection stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping WebSocket: {e}")

# Global instance
truedata_client = TrueDataWebSocketClient()

# Helper functions for backward compatibility
def initialize_truedata():
    """Initialize TrueData WebSocket connection"""
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

# Auto-start connection
logger.info("🚀 TrueData Native WebSocket Client ready")
print("✅ TrueData Native WebSocket implementation loaded")