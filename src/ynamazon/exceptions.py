class YnabSetupError(Exception):
    """Custom exception for YNAB setup errors."""

    pass

class MissingOpenAIAPIKey(Exception):
    """Raised when OpenAI API key is required but not found."""
    pass
