from typing import Annotated

from rich.console import Console
from rich.table import Table
from typer import Argument, Option, Typer
from ynab import Configuration

from .amazon_transactions import AmazonConfig, get_amazon_transactions
from .main import process_transactions
from .settings import settings
from .ynab_transactions import get_ynab_transactions

cli = Typer()


@cli.command()
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
    """Prints YNAB transactions.

    All arguments will use defaults in .env file if not provided.

    Arguments:
        api_key: YNAB API key.
        budget_id: YNAB Budget ID.
        needs_memo_payee: YNAB Payee Name to be processed.
        completed_payee: YNAB Payee Name completed.
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


@cli.command()
def print_amazon_transactions(
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
        list[int] | None,
        Option("-y", "--years", help="Order years; leave empty for current year"),
    ] = None,
    transaction_days: Annotated[
        int, Option("-d", "--days", help="Days of transactions to retrieve")
    ] = 31,
) -> None:
    """Prints Amazon transactions.

    All required arguments will use defaults in .env file if not provided.

    Arguments:
        user_email: Amazon username.
        user_password: Amazon password.
        order_years: Order years; leave empty for current year.
        transaction_days: Days of transactions to retrieve.
    """
    console = Console()

    config = AmazonConfig(username=user_email, password=user_password)  # type: ignore[arg-type]

    transactions = get_amazon_transactions(
        configuration=config,
        order_years=order_years,
        transaction_days=transaction_days,
    )

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
) -> None:
    """Match YNAB transactions to Amazon Transactions and optionally update YNAB Memos.

    All required arguments will use defaults in .env file if not provided.

    Arguments:
        ynab_api_key: YNAB API key.
        ynab_budget_id: YNAB Budget ID.
        amazon_user: Amazon username.
        amazon_password: Amazon password.
    """
    process_transactions(
        amazon_config=AmazonConfig(username=amazon_user, password=amazon_password),  # type: ignore[arg-type]
        ynab_config=Configuration(access_token=ynab_api_key),
        budget_id=ynab_budget_id,
    )
