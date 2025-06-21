import logging.config
import os
import json

# Default log level if setup_logging is called without arguments (e.g. standalone execution)
# The main application flow in server.py will pass settings.LOG_LEVEL.
MODULE_DEFAULT_LOG_LEVEL = "INFO"

DEFAULT_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(module)s %(funcName)s %(lineno)d %(message)s'
        }
    },
    'handlers': {
        'default': {
            'level': MODULE_DEFAULT_LOG_LEVEL, # Will be overridden by setup_logging argument
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        },
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['default'],
            'level': MODULE_DEFAULT_LOG_LEVEL, # Will be overridden
            'propagate': False
        },
        'uvicorn': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False
        },
        'uvicorn.error': {
            'level': 'INFO',
            'handlers': ['default'],
            'propagate': False
        },
        'uvicorn.access': {
            'level': 'WARNING',
            'handlers': ['default'],
            'propagate': False
        },
        'fastapi': {
            'handlers': ['default'],
            'level': MODULE_DEFAULT_LOG_LEVEL, # Will be overridden
            'propagate': False
        },
    }
}

def setup_logging(log_level: str = MODULE_DEFAULT_LOG_LEVEL):
    """
    Configures logging for the application.
    The log_level parameter will override the default if provided.
    """
    # Create a deep copy to avoid modifying the global DEFAULT_LOGGING_CONFIG dict
    current_config = json.loads(json.dumps(DEFAULT_LOGGING_CONFIG)) # Simple deep copy for dicts

    effective_log_level = log_level.upper()

    # Override levels based on the passed log_level
    if 'default' in current_config['handlers']:
        current_config['handlers']['default']['level'] = effective_log_level
    if '' in current_config['loggers']:
        current_config['loggers']['']['level'] = effective_log_level
    if 'fastapi' in current_config['loggers']: # Also set FastAPI logger level
        current_config['loggers']['fastapi']['level'] = effective_log_level

    # (python-json-logger check and fallback as before)
    using_json_formatter = any(
        handler_config.get('formatter') == 'json'
        for handler_config in current_config['handlers'].values()
    )
    if using_json_formatter:
        try:
            import pythonjsonlogger.jsonlogger
            # logging.info("python-json-logger is available.") # Cannot use logging before dictConfig
        except ImportError:
            # Using basic print for this pre-config warning
            print("WARNING: python-json-logger is not installed, but JSON formatter is configured. JSON logging might not work as expected.")
            for handler_name, handler_config in current_config['handlers'].items():
                if handler_config.get('formatter') == 'json':
                    handler_config['formatter'] = 'standard'
            if 'json' in current_config['formatters']:
                del current_config['formatters']['json']

    logging.config.dictConfig(current_config)
    logger = logging.getLogger(__name__) # Get logger after config is applied
    logger.info(f"Logging configured. Effective root log level: {effective_log_level}")

if __name__ == '__main__':
    # This block is for testing logging_config.py directly
    # It will use MODULE_DEFAULT_LOG_LEVEL unless overridden by setup_logging call.

    # Test with default level (INFO)
    setup_logging() # Uses MODULE_DEFAULT_LOG_LEVEL = "INFO"
    logger_main = logging.getLogger() # Get root logger configured by setup_logging

    logger_main.debug("This is a debug message (should not appear with INFO level).")
    logger_main.info("This is an info message (INFO level).")
    logger_main.warning("This is a warning message (INFO level).")

    # Test with DEBUG level
    setup_logging(log_level="DEBUG")
    logger_main.debug("This is a debug message (DEBUG level - should appear now).")
    logger_main.info("This is an info message (DEBUG level).")

    # Test specific loggers defined in config
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    # Uvicorn access is set to WARNING, so info/debug won't show unless its handler level is also changed
    uvicorn_access_logger.info("Uvicorn access info log (should be suppressed by default uvicorn.access config).")
    uvicorn_access_logger.warning("Uvicorn access warning log (should show).")

    fastapi_logger = logging.getLogger("fastapi")
    fastapi_logger.debug("FastAPI debug log (should show if root is DEBUG and fastapi logger is DEBUG).")
