"""
Global configuration for DynamicBeltPosition.
This module centralizes file paths, constants, and test parameters for the project. Also provides helper functions to setup environment.
"""

from pathlib import Path
from datetime import datetime

# ------------------------------------------
# Base directories
# ------------------------------------------
PROJECT_ROOT_DIR = Path(__file__).resolve().parents[1]    # Project root directory
TEST_ID = ""                                              # Current test ID
DATA_ROOT_DIR = None                                      # Directory for raw data                            
XSENSOR_DATA_PATH = None                                  # Pressure Sensor(csv files) data directory for current test
EXCEL_FILES_PATH  = None                                  # Excel files directory for current test
DATA_PROCESSED = None                                     # Directory for processed data
LOGS_DIR = PROJECT_ROOT_DIR / "logs"                      # Directory for log files

# ------------------------------------------
# Input data parameters
# ------------------------------------------
FRAME_RATE = 3300.0                       # Pressure Sensor Frame rate (Hz), used for time calculations
PRESSURE_THRESHOLD = 20                   # Threshold to consider frame cell pressure valid
PRESSURE_UNIT = 'kPa'                     # Pressure unit 
START_TIME = 0.0                          # Start time 
END_TIME = 0.125                          # End time 
TIME_PRECISION = 4                        # Decimal places for time rounding   
                  
# ------------------------------------------ 
# Algorithm Parameters
# ------------------------------------------
MINIMUM_POINTS = 5                        # Minimum points for a line to be considered an edge
SPECKLE_DIFF = 500                        # Maximum allowable pressure difference for speckle removal
SPECKLE_RATIO = 10                        # Ratio threshold for identifying pressure speckle noise


# ------------------------------------------
# Logging configuration
# ------------------------------------------
ENABLE_LOGGING = True     # Produce log files if True
ENABLE_DEBUG = False      # Produce DEBUG level logs if True
LOG_FILE = None           # File for log output      

# ------------------------------------------
# Utility constants
# ------------------------------------------

def update_settings(**kwargs):
    """
    Update configuration dynamically and recompute dependent paths.

    This function updates global configuration variables with provided values
    and recalculates derived paths for processed data, logs, and input files.

    Args:
        **kwargs: Key-value pairs of configuration to update.
            Supported keys include:
            - TEST_ID, DATA_ROOT_DIR, START_TIME, END_TIME, PRESSURE_THRESHOLD,
              PRESSURE_UNIT, MINIMUM_POINTS, SPECKLE_DIFF, SPECKLE_RATIO.

    Side Effects:
        - Updates global variables for paths and parameters.
        - Recomputes dependent paths for processed data and logs.
    """
    global TEST_ID, DATA_ROOT_DIR, DATA_PROCESSED, LOGS_DIR, LOG_FILE, XSENSOR_DATA_PATH, EXCEL_FILES_PATH, START_TIME, END_TIME, PRESSURE_THRESHOLD, PRESSURE_UNIT,MINIMUM_POINTS, SPECKLE_DIFF, SPECKLE_RATIO
    
    for k, v in kwargs.items():
        if k in globals() and v is not None:
            globals()[k] = v
    
    # Recompute dependent paths
    TEST_ROOT_DIR = Path(DATA_ROOT_DIR) / Path(TEST_ID)
    DATA_PROCESSED = Path(DATA_ROOT_DIR) / Path(TEST_ID) / "DATA" / "XSENSOR" / "Rear" / "Belt Position Debug"
    DATA_ROOT_DIR = TEST_ROOT_DIR / "DATA"
    LOGS_DIR = DATA_PROCESSED / "logs"
    LOG_FILE = LOGS_DIR / f"log_{TEST_ID}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    XSENSOR_DATA_PATH = DATA_ROOT_DIR / "XSENSOR" / "Rear" / "Frame Data"
    EXCEL_FILES_PATH = DATA_ROOT_DIR / "EXCEL"


def get_settings():
    """
    Return current configuration as a dictionary.

    Returns:
        dict: Current global configuration with keys such as:
            - PROJECT_ROOT_DIR, TEST_ID, DATA_ROOT_DIR
            - XSENSOR_DATA_PATH (frame CSV files), EXCEL_FILES_PATH
            - DATA_PROCESSED, LOGS_DIR, LOG_FILE
            - START_TIME, END_TIME, PRESSURE_THRESHOLD, PRESSURE_UNIT
            - MINIMUM_POINTS, SPECKLE_DIFF, SPECKLE_RATIO
            - ENABLE_LOGGING
    """
    return {
        "PROJECT_ROOT_DIR": PROJECT_ROOT_DIR,
        "TEST_ID": TEST_ID,
        "DATA_ROOT_DIR": DATA_ROOT_DIR,
        "XSENSOR_DATA_PATH": XSENSOR_DATA_PATH,
        "EXCEL_FILES_PATH": EXCEL_FILES_PATH,
        "DATA_PROCESSED": DATA_PROCESSED,
        "LOGS_DIR": LOGS_DIR,
        "START_TIME": START_TIME,
        "END_TIME": END_TIME,
        "PRESSURE_THRESHOLD": PRESSURE_THRESHOLD,
        "PRESSURE_UNIT": PRESSURE_UNIT,
        "LOG_FILE": LOG_FILE,
        "LOGS_DIR": LOGS_DIR,
        "ENABLE_LOGGING": ENABLE_LOGGING,
        "MINIMUM_POINTS": MINIMUM_POINTS,
        "SPECKLE_DIFF": SPECKLE_DIFF,
        "SPECKLE_RATIO": SPECKLE_RATIO
    }

def setup_environment():
    """
    Perform one-time environment setup after settings are finalized.
    - Create required directories
    """
    # Ensure directories exist
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
 