"""
DataFrame Cleaning Helpers

Provides simple utility functions to sanitize pandas DataFrames by handling
NaN and infinite values.
"""

from __future__ import annotations
from typing import Optional, Sequence
import numpy as np
import pandas as pd


def sanitize_dataframe(
    df: pd.DataFrame,
    cols: Optional[Sequence[str]] = None,
) -> pd.DataFrame:
    """
    Drop rows with NaN or infinite values from a DataFrame.

    This function:
    - Replaces positive and negative infinity with NaN.
    - Drops rows containing NaN values.
    - Resets the index of the resulting DataFrame.

    Args:
        df (pd.DataFrame): Input DataFrame to sanitize.
        cols (Optional[Sequence[str]]): Specific columns to check for NaN/inf.
            If None, all columns are checked.

    Returns:
        pd.DataFrame: Sanitized DataFrame with selected rows removed and index reset.

    Notes:
        - Does not modify the original DataFrame in place.
    """
    df = df.replace([np.inf, -np.inf], np.nan)
    if cols:
        df = df.dropna(subset=cols)
    else:
        df = df.dropna()
    return df.reset_index(drop=True)

