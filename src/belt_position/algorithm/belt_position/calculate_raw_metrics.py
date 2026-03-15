"""
Belt Position Metrics Module.

Calculates:
- Maximum belt position
- Belt position at maximum chest deflection

Also handles saving the metrics to Excel for debugging/tracking.
"""

import datetime
import pandas as pd
from belt_position.services.logging_service import log
import belt_position.config.settings as cfg

def calculate_unfiltered_belt_metrics(interpolated_belt_chest_data: pd.DataFrame) -> pd.DataFrame:
    """
    Compute belt position metrics and save to Excel.

    Args:
        interpolated_belt_chest_data (pd.DataFrame): DataFrame with columns
            ['frame', 'time', 'belt_position', 'chest_deflection'].

    Returns:
        pd.DataFrame: DataFrame containing the computed metrics for this run.
    """
    # Maximum belt position
    max_belt_row = interpolated_belt_chest_data.loc[
        interpolated_belt_chest_data['belt_position'].idxmax()
    ]
    max_belt_position = max_belt_row['belt_position']
    max_belt_time = max_belt_row['time']
    max_belt_frame = max_belt_row['frame']

    # Belt position at max chest deflection
    max_chest_row = interpolated_belt_chest_data.loc[
        interpolated_belt_chest_data['chest_deflection'].idxmax()
    ]
    max_chest_deflection = max_chest_row['chest_deflection']
    belt_at_max_cd = max_chest_row['belt_position']
    time_at_max_cd = max_chest_row['time']
    frame_at_max_cd = max_chest_row['frame']

    # Add timestamp ID for this run
    run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Prepare DataFrame for export
    metrics_df = pd.DataFrame([{
        "run_id": run_id,
        "test_id": cfg.TEST_ID,
        "Maximum belt position": max_belt_position,
        "time_bp": max_belt_time,
        "frame_bp": max_belt_frame,
        "max chest deflection": max_chest_deflection,
        "belt position at max CD": belt_at_max_cd,
        "time_cd": time_at_max_cd,
        "frame_cd": frame_at_max_cd
    }])

    # Save to Excel (append if file exists)
    metrics_path = cfg.DATA_PROCESSED / "debug_belt_position_raw_metrics.xlsx"
    if metrics_path.exists():
        existing_df = pd.read_excel(metrics_path)
        combined_df = pd.concat([existing_df, metrics_df], ignore_index=True)
    else:
        combined_df = metrics_df

    combined_df.to_excel(metrics_path, index=False)
    log(f"Saved belt position metrics → {metrics_path}")

    return metrics_df
