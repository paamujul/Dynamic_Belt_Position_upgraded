import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from belt_position.services.logging_service import log
from belt_position.services.sanitize_data import sanitize_dataframe

def fit_edge_line(edge_points, n_samples):
    """
    Fit a robust line (Z ~ Y) to a set of edge points using random 2-point sampling.

    The function performs the following steps:
        1. Drops NaN values in 'Y' and 'Z'.
        2. Performs `n_samples` random 2-point linear fits and records slopes/intercepts.
        3. Computes the median slope and intercept from successful fits.
        4. Removes points with predicted Z deviation > 5 units.
        5. Fits a final linear regression to the refined points.

    Args:
        edge_points (pd.DataFrame): DataFrame containing at least columns ['Y', 'Z'].
        n_samples (int): Number of random 2-point samples used for robust fitting.

    Returns:
        dict or None: Dictionary containing:
            - 'points' (pd.DataFrame): Refined points used for the final fit.
            - 'slope' (float): Fitted slope of the line.
            - 'intercept' (float): Fitted intercept of the line.
        Returns None if there are not enough points to perform fitting or if fitting fails.
    """
    # Remove rows where Y or Z are NaN
    edge_points = sanitize_dataframe(edge_points, ['Y', 'Z'])

    if len(edge_points) < 2:
        log("Not enough points to fit a line")
        return None

    # DEBUG
    # log(f"Number of edge points: {len(edge_points)}")

    # Step 1: Random sampling and fitting
    sample_fits = []
    random_state = 42
    rng = np.random.default_rng(42)
    for _ in range(n_samples):
        try:
            # Randomly select 2 points without replacement
            # sample_points = edge_points.sample(n=2, replace=False) 
            # sample_points = edge_points.sample(n=2, replace=False, random_state=random_state + _)
            sample_points = edge_points.sample(
                n=2,
                replace=False,
                random_state=rng.integers(0, 2**32 - 1)
            )   
            X = sample_points[['Y']].values # Predictor
            y = sample_points['Z'].values   # Response

            # Fit linear regression model
            model = LinearRegression().fit(X, y)
            # Extract intercept and slope
            coef = [model.intercept_, model.coef_[0]]
            # Skip if fit failed or has NaN values
            if coef[0] is None or np.isnan(coef[0]) or coef[1] is None or np.isnan(coef[1]):
                continue
            sample_fits.append(coef)
        except Exception as e:
            log(f"Error in fitting: {e}")
            continue

    # Remove None/failed fits
    if len(sample_fits) == 0:
        log("Failed to fit any lines")
        return None

    log(f"Number of successful fits: {len(sample_fits)}","DEBUG")

    # Median fit
    sample_fits = np.array(sample_fits)
    median_fit = np.median(sample_fits, axis=0)
    intercept, slope = median_fit[0], median_fit[1]
    log(f"Initial fit - Slope: {slope}, Intercept: {intercept}","DEBUG")

    # Step 2: Remove outliers
    edge_points = edge_points.copy()
    edge_points['pred_Z'] = slope * edge_points['Y'] + intercept
    edge_points['diff'] = edge_points['Z'] - edge_points['pred_Z']
    refined_edge = edge_points[np.abs(edge_points['diff']) <= 5]

    log(f"Number of points after removing outliers: {len(refined_edge)}","DEBUG")

    if len(refined_edge) < 2:
        log("Not enough points after removing outliers")
        return None

    # Step 3: Fit final line
    try:
        X_final = refined_edge[['Y']].values
        y_final = refined_edge['Z'].values
        final_model = LinearRegression().fit(X_final, y_final)
        final_intercept = final_model.intercept_
        final_slope = final_model.coef_[0]
    except Exception as e:
        log(f"Error in final fit: {e}")
        return None

    return {
        'points': refined_edge.reset_index(drop=True),
        'slope': final_slope,
        'intercept': final_intercept
    }
