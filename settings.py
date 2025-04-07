from pydantic import EmailStr, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings configuration for project."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    ynab_api_key: SecretStr
    ynab_budget_id: SecretStr
    amazon_user: EmailStr
    amazon_password: SecretStr

    ynab_payee_name_to_be_processed: str = "Amazon - Needs Memo"
    ynab_payee_name_processing_completed: str = "Amazon"


settings = Settings()  # type: ignore[call-arg]
