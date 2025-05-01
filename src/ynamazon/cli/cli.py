# ruff: noqa: D212, D415
from typing import Annotated

from rich.console import Console
from rich.table import Table
from typer import Argument, Option, Typer
from ynab import Configuration
from typer import Context
from typer import run as typer_run
from rich import print as rprint

from ynamazon.amazon_transactions import AmazonConfig, AmazonTransactionRetriever
from ynamazon.main import process_transactions
from ynamazon.settings import settings
from ynamazon.ynab_transactions import get_ynab_transactions

from . import utils

cli = Typer(rich_markup_mode="rich")
cli.add_typer(utils.app, name="utils", help="[bold cyan]Utility commands[/]")


@cli.command("print-ynab")
def print_ynab_transactions(
    api_key: Annotated[
        str | None,
        Argument(
            help="YNAB API key",
            default_factory=lambda: settings.ynab_api_key.get_secret_value(),
        ),
    ],
    budget_id: Annotated[
        str | None,
        Argument(
            help="YNAB Budget ID",
            default_factory=lambda: settings.ynab_budget_id.get_secret_value(),
        ),
    ],
) -> None:
    """
    [bold cyan]Prints YNAB transactions.[/]

    [yellow i]All arguments will use defaults in .env file if not provided.[/]
    """
    console = Console()

    configuration = Configuration(access_token=api_key)
    transactions, _payee = get_ynab_transactions(
        configuration=configuration, budget_id=budget_id
    )

    console.print(f"[bold green]Found {len(transactions)} transactions.[/]")

    if not transactions:
        console.print("[bold red]No transactions found.[/]")
        exit(1)

    table = Table(title="YNAB Transactions")
    table.add_column("Date", justify="left", style="cyan", no_wrap=True)
    table.add_column("Amount", justify="right", style="green")
    table.add_column("Memo", justify="left", style="yellow")

    for transaction in transactions:
        table.add_row(
            str(transaction.var_date),
            f"${-transaction.amount_decimal:.2f}",
            transaction.memo or "n/a",
        )

    console.print(table)


@cli.command("print-amazon")
def print_amazon_transactions(
    ctx: Context,
    user_email: Annotated[
        str,
        Argument(help="Amazon username", default_factory=lambda: settings.amazon_user),
    ],
    user_password: Annotated[
        str,
        Argument(
            help="Amazon password",
            default_factory=lambda: settings.amazon_password.get_secret_value(),
        ),
    ],
    order_years: Annotated[
        list[str] | None,
        Option("-y", "--years", help="Order years; leave empty for current year"),
    ] = None,
    transaction_days: Annotated[
        int, Option("-d", "--days", help="Days of transactions to retrieve")
    ] = 31,
) -> None:
    """
    [bold cyan]Prints Amazon transactions.[/]

    [yellow i]All required arguments will use defaults in .env file if not provided.[/]
    """
    console = Console()

    amazon_config = AmazonConfig(username=user_email, password=user_password) # type: ignore[arg-type]

    transactions = AmazonTransactionRetriever(
        amazon_config=amazon_config,
        order_years=order_years,
        transaction_days=transaction_days,
        force_refresh_amazon=ctx.obj["force_refresh_amazon"]
    ).get_amazon_transactions()

    console.print(f"[bold green]Found {len(transactions)} transactions.[/]")

    if not transactions:
        console.print("[bold red]No transactions found.[/]")
        exit(1)

    table = Table(title="Amazon Transactions")
    table.add_column("Completed Date", justify="left", style="cyan", no_wrap=True)
    table.add_column("Transaction Total", justify="right", style="green")
    table.add_column("Order Total", justify="right", style="green")
    table.add_column("Order Number", justify="center", style="cyan")
    table.add_column("Order Link", justify="center", style="blue underline")
    table.add_column("Item Names", justify="left", style="yellow")

    for transaction in transactions:
        table.add_row(
            str(transaction.completed_date),
            f"${transaction.transaction_total:.2f}",
            f"${transaction.order_total:.2f}",
            transaction.order_number,
            str(transaction.order_link),
            " | ".join(item.title for item in transaction.items),
        )

    console.print(table)


@cli.command()
def ynamazon(
    ctx: Context,
    ynab_api_key: Annotated[
        str | None,
        Argument(
            help="YNAB API key",
            default_factory=lambda: settings.ynab_api_key.get_secret_value(),
        ),
    ],
    ynab_budget_id: Annotated[
        str | None,
        Argument(
            help="YNAB Budget ID",
            default_factory=lambda: settings.ynab_budget_id.get_secret_value(),
        ),
    ],
    amazon_user: Annotated[
        str,
        Argument(
            help="Amazon username",
            default_factory=lambda: settings.amazon_user,
        ),
    ],
    amazon_password: Annotated[
        str,
        Argument(
            help="Amazon password",
            default_factory=lambda: settings.amazon_password.get_secret_value(),
        ),
    ],
    force_refresh_amazon: Annotated[
        bool,
        Option(
            "--force-refresh-amazon",
            help="Force refresh of Amazon transactions instead of depending on cached data",
            is_flag=True,
        ),
    ] = False,
) -> None:
    """
    [bold cyan](Default) Match YNAB transactions to Amazon Transactions and optionally update YNAB Memos.[/]

    [yellow i]All required arguments will use defaults in .env file if not provided.[/]
    """
    # Store the flag in the Typer context for use in commands
    ctx.obj = {"force_refresh_amazon": force_refresh_amazon}

    process_transactions(
        amazon_config=AmazonConfig(username=amazon_user, password=amazon_password, force_refresh_amazon=ctx.obj["force_refresh_amazon"]),  # type: ignore[arg-type]
        ynab_config=Configuration(access_token=ynab_api_key),
        budget_id=ynab_budget_id,
    )


@cli.callback(invoke_without_command=True)
def yna_callback(
    ctx: Context,
    force_refresh_amazon: Annotated[
        bool,
        Option(
            "--force-refresh-amazon",
            help="Force refresh of Amazon transactions (don't use the cached data)",
            is_flag=True,
        ),
    ] = False,
) -> None:
    """
    [bold cyan]Run 'yna' to match and update transactions using the arguements in .env. [/]

    [yellow i]Use 'yna ynamazon [ARGS]' to use command-line arguements to override .env. [/]
    """
    # Store the flag in the Typer context for use in commands
    ctx.obj = {"force_refresh_amazon": force_refresh_amazon}
    
    rprint("[bold cyan]Starting YNAmazon processing...[/]")
    if ctx.invoked_subcommand is None:
        typer_run(function=ynamazon)
