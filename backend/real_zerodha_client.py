"""
REAL Zerodha Market Data Client
For PAID Zerodha subscription - gets actual live market data
"""

import asyncio
import logging
from typing import Dict, Optional, List
import os
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class RealZerodhaClient:
    """Real Zerodha client for PAID subscription"""
    
    def __init__(self):
        self.api_key = os.getenv('ZERODHA_API_KEY')
        self.api_secret = os.getenv('ZERODHA_API_SECRET')
        self.client_id = os.getenv('ZERODHA_CLIENT_ID')
        
        self.kite = None
        self.access_token = os.getenv('ZERODHA_ACCESS_TOKEN')  # Will need this
        self.authenticated = False
        
        # Check if we have valid credentials
        self.has_credentials = bool(
            self.api_key and 
            self.api_secret and 
            self.api_key != 'your_zerodha_api_key'
        )
        
        if self.has_credentials:
            self._initialize_kite()
        else:
            logger.warning("⚠️ Zerodha credentials not configured - need real API keys")
    
    def _initialize_kite(self):
        """Initialize KiteConnect with real credentials"""
        try:
            from kiteconnect import KiteConnect
            
            self.kite = KiteConnect(api_key=self.api_key)
            
            # If we have access token, set it
            if self.access_token:
                self.kite.set_access_token(self.access_token)
                self.authenticated = True
                logger.info("✅ Zerodha authenticated with access token")
            else:
                logger.warning("⚠️ Zerodha needs access token for live data")
            
        except Exception as e:
            logger.error(f"Zerodha initialization error: {e}")
    
    async def get_live_quotes(self, symbols: List[str]) -> Optional[Dict]:
        """Get REAL live market quotes from Zerodha"""
        try:
            if not self.authenticated or not self.kite:
                return await self._return_auth_needed_status(symbols)
            
            # Map symbols to Zerodha instrument tokens
            zerodha_symbols = self._map_to_zerodha_symbols(symbols)
            
            # Get real quotes from Zerodha
            quotes = self.kite.quote(zerodha_symbols)
            
            # Format the real data
            formatted_data = self._format_zerodha_quotes(quotes, symbols)
            
            logger.info(f"✅ Got REAL market data from Zerodha for {len(formatted_data)} symbols")
            return formatted_data
            
        except Exception as e:
            logger.error(f"Error getting real Zerodha quotes: {e}")
            return await self._return_error_status(symbols, str(e))
    
    def _map_to_zerodha_symbols(self, symbols: List[str]) -> List[str]:
        """Map our symbols to Zerodha format"""
        zerodha_symbols = []
        
        for symbol in symbols:
            if symbol == "NIFTY":
                zerodha_symbols.append("NSE:NIFTY 50")
            elif symbol == "BANKNIFTY":
                zerodha_symbols.append("NSE:NIFTY BANK")
            elif symbol == "FINNIFTY":
                zerodha_symbols.append("NSE:NIFTY FIN SERVICE")
            else:
                zerodha_symbols.append(f"NSE:{symbol}")
        
        return zerodha_symbols
    
    def _format_zerodha_quotes(self, quotes: Dict, original_symbols: List[str]) -> Dict:
        """Format Zerodha quotes to our standard format"""
        formatted_data = {}
        
        # Reverse mapping
        symbol_mapping = {
            "NSE:NIFTY 50": "NIFTY",
            "NSE:NIFTY BANK": "BANKNIFTY",
            "NSE:NIFTY FIN SERVICE": "FINNIFTY"
        }
        
        for zerodha_symbol, quote_data in quotes.items():
            our_symbol = symbol_mapping.get(zerodha_symbol, zerodha_symbol.split(":")[-1])
            
            if our_symbol in original_symbols:
                # Extract real market data
                last_price = quote_data.get('last_price', 0)
                prev_close = quote_data.get('ohlc', {}).get('close', last_price)
                
                change = last_price - prev_close
                change_percent = (change / prev_close * 100) if prev_close > 0 else 0
                
                formatted_data[our_symbol] = {
                    "symbol": our_symbol,
                    "ltp": round(last_price, 2),
                    "change": round(change, 2),
                    "change_percent": round(change_percent, 2),
                    "volume": quote_data.get('volume', 0),
                    "high": quote_data.get('ohlc', {}).get('high', last_price),
                    "low": quote_data.get('ohlc', {}).get('low', last_price),
                    "open": quote_data.get('ohlc', {}).get('open', last_price),
                    "data_source": "REAL_ZERODHA_PAID",
                    "market_status": "OPEN" if self._is_market_open() else "CLOSED",
                    "timestamp": datetime.now().isoformat(),
                    "connection_status": "Live Zerodha paid subscription",
                    "note": "REAL MARKET DATA from Zerodha paid API"
                }
        
        return formatted_data
    
    async def _return_auth_needed_status(self, symbols: List[str]) -> Dict:
        """Return status when authentication is needed"""
        auth_status = {}
        
        for symbol in symbols:
            auth_status[symbol] = {
                "symbol": symbol,
                "ltp": 0,
                "change": 0,
                "change_percent": 0,
                "volume": 0,
                "high": 0,
                "low": 0,
                "open": 0,
                "data_source": "ZERODHA_AUTH_NEEDED",
                "market_status": "UNKNOWN",
                "timestamp": datetime.now().isoformat(),
                "connection_status": "Zerodha authentication required",
                "note": "NEED: Zerodha access token for paid subscription",
                "has_credentials": self.has_credentials,
                "needs_access_token": not bool(self.access_token)
            }
        
        return auth_status
    
    async def _return_error_status(self, symbols: List[str], error: str) -> Dict:
        """Return error status"""
        error_status = {}
        
        for symbol in symbols:
            error_status[symbol] = {
                "symbol": symbol,
                "ltp": 0,
                "change": 0,
                "change_percent": 0,
                "volume": 0,
                "high": 0,
                "low": 0,
                "open": 0,
                "data_source": "ZERODHA_ERROR",
                "market_status": "ERROR",
                "timestamp": datetime.now().isoformat(),
                "connection_status": f"Zerodha error: {error}",
                "note": f"ERROR: {error}"
            }
        
        return error_status
    
    def _is_market_open(self) -> bool:
        """Check if market is open"""
        current_time = datetime.now().time()
        market_open = datetime.strptime("09:15", "%H:%M").time()
        market_close = datetime.strptime("15:30", "%H:%M").time()
        
        return market_open <= current_time <= market_close
    
    def get_login_url(self) -> Optional[str]:
        """Get Zerodha login URL for authentication"""
        if not self.kite:
            return None
        
        try:
            login_url = self.kite.login_url()
            return login_url
        except Exception as e:
            logger.error(f"Error getting login URL: {e}")
            return None
    
    def authenticate_with_request_token(self, request_token: str) -> bool:
        """Authenticate using request token from login"""
        try:
            if not self.kite:
                return False
            
            # Generate access token
            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            self.access_token = data["access_token"]
            
            # Set access token
            self.kite.set_access_token(self.access_token)
            self.authenticated = True
            
            logger.info("✅ Zerodha authentication successful!")
            return True
            
        except Exception as e:
            logger.error(f"Zerodha authentication failed: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Get Zerodha connection status"""
        return {
            "has_credentials": self.has_credentials,
            "authenticated": self.authenticated,
            "api_key_configured": bool(self.api_key and self.api_key != 'your_zerodha_api_key'),
            "access_token_available": bool(self.access_token),
            "kite_initialized": bool(self.kite),
            "subscription_type": "PAID" if self.has_credentials else "UNKNOWN",
            "ready_for_live_data": self.authenticated
        }

# Global instance
real_zerodha_client = RealZerodhaClient()

def get_real_zerodha_client():
    """Get the real Zerodha client instance"""
    return real_zerodha_client