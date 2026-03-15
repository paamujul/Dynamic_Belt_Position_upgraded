"""
Data loading and preprocessing module.

Provides functions to:
- Load baseline sensor data, chestpot coordinates, belt positions from Excel.
- Load chest deflection time series from Excel.
- Load individual and all frame CSV files into long-format DataFrames.
- Combine frame data with baseline for downstream processing.

Main functions:
- load_baseline_from_file
- load_chest_deflection
- read_frame_csv
- load_frame_data_and_pressure_unit
- load_all_data
- load_vehicle_info_file
"""

from pathlib import Path
import numpy as np
import pandas as pd
import belt_position.config.settings as cfg
from belt_position.services.data_loading.discover_data import list_csv_files
from belt_position.services.logging_service import log
from belt_position.services.exceptions import DataNotFoundError
from belt_position.services.data_loading.discover_data import find_excel_file
from belt_position.services.data_loading.discover_data import check_belt_and_chest_files
from belt_position.algorithm.units.resolve_pressure import TO_KPA, CANONICAL_UNIT


def load_baseline_from_file(belt_file_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load baseline sensor data and chestpot coordinates from a belt positions Excel file.

    Args:
        belt_file_path (str): Path to the belt positions Excel file.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]:
            - baseline: DataFrame containing pressure sensor baseline values with columns ['Row', 'Column', 'X', 'Y', 'Z'].
            - chestpot: DataFrame containing dummy thorax coordinates ['x', 'y', 'z'].

    Raises:
        DataNotFoundError: If the file path is missing or invalid.
        Exception: If reading Excel fails.
    """
    try:
        if not belt_file_path:
            raise DataNotFoundError("Belt position file not found or multiple files match the pattern.")

        baseline = pd.read_excel(belt_file_path, sheet_name="Pressure sensor baseline")
        # Keep only first 5 columns [Row,Column,X,Y,Z]
        baseline = baseline.iloc[:, :5]
        baseline = baseline.dropna(subset=["X", "Y", "Z"])
        
        n_rows = len(baseline)
        pattern = np.repeat(np.arange(0, 49), 37)  # base pattern
        baseline.iloc[:, 0] = np.resize(pattern, n_rows)  # auto-recycle

        # Drop rows where Row or Column is 0
        baseline = baseline[(baseline["Row"] != 0) & (baseline["Column"] != 0)]
    
        log(f"Loaded baseline sheet with shape {baseline.shape}")

        # Chest pot: C13:E13 (0-indexed: rows 12, cols 2-4)
        chestpot = pd.read_excel(
            belt_file_path,
            sheet_name="Dummy thorax coordinate system",
            usecols="C:E",
            skiprows=12,
            nrows=1,
            header=None
        )
        chestpot.columns = ["x", "y", "z"]
        log(f"Loaded chestpot: {chestpot.iloc[0].to_dict()}")
        
        return baseline, chestpot

    except Exception as e:
        log(f"Error loading baseline data from {belt_file_path}: {e}")
        raise


def load_chest_deflection(file_path: Path | None = None, folder: Path = cfg.EXCEL_FILES_PATH) -> pd.DataFrame:
    """
    Load chest deflection data from an Excel file.

    The function either uses a provided `file_path` or searches the given `folder`.

    Args:
        file_path (Path | None): Direct path to the Excel file. If None, searches the folder.
        folder (Path): Folder to search for the chest deflection Excel file if `file_path` is None.

    Returns:
        pd.DataFrame: Loaded chest deflection data.

    Raises:
        DataNotFoundError: If the file cannot be found.
        Exception: If reading the Excel file fails.
    """
    try:
        if file_path is None:
            file_path = find_excel_file("deflection", folder)

        if not file_path:
            raise DataNotFoundError("Chest deflection file not found.")

        # Read first (only) sheet
        chest_def = pd.read_excel(file_path)

        if chest_def.shape[1] < 2:
            raise ValueError("Expected at least 2 columns: time and chest deflection")

        # Rename by position
        chest_def = chest_def.iloc[:, :2]
        chest_def.columns = ["time", "chest_deflection"]
        
        # Flip sign
        chest_def["chest_deflection"] *= -1
        log(f"Loaded chest deflection data with shape {chest_def.shape}")
        return chest_def

    except Exception as e:
        log(f"Error loading chest deflection data: {e}")
        raise


def read_frame_csv(file_path: Path) -> pd.DataFrame:
    """
    Load a single frame CSV file and return it in long-format.

    The returned DataFrame contains frame, time, row, column, and pressure values.

    Args:
        file_path (Path): Path to the frame CSV file.

    Returns:
        pd.DataFrame: Long-format DataFrame with columns ['frame', 'time', 'Row', 'Column', 'pressure'].
        str: Pressure unit

    Raises:
        ValueError: If required metadata lines ("FRAME" or "Time") or the 'SENSELS' marker are missing.
        Exception: For any other file reading or parsing errors.
    """
    try:
        with open(file_path, encoding='latin1') as f:
            # lines = [next(f) for _ in range(10)]
            lines = f.readlines()
            
        # Normalize lines
        stripped = [line.strip().replace('"', '') for line in lines]
        stripped = [line.strip().replace(':', '') for line in stripped]
        

        # Extract metadata
        frame_line = next((l for l in stripped if l.startswith("FRAME,")), None)
        time_line = next((l for l in stripped if l.startswith("Time,")), None)
        
        
        if frame_line is None or time_line is None:
            raise ValueError(f"Missing FRAME, Time or Unit line in {file_path.name}")

        frame_number = int(frame_line.split(",")[1])
        frame_time = float(time_line.split(",")[1])
        

        
        # Find line containing SENSELS (with or without quotes, case-insensitive)
        sensel_line_index = next(
            (i for i, line in enumerate(lines) if "SENSELS" in line.upper().replace('"', '')),
            None,
        )
        if sensel_line_index is None:
            raise ValueError(f"'SENSELS' marker not found in {file_path.name}")

        sensel_start_idx = sensel_line_index + 1

        data = pd.read_csv(
            file_path,
            skiprows=sensel_start_idx,
            nrows=48,
            usecols=range(36),
            header=None,
        )
        
        data_long = data.stack().reset_index()
        data_long.columns = ["Row", "Column", "pressure"]
        data_long["Row"] += 1
        data_long["Column"] += 1
        data_long["frame"] = frame_number
        data_long["time"] = frame_time

        return data_long[["frame", "time", "Row", "Column", "pressure"]]

    except Exception as e:
        log(f"Error reading CSV {file_path}: {e}")
        raise
    
   
def load_frame_data_and_pressure_unit(folder: Path = cfg.XSENSOR_DATA_PATH) -> tuple[pd.DataFrame, str | None]:
    """
    Load all pressure sensor CSV files and extract the pressure unit from the first file.

    Args:
        folder (Path | None): Folder containing pressure Sensor CSV files.
                              If None, uses settings['XSENSOR_DATA_PATH'].

    Returns:
        tuple:
        - pd.DataFrame: Combined pressure sensor frame data with columns ['frame', 'time', 'Row', 'Column', 'pressure'].
        - str: Unit of pressure | None
    """

    log(f"Loading Pressure Sensor data")

    # Discover CSV files
    csv_files = list_csv_files(folder)
    if not csv_files:
        raise DataNotFoundError(f"No CSV files found in {folder}")


    # 1. Load all CSVs
    all_data = []
    for fpath in csv_files:
        all_data.append(read_frame_csv(fpath))

    frame_data = pd.concat(all_data, ignore_index=True)
    log(f"Loaded {len(csv_files)} frame CSV files")
    
    # 2. Validate time 0 exists
    if not (frame_data["time"] == 0.0).any():
        raise DataNotFoundError(
            "Reference frame with exact time 0.0 not found in pressure sensor data."
        )

    # 3. Extract pressure unit from first file
    unit = None
    first_file = csv_files[0]

    try:
        with open(first_file, "r") as f:
            for line in f:
                clean = line.strip().replace('"', '').replace(':', '')
                if clean.startswith("Units,"):
                    parts = clean.split(',')
                    if len(parts) > 1:
                        unit = parts[1].strip()
                    log(f"Extracted pressure unit: {unit}","DEBUG")
                    break
    except Exception as e:
        log(f"Error reading pressure unit from {first_file}: {e}","ERROR")

    # Normalize pressure to canonical unit (kPa)
    if unit not in TO_KPA:
        raise ValueError(f"Unsupported pressure unit in frame data: {unit}","ERROR")

    frame_data["pressure"] = frame_data["pressure"] * TO_KPA[unit]

    if str(unit).lower() != str(CANONICAL_UNIT).lower():
        log(f"Normalized pressure data from {unit} to {CANONICAL_UNIT}","DEBUG")

    return frame_data, CANONICAL_UNIT


def load_all_data(folder: Path = cfg.DATA_ROOT_DIR) -> dict[str, pd.DataFrame]:
    """
    Load all relevant test data from a folder.

    Data includes:
    - Baseline sensor values
    - Chestpot coordinates
    - Chest deflection measurements
    - Combined per-frame CSV data

    Args:
        folder (Path): Path to the test data folder containing Excel and CSV files.

    Returns:
        dict[str, pd.DataFrame]: Dictionary with keys:
            - 'baseline': Sensor baseline DataFrame
            - 'chestpot': Chestpot coordinates DataFrame
            - 'chest_deflection': Chest deflection DataFrame
            - 'frame_data': Combined frame CSV data DataFrame
            - 'pressure_unit': Unit of pressure

    Raises:
        DataNotFoundError: If required files are missing.
        Exception: If any of the loading steps fail.
    """
    log("Loading data for {}".format(cfg.TEST_ID))
    try:
        # Find belt and chest files once
        belt_file, chest_file = check_belt_and_chest_files(folder)

        # Load baseline and belt metrics
        baseline, chestpot= load_baseline_from_file(belt_file)
        
        if cfg.ENABLE_DEBUG:
            baseline.to_excel(f"{cfg.DATA_PROCESSED}/debug_cleaned_baseline.xlsx", index=False)
    
        # Load chest deflection using discovered file
        chest_deflection = load_chest_deflection(file_path=chest_file)
        
        frame_data, pressure_unit = load_frame_data_and_pressure_unit(cfg.XSENSOR_DATA_PATH)

        return {
            "baseline": baseline,
            "chestpot": chestpot,
            "chest_deflection": chest_deflection,
            "frame_data": frame_data,
            "pressure_unit":pressure_unit
        }

    except Exception as e:
        log(f"Error loading all data: {e}")
        raise


def load_vehicle_info_file(folder_path: Path) -> str:
    """
    Load vehicle information from 'info.txt' in the given folder.

    Args:
        folder_path (Path): Path to the folder containing 'info.txt'.

    Returns:
        str: The content of 'info.txt' (vehicle info), or empty string if not found or on error.
    """
    try:
        folder = Path(folder_path)
        info_path = folder / "info.txt"

        if info_path.exists() and info_path.is_file():
            with open(info_path, 'r', encoding='utf-8') as f:
                line = f.readline().strip()
            return line
        else:
            log(f"Info file not found in folder: {folder_path}")
            return ""
    except Exception as e:
        log(f"Error reading info file in {folder_path}: {e}")
        return ""
