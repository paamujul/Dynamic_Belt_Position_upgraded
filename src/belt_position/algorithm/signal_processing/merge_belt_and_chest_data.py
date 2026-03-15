import pandas as pd
import belt_position.config.settings as cfg
from belt_position.services.logging_service import log

def merge_belt_chest(belt_data_interpolated: pd.DataFrame, chest_data: pd.DataFrame,  save_path: str | None = None):
    """
    Merge interpolated belt data with chest deflection data based on rounded time.

    Both `belt_data_interpolated` and `chest_data` are rounded to `cfg.TIME_PRECISION` 
    to align time points. The resulting DataFrame contains only rows where 
    `belt_position` is not NaN.

    Args:
        belt_data_interpolated (pd.DataFrame): Interpolated belt data with columns:
            - 'time' (float): Time in seconds.
            - 'belt_position' (float): Interpolated belt position.
            - 'frame' (int, optional): Original frame number.
        chest_data (pd.DataFrame): Chest deflection data with columns:
            - 'time' (float): Time in seconds.
            - 'chest_deflection' (float): Measured chest deflection.
        save_path (str or Path, optional): If provided, saves the merged DataFrame to an Excel file.

    Returns:
        pd.DataFrame: Merged DataFrame with columns:
            - 'time' (float): Time in seconds (from chest data).
            - 'chest_deflection' (float): Chest deflection.
            - 'belt_position' (float): Interpolated belt position.
            - 'frame' (int, optional): Original frame number from belt data.

    """
    chest_copy = chest_data.copy()
    chest_copy['time_rounded'] = chest_copy['time'].round(cfg.TIME_PRECISION)
    
    belt_copy = belt_data_interpolated.copy()
    belt_copy['time_rounded'] = belt_copy['time'].round(cfg.TIME_PRECISION)
    
    # Drop time column for belt data
    belt_copy = belt_copy.drop(columns=['time'])

    # Merge on rounded time
    merged = pd.merge(
        chest_copy,
        belt_copy,
        on='time_rounded',
        how='outer'
    ).sort_values('time_rounded').reset_index(drop=True)

    # Drop column time_rounded
    merged = merged.drop(columns=['time_rounded'])
    
    # Drop rows where belt_position is NaN
    merged = merged.dropna(subset=['belt_position']).reset_index(drop=True)
    
    merged = merged.rename(columns={'belt_position': 'unfiltered_belt_position'})
    
    if save_path is not None:
        merged.to_excel(save_path, index=False)
        
    return merged
