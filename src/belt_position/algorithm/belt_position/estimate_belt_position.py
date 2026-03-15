from belt_position.algorithm.belt_position.detect_edges import detect_edges
from belt_position.algorithm.belt_position.clean_edge_points import clean_edge_points
from belt_position.algorithm.belt_position.fit_edge_line import fit_edge_line
from belt_position.algorithm.belt_position.ensure_consistent_direction import ensure_consistent_direction
from belt_position.services.logging_service import log
import pandas as pd
import numpy as np

def estimate_belt_position(data, frame_number, chest_pot, threshold,
                                              min_points, n_samples, total_rows, total_cols):
    """
    Estimate the dynamic belt position for a single frame.

    This function detects edges of the belt based on a pressure threshold, cleans the edge points,
    fits robust lines to the left and right edges, ensures consistent line direction, calculates
    the center line, and computes the vertical distance between the chest pot and the belt.

    Args:
        data (pd.DataFrame): Merged frame and baseline data with columns ['frame', 'Row', 'Column', 'pressure', 'Y', 'Z'].
        frame_number (int): Frame index to process.
        chest_pot (list or np.ndarray): Coordinates of the chest pot [x, y, z].
        threshold (float): Pressure threshold to detect belt edges.
        min_points (int): Minimum number of edge points required to attempt line fitting.
        n_samples (int): Number of random 2-point samples for robust line fitting.
        total_rows (int): Total number of sensor rows.
        total_cols (int): Total number of sensor columns.

    Returns:
        dict or None: Dictionary containing:
            - 'left_edges' (pd.DataFrame): Raw detected left edge points.
            - 'right_edges' (pd.DataFrame): Raw detected right edge points.
            - 'left_edge' (pd.DataFrame): Cleaned left edge points.
            - 'right_edge' (pd.DataFrame): Cleaned right edge points.
            - 'left_line' (dict): Fitted line to left edge {'points', 'slope', 'intercept'}.
            - 'right_line' (dict): Fitted line to right edge {'points', 'slope', 'intercept'}.
            - 'final_left_line' (dict): Left line after direction correction.
            - 'final_right_line' (dict): Right line after direction correction.
            - 'left_slope' (float): Final left line slope.
            - 'left_intercept' (float): Final left line intercept.
            - 'right_slope' (float): Final right line slope.
            - 'right_intercept' (float): Final right line intercept.
            - 'center_slope' (float): Average slope of left and right lines.
            - 'center_intercept' (float): Average intercept of left and right lines.
            - 'center_line' (pd.DataFrame): Generated points for center line with columns ['Y', 'Z'].
            - 'predicted_z' (float): Predicted Z-coordinate of the chest pot on the center line.
            - 'vertical_distance' (float): Vertical distance between chest pot Z and predicted Z.
        Returns None if insufficient points are available for edge detection or line fitting.
    """
    # Filter the data for the specific frame
    frame_data = data[data['frame'] == frame_number]

    # Step 1: Detect edges
    edge_result = detect_edges(frame_data, threshold)
    left_edges = edge_result['left_edges']
    right_edges = edge_result['right_edges']

    if 'warning' in edge_result and edge_result['warning']:
        log(f"Warning in frame {frame_number}: {edge_result['warning']}")

    # Check if we have enough points for each edge
    if len(left_edges) < min_points or len(right_edges) < min_points:
        log(f"Not enough points for one or both edges in frame {frame_number}")
        log(f"Left edge points: {len(left_edges)}, Right edge points: {len(right_edges)}","DEBUG")
        return None

    # Step 2: Clean and filter edge points
    cleaned_left_edges = clean_edge_points(left_edges, total_rows, total_cols)
    cleaned_right_edges = clean_edge_points(right_edges, total_rows, total_cols)

    # DEBUG: Log cleaned edge counts
    log(f"Cleaned left edge points: {len(cleaned_left_edges)}, Cleaned right edge points: {len(cleaned_right_edges)}","DEBUG")

    # Separate left and right edges
    left_edge = cleaned_left_edges[cleaned_left_edges['edge_type'] == 'left']
    right_edge = cleaned_right_edges[cleaned_right_edges['edge_type'] == 'right']

    # Check if we have enough points for each edge
    if len(left_edge) < min_points or len(right_edge) < min_points:
        log(f"Not enough points for one or both edges in frame {frame_number} after cleaning")
        return None

    # Step 3: Fit lines to left and right edges
    left_line = fit_edge_line(left_edge, n_samples)
    right_line = fit_edge_line(right_edge, n_samples)

    if (left_line is None or right_line is None or
        len(left_line['points']) < min_points or len(right_line['points']) < min_points):
        log(f"Not enough points for one or both refined edges in frame {frame_number}")
        left_count = "NULL" if left_line is None else len(left_line['points'])
        right_count = "NULL" if right_line is None else len(right_line['points'])
        log(f"Left refined edge points: {left_count}, Right refined edge points: {right_count}","DEBUG")
        return None

    # Check if slopes are negative
    if left_line['slope'] <= 0 or right_line['slope'] <= 0:
        log(f"Either left or right edge line slope is negative or 0 for {frame_number}")
        return None

    # Step 4: Ensure consistent direction for center line
    log("Calculating consistent direction","DEBUG")
    final_left_line = ensure_consistent_direction(left_line['points'])
    final_right_line = ensure_consistent_direction(right_line['points'])
    n_l_rows = len(final_left_line.get("points", pd.DataFrame()))
    n_r_rows = len(final_right_line.get("points", pd.DataFrame()))

    if final_left_line is None or final_right_line is None:
        log("One or both of final_left_line or final_right_line is NULL")
        return None

    # log(f"Final left line points: {len(final_left_line)}, Final right line points: {len(final_right_line)}")
    log(f"Final left line points: {n_l_rows}, Final right line points:{n_r_rows}","DEBUG")


    # Step 5: Calculate center line
    center_slope = (final_left_line['slope'] + final_right_line['slope']) / 2
    center_intercept = (final_left_line['intercept'] + final_right_line['intercept']) / 2

    # Step 6: Generate points for center line
    y_min = min(final_left_line['points']['Y'].min(), final_right_line['points']['Y'].min())
    y_max = max(final_left_line['points']['Y'].max(), final_right_line['points']['Y'].max())
    y_seq = np.linspace(y_min, y_max, 100)
    center_line = pd.DataFrame({'Y': y_seq})
    center_line['Z'] = center_line['Y'] * center_slope + center_intercept

    # Step 7: Predict Z and calculate vertical distance
    predicted_z = center_slope * chest_pot[1] + center_intercept
    # vertical_distance = math.floor(abs(chest_pot[2] - predicted_z))
    vertical_distance = chest_pot[2] - predicted_z
    # log(f"Successfully processed frame {frame_number}")

    # Return results
    return {
        'left_edges': left_edges,
        'right_edges': right_edges,
        'left_edge': left_edge,
        'right_edge': right_edge,
        'left_line': left_line,
        'right_line': right_line,
        'final_left_line': final_left_line,
        'final_right_line': final_right_line,
        'left_slope': final_left_line['slope'],
        'left_intercept': final_left_line['intercept'],
        'right_slope': final_right_line['slope'],
        'right_intercept': final_right_line['intercept'],
        'center_slope': center_slope,
        'center_intercept': center_intercept,
        'center_line': center_line,
        'predicted_z': predicted_z,
        'vertical_distance': vertical_distance
    }
