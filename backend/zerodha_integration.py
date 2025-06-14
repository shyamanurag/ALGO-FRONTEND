"""
Zerodha Integration Module for Elite Trading Platform
Real broker integration for live trading
"""
import os
import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import hashlib
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from kiteconnect import KiteConnect
    KITECONNECT_AVAILABLE = True
except ImportError:
    KITECONNECT_AVAILABLE = False
    logging.warning("KiteConnect not available - Zerodha integration disabled")

logger = logging.getLogger(__name__)

class ZerodhaManager:
    def __init__(self):
        # Load credentials from environment
        self.api_key = os.environ.get('ZERODHA_API_KEY')
        self.api_secret = os.environ.get('ZERODHA_API_SECRET')
        self.client_id = os.environ.get('ZERODHA_CLIENT_ID')
        self.account_name = os.environ.get('ZERODHA_ACCOUNT_NAME', 'Unknown')
        
        self.kite = None
        self.access_token = None
        self.is_connected = False
        self.last_connection_attempt = None
        self.connection_error = None
        
        logger.info(f"Initializing Zerodha Manager for account: {self.account_name}")
        logger.info(f"API Key configured: {'Yes' if self.api_key else 'No'}")
        logger.info(f"Client ID: {self.client_id}")
        
        if self.api_key and self.api_secret and KITECONNECT_AVAILABLE:
            self.kite = KiteConnect(api_key=self.api_key)
            logger.info("Zerodha KiteConnect instance created successfully")
        elif not KITECONNECT_AVAILABLE:
            logger.error("KiteConnect library not available")
        else:
            logger.warning("Zerodha API credentials not found in environment")
    
    def get_login_url(self) -> Optional[str]:
        """Get the login URL for Zerodha authentication"""
        if not self.kite:
            return None
        
        try:
            login_url = self.kite.login_url()
            logger.info("Generated Zerodha login URL")
            return login_url
        except Exception as e:
            logger.error(f"Error generating login URL: {e}")
            return None
    
    async def connect_with_request_token(self, request_token: str) -> Dict[str, Any]:
        """Connect to Zerodha using the request token from login"""
        try:
            if not self.kite:
                return {
                    "success": False,
                    "error": "Zerodha API credentials not configured"
                }
            
            # Generate access token
            data = self.kite.generate_session(
                request_token=request_token,
                api_secret=self.api_secret
            )
            
            self.access_token = data["access_token"]
            self.kite.set_access_token(self.access_token)
            
            # Test the connection by fetching profile
            profile = self.kite.profile()
            
            self.is_connected = True
            self.last_connection_attempt = datetime.utcnow()
            self.connection_error = None
            
            logger.info(f"Successfully connected to Zerodha for user: {profile.get('user_name', 'Unknown')}")
            
            return {
                "success": True,
                "profile": {
                    "user_id": profile.get("user_id"),
                    "user_name": profile.get("user_name"),
                    "email": profile.get("email"),
                    "broker": profile.get("broker"),
                    "exchanges": profile.get("exchanges", []),
                    "products": profile.get("products", []),
                    "order_types": profile.get("order_types", [])
                },
                "access_token": self.access_token,
                "connected_at": self.last_connection_attempt.isoformat()
            }
            
        except Exception as e:
            self.is_connected = False
            self.connection_error = str(e)
            self.last_connection_attempt = datetime.utcnow()
            
            logger.error(f"Failed to connect to Zerodha: {e}")
            return {
                "success": False,
                "error": str(e),
                "attempted_at": self.last_connection_attempt.isoformat()
            }
    
    async def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status"""
        if not self.api_key or not self.api_secret:
            return {
                "connected": False,
                "status": "NOT_CONFIGURED",
                "message": "Zerodha API credentials not configured",
                "account_name": self.account_name,
                "api_key": self.api_key[:8] + "..." if self.api_key else None
            }
        
        if self.is_connected and self.access_token:
            try:
                # Test connection by fetching margins
                margins = self.kite.margins()
                
                return {
                    "connected": True,
                    "status": "CONNECTED",
                    "message": "Connected to Zerodha successfully",
                    "account_name": self.account_name,
                    "api_key": self.api_key[:8] + "...",
                    "client_id": self.client_id,
                    "last_connected": self.last_connection_attempt.isoformat() if self.last_connection_attempt else None,
                    "available_cash": margins.get("equity", {}).get("available", {}).get("cash", 0),
                    "used_margin": margins.get("equity", {}).get("utilised", {}).get("debits", 0)
                }
            except Exception as e:
                self.is_connected = False
                self.connection_error = str(e)
                logger.error(f"Zerodha connection test failed: {e}")
        
        return {
            "connected": False,
            "status": "DISCONNECTED",
            "message": self.connection_error or "Not connected to Zerodha",
            "account_name": self.account_name,
            "api_key": self.api_key[:8] + "..." if self.api_key else None,
            "client_id": self.client_id,
            "last_attempt": self.last_connection_attempt.isoformat() if self.last_connection_attempt else None,
            "error": self.connection_error
        }
    
    async def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Place an order through Zerodha"""
        if not self.is_connected or not self.kite:
            return {
                "success": False,
                "error": "Not connected to Zerodha"
            }
        
        try:
            order_id = self.kite.place_order(
                variety=order_data.get("variety", "regular"),
                exchange=order_data.get("exchange", "NSE"),
                tradingsymbol=order_data["symbol"],
                transaction_type=order_data["action"],  # BUY or SELL
                quantity=order_data["quantity"],
                product=order_data.get("product", "MIS"),  # MIS for intraday
                order_type=order_data.get("order_type", "MARKET"),
                price=order_data.get("price"),
                validity=order_data.get("validity", "DAY"),
                disclosed_quantity=order_data.get("disclosed_quantity"),
                trigger_price=order_data.get("trigger_price"),
                tag=order_data.get("tag", "elite_trading")
            )
            
            logger.info(f"Order placed successfully: {order_id}")
            return {
                "success": True,
                "order_id": order_id,
                "message": "Order placed successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_positions(self) -> Dict[str, Any]:
        """Get current positions from Zerodha"""
        if not self.is_connected or not self.kite:
            return {
                "success": False,
                "positions": [],
                "error": "Not connected to Zerodha"
            }
        
        try:
            positions = self.kite.positions()
            
            return {
                "success": True,
                "positions": positions.get("day", []) + positions.get("net", []),
                "day_positions": positions.get("day", []),
                "net_positions": positions.get("net", [])
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch positions: {e}")
            return {
                "success": False,
                "positions": [],
                "error": str(e)
            }
    
    async def get_orders(self) -> Dict[str, Any]:
        """Get orders from Zerodha"""
        if not self.is_connected or not self.kite:
            return {
                "success": False,
                "orders": [],
                "error": "Not connected to Zerodha"
            }
        
        try:
            orders = self.kite.orders()
            
            return {
                "success": True,
                "orders": orders
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch orders: {e}")
            return {
                "success": False,
                "orders": [],
                "error": str(e)
            }
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        if not self.is_connected or not self.kite:
            return {
                "success": False,
                "error": "Not connected to Zerodha"
            }
        
        try:
            result = self.kite.cancel_order(
                variety="regular",
                order_id=order_id
            )
            
            logger.info(f"Order cancelled successfully: {order_id}")
            return {
                "success": True,
                "order_id": result,
                "message": "Order cancelled successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_funds(self) -> Dict[str, Any]:
        """Get account funds and margins"""
        if not self.is_connected or not self.kite:
            return {
                "success": False,
                "funds": {},
                "error": "Not connected to Zerodha"
            }
        
        try:
            margins = self.kite.margins()
            
            return {
                "success": True,
                "funds": margins
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch funds: {e}")
            return {
                "success": False,
                "funds": {},
                "error": str(e)
            }
    
    async def disconnect(self) -> Dict[str, Any]:
        """Disconnect from Zerodha"""
        try:
            self.is_connected = False
            self.access_token = None
            self.connection_error = None
            
            logger.info("Disconnected from Zerodha")
            return {
                "success": True,
                "message": "Disconnected from Zerodha successfully"
            }
            
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Global Zerodha manager instance
zerodha_manager = ZerodhaManager()