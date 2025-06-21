import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, date, time

logger = logging.getLogger(__name__)

def create_api_success_response(
    data: Optional[Any] = None,
    message: Optional[str] = None,
    status_code: int = 200, # Though FastAPI handles status code separately in Response
    **extra_fields
) -> Dict[str, Any]:
    """
    Creates a standardized successful API response dictionary.
    """
    response_content = {"success": True}
    if data is not None:
        response_content["data"] = data
    if message:
        response_content["message"] = message
    if extra_fields:
        response_content.update(extra_fields)
    return response_content

def format_datetime_for_api(dt_object: Optional[datetime]) -> Optional[str]:
    """
    Formats a datetime object into a standardized ISO string for API responses.
    Returns None if the input is None.
    """
    if dt_object is None:
        return None
    if not isinstance(dt_object, datetime):
        logger.warning(f"format_datetime_for_api received non-datetime object: {type(dt_object)}. Returning as string.")
        return str(dt_object)
    return dt_object.isoformat()

def format_date_for_api(date_object: Optional[date]) -> Optional[str]:
    """
    Formats a date object into a standardized ISO string (YYYY-MM-DD) for API responses.
    Returns None if the input is None.
    """
    if date_object is None:
        return None
    if not isinstance(date_object, date): # Handles datetime objects too, but explicitly for date
        logger.warning(f"format_date_for_api received non-date object: {type(date_object)}. Returning as string.")
        return str(date_object)
    return date_object.isoformat()

# Example of a more specific utility if needed elsewhere, e.g. for normalizing symbol names
def normalize_symbol(symbol: str) -> str:
    """
    Normalizes a trading symbol to a common format (e.g., uppercase, strip whitespace).
    """
    return symbol.upper().strip()

# Added WebSocket broadcast utility
import json # For broadcast_websocket_message
from typing import Set, Any # For broadcast_websocket_message, Any for WebSocket connection type

async def broadcast_websocket_message(websocket_connections: Set[Any], message: Dict):
    """
    Broadcasts a JSON message to all connected WebSocket clients.
    Manages disconnections by removing clients that fail to send.

    Args:
        websocket_connections: A set of active WebSocket connection objects.
                               This set is modified in place if disconnections occur.
        message: A dictionary representing the JSON message to send.
    """
    if not websocket_connections:
        # logger.debug("No active WebSocket connections to broadcast to.") # logger is module level
        logging.getLogger(__name__).debug("No active WebSocket connections to broadcast to.")
        return

    message_json = json.dumps(message)
    disconnected_clients = set()

    # Create a copy of the set for iteration, as it might be modified
    for websocket in list(websocket_connections):
        try:
            await websocket.send_text(message_json)
            # logging.getLogger(__name__).debug(f"Message broadcasted to client: {websocket.client.host}:{websocket.client.port if websocket.client else 'N/A'}")
        except Exception as e: # Catches WebSocketRequestClosed, ConnectionClosed, etc.
            logging.getLogger(__name__).warning(f"Failed to send message to WebSocket client {websocket.client.host if websocket.client else 'N/A'}: {e}. Marking for removal.")
            disconnected_clients.add(websocket)

    if disconnected_clients:
        logging.getLogger(__name__).info(f"Removing {len(disconnected_clients)} disconnected WebSocket clients.")
        for client in disconnected_clients:
            websocket_connections.discard(client)
        # Note: If a counter (like app_state.system_status.websocket_connections) is maintained outside,
        # it should be updated after this function call based on len(websocket_connections).

if __name__ == "__main__":
    # Setup basic logging for testing this module directly
    try:
        from .logging_config import setup_logging # Relative import if core is a package
        setup_logging(log_level="DEBUG")
    except ImportError: # Fallback if run directly and relative import fails
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
        logging.warning("Could not import setup_logging for utils.py direct execution. Using basicConfig.")

    logger_utils_test = logging.getLogger(__name__)

    logger_utils_test.info("--- Testing create_api_success_response ---")
    response1 = create_api_success_response(data={"user_id": 1, "name": "Test"}, message="User created")
    logger_utils_test.info(f"Response 1: {response1}")

    response2 = create_api_success_response(message="Operation complete", record_count=50)
    logger_utils_test.info(f"Response 2: {response2}")

    response3 = create_api_success_response(data=[{"id":1}, {"id":2}])
    logger_utils_test.info(f"Response 3: {response3}")

    logger_utils_test.info("\n--- Testing format_datetime_for_api ---")
    now_dt = datetime.utcnow()
    logger_utils_test.info(f"Formatted datetime: {format_datetime_for_api(now_dt)}")
    logger_utils_test.info(f"Formatted None datetime: {format_datetime_for_api(None)}")
    logger_utils_test.info(f"Formatted date as datetime: {format_datetime_for_api(date(2023,1,1))}")

    logger_utils_test.info("\n--- Testing format_date_for_api ---")
    today_date = date.today()
    logger_utils_test.info(f"Formatted date: {format_date_for_api(today_date)}")
    logger_utils_test.info(f"Formatted None date: {format_date_for_api(None)}")
    # format_date_for_api would also stringify a datetime object if passed by mistake, which is acceptable.

    logger_utils_test.info("\n--- Testing normalize_symbol ---")
    logger_utils_test.info(f"Normalized ' nifty 50 ': '{normalize_symbol(' nifty 50 ')}'")
    logger_utils_test.info(f"Normalized 'RELIANCE': '{normalize_symbol('RELIANCE')}'")

