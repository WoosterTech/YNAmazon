from pydantic import EmailStr, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecretApiKey(SecretStr):
    """Secret API key."""

    def _display(self) -> str:
        """Masked secret API key."""
        if self._secret_value is None:
            return "****empty****"
        return self._secret_value[:4] + "****" + self._secret_value[-4:]


class SecretBudgetId(SecretStr):
    """Secret Budget ID."""

    def _display(self) -> str:
        """Masked secret Budget ID."""
        if self._secret_value is None:
            return "****empty****"
        return self._secret_value[:4] + "****" + self._secret_value[-4:]


class Settings(BaseSettings):
    """Settings configuration for project."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    ynab_api_key: SecretApiKey
    ynab_budget_id: SecretBudgetId
    amazon_user: EmailStr
    amazon_password: SecretStr

    ynab_payee_name_to_be_processed: str = "Amazon - Needs Memo"
    ynab_payee_name_processing_completed: str = "Amazon"
    ynab_use_markdown: bool = False


settings = Settings()  # type: ignore[call-arg]
