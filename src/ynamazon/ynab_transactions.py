from collections.abc import Iterable
from decimal import Decimal
from typing import Any, TypeVar, Union

from loguru import logger
from pydantic import AnyUrl, BaseModel, Field
from rich import print as rprint
from rich.table import Table
from ynab.api.payees_api import PayeesApi
from ynab.api.transactions_api import TransactionsApi
from ynab.api_client import ApiClient
from ynab.configuration import Configuration
from ynab.models.existing_transaction import ExistingTransaction
from ynab.models.hybrid_transaction import HybridTransaction
from ynab.models.payee import Payee
from ynab.models.put_transaction_wrapper import PutTransactionWrapper
from ynab.models.transaction_flag_color import TransactionFlagColor

from ynamazon.amazon.models import Transaction
from ynamazon.exceptions import YnabSetupError
from ynamazon.settings import settings

default_configuration = Configuration(
    access_token=settings.ynab_api_key.get_secret_value()
)
my_budget_id = settings.ynab_budget_id

PARTIAL_ORDER_MEMO = "-This transaction doesn't represent the entire order. The order total is ${order_total:.2f}-"
YNAB_MAX_MEMO_LENGTH = 500


class MemoField(BaseModel):
    header_lines: list[str] = Field(default_factory=list)
    item_lines: list[tuple[int, str]] = Field(default_factory=list)
    footer_lines: list[str] = Field(default_factory=list)

    def __str__(self) -> str:
        if len(items := self.item_lines) == 1:
            items_str = [f"- {items[0][1]!s}"]
        else:
            items_str = [f"- {i}. {item}" for i, item in items]
        return "\n".join([*self.header_lines, *items_str, *self.footer_lines])

    def __len__(self) -> int:
        return len(str(self))


class TempYnabTransaction(HybridTransaction):
    """Temporary YNAB transaction."""

    _memo: Union[str, None] = None
    _memo_truncated: Union[bool, None] = None

    @property
    def rendered_memo(self) -> str:
        return self._memo or ""

    @property
    def amount_decimal(self) -> Decimal:
        """Returns the amount in currency."""
        return self.amount / Decimal("1000")

    def create_memo(self, amazon_transaction: Transaction) -> None:
        """Creates a memo for the transaction."""
        if amazon_transaction.order is None:
            msg = "amazon_transaction must be matched to an order!"
            raise ValueError(msg)
        items = amazon_transaction.order.items

        memo = MemoField()
        if (
            amazon_transaction.grand_total.compare(
                order_total := -amazon_transaction.order.grand_total
            )
            != 0
        ):
            logger.debug(
                f"Transaction total {amazon_transaction.grand_total} doesn't match order total {order_total}"
            )
            memo.header_lines.append(PARTIAL_ORDER_MEMO.format(order_total=order_total))

        if len(items) > 1:
            memo.header_lines.append("**Items**")
            for i, item in enumerate(items, start=1):
                memo.item_lines.append((i, str(item)))
        if len(items) == 1:
            memo.item_lines.append((0, str(items[0])))

        assert amazon_transaction.order.order_details_link is not None, (
            "Order details link is None. This shouldn't happen."
        )
        memo.footer_lines.append(
            markdown_formatted_link(
                f"Order #{amazon_transaction.order.order_number}",
                url=amazon_transaction.order.order_details_link,
            )
        )

        truncated, memo_str = simple_memo_truncate(memo)
        self._memo = memo_str
        self._memo_truncated = truncated


def simple_memo_truncate(
    memo: MemoField,
    *,
    max_length: int = YNAB_MAX_MEMO_LENGTH,
    ellipsis: str = "...",
    truncated_text: str = "[truncated]",
) -> tuple[bool, str]:
    """Truncates the memo to a maximum length.

    Args:
        memo (str): The memo to truncate.
        max_length (int): The maximum length of the memo.
        ellipsis (str): The string to append to the end of the memo if it is truncated.
        truncated_text (str): The string to append to the end of the memo if it is truncated.

    Returns:
        tuple[bool, str]: A tuple containing a boolean indicating if the memo was truncated and the truncated memo.
    """
    old_memo = memo
    new_memo = old_memo.model_copy()
    truncated = False
    if (length := len(new_memo)) > max_length:
        truncated = True
        # if no items, do a naive truncation
        if len(new_memo.item_lines) == 0:
            return truncated, str(new_memo)[
                : max_length - len(truncated_text) - 1
            ] + truncated_text

        excess_chars = length - max_length

        chars_per_line = excess_chars // len(new_memo.item_lines)

        for line in new_memo.item_lines:
            if len(line_text := line[1]) > chars_per_line:
                line = (
                    line[0],
                    line_text[: max_length - len(truncated_text) - 1] + ellipsis,
                )

    assert len(new_memo) <= max_length, (
        f"Memo is still too long after truncation: {len(new_memo)} > {max_length}"
    )
    return truncated, str(new_memo)


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
        logger.warning(
            f"Memo exceeds 500 character limit ({len(memo_str)} chars). Truncating..."
        )
        # Keep the important parts - first warning line, and the URL at the end
        lines = memo_str.split("\n")

        # Extract the URL at the end (it must be preserved)
        url_line = lines[-1]

        # Keep the warning header if it exists
        header = ""
        if len(lines) > 0 and "-This transaction doesn" in lines[0]:
            header = lines[0] + "\n\n"

        # Calculate remaining space for content
        remaining_space = 500 - len(header) - len(url_line) - 4  # 4 chars for "...\n"

        # Get middle content (item list) and truncate if needed
        middle_content = "\n".join(lines[1:-1])
        if len(middle_content) > remaining_space:
            middle_content = middle_content[:remaining_space] + "..."

        # Combine the parts to stay under 500 chars
        memo_str = f"{header}{middle_content}\n{url_line}"

    data.transaction.memo = memo_str
    data.transaction.payee_id = payee_id
    data.transaction.flag_color = TransactionFlagColor.ORANGE
    with ApiClient(configuration=configuration) as api_client:
        update_response = TransactionsApi(api_client=api_client).update_transaction(
            budget_id=budget_id, transaction_id=transaction.id, data=data
        )

    print(update_response)


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
