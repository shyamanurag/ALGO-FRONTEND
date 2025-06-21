from fastapi import APIRouter, HTTPException, Request, Depends
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from src.app_state import AppState, MarketDataState
from src.core.utils import create_api_success_response, format_datetime_for_api # Import utilities

try:
    from backend.server import get_market_data_state, get_app_state
except ImportError:
    # Use fallback functions (this is expected due to circular imports)
    from src.app_state import app_state as _global_app_state_instance
    def get_market_data_state(): return _global_app_state_instance.market_data
    def get_app_state(): return _global_app_state_instance

logger = logging.getLogger(__name__)

webhook_router = APIRouter(prefix="/webhook", tags=["Webhooks"])

@webhook_router.post("/truedata", summary="Receive live market data from TrueData")
async def truedata_webhook_route(
    request: Request,
    market_data_state: MarketDataState = Depends(get_market_data_state)
):
    try:
        data = await request.json()

        if not isinstance(data, list) and not isinstance(data, dict):
             # This will be caught by the http_exception_handler and formatted
             raise HTTPException(status_code=400, detail="Invalid payload type, expected JSON object or array.")

        ticks_to_process = data if isinstance(data, list) else [data]
        symbols_processed_this_call = []

        for tick in ticks_to_process:
            if 'symbol' in tick and ('ltp' in tick or 'LTP' in tick):
                symbol = tick['symbol']
                ltp_val = tick.get('ltp', tick.get('LTP'))

                if not isinstance(symbol, str) or not isinstance(ltp_val, (int, float)):
                    logger.warning(f"Skipping invalid tick due to type mismatch: {tick}")
                    continue

                symbols_processed_this_call.append(symbol)
                market_data_state.live_market_data[symbol] = {
                    'symbol': symbol, 'ltp': float(ltp_val),
                    'volume': int(tick.get('volume', tick.get('Volume', 0))),
                    'open': float(tick.get('open', tick.get('Open', 0))),
                    'high': float(tick.get('high', tick.get('High', 0))),
                    'low': float(tick.get('low', tick.get('Low', 0))),
                    'change': float(tick.get('change', tick.get('Change', 0))),
                    'change_percent': float(tick.get('change_percent', tick.get('PercentChange', tick.get('percentChange', 0)))),
                    'timestamp': format_datetime_for_api(datetime.utcnow()),
                    'original_timestamp': tick.get('timestamp', tick.get('Timestamp', tick.get('feed_timestamp', None))),
                    'data_source': 'TRUEDATA_WEBHOOK_LIVE'
                }
            else:
                logger.warning(f"Invalid or incomplete TrueData tick data in list: {tick}")

        if symbols_processed_this_call:
            market_data_state.market_data_last_update = datetime.utcnow()
            if not market_data_state.truedata_connected:
                market_data_state.truedata_connected = True
                if market_data_state.active_data_source is None or market_data_state.active_data_source != "truedata":
                    market_data_state.active_data_source = "truedata"
                    logger.info("TrueData connection status True and active_data_source set via webhook.")
                else:
                    logger.info("TrueData connection status True via webhook data.")

            return create_api_success_response(
                data={
                    "symbols_received_count": len(symbols_processed_this_call),
                    "symbols": symbols_processed_this_call,
                    "timestamp": format_datetime_for_api(datetime.utcnow())
                },
                message="TrueData webhook data processed."
            )
        else:
            logger.warning(f"No valid ticks processed from TrueData webhook data: {data}")
            # Changed to raise HTTPException for consistency with error handling
            raise HTTPException(status_code=400, detail="No valid ticks with symbol and ltp found in payload.")

    except json.JSONDecodeError:
        logger.error("Error decoding JSON from TrueData webhook", exc_info=True)
        body = await request.body()
        logger.error(f"Webhook raw body: {body.decode(errors='ignore')}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload") # Caught by http_exception_handler
    except HTTPException as http_exc: # Re-raise if it's already an HTTPException
        raise http_exc
    except Exception as e: # Catch any other exception
        logger.error(f"TrueData webhook processing error: {e}", exc_info=True)
        body_preview = ""
        try:
            body_bytes = await request.body()
            body_preview = body_bytes.decode(errors='ignore')[:500]
        except Exception as read_err: logger.error(f"Could not read request body during error handling: {read_err}")
        # This will be caught by generic_exception_handler
        raise Exception(f"Internal server error processing webhook: {str(e)}. Body preview: {body_preview}")

