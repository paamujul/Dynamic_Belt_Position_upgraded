"""
Custom Exceptions for Automated Belt Position Calculation

Defines base and specialized exceptions used across data loading,
validation, configuration, and calculation modules.
"""
# ----------------------
# # Base Exception
# ----------------------
class AutomatedBeltCalculationError(Exception):
    """Base class for all custom exceptions."""
    pass


# ----------------------
# Data-related Exceptions
# ----------------------
class DataNotFoundError(AutomatedBeltCalculationError):
    """Raised when expected data is missing."""
    pass

class DataValidationError(AutomatedBeltCalculationError):
    """Raised when data fails validation checks."""
    pass


# ----------------------
# Configuration Exceptions
# ----------------------
class InvalidConfigurationError(AutomatedBeltCalculationError):
    """Raised when config values are invalid or missing."""
    pass


# ----------------------
# Calculation / Processing Exceptions
# ----------------------
class CalculationError(AutomatedBeltCalculationError):
    """Raised when a calculation fails."""
    pass