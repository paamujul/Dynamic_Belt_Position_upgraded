import os
from pathlib import Path
import belt_position.config.settings as cfg
from belt_position.services.logging_service import log

def clean_side_effects():
    """
    Clean up side effects: all variations of 'chest deflection.xlsx'
    regardless of case.
    """
    try:
        folder = Path(cfg.EXCEL_FILES_PATH)
        pattern = "chest deflection.xlsx"

        # Iterate all files in the folder
        for file in folder.iterdir():
            if file.is_file() and file.name.lower() == pattern.lower():
                os.remove(file)
                log(f"File '{file}' has been deleted.")
    except Exception as e:
        log(f"Error cleaning side-effect files in '{folder}': {e}", "ERROR")