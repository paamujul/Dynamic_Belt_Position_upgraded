"""
Frame Outlier Removal Module

Provides a function to detect and remove pressure sensor frames with abrupt
pressure changes based on a standard deviation threshold.
"""
import pandas as pd

def remove_outlier_frames(df: pd.DataFrame, frame_col="frame", pressure_col="pressure", sigma_threshold=2):
    """
    Remove frames with abrupt pressure changes using standard deviation threshold.

    Args:
        df (pd.DataFrame): frame data with columns [frame, Row, Column, pressure].
        frame_col (str): Name of the frame column.
        pressure_col (str): Name of the pressure column.
        sigma_threshold (float): Number of standard deviations to define outliers.

    Returns:
        cleaned_df (pd.DataFrame): DataFrame with outlier frames removed.
        summary (dict): Dictionary with original, removed, and remaining frame counts.
    """
    # Compute mean pressure for each frame
    frame_averages = (
        df.groupby(frame_col, as_index=False)
        [pressure_col].mean()
        .rename(columns={pressure_col: "avg_pressure"})
    )

    # Compute difference with previous frame
    frame_averages["prev_diff"] = frame_averages["avg_pressure"].diff()
    # Compute difference with next frame
    frame_averages["next_diff"] = frame_averages["avg_pressure"].shift(-1) - frame_averages["avg_pressure"]

    # Define threshold for outlier detection
    pressure_threshold = frame_averages["avg_pressure"].std(skipna=True) * sigma_threshold

    # Identify frames where pressure changes exceed threshold
    frames_to_remove = frame_averages.loc[
        (frame_averages["prev_diff"].abs() > pressure_threshold)
        | (frame_averages["next_diff"].abs() > pressure_threshold),
        frame_col,
    ].tolist()

    # Remove outlier frames from original data
    cleaned_df = df[~df[frame_col].isin(frames_to_remove)].copy()

    # Summary of removal for debug
    summary = {
        "original_frames": df[frame_col].nunique(),
        "removed_frames": len(frames_to_remove),
        "remaining_frames": cleaned_df[frame_col].nunique(),
    }

    return cleaned_df, summary
