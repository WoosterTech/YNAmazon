from datetime import date
from decimal import Decimal
from typing import Annotated, Union  # ,  Self  # not available python <3.11

from amazonorders.entity.order import Order
from amazonorders.entity.transaction import Transaction
from amazonorders.orders import AmazonOrders
from amazonorders.session import AmazonSession
from amazonorders.transactions import AmazonTransactions
from loguru import logger
from pydantic import AnyUrl, BaseModel, EmailStr, Field, SecretStr, field_validator
from rich import print as rprint
from rich.table import Table

from .settings import settings
from .types_pydantic import AmazonItemType


class AmazonTransactionWithOrderInfo(BaseModel):
    """Amazon transaction with order info."""

    completed_date: date
    transaction_total: Annotated[
        Decimal, Field(description="Value is inverted, e.g. -10.00 -> 10.00")
    ]
    order_total: Decimal
    order_number: str
    order_link: AnyUrl
    items: list[AmazonItemType]

    @field_validator("transaction_total", mode="after")
    @classmethod
    def invert_value(cls, value: Decimal) -> Decimal:
        """Inverts the value."""
        return -value

    # TODO: when dropping support for python <3.11, use Self
    @classmethod
    def from_transaction_and_orders(
        cls, orders_dict: "dict[str, Order]", transaction: Transaction
    ):
        """Creates an instance from an order and transactions."""
        order = orders_dict.get(transaction.order_number)
        if order is None:
            raise ValueError(f"Order with number {transaction.order_number} not found.")
        return cls(
            completed_date=transaction.completed_date,
            transaction_total=transaction.grand_total,
            order_total=order.grand_total,
            order_number=order.order_number,
            order_link=order.order_details_link,
            items=order.items,
        )


class AmazonConfig(BaseModel):
    """Configuration for Amazon transactions.

    Attributes:
        username (EmailStr): Amazon account email.
        password (SecretStr): Amazon account password.
    """

    username: EmailStr = Field(default_factory=lambda: settings.amazon_user)
    password: SecretStr = Field(default_factory=lambda: settings.amazon_password)

    def amazon_session(self) -> AmazonSession:
        """Creates an Amazon session."""
        return AmazonSession(
            username=self.username,
            password=self.password.get_secret_value(),
        )


def get_amazon_transactions(
    order_years: Union[list[int], None] = None,
    transaction_days: int = 31,
    configuration: Union[AmazonConfig, None] = None,
) -> list[AmazonTransactionWithOrderInfo]:
    """Returns a list of transactions with order info.

    Args:
        order_years (list[int] | None): A list of years to fetch transactions for. `None` for the current year.
        transaction_days (int): Number of days to fetch transactions for.
        configuration (AmazonConfig | None): Amazon configuration.

    Returns:
        list[TransactionWithOrderInfo]: A list of transactions with order info
    """
    if configuration is None:
        configuration = AmazonConfig()
    amazon_session = configuration.amazon_session()
    amazon_session.login()

    orders = _fetch_amazon_order_history(session=amazon_session, years=order_years)
    orders_dict = {order.order_number: order for order in orders}

    amazon_transactions = _fetch_sorted_amazon_transactions(
        transaction_days=transaction_days, amazon_session=amazon_session
    )

    amazon_transaction_with_order_details: list[AmazonTransactionWithOrderInfo] = []
    for transaction in amazon_transactions:
        try:
            amazon_transaction_with_order_details.append(
                AmazonTransactionWithOrderInfo.from_transaction_and_orders(
                    orders_dict=orders_dict, transaction=transaction
                )
            )
        except ValueError:
            logger.debug(
                f"Transaction {transaction.order_number} not found in retrieved orders."
            )
            continue

    return amazon_transaction_with_order_details


def _fetch_amazon_order_history(
    *, session: AmazonSession, years: Union[list[int], None] = None
) -> list[Order]:
    """Returns a list of Amazon orders.

    Args:
        session (AmazonSession): Amazon session (must be logged in).
        years (Sequence[int] | None): A sequence of years to fetch orders for. `None` for the current year.

    Returns:
        list[Order]: A list of Amazon orders.
    """
    if not session.is_authenticated:
        raise ValueError("Session must be authenticated.")
    amazon_orders = AmazonOrders(session)
    if years is None:
        years = [date.today().year]
    all_orders: list[Order] = []
    for year in years:
        if len(year_str := str(year)) == 2:
            year_str = "20" + year_str
        all_orders.extend(amazon_orders.get_order_history(year=year_str))
    all_orders.sort(key=lambda order: order.order_placed_date)

    return all_orders


def _fetch_sorted_amazon_transactions(
    *, amazon_session: AmazonSession, transaction_days: int = 31
) -> list[Transaction]:
    """Fetches and sorts Amazon transactions."""
    if not amazon_session.is_authenticated:
        raise ValueError("Session must be authenticated.")
    amazon_transactions = AmazonTransactions(
        amazon_session=amazon_session
    ).get_transactions(days=transaction_days)
    amazon_transactions.sort(key=lambda trans: trans.completed_date)
    return amazon_transactions


def print_amazon_transactions(
    amazon_transaction_with_order_details: list[AmazonTransactionWithOrderInfo],
):
    """Prints a list of transactions to the screen for inspection.

    Args:
        amazon_transaction_with_order_details (list[TransactionWithOrderInfo]): a list of transactions to print
    """
    rprint(f"found {len(amazon_transaction_with_order_details)} transactions")
    table = Table(title="Amazon Transactions")
    table.add_column("Completed Date", justify="center")
    table.add_column("Transaction Total", justify="right")
    table.add_column("Order Total", justify="right")
    table.add_column("Order Number", justify="center")
    table.add_column("Order Link", justify="center")
    table.add_column("Item Names", justify="left")

    for transaction in amazon_transaction_with_order_details:
        table.add_row(
            str(transaction.completed_date),
            f"${transaction.transaction_total:.2f}",
            f"${transaction.order_total:.2f}",
            transaction.order_number,
            str(transaction.order_link),
            " | ".join(_truncate_title(item.title) for item in transaction.items),
        )

    rprint(table)


def _truncate_title(title: str, max_length: int = 20) -> str:
    """Truncates the title to a maximum length."""
    if len(title) > max_length:
        return title[: max_length - 3] + "..."
    return title


def locate_amazon_transaction_by_amount(
    amazon_trans: list[AmazonTransactionWithOrderInfo], amount: Union[float, Decimal]
) -> Union[int, None]:
    """Given an amount, locate a matching Amazon transaction.

    Args:
        amazon_trans (list[TransactionWithOrderInfo]): A list of Amazon transactions
        amount (int): An amount to match

    Returns:
        int | None: Index of matched transaction in `amazon_trans` or None if no match
    """
    amount = Decimal(amount)
    for idx, a_tran in enumerate(amazon_trans):
        if a_tran.transaction_total == -amount:
            return idx

    return None


if __name__ == "__main__":
    print_amazon_transactions(get_amazon_transactions())
