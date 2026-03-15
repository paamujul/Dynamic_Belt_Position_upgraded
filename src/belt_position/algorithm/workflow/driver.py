"""
Module to loop over frames to produce belt position calculations and plots.
"""
import shutil
import pandas as pd
import matplotlib.pyplot as plt    
import numpy as np
from pathlib import Path
from belt_position.algorithm.belt_position.estimate_belt_position import estimate_belt_position
from belt_position.services.logging_service import log
import belt_position.config.settings as cfg
from belt_position.algorithm.units.resolve_pressure import resolve_pressure_threshold

def run_frame_wise_belt_estimation(frame_baseline_merged_df : pd.DataFrame, chestpot : pd.DataFrame, pressure_unit: str, save_path: str | None = None):

    
    """
    Run frame-wise belt position detection and generate plots.

    This function processes each frame of cleaned frame data, estimates the left, right, 
    and center lines of the belt, and visualizes the results as scatter plots. 
    It stores vertical distances from chestpot to belt for each frame.

    Args:
        - frame_baseline_merged_df (pd.DataFrame): Cleaned frame data merged with baseline data.
        - chestpot (pd.DataFrame or array): Chest pot coordinates.
        - pressure_unit (str): Pressure unit detected in frame csv files
        - save_path (str | None, optional): Path to save estimated vertical distances
        
    Outputs / Side Effects:
        - belt position plots in belt_position_plots folder

    Returns:
        - belt_position_by_frame (dict): Dictionary keyed by frame number containing belt position information (left/right/final line points, center line, slopes, intercepts, vertical_distance).
        - vertical_distances_df (pd.DataFrame): DataFrame containing vertical distances from chestpot to belt for each frame. Columns: ['frame', 'time', 'distance'].
    
    Side Effects:
        - Creates a folder `belt_position_plots` under `cfg.DATA_PROCESSED` and saves per-frame PNG plots.
   
    """
    # -------------------- Parameters --------------------
    threshold = resolve_pressure_threshold(cfg.PRESSURE_UNIT, cfg)
    total_rows = 48
    total_cols = 36
    min_points = cfg.MINIMUM_POINTS
    n_samples = 200
    start_time = cfg.START_TIME
    end_time = cfg.END_TIME

    chest_pot_df = pd.DataFrame(chestpot)
    all_frames = np.sort(frame_baseline_merged_df['frame'].unique())
    all_times = np.sort(frame_baseline_merged_df['time'].unique())
    start_row = np.searchsorted(all_times, start_time)
    end_row = np.searchsorted(all_times, end_time, side='right') - 1
    run_frames = all_frames[start_row:end_row+1]

    global_min_pressure = frame_baseline_merged_df['pressure'].min()
    global_max_pressure = frame_baseline_merged_df['pressure'].max()

    # -------------------- Storage --------------------
    vertical_distances_df = pd.DataFrame(columns=['frame', 'time', 'distance'])
    belt_position_by_frame = {}
    left_line_data_list = {}
    right_line_data_list = {}
    plots_folder = cfg.DATA_PROCESSED / "belt_position_plots"
    if plots_folder.exists():
        shutil.rmtree(plots_folder)
    plots_folder.mkdir(parents=True, exist_ok=True)


    # -------------------- Loop through frames --------------------
    for frame_number in run_frames:
        try:
            log(f"Processing frame: {frame_number}")
            frame_data = frame_baseline_merged_df[frame_baseline_merged_df['frame'] == frame_number]

            # DEBUG BAD FRAME DATA
            expected_rows = set(range(1, total_rows+1))
            expected_cols = set(range(1, total_cols+1))
            extra_points = frame_data[~frame_data['Row'].isin(expected_rows) | ~frame_data['Column'].isin(expected_cols)]
            log(extra_points[['Row', 'Column', 'Y', 'Z', 'pressure']],"DEBUG")

            if (frame_data['pressure'] > threshold).sum() > 0:
                belt_position = estimate_belt_position(
                    frame_baseline_merged_df,
                    frame_number,
                    chest_pot_df.values[0],
                    threshold,
                    min_points,
                    n_samples,
                    total_rows,
                    total_cols
                )

                if belt_position is None:
                    log(f"Skipping frame {frame_number} due to insufficient data")
                    continue

                belt_position_by_frame[frame_number] = belt_position

                # Merge center line with frame data
                selected_centers = belt_position['center_line'].copy()
                selected_centers['is_center'] = True

                filtered_result_with_centers = frame_data.merge(
                    selected_centers[['Y', 'Z', 'is_center']], on=['Y', 'Z'], how='left'
                )
                filtered_result_with_centers['is_center'] = filtered_result_with_centers['is_center'].fillna(False)

                # Left and right fitted lines
                left_line_data = pd.DataFrame({
                    'Y': [belt_position['final_left_line']['points']['Y'].min(),
                        belt_position['final_left_line']['points']['Y'].max()],
                    'Z': [belt_position['left_slope'] * belt_position['final_left_line']['points']['Y'].min() + belt_position['left_intercept'],
                        belt_position['left_slope'] * belt_position['final_left_line']['points']['Y'].max() + belt_position['left_intercept']]
                })
                right_line_data = pd.DataFrame({
                    'Y': [belt_position['final_right_line']['points']['Y'].min(),
                        belt_position['final_right_line']['points']['Y'].max()],
                    'Z': [belt_position['right_slope'] * belt_position['final_right_line']['points']['Y'].min() + belt_position['right_intercept'],
                        belt_position['right_slope'] * belt_position['final_right_line']['points']['Y'].max() + belt_position['right_intercept']]
                })

                left_line_data_list[str(frame_number)] = left_line_data
                right_line_data_list[str(frame_number)] = right_line_data

                # -------------------- Plotting --------------------
                fig, ax = plt.subplots(figsize=(6, 6))

                # Define consistent colormap and limits
                import matplotlib.colors as mcolors
                colors = ["darkblue", "blue", "yellow", "red"]
                positions = [0, 0.05, 0.2, 1]
                cmap = mcolors.LinearSegmentedColormap.from_list("pressure_rstyle", list(zip(positions, colors)))
                norm = mcolors.Normalize(vmin=global_min_pressure, vmax=global_max_pressure)

                # Scatter with fixed color scale
                sc = ax.scatter(
                    filtered_result_with_centers['Y'],
                    filtered_result_with_centers['Z'],
                    c=filtered_result_with_centers['pressure'],
                    cmap=cmap,
                    norm=norm,
                    s=50,
                    marker='s',
                    edgecolors='black',
                    linewidths=1
                )

                # Add colorbar
                cbar = fig.colorbar(sc, ax=ax, shrink=0.3)
                cbar.set_label(f"Pressure ({pressure_unit})")


                # Add all overlayed features
                ax.plot([chest_pot_df.at[0, 'y'], chest_pot_df.at[0, 'y']],
                        [chest_pot_df.at[0, 'z'], belt_position['predicted_z']], color='white', linewidth=1)

                # UNCOMMENT THE FOLLOWING TO SEE INITIAL FITS
                # ax.scatter(belt_position['left_edges']['Y'], belt_position['left_edges']['Z'], c='yellow', s=40)
                # ax.scatter(belt_position['right_edges']['Y'], belt_position['right_edges']['Z'], c='yellow', s=40)
                # ax.scatter(belt_position['left_edge']['Y'], belt_position['left_edge']['Z'], c='white', s=40)
                # ax.scatter(belt_position['right_edge']['Y'], belt_position['right_edge']['Z'], c='slategrey', s=40)
                # ax.scatter(belt_position['left_line']['points']['Y'], belt_position['left_line']['points']['Z'], c='black', s=20)
                # ax.scatter(belt_position['right_line']['points']['Y'], belt_position['right_line']['points']['Z'], c='black', s=20)
                
                # FINAL FIT
                ax.scatter(belt_position['final_left_line']['points']['Y'], belt_position['final_left_line']['points']['Z'], c='red', s=40)
                ax.scatter(belt_position['final_right_line']['points']['Y'], belt_position['final_right_line']['points']['Z'], c='red', s=40)
                ax.plot(left_line_data['Y'], left_line_data['Z'], c='white', linewidth=1)
                ax.plot(right_line_data['Y'], right_line_data['Z'], c='white', linewidth=1)
                ax.plot(belt_position['center_line']['Y'], belt_position['center_line']['Z'], c='red', linewidth=1)
                

                # Set uniform axes and appearance
                
                # Main title
                # ax.set_title(f"Dynamic belt position: {cfg.TEST_ID}", fontsize=12, pad=25)
                ax.set_title(f"{cfg.TEST_ID}: Dynamic belt position (Unfiltered, 3300 Hz)", fontsize=12, pad=25)
                # Subtitle with frame, time, belt
                # subtitle = f"Frame: {frame_number}, Time: {filtered_result_with_centers['time'].iloc[0]:.3f} s, Belt position: {math.floor(belt_position['vertical_distance'])} mm"
                subtitle = f"Frame: {frame_number}, Time: {filtered_result_with_centers['time'].iloc[0]:.3f} s"
                ax.text(
                    0.5, 1.02, subtitle, transform=ax.transAxes, ha='center', va='bottom', fontsize=10
                )

                ax.set_xlabel("Y Coordinate (mm)")
                ax.set_ylabel("Z Coordinate (mm)")
                ax.set_aspect('equal', adjustable='box')

                # Use consistent global limits for all frames
                y_min, y_max = frame_baseline_merged_df['Y'].min(), frame_baseline_merged_df['Y'].max()
                z_min, z_max = frame_baseline_merged_df['Z'].min(), frame_baseline_merged_df['Z'].max()
                
                # zoom out by 5%
                margin_y = (y_max - y_min) * 0.05  
                margin_z = (z_max - z_min) * 0.05
                ax.set_xlim(y_min - margin_y, y_max + margin_y)
                ax.set_ylim(z_min - margin_z, z_max + margin_z)

                # Invert axes to mimick pressure sensor orientation
                ax.invert_xaxis()
                ax.invert_yaxis()
                ax.scatter(chest_pot_df.at[0, 'y'], chest_pot_df.at[0, 'z'], marker='^', color='green', s=40, zorder = 3)
                plt.tight_layout()
                
                # Save and close
                plot_path = plots_folder / f"frame_{frame_number:04d}.png"
                fig.savefig(plot_path, dpi=150)
                plt.close(fig)

                # Store vertical distance
                vertical_distances_df = pd.concat([
                    vertical_distances_df,
                    pd.DataFrame({
                        'frame': [frame_number],
                        'time': [filtered_result_with_centers['time'].iloc[0]],
                        'distance': [belt_position['vertical_distance']]
                    })
                ], ignore_index=True)


            else:
                log(f"Skipping frame {frame_number} due to no pressure above threshold")

        except Exception as e:
            log(f"Error in frame {frame_number}: {e}")

    if save_path is not None:
        vertical_distances_df.to_excel(save_path, index=False)

    return belt_position_by_frame, vertical_distances_df