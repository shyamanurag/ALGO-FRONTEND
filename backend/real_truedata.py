"""
REAL TrueData WebSocket Integration
Connects to actual TrueData push.truedata.in servers
"""
import asyncio
import websocket
import threading
import json
import time
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# TrueData Configuration
TRUEDATA_USERNAME = os.environ.get('TRUEDATA_USERNAME', '')
TRUEDATA_PASSWORD = os.environ.get('TRUEDATA_PASSWORD', '')
TRUEDATA_PORT = int(os.environ.get('TRUEDATA_PORT', '8086'))
TRUEDATA_URL = os.environ.get('TRUEDATA_URL', 'push.truedata.in')

# Global state
truedata_ws = None
truedata_thread = None
real_market_data = {}
truedata_connected = False

def start_truedata_websocket():
    """Start REAL TrueData WebSocket connection"""
    global truedata_ws, truedata_connected, real_market_data
    
    try:
        # Real TrueData WebSocket URL
        ws_url = f"ws://{TRUEDATA_URL}:{TRUEDATA_PORT}"
        
        def on_message(ws, message):
            try:
                # Parse TrueData message format
                data = json.loads(message)
                
                # Handle different message types
                if data.get('type') == 'tick':
                    symbol = data.get('instrument_token', '')
                    
                    # Map instrument token to symbol names
                    symbol_map = {
                        '256265': 'NIFTY',
                        '260105': 'BANKNIFTY', 
                        '257801': 'FINNIFTY'
                    }
                    
                    symbol_name = symbol_map.get(str(symbol), symbol)
                    
                    if symbol_name:
                        real_market_data[symbol_name] = {
                            'symbol': symbol_name,
                            'ltp': float(data.get('last_price', 0)),
                            'volume': int(data.get('volume', 0)),
                            'change': float(data.get('change', 0)),
                            'change_percent': float(data.get('change_percent', 0)),
                            'high': float(data.get('ohlc', {}).get('high', 0)),
                            'low': float(data.get('ohlc', {}).get('low', 0)),
                            'open': float(data.get('ohlc', {}).get('open', 0)),
                            'bid': float(data.get('depth', {}).get('buy', [{}])[0].get('price', 0)),
                            'ask': float(data.get('depth', {}).get('sell', [{}])[0].get('price', 0)),
                            'timestamp': datetime.utcnow().isoformat(),
                            'data_source': 'TRUEDATA_LIVE',
                            'market_status': 'OPEN'
                        }
                        
                        logger.info(f"📈 REAL TRUEDATA: {symbol_name} - LTP: {data.get('last_price')}, Vol: {data.get('volume')}")
                        
            except Exception as e:
                logger.error(f"Error parsing TrueData message: {e}")
        
        def on_error(ws, error):
            logger.error(f"TrueData WebSocket error: {error}")
            global truedata_connected
            truedata_connected = False
        
        def on_close(ws, close_status_code, close_msg):
            logger.warning("TrueData WebSocket connection closed")
            global truedata_connected
            truedata_connected = False
        
        def on_open(ws):
            logger.info("✅ REAL TrueData WebSocket connected")
            global truedata_connected
            truedata_connected = True
            
            # Send authentication message
            auth_msg = {
                "a": "authorization",
                "user": TRUEDATA_USERNAME,
                "token": TRUEDATA_PASSWORD
            }
            ws.send(json.dumps(auth_msg))
            
            # Subscribe to NIFTY, BANKNIFTY, FINNIFTY
            subscribe_msg = {
                "a": "subscribe",
                "v": [256265, 260105, 257801]  # NIFTY, BANKNIFTY, FINNIFTY tokens
            }
            ws.send(json.dumps(subscribe_msg))
            logger.info("📊 Subscribed to NIFTY, BANKNIFTY, FINNIFTY")
        
        # Create WebSocket connection
        truedata_ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        # Run WebSocket (blocking)
        logger.info(f"🔄 Connecting to REAL TrueData: {ws_url}")
        truedata_ws.run_forever()
        
    except Exception as e:
        logger.error(f"TrueData WebSocket critical error: {e}")
        truedata_connected = False

def initialize_truedata():
    """Initialize REAL TrueData connection"""
    global truedata_thread
    
    try:
        if not TRUEDATA_USERNAME or not TRUEDATA_PASSWORD:
            logger.error("❌ TrueData credentials missing - cannot connect to REAL data")
            return False
            
        # Start TrueData WebSocket in separate thread
        truedata_thread = threading.Thread(target=start_truedata_websocket, daemon=True)
        truedata_thread.start()
        
        logger.info(f"🚀 REAL TrueData connection started for user: {TRUEDATA_USERNAME}")
        return True
        
    except Exception as e:
        logger.error(f"TrueData initialization error: {e}")
        return False

def get_real_market_data(symbol):
    """Get REAL market data for symbol"""
    global real_market_data, truedata_connected
    
    if truedata_connected and symbol in real_market_data:
        return real_market_data[symbol]
    
    return None

def is_truedata_connected():
    """Check if TrueData is connected"""
    return truedata_connected

def get_connection_status():
    """Get detailed connection status"""
    return {
        "connected": truedata_connected,
        "username": TRUEDATA_USERNAME,
        "url": f"{TRUEDATA_URL}:{TRUEDATA_PORT}",
        "symbols_count": len(real_market_data),
        "symbols": list(real_market_data.keys())
    }