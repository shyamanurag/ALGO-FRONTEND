import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, Callable, List
import websockets
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config/production.env')

logger = logging.getLogger(__name__)

class TrueDataFeed:
    def __init__(self):
        self.username = os.getenv('TRUEDATA_USERNAME')
        self.password = os.getenv('TRUEDATA_PASSWORD')
        self.url = os.getenv('TRUEDATA_URL', 'push.truedata.in')
        self.port = int(os.getenv('TRUEDATA_PORT', '8086'))
        self.ws_url = f"wss://{self.url}:{self.port}"
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.subscribers: Dict[str, List[Callable]] = {}
        self.reconnect_delay = 5
        self.max_reconnect_attempts = 5
        self.current_reconnect_attempt = 0

    async def connect(self):
        """Establish connection to TrueData WebSocket"""
        try:
            self.websocket = await websockets.connect(
                self.ws_url,
                ssl=True,
                extra_headers={
                    'Authorization': f'Basic {self.username}:{self.password}'
                }
            )
            self.connected = True
            self.current_reconnect_attempt = 0
            logger.info("Connected to TrueData feed")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to TrueData: {str(e)}")
            return False

    async def subscribe(self, symbols: List[str]):
        """Subscribe to market data for given symbols"""
        if not self.connected:
            await self.connect()
        
        try:
            subscription_msg = {
                "type": "subscribe",
                "symbols": symbols
            }
            await self.websocket.send(json.dumps(subscription_msg))
            logger.info(f"Subscribed to symbols: {symbols}")
        except Exception as e:
            logger.error(f"Failed to subscribe to symbols: {str(e)}")
            await self.reconnect()

    async def unsubscribe(self, symbols: List[str]):
        """Unsubscribe from market data for given symbols"""
        if not self.connected:
            return
        
        try:
            unsubscribe_msg = {
                "type": "unsubscribe",
                "symbols": symbols
            }
            await self.websocket.send(json.dumps(unsubscribe_msg))
            logger.info(f"Unsubscribed from symbols: {symbols}")
        except Exception as e:
            logger.error(f"Failed to unsubscribe from symbols: {str(e)}")

    async def add_subscriber(self, symbol: str, callback: Callable):
        """Add a callback function for a symbol"""
        if symbol not in self.subscribers:
            self.subscribers[symbol] = []
        self.subscribers[symbol].append(callback)

    async def remove_subscriber(self, symbol: str, callback: Callable):
        """Remove a callback function for a symbol"""
        if symbol in self.subscribers and callback in self.subscribers[symbol]:
            self.subscribers[symbol].remove(callback)

    async def process_message(self, message: str):
        """Process incoming WebSocket message"""
        try:
            data = json.loads(message)
            symbol = data.get('symbol')
            
            if symbol and symbol in self.subscribers:
                for callback in self.subscribers[symbol]:
                    try:
                        await callback(data)
                    except Exception as e:
                        logger.error(f"Error in subscriber callback: {str(e)}")
        except json.JSONDecodeError:
            logger.error(f"Failed to parse message: {message}")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")

    async def reconnect(self):
        """Attempt to reconnect to TrueData"""
        if self.current_reconnect_attempt >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            return False

        self.current_reconnect_attempt += 1
        logger.info(f"Attempting to reconnect (attempt {self.current_reconnect_attempt})")
        
        await asyncio.sleep(self.reconnect_delay)
        return await self.connect()

    async def start(self):
        """Start the TrueData feed"""
        while True:
            try:
                if not self.connected:
                    if not await self.connect():
                        await asyncio.sleep(self.reconnect_delay)
                        continue

                async for message in self.websocket:
                    await self.process_message(message)

            except websockets.ConnectionClosed:
                logger.warning("Connection to TrueData closed")
                self.connected = False
                await self.reconnect()
            except Exception as e:
                logger.error(f"Error in TrueData feed: {str(e)}")
                self.connected = False
                await self.reconnect()

    async def stop(self):
        """Stop the TrueData feed"""
        if self.websocket:
            await self.websocket.close()
        self.connected = False
        logger.info("TrueData feed stopped") 