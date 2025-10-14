"""
Logging utility for the Tableau Dashboard Generator.
Provides structured logging with rotation and proper formatting.
"""

import sys
import os
from typing import Optional
from pathlib import Path
from loguru import logger as loguru_logger
from loguru import logger

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    rotation: str = "1 day",
    retention: str = "30 days",
    format_string: Optional[str] = None
):
    """
    Setup application logging with loguru.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file. If None, only console logging is used.
        rotation: Log rotation policy (e.g., "1 day", "100 MB")
        retention: Log retention policy (e.g., "30 days", "10 files")
        format_string: Custom log format string
    """
    # Remove default handler
    loguru_logger.remove()
    
    # Default format
    if format_string is None:
        format_string = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    
    # Add console handler
    loguru_logger.add(
        sys.stderr,
        format=format_string,
        level=log_level.upper(),
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        loguru_logger.add(
            log_path,
            format=format_string,
            level=log_level.upper(),
            rotation=rotation,
            retention=retention,
            compression="zip",
            backtrace=True,
            diagnose=True
        )
    
    loguru_logger.info(f"Logging initialized - Level: {log_level.upper()}, File: {log_file}")

def get_logger(name: Optional[str] = None):
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__ of the module)
        
    Returns:
        Logger instance
    """
    if name:
        return loguru_logger.bind(name=name)
    return loguru_logger

# Initialize default logging
def init_default_logging():
    """Initialize logging with default settings"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    setup_logging(
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_file=log_dir / "tableau_generator.log",
        rotation="1 day",
        retention="30 days"
    )