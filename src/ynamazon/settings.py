from pydantic import EmailStr, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from .exceptions import MissingOpenAIAPIKey


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

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=True,
        extra="ignore"
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

    @classmethod
    def convert_bool(cls, v: str | bool) -> bool:
        if isinstance(v, bool):
            return v
        return v.lower() in ("true", "1", "t", "y", "yes")

    @field_validator("use_ai_summarization")
    @classmethod
    def validate_ai_summarization(cls, v: bool, info) -> bool:
        """Validate that OpenAI API key is present when AI summarization is enabled."""
        if v and not info.data.get("openai_api_key"):
            raise MissingOpenAIAPIKey("OpenAI API key is required when AI summarization is enabled")
        return v


settings = Settings()  # type: ignore[call-arg]
