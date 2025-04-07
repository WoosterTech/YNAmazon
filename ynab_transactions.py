# ruff: noqa: E501
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, TypeVar

import ynab
from loguru import logger
from rich import print as rprint
from rich.table import Table
from ynab.models.existing_transaction import ExistingTransaction
from ynab.models.payee import Payee
from ynab.models.put_transaction_wrapper import PutTransactionWrapper

from settings import settings as config

if TYPE_CHECKING:
    from ynab.models.hybrid_transaction import HybridTransaction

default_configuration = ynab.Configuration(
    access_token=config.ynab_api_key.get_secret_value()
)
my_budget_id = config.ynab_budget_id
rprint(config.amazon_user)


def get_payees_by_budget(
    configuration: ynab.Configuration | None = None,
    budget_id: str | None = None,
) -> list["Payee"]:
    """Returns a list of payees by budget ID.

    Args:
        configuration (Configuration | None): The YNAB API configuration.
        budget_id (str | None): The budget ID.

    Returns:
        list[Payee]: A list of payees.
    """
    configuration = configuration or default_configuration
    budget_id = budget_id or my_budget_id.get_secret_value()
    with ynab.ApiClient(configuration=configuration) as api_client:
        response = ynab.PayeesApi(api_client).get_payees(budget_id=budget_id)

    return response.data.payees


def get_transactions_by_payee(
    payee: Payee,
    configuration: ynab.Configuration | None = None,
    budget_id: str | None = None,
) -> list["HybridTransaction"]:
    """Returns a list of transactions by payee.

    Args:
        payee (Payee): The payee object.
        configuration (Configuration | None): The YNAB API configuration.
        budget_id (str | None): The budget ID.

    Returns:
        list[HybridTransaction]: A list of transactions.
    """
    configuration = configuration or default_configuration
    budget_id = budget_id or my_budget_id.get_secret_value()
    with ynab.ApiClient(configuration=configuration) as api_client:
        response = ynab.TransactionsApi(api_client).get_transactions_by_payee(
            budget_id=budget_id,
            payee_id=payee.id,
        )

    return response.data.transactions


def get_ynab_transactions(
    configuration: ynab.Configuration | None = None,
    budget_id: str | None = None,
) -> tuple[list["HybridTransaction"], "Payee"] | None:
    """Returns a tuple of YNAB transactions and the payee.

    Args:
        configuration (Configuration | None): The YNAB API configuration.
        budget_id (str | None): The budget ID.

    Returns:
        tuple[list[HybridTransaction], Payee] | None: A tuple of YNAB transactions and the payee.
    """
    configuration = configuration or default_configuration
    budget_id = budget_id or my_budget_id.get_secret_value()

    payees = get_payees_by_budget(configuration, budget_id)

    rprint("Finding payees...")
    amazon_needs_memo_payee = find_item_by_attribute(
        items=payees,
        attribute="name",
        value=config.ynab_payee_name_to_be_processed,
    )
    amazon_with_memo_payee = find_item_by_attribute(
        items=payees,
        attribute="name",
        value=config.ynab_payee_name_processing_completed,
    )
    if not (amazon_needs_memo_payee and amazon_with_memo_payee):
        rprint("[bold red]Unable to find payees, exiting.[/]")
        return None

    ynab_transactions = get_transactions_by_payee(
        budget_id=budget_id, payee=amazon_needs_memo_payee
    )
    return ynab_transactions, amazon_with_memo_payee


def update_ynab_transaction(
    transaction: "HybridTransaction",
    memo: str,
    payee_id: str,
    configuration: ynab.Configuration | None = None,
    budget_id: str | None = None,
) -> None:
    """Updates a YNAB transaction with the given memo and payee ID.

    Args:
        transaction (HybridTransaction): The transaction to update.
        memo (str): The memo to set.
        payee_id (str): The payee ID to set.
        configuration (Configuration | None): The YNAB API configuration.
        budget_id (str | None): The budget ID.
    """
    configuration = configuration or default_configuration
    budget_id = budget_id or my_budget_id.get_secret_value()
    data = PutTransactionWrapper(
        transaction=ExistingTransaction.model_validate(transaction)
    )
    data.transaction.memo = memo
    data.transaction.payee_id = payee_id
    with ynab.ApiClient(configuration=configuration) as api_client:
        _ = ynab.TransactionsApi(api_client=api_client).update_transaction(
            budget_id=budget_id, transaction_id=transaction.id, data=data
        )


_T = TypeVar("_T", bound=Payee)


def find_item_by_attribute(
    items: Iterable[_T], attribute: str, value: Any
) -> _T | None:
    """Finds an item in a list by its attribute value.

    Args:
        items (Iterable[_T]): The list of items to search.
        attribute (str): The attribute name to search for.
        value (Any): The value to match.

    Returns:
        _T | None: The found item or None if not found.
    """
    for item in items:
        item_value = getattr(item, attribute)
        if item_value == value:
            logger.debug(f"found {attribute}: {item_value}")
            return item

    return None


def print_ynab_transactions(transactions: list["HybridTransaction"]) -> None:
    """Prints YNAB transactions in a table format.

    Args:
        transactions (list[HybridTransaction]): The list of transactions to print.
    """
    rprint(f"found {len(transactions)} transactions")
    table = Table(title="YNAB Transactions")
    table.add_column("Date", justify="left", style="cyan", no_wrap=True)
    table.add_column("Amount", justify="right", style="green")

    for transaction in transactions:
        table.add_row(str(transaction.var_date), f"${transaction.amount / -1000:.2f}")

    rprint(table)


if __name__ == "__main__":
    ynab_transactions = get_ynab_transactions()
    if ynab_transactions is None:
        rprint("[bold red]No transactions found.[/]")
        exit(1)

    transactions, payee = ynab_transactions
    print_ynab_transactions(transactions=transactions)
