"""
Logging utility for AI Travel Agent
Provides centralized logging configuration
"""

import os
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

from config import Config

def setup_logger(name: str, level: str = None) -> logging.Logger:
    """
    Setup logger with file and console handlers
    
    Args:
        name: Logger name
        level: Log level (optional, uses config default)
        
    Returns:
        Configured logger instance
    """
    config = Config()
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Set log level
    log_level = getattr(logging, level or config.LOG_LEVEL, logging.INFO)
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(config.LOG_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    try:
        # Ensure logs directory exists
        os.makedirs(config.LOGS_DIR, exist_ok=True)
        
        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            config.LOG_FILE,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    except Exception as e:
        logger.warning(f"Could not setup file logging: {str(e)}")
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get existing logger by name
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

class LoggerMixin:
    """Mixin class to add logging capability to any class"""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for the class"""
        if not hasattr(self, '_logger'):
            self._logger = setup_logger(self.__class__.__name__)
        return self._logger

def log_execution_time(func):
    """
    Decorator to log function execution time
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    def wrapper(*args, **kwargs):
        logger = setup_logger(f"{func.__module__}.{func.__name__}")
        start_time = datetime.now()
        
        try:
            result = func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.debug(f"Function {func.__name__} executed in {execution_time:.3f} seconds")
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Function {func.__name__} failed after {execution_time:.3f} seconds: {str(e)}")
            raise
    
    return wrapper

def log_memory_usage():
    """Log current memory usage"""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        logger = setup_logger('memory_monitor')
        logger.debug(f"Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")
    except ImportError:
        pass  # psutil not available

def setup_error_handler():
    """Setup global error handler for uncaught exceptions"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Allow keyboard interrupt to pass through
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger = setup_logger('global_error_handler')
        logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    import sys
    sys.excepthook = handle_exception
