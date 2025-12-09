import logging
import sys
from datetime import datetime
from typing import Optional

from .config import settings

# Create a custom logger
logger = logging.getLogger("hybrid_chatbot")
logger.setLevel(logging.DEBUG)

# Create formatters
detailed_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s'
)
simple_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)

# Create console handler with higher log level
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(simple_formatter)

# Create file handler
if settings.LOG_FILE:
    file_handler = logging.FileHandler(settings.LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
else:
    # If no log file specified, create a dummy handler
    file_handler = logging.NullHandler()
    file_handler.setLevel(logging.DEBUG)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Prevent propagation to root logger to avoid duplicate logs
logger.propagate = False


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with optional name extension
    """
    if name:
        return logger.getChild(name)
    return logger


def setup_logging() -> None:
    """
    Setup logging configuration
    """
    global logger
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Set level
    logger.setLevel(settings.LOG_LEVEL.upper())
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if settings.LOG_FILE:
        file_handler = logging.FileHandler(settings.LOG_FILE)
        file_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    # Error file handler
    if settings.ERROR_LOG_FILE:
        error_handler = logging.FileHandler(settings.ERROR_LOG_FILE)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)
    
    logger.info("Logging setup complete")


def log_exception(exc: Exception, context: str = "") -> None:
    """
    Log an exception with context
    """
    logger.exception(f"Exception in {context}: {str(exc)}")


# Initialize logging
setup_logging()