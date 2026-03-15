"""
Main execution script for the belt position estimation workflow.

Pipeline:
1. Load all raw datasets from configured paths.
2. Clean pressure sensor frame data.
3. Merge cleaned pressures with baseline metadata.
4. Run belt position calculations.
5. Save intermediate and final outputs to the processed directory.
"""

import argparse
import pandas as pd
import warnings
from belt_position.algorithm.belt_position.calculate_raw_metrics import (
    calculate_unfiltered_belt_metrics,
)
from belt_position.algorithm.signal_processing.merge_belt_and_chest_data import (
    merge_belt_chest,
)
from belt_position.algorithm.signal_processing.trim_channels import trim_channels
from belt_position.services.cleanup import clean_side_effects
from belt_position.services.logging_service import log
from belt_position.services.data_loading.load_data import load_all_data
from belt_position.services.data_loading.merge_baseline_frame_data import (
    merge_frame_with_baseline,
)
from belt_position.algorithm.data_cleaning.clean_frame_data import clean_frame_data
from belt_position.algorithm.workflow.driver import run_frame_wise_belt_estimation
from belt_position.algorithm.signal_processing.interpolate_belt_position import (
    interpolate_belt_positions,
)
from belt_position.algorithm.visualization.animate_estimated_belt_position import (
    create_belt_position_animations,
)


# ------SETUP-----
pd.set_option("future.no_silent_downcasting", True)
warnings.filterwarnings("ignore", category=FutureWarning)


def run_belt_position_workflow():
    """
    Execute the full belt position estimation pipeline.

    Steps:
        1. Load raw data.
        2. Clean pressure sensor frame data.
        3. Merge cleaned data with baseline metadata.
        4. Estimate belt position frame-wise.
        5. Create animation of belt positions.
        6. Trim belt and chest channels to common time window.
        7. Interpolate belt data.
        8. Merge interpolated belt data with chest data.
        9. Optional: calculate raw belt metrics.
        10. Cleanup temporary files and side effects.

    Side Effects:
        - Saves cleaned, merged, interpolated data, and animation to the processed directory.
        - Logs progress at each pipeline stage.

    Returns:
        None
    """
    # ------------------------------------------------------------
    # 1. Load raw data
    # ------------------------------------------------------------
    log("========= Loading all data =========")
    data = load_all_data(cfg.DATA_ROOT_DIR)

    # ------------------------------------------------------------
    # 2. Clean pressure sensor frame data
    # ------------------------------------------------------------
    log("========= Cleaning Frame Data =========")
    raw_frame_df = data["frame_data"]
    save_path = cfg.DATA_PROCESSED / "cleaned_frame_data.csv"
    cleaned_frame_df = clean_frame_data(raw_frame_df)

    # ------------------------------------------------------------
    # 3. Merge cleaned data with baseline metadata
    # ------------------------------------------------------------
    log("========= Merging Cleaned Frame Data with Baseline =========")
    save_path = cfg.DATA_PROCESSED / "merged_frame_and_baseline_data.csv"
    frame_baseline_merged_df = merge_frame_with_baseline(
        cleaned_frame_df, data["baseline"]
    )

    # ------------------------------------------------------------
    # 4. Belt Position Estimation
    # ------------------------------------------------------------
    log("========= Starting Belt Position Estimation =========")
    save_path = cfg.DATA_PROCESSED / "vertical_distances.xlsx"
    belt_analysis_by_frame, vertical_distances_df = run_frame_wise_belt_estimation(
        frame_baseline_merged_df,
        data["chestpot"],
        data["pressure_unit"],
        save_path=save_path,
    )
    log(f"Processed {len(belt_analysis_by_frame)} frames.")

    # ------------------------------------------------------------
    # 5. Create Animation
    # ------------------------------------------------------------
    log("========= Creating Belt Position Video =========")
    frames_dir = cfg.DATA_PROCESSED / "belt_position_plots"
    output_dir = cfg.DATA_ROOT_DIR / "EXCEL"
    create_belt_position_animations(frames_dir, output_dir, fps=10)

    # ------------------------------------------------------------
    # 6. Trim belt position and chest data channels
    # ------------------------------------------------------------
    log("========= Trimming Channels to Input Time =========")
    belt_data = vertical_distances_df.copy()
    chest_data = data["chest_deflection"].copy()
    belt_data, chest_data = trim_channels(belt_data, chest_data)

    # ------------------------------------------------------------
    # 7. Interpolation
    # ------------------------------------------------------------
    log("========= Interpolating Belt Data  =========")
    save_path = cfg.DATA_PROCESSED / "interpolated_belt_data.xlsx"
    interpolated_belt_data = interpolate_belt_positions(belt_data)

    # ------------------------------------------------------------
    # 8. Merge interpolated belt data with chest data
    # ------------------------------------------------------------
    log("========= Merging Interpolated Belt Data with Chest Data =========")
    interpolated_belt_chest_data = merge_belt_chest(
        interpolated_belt_data,
        chest_data,
        cfg.DATA_PROCESSED / "interpolated_belt_chest_data.xlsx",
    )

    # ------------------------------------------------------------
    # 9. Calculate Maximum Belt & Belt at Max Chest Deflection
    # ------------------------------------------------------------
    if cfg.ENABLE_DEBUG:
        log("========= Calculating Raw Belt Position Metrics =========")
        calculate_unfiltered_belt_metrics(interpolated_belt_chest_data)

    log("========= Cleanup =========")
    clean_side_effects()

    log("========= You can close this window now =========")


def parse_cli():
    """
    Parse command-line arguments for belt position workflow.

    Command-line arguments can override config settings.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Belt Position Calculation")

    parser.add_argument(
        "--test-id", type=str, required=True, help="Override TEST_ID from config"
    )
    parser.add_argument(
        "--data-path",
        type=str,
        required=False,
        help="Override DATA_ROOT_DIR from config",
    )
    parser.add_argument(
        "--start-time",
        type=float,
        required=False,
        help="Override START_TIME from config",
    )
    parser.add_argument(
        "--end-time", type=float, required=False, help="Override END_TIME from config"
    )
    parser.add_argument(
        "--pressure-threshold",
        type=float,
        required=False,
        help="Override pressure threshold from config",
    )
    parser.add_argument(
        "--pressure-unit", required=False, help="Override pressure unit from config"
    )
    parser.add_argument(
        "--minimum-points",
        type=int,
        required=False,
        help="Override minimum points from config",
    )
    parser.add_argument(
        "--speckle-diff",
        type=float,
        required=False,
        help="Override speckle diff from config",
    )
    parser.add_argument(
        "--speckle-ratio",
        type=float,
        required=False,
        help="Override speckle ratio from config",
    )
    return parser.parse_args()


if __name__ == "__main__":
    import belt_position.config.settings as cfg

    # Parse CLI arguments
    args = parse_cli()

    # Convert args to dict for overrides
    overrides = {
        "TEST_ID": args.test_id,
        "DATA_ROOT_DIR": args.data_path,
        "START_TIME": args.start_time,
        "END_TIME": args.end_time,
        "PRESSURE_THRESHOLD": args.pressure_threshold,
        "PRESSURE_UNIT": args.pressure_unit,
        "MINIMUM_POINTS": args.minimum_points,
        "SPECKLE_DIFF": args.speckle_diff,
        "SPECKLE_RATIO": args.speckle_ratio,
    }

    cfg.update_settings(**{k: v for k, v in overrides.items()})
    cfg.setup_environment()

    from belt_position.services.logging_service import setup_logging

    setup_logging()

    run_belt_position_workflow()
