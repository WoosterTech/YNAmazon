class YnabSetupError(Exception):
    """Custom exception for YNAB setup errors."""

    pass


class MissingOptionalSettingError(Exception):
    """Exception raised when a setting only required for a specific task is missing."""


class InvalidSettingError(Exception):
    """Exception raised when a setting is invalid."""
