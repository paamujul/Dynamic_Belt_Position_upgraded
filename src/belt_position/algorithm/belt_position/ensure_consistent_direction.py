from belt_position.services.logging_service import log
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

def ensure_consistent_direction(centers, tolerance=1e-6):
    """
    Ensure that a series of center points forms a line with a consistent direction.

    This function sorts the points by Y-coordinate and iteratively removes points that cause 
    direction reversals in the slope between consecutive points. After removing inconsistent 
    points, it fits a linear regression to the remaining points to obtain a robust slope and intercept.

    Args:
        centers (pd.DataFrame): DataFrame with at least columns ['Y', 'Z'] representing center line points.
        tolerance (float): Minimum change in slope considered as a direction change. Defaults to 1e-6.

    Returns:
        dict or None: Dictionary with keys:
            - 'points' (pd.DataFrame): Points used for final line fit after removing inconsistent points.
            - 'slope' (float): Slope of the fitted line.
            - 'intercept' (float): Intercept of the fitted line.
        Returns None if:
            - Input is None or contains fewer than 2 points.
            - Not enough points remain after removing direction changes.
            - Final linear regression fails.
    """
    if centers is None or len(centers) < 2:
        log("Not enough points to ensure consistent direction")
        return None

    # Sort by Y and iteratively remove points that cause direction changes
    sorted_centers = centers.sort_values('Y').reset_index(drop=True)

    while True:
        # Compute slopes between consecutive points
        delta_Y = sorted_centers['Y'].diff().iloc[1:].values
        delta_Z = sorted_centers['Z'].diff().iloc[1:].values
        slopes = delta_Z / delta_Y

        # Detect direction changes
        sign_changes = np.diff(np.sign(slopes))
        slope_diffs = np.diff(slopes)
        direction_changes = np.where((np.abs(sign_changes) > 0) & (np.abs(slope_diffs) > tolerance))[0]

        if len(direction_changes) == 0:
            break

        # Remove the first problematic point
        sorted_centers = sorted_centers.drop(index=direction_changes[0] + 1).reset_index(drop=True)

        if len(sorted_centers) < 2:
            log("Not enough points left after removing direction changes")
            return None

    # Refit final line
    X_final = sorted_centers[['Y']].values
    y_final = sorted_centers['Z'].values
    try:
        model = LinearRegression().fit(X_final, y_final)
        slope = model.coef_[0]
        intercept = model.intercept_
    except Exception as e:
        log(f"Error in final fit: {e}")
        return None

    return {
        'points': sorted_centers,
        'slope': slope,
        'intercept': intercept
    }