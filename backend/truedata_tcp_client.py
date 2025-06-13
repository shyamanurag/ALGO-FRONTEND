"""
TrueData TCP Client - Alternative approach
Uses TCP socket instead of WebSocket for TrueData connection
"""

import socket
import json
import threading
import time
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class TrueDataTCPClient:
    """Simple TrueData TCP client"""
    
    def __init__(self):
        self.host = "push.truedata.in"
        self.port = 8086
        self.username = "Trial106"
        self.password = "shyam106"
        
        self.socket = None
        self.connected = False
        self.running = False
        self.thread = None
        self.live_data = {}
        
    def connect(self):
        """Connect to TrueData TCP server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(30)
            
            logger.info(f"🔗 Connecting to TrueData TCP: {self.host}:{self.port}")
            self.socket.connect((self.host, self.port))
            
            # Send authentication
            auth_message = f"LOGIN {self.username} {self.password}\r\n"
            self.socket.send(auth_message.encode())
            
            # Wait for response
            response = self.socket.recv(1024).decode()
            logger.info(f"📨 TrueData response: {response.strip()}")
            
            if "LOGIN OK" in response or "SUCCESS" in response:
                self.connected = True
                logger.info("✅ TrueData TCP authentication successful")
                
                # Subscribe to symbols
                self._subscribe_symbols()
                
                # Start listening thread
                self.running = True
                self.thread = threading.Thread(target=self._listen)
                self.thread.daemon = True
                self.thread.start()
                
                return True
            else:
                logger.error(f"❌ TrueData authentication failed: {response}")
                return False
                
        except Exception as e:
            logger.error(f"TrueData TCP connection error: {e}")
            self.connected = False
            return False
    
    def _subscribe_symbols(self):
        """Subscribe to market symbols"""
        try:
            # Subscribe to NIFTY indices
            symbols = ["NIFTY", "BANKNIFTY", "FINNIFTY"]
            
            for symbol in symbols:
                subscribe_msg = f"SUBSCRIBE {symbol}\r\n"
                self.socket.send(subscribe_msg.encode())
                logger.info(f"📊 Subscribed to {symbol}")
            
        except Exception as e:
            logger.error(f"Error subscribing to symbols: {e}")
    
    def _listen(self):
        """Listen for incoming market data"""
        buffer = ""
        
        while self.running and self.connected:
            try:
                data = self.socket.recv(1024).decode()
                if not data:
                    break
                
                buffer += data
                
                # Process complete messages
                while "\r\n" in buffer:
                    message, buffer = buffer.split("\r\n", 1)
                    self._process_message(message)
                    
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"TrueData listening error: {e}")
                break
        
        logger.warning("TrueData TCP connection closed")
        self.connected = False
    
    def _process_message(self, message: str):
        """Process incoming market data message"""
        try:
            # TrueData might send data in different formats
            # This is a simplified parser
            
            parts = message.split(",")
            if len(parts) >= 3:
                symbol = parts[0]
                ltp = float(parts[1]) if parts[1].replace(".", "").isdigit() else 0
                
                self.live_data[symbol] = {
                    "symbol": symbol,
                    "ltp": ltp,
                    "timestamp": time.time(),
                    "raw_message": message
                }
                
                logger.debug(f"📊 Updated {symbol}: ₹{ltp}")
                
        except Exception as e:
            logger.debug(f"Error processing message '{message}': {e}")
    
    def get_live_data(self) -> Dict:
        """Get current live data"""
        return self.live_data.copy()
    
    def is_connected(self) -> bool:
        """Check connection status"""
        return self.connected
    
    def disconnect(self):
        """Disconnect from TrueData"""
        self.running = False
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        logger.info("TrueData TCP connection closed")

# Global instance
truedata_tcp_client = TrueDataTCPClient()

def start_truedata_tcp():
    """Start TrueData TCP connection"""
    return truedata_tcp_client.connect()

def get_truedata_tcp_data():
    """Get TrueData TCP live data"""
    return truedata_tcp_client.get_live_data()

def is_truedata_tcp_connected():
    """Check TrueData TCP connection"""
    return truedata_tcp_client.is_connected()