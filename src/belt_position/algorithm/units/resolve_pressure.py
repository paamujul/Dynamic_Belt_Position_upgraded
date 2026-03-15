
CANONICAL_UNIT = "kPa"

TO_KPA = {
    "kPa": 1.0,
    "bar": 100.0,
}

DEFAULT_THRESHOLD_MAP = {
    "kPa": 20.0,
    "bar": 0.25,
}

def resolve_pressure_threshold(
    default_unit: str,
    cfg
) -> float:
    """
    This function returns a standardized threshold in kPa, using:
    1. The default threshold for the given unit (from DEFAULT_THRESHOLD_MAP)
    2. Optional overrides from a GUI/configuration object (`cfg`) if specified.
    GUI overrides defaults if provided.
    """

    # ---- validate units ----
    if default_unit not in TO_KPA:
        raise ValueError(f"Unsupported default unit: {default_unit}")

    # ---- default path ----
    default_value = DEFAULT_THRESHOLD_MAP[default_unit]
    threshold_kpa = default_value * TO_KPA[default_unit]

    # ---- GUI override path ----
    if cfg.PRESSURE_THRESHOLD is not None and cfg.PRESSURE_UNIT is not None:
        if cfg.PRESSURE_UNIT not in TO_KPA:
            raise ValueError(f"Unsupported GUI unit: {cfg.PRESSURE_UNIT}")

        threshold_kpa = cfg.PRESSURE_THRESHOLD * TO_KPA[cfg.PRESSURE_UNIT]

    return threshold_kpa
