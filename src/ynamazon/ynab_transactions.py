from collections.abc import Iterable
from decimal import Decimal
from typing import Any, TypeVar, Union

from loguru import logger
from pydantic import AnyUrl
from rich import print as rprint
from rich.table import Table
from ynab import ApiClient, Configuration, PayeesApi, TransactionsApi
from ynab.models.existing_transaction import ExistingTransaction
from ynab.models.hybrid_transaction import HybridTransaction
from ynab.models.payee import Payee
from ynab.models.put_transaction_wrapper import PutTransactionWrapper

from ynamazon.exceptions import YnabSetupError
from ynamazon.settings import settings

default_configuration = Configuration(
    access_token=settings.ynab_api_key.get_secret_value()
)
my_budget_id = settings.ynab_budget_id


class TempYnabTransaction(HybridTransaction):
    """Temporary YNAB transaction."""

    @property
    def amount_decimal(self) -> Decimal:
        """Returns the amount in currency."""
        return self.amount / Decimal("1000")


def translate_hybrid_to_temp(
    transactions: list["HybridTransaction"],
) -> list[TempYnabTransaction]:
    """Converts a list of YNAB transactions to temporary YNAB transactions.

    Args:
        transactions (list[HybridTransaction]): The list of YNAB transactions.

    Returns:
        list[TempYnabTransaction]: The list of temporary YNAB transactions.
    """
    return [
        TempYnabTransaction.model_validate(transaction.model_dump())
        for transaction in transactions
    ]


