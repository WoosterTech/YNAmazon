from os import PathLike
from pathlib import Path

from pydantic import BaseModel, ConfigDict, EmailStr, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecretApiKey(SecretStr):
    """Secret API key."""

    def _display(self) -> str:
        """Masked secret API key."""
        if self._secret_value is None:
            return "****empty****"
        if len(self._secret_value) > 16:
            return self._secret_value[:4] + "****" + self._secret_value[-4:]
        if len(self._secret_value) > 8:
            return "******" + self._secret_value[-2:]
        return "********"


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


class ConfigFile(BaseModel):
    """Configuration file for CLI."""

    model_config = ConfigDict(extra="forbid")
    ynab_api_key: SecretApiKey | None = None
    ynab_budget_id: SecretBudgetId | None = None
    amazon_user: EmailStr | None = None
    amazon_password: SecretStr | None = None

    ynab_payee_name_to_be_processed: str | None = None
    ynab_payee_name_processing_completed: str | None = None
    ynab_use_markdown: bool | None = None

    @classmethod
    def from_config(cls, file: str | PathLike):
        file_path = Path(file)
        if not file_path.exists():
            raise FileNotFoundError(f"Config file {file_path} does not exist.")
        if not file_path.is_file():
            raise ValueError(f"Config file {file_path} is not a file.")

        match file_path.suffix:
            case ".yaml":
                return cls.model_validate_yaml(file_path.read_text())
            case ".toml":
                return cls.model_validate_toml(file_path.read_text())
            case _:
                raise ValueError(
                    f"Config file {file_path} must be a .toml or .yaml file."
                )

    @classmethod
    def model_validate_yaml(cls, yaml_str: str):
        """Validates a YAML string and returns a model instance."""
        import yaml

        data = yaml.safe_load(yaml_str)
        return cls.model_validate(data)

    @classmethod
    def model_validate_toml(cls, toml_str: str):
        """Validates a TOML string and returns a model instance."""
        import toml

        data = toml.loads(toml_str)
        return cls.model_validate(data)
