import pandas as pd
import numpy as np
import belt_position.config.settings as cfg
from belt_position.services.logging_service import log

def interpolate_belt_positions(belt_data: pd.DataFrame, save_path: str | None = None) -> pd.DataFrame:
    """
    Interpolates belt positions onto a high-frequency uniform time vector.

    A 10 kHz time vector is generated between `cfg.START_TIME` and `cfg.END_TIME`. 
    Belt positions are interpolated linearly onto this vector without extrapolation.
    Times outside the original belt data range are assigned NaN. Original frame numbers
    are mapped to the interpolated times based on rounding to `cfg.TIME_PRECISION`.

    Args:
        belt_data (pd.DataFrame): Input belt measurements. Must contain columns:
            - 'time' (float): Measurement time in seconds.
            - 'frame' (int): Original frame number.
            - 'distance' (float): Belt position (e.g., vertical distance in mm).
        save_path (str or Path, optional): Path to save an Excel file with two sheets:
            "Before_Interpolation" (original data) and "After_Interpolation" (interpolated data).

    Returns:
        pd.DataFrame: Interpolated belt positions with columns:
            - 'time' (float): High-frequency time vector (seconds).
            - 'belt_position' (float): Interpolated belt positions.
            - 'time_rounded' (float): Time rounded to `cfg.TIME_PRECISION` for frame mapping.
            - 'frame' (int): Original frame number corresponding to the interpolated time (NaN if no match).

    Raises:
        ValueError: If `belt_data` is missing required columns.
    """
    
    # Generate a 10kHz frequency time vector using the trimmed global time window
    new_time_vector = np.linspace(
        cfg.START_TIME,
        cfg.END_TIME,
        num=int((cfg.END_TIME - cfg.START_TIME) * 10000) + 1  # 10 kHz sample rate
    )
    
    # log(f"First 10 rows of new time vector:\n {new_time_vector[10]}")

    # Interpolation
    interpolated_values = np.interp(
        new_time_vector,
        belt_data['time'].to_numpy(),
        belt_data['distance'].to_numpy(),
        left = np.nan,
        right = np.nan
    )
    
    # Create DataFrame with original times and frames
    original_df = belt_data[['time', 'frame']].copy()
    original_df = original_df.rename(columns={'frame': 'frame_original'})
    
    # Create interpolated DataFrame
    interpolated = pd.DataFrame({'time': new_time_vector})
    interpolated['belt_position'] = interpolated_values
    interpolated['time_rounded'] = interpolated['time'].round(cfg.TIME_PRECISION)
    
    # Merge original frames onto interpolated DataFrame
    original_df['time_rounded'] = original_df['time'].round(cfg.TIME_PRECISION)
    time_to_frame = dict(zip(original_df['time_rounded'], original_df['frame_original']))
    interpolated['frame'] = interpolated['time_rounded'].map(time_to_frame)
    
    interpolated = interpolated.dropna(subset=['belt_position']).reset_index(drop=True)
    
    if save_path is not None:
        with pd.ExcelWriter(save_path, engine='openpyxl', mode='w') as writer:
            belt_data.to_excel(writer, sheet_name="Before_Interpolation", index=False)
            interpolated.to_excel(writer, sheet_name="After_Interpolation", index=False)

    return interpolated
