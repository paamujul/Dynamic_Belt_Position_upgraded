import pandas as pd
from belt_position.services.logging_service import log

def clean_edge_points(edges, total_rows, total_cols):
    """
    Clean and filter detected edge points by removing outliers based on normalized row/column ratios.

    Each edge point is assigned a `row_col_ratio` (row fraction + column fraction) relative to 
    the total number of rows and columns. Points that deviate too far from the median ratio 
    within their edge type ('left' or 'right') are removed.

    Args:
        edges (pd.DataFrame): DataFrame of detected edge points. Must contain columns
            ['Row', 'Column', 'edge_type'].
        total_rows (int): Total number of rows in the sensor grid.
        total_cols (int): Total number of columns in the sensor grid.

    Returns:
        pd.DataFrame: Cleaned edge points with additional columns:
            - 'row_col_ratio': Normalized row/column ratio for each point.
            - 'threshold': Median ratio used for filtering.
            - 'diff': Absolute difference from normalized reference ratio.
            - 'threshold1': Fixed reference value (0.1) for debugging or filtering.
            - Other original columns from `edges`.
    """
    if edges.empty:
        log("No edge points to clean")
        return edges

    # DEBUG
    log(f"Number of edge points before cleaning: {len(edges)}","DEBUG")

    # Compute a normalized row/column ratio for each point
    # row_col_ratio = fraction of row relative to total rows + fraction of column relative to total columns
    edges = edges.copy()
    edges['row_col_ratio'] = edges['Row'] / total_rows + edges['Column'] / total_cols

    # Group by edge_type to calculate median threshold and diff
    def process_group(group):
        # Median of row_col_ratio used as a threshold to identify outliers
        threshold = group['row_col_ratio'].median()
        group['threshold'] = threshold
        # Difference from normalized 1.0 reference (for debugging or filtering)
        group['diff'] = abs(1 - group['row_col_ratio'] / threshold)
        group['threshold1'] = 0.1

        # Edge-type-specific filtering: keep points within ±0.2 of median ratio
        if 'edge_type' in group.columns:
            mask = pd.Series(True, index=group.index)
            # Filter left edges
            mask[group['edge_type'] == 'left'] = group.loc[group['edge_type'] == 'left', 'row_col_ratio'].between(threshold - 0.2, threshold + 0.2)
            # Filter right edges
            mask[group['edge_type'] == 'right'] = group.loc[group['edge_type'] == 'right', 'row_col_ratio'].between(threshold - 0.2, threshold + 0.2)
            # Apply mask to remove outliers
            group = group[mask]

        return group

    # Apply processing to each edge_type group
    cleaned_edges = edges.groupby('edge_type', group_keys=False).apply(process_group)
    cleaned_edges = cleaned_edges.reset_index(drop=True)

    # DEBUG
    log(f"Number of edge points after cleaning: {len(cleaned_edges)}","DEBUG")
    
    return cleaned_edges
