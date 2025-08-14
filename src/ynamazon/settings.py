from typing import override

from pydantic import EmailStr, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .exceptions import MissingOpenAIAPIKey


class SecretApiKey(SecretStr):
    """Secret API key."""

    @override
    def _display(self) -> str:
        """Masked secret API key."""
        if self._secret_value is None:  # pyright: ignore[reportUnnecessaryComparison]
            return "****empty****"
        return self._secret_value[:4] + "****" + self._secret_value[-4:]


class SecretBudgetId(SecretStr):
    """Secret Budget ID."""

    @override
    def _display(self) -> str:
        """Masked secret Budget ID."""
        if self._secret_value is None:  # pyright: ignore[reportUnnecessaryComparison]
            return "****empty****"
        return self._secret_value[:4] + "****" + self._secret_value[-4:]


class Settings(BaseSettings):
    """Settings configuration for project."""

    model_config: SettingsConfigDict = SettingsConfigDict(  # pyright: ignore[reportIncompatibleVariableOverride]
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        extra="ignore",
    )

    ynab_api_key: SecretApiKey
    ynab_budget_id: SecretBudgetId
    amazon_user: EmailStr
    amazon_password: SecretStr
    openai_api_key: SecretApiKey | None = None

    ynab_payee_name_to_be_processed: str = "Amazon - Needs Memo"
    ynab_payee_name_processing_completed: str = "Amazon"
    ynab_use_markdown: bool = False
    use_ai_summarization: bool = False
    suppress_partial_order_warning: bool = False

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        """Validate that OpenAI API key is present when AI summarization is enabled."""
        if self.use_ai_summarization and self.openai_api_key is None:
            raise MissingOpenAIAPIKey("OpenAI API key is required when AI summarization is enabled")
        return self


settings = Settings()  # pyright: ignore[reportCallIssue]
