import pandas as pd
import numpy as np
import belt_position.config.settings as cfg

TIME_PRECISION = 4

def trim_channels(belt_data: pd.DataFrame, chest_data: pd.DataFrame):
    """
    Trim belt to the overlap window between start_time/end_time and actual belt time range.
    """
  # Determine overlap window between Global window (START_TIME–END_TIME) and Actual belt range
    belt_min = belt_data['time'].min()
    belt_max = belt_data['time'].max()
    
    t_start = max(cfg.START_TIME, belt_min)
    t_end   = min(cfg.END_TIME, belt_max)

    belt_trimmed = belt_data[
        (belt_data['time'] >= t_start) & 
        (belt_data['time'] <= t_end)
    ].reset_index(drop=True)
    
    chest_trimmed = chest_data

    return belt_trimmed, chest_trimmed

