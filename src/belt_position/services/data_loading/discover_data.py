"""
Data Discovery and Validation Module

Provides utility functions to locate and validate test data files.
Includes methods to find Excel and CSV files, and to check for required info files.
"""
from pathlib import Path
import belt_position.config.settings as cfg
from belt_position.services.logging_service import log


def find_excel_file(keyword: str, folder: Path = cfg.EXCEL_FILES_PATH) -> Path | None:
    """
    Search for the first Excel file (.xlsx or .xlsm) in a folder whose name contains the given keyword.

    Args:
        keyword (str): Keyword to match in Excel filenames.
        folder (Path): Folder to search. Defaults to EXCEL_FILES_PATH.

    Returns:
        Path | None: Full path to the matching Excel file, or None if not found.
    """
    try:
        if not folder.exists():
            raise FileNotFoundError(f"Folder does not exist: {folder}")
        
        for ext in ("*.xlsx", "*.xlsm"):
            excel_files = list(folder.rglob(ext))
            for file in excel_files:
                if keyword.lower() in file.name.lower():
                    return file
        
        log(f"No Excel file found for '{keyword}' in folder {folder}")
        return None

    except Exception as e:
        log(f"Error searching for Excel file '{keyword}' in {folder}: {e}")
        return None


def check_belt_and_chest_files(folder: Path = cfg.EXCEL_FILES_PATH) -> tuple[Path | None, Path | None]:
    """
    Locate the belt positions and chest deflection Excel files in the specified folder.

    Args:
        folder (Path): Folder to search. Defaults to EXCEL_FILES_PATH.

    Returns:
        tuple[Path | None, Path | None]: Paths to:
            - belt_file: Belt positions Excel file, or None if not found.
            - chest_def_file: Chest deflection Excel file, or None if not found.
    """
    try:
        belt_file = find_excel_file("rear", folder)
        chest_def_file = find_excel_file("deflection", folder)
        if not belt_file:
            log("Belt positions file not found.", "ERROR")
        if not chest_def_file:
            log("Chest deflection file not found.", "ERROR")
        return belt_file, chest_def_file

    except Exception as e:
        log(f"Error retrieving belt/chest files from {folder}: {e}")
        return None, None


def list_csv_files(folder: Path = cfg.XSENSOR_DATA_PATH) -> list[Path]:
    """
    List all CSV files in the XSensor frames data folder, sorted alphabetically.

    Args:
        folder (Path): Folder containing CSV files. Defaults to XSENSOR_DATA_PATH.

    Returns:
        list[Path]: List of CSV file paths. Empty list if folder does not exist or an error occurs.
    """
    try:
        if not folder.exists():
            raise FileNotFoundError(f"Folder containing CSV files does not exist: {folder}")
        
        csv_files = sorted(folder.rglob("*.csv"))
        return csv_files

    except Exception as e:
        log(f"ListCSV: Error finding CSV files in {folder}: {e}","ERROR")
        return []
    