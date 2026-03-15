import pandas as pd
import numpy as np
from belt_position.services.logging_service import log

def detect_edges(frame_data, threshold, min_points=5):
    """
    Detect left and right edge points in a single frame of pressure sensor data.

    For each row in the frame, this function finds the first valid sensor above the 
    threshold from the left (left edge) and from the right (right edge). Validity 
    is determined by both the pressure value exceeding the threshold and having 
    valid neighboring pressures in the expected directions.

    The function trims excessive points in the first column and merges edge points 
    with corresponding Y/Z coordinates.

    Args:
        frame_data (pd.DataFrame): DataFrame containing sensor measurements for a single frame.
            Must include columns ['Row', 'Column', 'pressure', 'Y', 'Z'].
        threshold (float): Pressure threshold above which a sensor is considered "active".
        min_points (int, optional): Minimum number of edge points required to proceed. Defaults to 5.

    Returns:
        dict: Dictionary with keys:
            - 'left_edges' (pd.DataFrame): Detected left edge points with columns ['Row', 'Column', 'Y', 'Z', 'edge_type'].
            - 'right_edges' (pd.DataFrame): Detected right edge points with columns ['Row', 'Column', 'Y', 'Z', 'edge_type'].
            - 'warning' (str or None): Warning message if detection fails or insufficient points found.
    """
    try:     
        # Helper to check if a pressure value is valid (numeric and above threshold)
        def is_valid_pressure(value):
            # Return True if value is numeric and above threshold
            return value is not None and not (isinstance(value, float) and np.isnan(value)) and value > threshold

        def find_left_edge(row_data):
            non_zero_idx = row_data.index[row_data['pressure'] > threshold].tolist()
            for idx in non_zero_idx:
                # Check if there's a point to the right AND a point below
                if idx + 1 in row_data.index and (row_data.at[idx, 'Row'] + 1) <= frame_data['Row'].max():
                    right_pressure = row_data.at[idx + 1, 'pressure']
                    # Get pressure from the sensor below in the same column
                    below_pressure_series = frame_data.loc[
                        (frame_data['Row'] == row_data.at[idx, 'Row'] + 1) &
                        (frame_data['Column'] == row_data.at[idx, 'Column']),
                        'pressure'
                    ]
                    below_pressure = below_pressure_series.values[0] if not below_pressure_series.empty else None

                    # Confirm both right and below pressures are valid
                    if is_valid_pressure(right_pressure) and is_valid_pressure(below_pressure):
                        # Return edge position as a series
                        return pd.Series({'Row': row_data.at[idx, 'Row'], 'Column': row_data.at[idx, 'Column']})
            return None

        def find_right_edge(row_data):
            non_zero_idx = row_data.index[row_data['pressure'] > threshold].tolist()
            for idx in reversed(non_zero_idx):
                # Check if there's a point to the left AND a point above
                if idx - 1 in row_data.index and (row_data.at[idx, 'Row'] - 1) >= frame_data['Row'].min():
                    left_pressure = row_data.at[idx - 1, 'pressure']
                    # Get pressure from the sensor above in the same column
                    above_pressure_series = frame_data.loc[
                        (frame_data['Row'] == row_data.at[idx, 'Row'] - 1) &
                        (frame_data['Column'] == row_data.at[idx, 'Column']),
                        'pressure'
                    ]
                    above_pressure = above_pressure_series.values[0] if not above_pressure_series.empty else None

                    # Confirm both left and above pressures are valid
                    if is_valid_pressure(left_pressure) and is_valid_pressure(above_pressure):
                        return pd.Series({'Row': row_data.at[idx, 'Row'], 'Column': row_data.at[idx, 'Column']})
            return None

        # Get unique row numbers in the frame
        unique_rows = frame_data['Row'].unique()
        # Detect left edges for all rows
        left_edges_list = [find_left_edge(frame_data[frame_data['Row'] == r]) for r in unique_rows]
        left_edges_df = pd.DataFrame([e for e in left_edges_list if e is not None])
        # Detect right edges for all rows
        right_edges_list = [find_right_edge(frame_data[frame_data['Row'] == r]) for r in unique_rows]
        right_edges_df = pd.DataFrame([e for e in right_edges_list if e is not None])

        # Check if enough points were found to proceed
        if len(left_edges_df) < min_points or len(right_edges_df) < min_points:
            log("Not enough initial points for one or both edges")
            return {'left_edges': pd.DataFrame(), 'right_edges': pd.DataFrame(), 'warning': None}

        # Label edge type
        left_edges_df['edge_type'] = 'left'
        right_edges_df['edge_type'] = 'right'

        # Helper to trim too many points in column 1
        def trim_column_one(edges_df, max_points=2):
            if edges_df.empty:
                return edges_df
            # Identify points in column 1
            col_one_rows = edges_df[edges_df['Column'] == 1].index
            if len(col_one_rows) > max_points:
                # Drop extra points beyond max_points
                edges_df = edges_df.drop(col_one_rows[max_points:])
            return edges_df

        # Apply trimming
        left_edges_df = trim_column_one(left_edges_df)
        right_edges_df = trim_column_one(right_edges_df)

        # Merge with frame coordinates for plotting or further calculations
        left_edges_df = left_edges_df.merge(frame_data[['Row', 'Column', 'Y', 'Z']], on=['Row', 'Column'], how='left')
        right_edges_df = right_edges_df.merge(frame_data[['Row', 'Column', 'Y', 'Z']], on=['Row', 'Column'], how='left')

        log(f"Number of left edge points detected: {len(left_edges_df)}","DEBUG")
        log(f"Number of right edge points detected: {len(right_edges_df)}","DEBUG")

        return {'left_edges': left_edges_df, 'right_edges': right_edges_df, 'warning': None}

    except Warning as w:
        return {'left_edges': pd.DataFrame(), 'right_edges': pd.DataFrame(), 'warning': str(w)}
    except Exception as e:
        return {'left_edges': pd.DataFrame(), 'right_edges': pd.DataFrame(), 'warning': f"Error in edge detection: {str(e)}"}
