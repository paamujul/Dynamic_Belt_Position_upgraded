"""
Logging Service Module

Provides a unified logging interface for the project. Logs messages to console
and optionally to a file if ENABLE_LOGGING is True in settings.

Settings used:
- ENABLE_LOGGING: bool, enables/disables file logging
- ENABLE_DEBUG: bool, enables/disables debug-level console output
- LOG_FILE: Path to the log file
- LOGS_DIR: Directory to store log files
"""
import logging
import belt_position.config.settings as cfg
from datetime import datetime


def setup_logging():
    """
    Configure logging after settings are updated.

    This sets up file logging if `ENABLE_LOGGING` is True and ensures that
    the log directory exists.

    Side Effects:
        - Creates `LOGS_DIR` if it does not exist.
        - Initializes Python logging to write messages to `LOG_FILE`.
    """
    if not cfg.ENABLE_LOGGING:
        return

    # Ensure directory exists
    cfg.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        filename=str(cfg.LOG_FILE),
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        force=True,  
    )

def log(msg: str, level: str | None = None):
    """
    Log a message to the console and optionally to a log file.

    Args:
        msg (str): The message to log.
        level (str | None): Logging level. Options: 'INFO', 'WARNING', 'ERROR', 'DEBUG'.
            Defaults to 'INFO' if None.

    Side Effects:
        - Prints the message to console with timestamp and level.
        - Writes to log file if `ENABLE_LOGGING` is True.

    Notes:
        - Debug messages are skipped if `ENABLE_DEBUG` is False.
        - Timestamp format: YYYY-MM-DD HH:MM:SS
    """
    if level is None:
        level = "INFO"
    
    # Always write to log file if enabled
    if cfg.ENABLE_LOGGING:
        if level.upper() == "ERROR":
            logging.error(msg)
        elif level.upper() == "WARNING":
            logging.warning(msg)
        elif level.upper() == "DEBUG":
            logging.debug(msg)
        else:
            logging.info(msg)
        
    # Skip debug messages if debug is disabled
    if level.upper() == "DEBUG" and not cfg.ENABLE_DEBUG:
        return
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console_msg = f"{timestamp} [{level}] {msg}"
    print(console_msg)
     
    