def get_payees_by_budget(
    configuration: Union[Configuration, None] = None,
    budget_id: Union[str, None] = None,
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
    with ApiClient(configuration=configuration) as api_client:
        response = PayeesApi(api_client).get_payees(budget_id=budget_id)

    return response.data.payees


def get_transactions_by_payee(
    payee: Payee,
    configuration: Union[Configuration, None] = None,
    budget_id: Union[str, None] = None,
) -> list[TempYnabTransaction]:
    """Returns a list of transactions by payee.

    Args:
        payee (Payee): The payee object.
        configuration (Configuration | None): The YNAB API configuration.
        budget_id (str | None): The budget ID.

    Returns:
        list[TempYnabTransaction]: A list of transactions.
    """
    configuration = configuration or default_configuration
    budget_id = budget_id or my_budget_id.get_secret_value()
    with ApiClient(configuration=configuration) as api_client:
        response = TransactionsApi(api_client).get_transactions_by_payee(
            budget_id=budget_id,
            payee_id=payee.id,
        )

    return translate_hybrid_to_temp(response.data.transactions)


def get_ynab_transactions(
    configuration: Union[Configuration, None] = None,
    budget_id: Union[str, None] = None,
) -> tuple[list[TempYnabTransaction], "Payee"]:
    """Returns a tuple of YNAB transactions and the payee.

    Args:
        configuration (Configuration | None): The YNAB API configuration.
        budget_id (str | None): The budget ID.

    Returns:
        tuple[list[HybridTransaction], Payee] | None: A tuple of YNAB transactions and the payee.

    Raises:
        YnabSetupError: If the payees are not found in YNAB.
    """
    configuration = configuration or default_configuration
    budget_id = budget_id or my_budget_id.get_secret_value()

    payees = get_payees_by_budget(configuration, budget_id)

    rprint("Finding payees...")
    amazon_needs_memo_payee = find_item_by_attribute(
        items=payees,
        attribute="name",
        value=settings.ynab_payee_name_to_be_processed,
    )
    amazon_with_memo_payee = find_item_by_attribute(
        items=payees,
        attribute="name",
        value=settings.ynab_payee_name_processing_completed,
    )
    if amazon_needs_memo_payee is None:
        raise YnabSetupError(
            f"Payee '{settings.ynab_payee_name_to_be_processed}' not found in YNAB."
        )
    if amazon_with_memo_payee is None:
        raise YnabSetupError(
            f"Payee '{settings.ynab_payee_name_processing_completed}' not found in YNAB."
        )

    ynab_transactions = get_transactions_by_payee(
        budget_id=budget_id, payee=amazon_needs_memo_payee
    )

    return ynab_transactions, amazon_with_memo_payee


def update_ynab_transaction(
    transaction: "HybridTransaction",
    memo: str,
    payee_id: str,
    configuration: Union[Configuration, None] = None,
    budget_id: Union[str, None] = None,
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
        transaction=ExistingTransaction.model_validate(transaction.to_dict())
    )

    # Convert memo to string if it's a MultiLineText object
    memo_str = str(memo)

    # Ensure memo doesn't exceed 500 character limit
    if len(memo_str) > 500:
        logger.warning(f"Memo exceeds 500 character limit ({len(memo_str)} chars). Truncating...")
        # Keep the important parts - first warning line, and the URL at the end
        lines = memo_str.split('\n')

        # Extract the URL at the end (it must be preserved)
        url_line = lines[-1]

        # Keep the warning header if it exists
        header = ""
        if len(lines) > 0 and '-This transaction doesn' in lines[0]:
            header = lines[0] + '\n\n'

        # Calculate remaining space for content
        remaining_space = 500 - len(header) - len(url_line) - 4  # 4 chars for "...\n"

        # Get middle content (item list) and truncate if needed
        middle_content = '\n'.join(lines[1:-1])
        if len(middle_content) > remaining_space:
            middle_content = middle_content[:remaining_space] + "..."

        # Combine the parts to stay under 500 chars
        memo_str = f"{header}{middle_content}\n{url_line}"

    data.transaction.memo = memo_str
    data.transaction.payee_id = payee_id
    with ApiClient(configuration=configuration) as api_client:
        _ = TransactionsApi(api_client=api_client).update_transaction(
            budget_id=budget_id, transaction_id=transaction.id, data=data
        )


_T = TypeVar("_T", bound=Payee)


def find_item_by_attribute(
    items: Iterable[_T], attribute: str, value: Any
) -> Union[_T, None]:
    """Finds an item in a list by its attribute value.

    Args:
        items (Iterable[_T]): The list of items to search.
        attribute (str): The attribute name to search for.
        value (Any): The value to match.

    Returns:
        _T | None: The found item or None if not found.
    """
    item_list = [item for item in items if getattr(item, attribute) == value]
    if not item_list:
        return None
    if len(item_list) > 1:
        logger.warning(
            f"Multiple items found with {attribute} = {value}. Returning the first one."
        )

    return item_list[0]


def print_ynab_transactions(transactions: list[TempYnabTransaction]) -> None:
    """Prints YNAB transactions in a table format.

    Args:
        transactions (list[HybridTransaction]): The list of transactions to print.
    """
    rprint(f"found {len(transactions)} transactions")
    table = Table(title="YNAB Transactions")
    table.add_column("Date", justify="left", style="cyan", no_wrap=True)
    table.add_column("Amount", justify="right", style="green")

    for transaction in transactions:
        table.add_row(str(transaction.var_date), f"${-transaction.amount_decimal:.2f}")

    rprint(table)


def markdown_formatted_title(title: str, url: Union[str, AnyUrl]) -> str:
    """Returns a formatted item title in markdown or raw format, dependent on ynab_use_markdown.

    Args:
        title (str): The name for the item
        url (str): The URL to link to

    Returns:
        str: A URL string suitable for injection into the memo
    """
    if settings.ynab_use_markdown:
        return f"[{title}]({url})"

    return title


def markdown_formatted_link(title: str, url: Union[str, AnyUrl]) -> str:
    """Returns a link in markdown or raw format, dependent on ynab_use_markdown.

    Args:
        title (str): The name for the link
        url (str): The URL to link to

    Returns:
        str: A URL string suitable for injection into the memo
    """
    if settings.ynab_use_markdown:
        return f"[{title}]({url})"

    if isinstance(url, AnyUrl):
        url = str(url)

    return url


if __name__ == "__main__":
    ynab_transactions, _ = get_ynab_transactions()
    if not ynab_transactions:
        rprint("[bold red]No transactions found.[/]")
        exit(1)
    print_ynab_transactions(transactions=ynab_transactions)
