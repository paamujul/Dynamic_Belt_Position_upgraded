"""
Frame Data Merging Module

Provides functions to merge cleaned frame pressure data with baseline sensor coordinates
and compute derived columns such as:
    - 'binary_value' indicating presence of pressure
    - 'time' adjusted relative to frame zero

Main functions:
- merge_frame_with_baseline: Merge frame data with baseline coordinates and add derived column for pressure.
"""

from belt_position.services.logging_service import log
import pandas as pd
import numpy as np
import belt_position.config.settings as cfg


def merge_frame_with_baseline(frame_data: pd.DataFrame, baseline: pd.DataFrame, save_path: str | None=None) -> pd.DataFrame:
    """
    Merge cleaned frame pressure data with baseline sensor coordinates and compute derived columns.

    This function:
    - Merges Pressure sensor long-format data with baseline coordinates on ['Row', 'Column'].
    - Adds 'binary_value' column: 1 if pressure > 0, else 0.
    - Adjusts 'time' relative to the frame closest to time zero.
    - Ensures 'frame' and 'Row' are integers.

    Args:
        frame_data (pd.DataFrame): Long-format pressure sensor data with columns
            ['frame', 'time', 'Row', 'Column', 'pressure'].
        baseline (pd.DataFrame): Baseline coordinates with columns
            ['Row', 'Column', 'X', 'Y', 'Z'].

    Returns:
        pd.DataFrame: Merged DataFrame including baseline coordinates, 'binary_value',
        and adjusted 'time'.

    Raises:
        Exception: If merging or processing fails, the error is logged and re-raised.
    """
    try:
       
        baseline_subset = baseline[["Row", "Column", "X", "Y", "Z"]].copy()
        baseline_subset = baseline_subset.dropna()
        baseline_subset = baseline_subset[baseline_subset["Row"] != 0]
        
        # Merge baseline coordinates into frame data
        merged = frame_data.merge(baseline_subset, on=["Row", "Column"], how="left")

        merged["binary_value"] = (merged["pressure"] > 0).astype(int)

        # Find frame corresponding to time zero
        frame_zero_idx = merged["time"].abs().idxmin()
        frame_zero = merged.loc[frame_zero_idx, "frame"]

        # Adjust time before 0.0 to negative values
        merged["time"] = np.where(
            merged["frame"] < frame_zero,
            (merged["frame"] - frame_zero) / 3300,
            merged["time"]
        )
        
        merged["frame"] = merged["frame"].astype(int)
        merged["Row"] = merged["Row"].astype(int)

        log(f"Frame closest to time zero = {frame_zero}")
        if cfg.ENABLE_DEBUG:
            log(f"Sample rows after merging baseline with frame data: \n {merged.iloc[2:18000:1730]}")
        
        if save_path is not None:
            merged.to_csv(save_path, index=False)
            log(f"Saved merged frame and baseline data")
            
        return merged

    except Exception as e:
        log(f"Error merging data: {e}")
        raise