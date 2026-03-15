"""
Frame Data Cleaning Module

Provides a full data cleaning pipeline for Frame pressure data, including:
1. Frame outlier removal
2. Speckle detection and smoothing

The output is a cleaned DataFrame ready for downstream belt position calculations.
"""
import pandas as pd
from belt_position.algorithm.data_cleaning.remove_outlier_frames import remove_outlier_frames
from belt_position.algorithm.data_cleaning.process_speckles import detect_speckles, filter_speckles
from belt_position.services.logging_service import log
import belt_position.config.settings as cfg

def clean_frame_data(df: pd.DataFrame, save_path: str | None = None):
    """
    Frame data cleaning pipeline:
    1. Frame outlier removal using `remove_outlier_frames`
    2. Speckle detection and smoothing using `speckle_find` and `speckle_filter`


     Args:
        df (pd.DataFrame): Raw Frame data with columns 
            ['frame', 'Row', 'Column', 'pressure'].

    Returns:
        final_df (pd.DataFrame): Fully cleaned frame data.
        summary (dict): Summary of cleaning steps including frame removal and speckles filtered.
    """
   
    # Step 1: Frame removal
    cleaned_df, frame_summary = remove_outlier_frames(df)

    # Step 2: Speckle filtering
    settings = cfg.get_settings()
    speckle_diff = settings['SPECKLE_DIFF']
    speckle_ratio = settings['SPECKLE_RATIO']
    speckles = detect_speckles(cleaned_df, diff_threshold=speckle_diff, ratio_threshold=speckle_ratio)
    xs_rows, xs_cols = cleaned_df["Row"].max(), cleaned_df["Column"].max()
    filtered_speckles = filter_speckles(speckles, cleaned_df, xs_rows, xs_cols)

    final_df = (
        cleaned_df.merge(filtered_speckles, on=["frame", "Row", "Column"], how="left")
        .assign(
            pressure=lambda x: x["pressure_mn"].combine_first(x["pressure"])
        )
        .drop(columns=["pressure_mn"], errors="ignore")
    )

    summary = {
        **frame_summary,
        "speckles_filtered": len(filtered_speckles)
    }
    
    log(summary)
    
     # Save to CSV if requested
    if save_path is not None:
        final_df.to_csv(save_path, index=False)
        log(f"Saved cleaned Frame data → {save_path}")

    return final_df
