from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Self

import typer
from pydantic import BaseModel, SecretStr
from rich.console import Console
from target_orders import get_orders
from ynab.configuration import Configuration

from ynamazon.settings import SecretApiKey, SecretBudgetId
from ynamazon.ynab_transactions import get_ynab_transactions

if TYPE_CHECKING:
    from target_orders.models import Order  # noqa: F401

app = typer.Typer(rich_markup_mode="rich")


@app.command()
def print_transactions(
    cookies: Annotated[
        Path | None,
        typer.Option(
            "-c",
            "--cookies",
            help="Path to the json file.",
            dir_okay=False,
        ),
    ] = None,
    delay: Annotated[
        int,
        typer.Option(
            "--delay", help="Number of seconds to wait for Orders page to laod."
        ),
    ] = 5,
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            help="Enable debug mode.",
            is_eager=True,
            is_flag=True,
        ),
    ] = False,
) -> None:
    """Print transactions from the cookies file."""
    console = Console()
    orders = get_orders(cookies_path=cookies, loading_delay=delay)

    console.print(orders)


class YNABConfigFile(BaseModel):
    # model_config = ConfigDict(extra="forbid")

    ynab_api_key: SecretApiKey | None = None
    ynab_budget_id: SecretBudgetId | None = None

    ynab_payee_name_to_be_processed: str = "Target - Needs Memo"
    ynab_payee_name_processing_completed: str = "Target"
    ynab_use_markdown: bool = False

    @classmethod
    def from_config(cls, file: str | PathLike) -> Self:
        file_path = Path(file)
        if not file_path.exists():
            raise FileNotFoundError(f"Config file {file_path} does not exist.")
        if not file_path.is_file():
            raise ValueError(f"Config file {file_path} is not a file.")

        if file_path.suffix == ".yaml":
            return cls.model_validate_yaml(file_path.read_text())
        if file_path.suffix == ".toml":
            return cls.model_validate_toml(file_path.read_text())
        raise ValueError(f"Config file {file_path} must be a .toml or .yaml file.")

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

    def get_secret_value(self, key: str) -> str | None:
        """Get secret API key or budget ID."""
        value = getattr(self, key)
        if value is None:
            return None
        if not isinstance(value, SecretStr):
            raise ValueError(f"{key} is not a SecretStr")
        return value.get_secret_value()


def api_key_parser(value: str) -> SecretApiKey:
    """Parse the API key from the command line."""
    return SecretApiKey(value)


def budget_id_parser(value: str) -> SecretBudgetId:
    """Parse the Budget ID from the command line."""
    return SecretBudgetId(value)


@app.command()
def ynab(  # noqa: C901
    ynab_api_key: Annotated[
        SecretApiKey | None,
        typer.Option(help="YNAB API key", parser=api_key_parser),
    ] = None,
    ynab_budget_id: Annotated[
        SecretBudgetId | None,
        typer.Option(help="YNAB Budget ID", parser=budget_id_parser),
    ] = None,
    unprocessed_payee: Annotated[
        str | None,
        typer.Option(
            "-u",
            "--unprocessed-payee",
            help="YNAB payee name to be processed.",
        ),
    ] = None,
    processed_payee: Annotated[
        str | None,
        typer.Option(
            "-p",
            "--processed-payee",
            help="YNAB payee name to be processed.",
        ),
    ] = None,
    config_path: Annotated[
        YNABConfigFile | None,
        typer.Option(
            "-c",
            "--config",
            help="Path to the config file.",
            parser=YNABConfigFile.from_config,
        ),
    ] = None,
    cookies: Annotated[
        Path | None,
        typer.Option(
            "-a",
            "--cookies",
            help="Path to the json file.",
            dir_okay=False,
        ),
    ] = None,
    delay: Annotated[
        int,
        typer.Option(
            "--delay", help="Number of seconds to wait for Orders page to laod."
        ),
    ] = 5,
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            help="Enable debug mode.",
            is_eager=True,
            is_flag=True,
        ),
    ] = False,
) -> None:
    """YNAB transactions from the cookies file."""
    console = Console()
    if ynab_api_key is None:
        if config_path is None or (api_key := config_path.ynab_api_key) is None:
            raise ValueError("YNAB API key is required.")
        ynab_api_key = api_key
    if ynab_budget_id is None:
        if config_path is None or (budget_id := config_path.ynab_budget_id) is None:
            raise ValueError("YNAB Budget ID is required.")
        ynab_budget_id = budget_id

    if unprocessed_payee is None:
        if (
            config_path is None
            or (unprocessed_payee := config_path.ynab_payee_name_to_be_processed)
            is None
        ):
            raise ValueError("YNAB payee name to be processed is required.")
        unprocessed_payee = unprocessed_payee

    if processed_payee is None:
        if (
            config_path is None
            or (processed_payee := config_path.ynab_payee_name_processing_completed)
            is None
        ):
            raise ValueError("YNAB payee name to be processed is required.")
        processed_payee = processed_payee

    ynab_config = Configuration(access_token=ynab_api_key.get_secret_value())

    ynab_trans, target_with_memo_payee = get_ynab_transactions(
        ynab_config,
        ynab_budget_id.get_secret_value(),
        unprocessed_payee=unprocessed_payee,
        processed_payee=processed_payee,
    )
    console.print(f"[bold green]Found {len(ynab_trans)} transactions to process.[/]")

    orders = get_orders(cookies_path=cookies, loading_delay=delay)

    for order in orders:
        filtered_ynab_transactions = ynab_trans.filter(
            amount_decimal__exact=order.order_total
        )
        match len(filtered_ynab_transactions):
            case 0:
                console.print(
                    f"[red]No matching transaction found for {order.order_number}[/]"
                )
            case 1:
                transaction = filtered_ynab_transactions[0]
                console.print(
                    f"[green]Matched {order.order_number} with {transaction.id}[/]"
                )
            case _:
                console.print(
                    f"[bold cyan]Select a matching transaction for {transaction.var_date} ${transaction.amount_decimal:.2f}[/]"
                )
                filtered_ynab_transactions.sort(key=lambda x: x.var_date, reverse=True)
                console.print(filtered_ynab_transactions)
