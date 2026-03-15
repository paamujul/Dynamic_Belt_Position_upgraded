import pandas as pd
import numpy as np

def detect_speckles(df: pd.DataFrame, diff_threshold=500, ratio_threshold=10) -> pd.DataFrame:
    """
    Identify speckles (isolated pressure spikes) in frame data.

    Args:
        df (pd.DataFrame): DataFrame with columns [frame, Row, Column, pressure].
        diff_threshold (float): Minimum pressure difference to detect speckles.
        ratio_threshold (float): Minimum pressure ratio to detect speckles.

    Returns:
        pd.DataFrame: DataFrame with columns [frame, Row, Column] of detected speckles.
    """
    # Sort by sensor (Row, Column) and frame to ensure chronological order
    df = df.sort_values(["Row", "Column", "frame"]).copy()

    # Previous frame pressure (0 if frame is not consecutive)
    df["lastP"] = np.where(df["frame"].diff() == 1, df["pressure"].shift(), 0)
    # Next frame pressure (0 if frame is not consecutive)
    df["nextP"] = np.where(df["frame"].shift(-1) - df["frame"] == 1, df["pressure"].shift(-1), 0)

    # Mean of previous and next frame pressures
    df["PrePost_mn"] = (df["lastP"] + df["nextP"]) / 2
    # Difference between current pressure and surrounding mean
    df["pressureDiff"] = df["pressure"] - df["PrePost_mn"]
    # Difference between current pressure and max of previous/next
    df["pressureDiffMin"] = df["pressure"] - np.maximum(df["lastP"], df["nextP"])
    # Ratio of current pressure to surrounding mean (inf if mean is 0)
    df["pressureRatio"] = np.where(df["PrePost_mn"] != 0, df["pressure"] / df["PrePost_mn"], np.inf)

    # Identify speckles based on thresholds
    speckles = df.loc[
        (df["pressureDiffMin"] > diff_threshold) | ((df["pressureRatio"] > ratio_threshold) & (df["pressureDiff"] > df["pressureDiffMin"])),
        ["frame", "Row", "Column"] # Keep only relevant column
    ].reset_index(drop=True)

    return speckles


def filter_speckles(speckle_df: pd.DataFrame, data_df: pd.DataFrame, xs_rows: int, xs_cols: int) -> pd.DataFrame:
    """
    Replace speckle pressures with neighborhood averages.

    Args:
        speckle_df (pd.DataFrame): Speckles detected from `speckle_find`.
        data_df (pd.DataFrame): Original cleaned data.
        xs_rows (int): Total number of rows in sensor grid.
        xs_cols (int): Total number of columns in sensor grid.

    Returns:
        pd.DataFrame: speckle_df with an additional 'pressure_mn' column.
    """
    results = speckle_df.copy()
    # Initialize column for neighborhood mean pressure
    results["pressure_mn"] = np.nan

    # Iterate over each detected speckle
    for i, row in results.iterrows():
        f, r, c = row["frame"], row["Row"], row["Column"]
        # Identify other speckles in the same frame to exclude from averaging
        exclude_cells = speckle_df[speckle_df["frame"] == f]
        # Select neighborhood around the current speckle (3x3 grid)
        neighborhood = data_df[
            (data_df["frame"] == f)
            & (data_df["Column"].between(c - 1, c + 1))
            & (data_df["Row"].between(r - 1, r + 1))
        ]

        # Define the valid grid indices, respecting sensor grid boundaries
        grid_rows = np.arange(max(1, r - 1), min(xs_rows, r + 1) + 1)
        grid_cols = np.arange(max(1, c - 1), min(xs_cols, c + 1) + 1)

        # Create full neighborhood grid (all Row/Column combinations)
        grid = pd.MultiIndex.from_product([grid_rows, grid_cols], names=["Row", "Column"]).to_frame(index=False)
        
        # Merge with neighborhood pressures, fill missing cells with 0
        grid = (
            grid.merge(
                neighborhood[["Row", "Column", "pressure"]],on=["Row", "Column"], how="left"
            )
            .astype({"pressure": "float64"})  # or relevant numeric type
            .fillna(0))

        # Exclude other detected speckles in the same frame from averaging
        grid = grid[
            ~((grid["Row"].isin(exclude_cells["Row"])) & (grid["Column"].isin(exclude_cells["Column"])))
        ]

        results.loc[i, "pressure_mn"] = grid["pressure"].mean()
        
    return results
