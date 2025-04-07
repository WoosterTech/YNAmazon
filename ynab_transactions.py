from typing import Any, List
import ynab
from ynab.models.payee import Payee
from ynab.models.put_transaction_wrapper import PutTransactionWrapper

from settings import settings

if TYPE_CHECKING:
    from ynab.models.hybrid_transaction import HybridTransaction

default_configuration = ynab.Configuration(
    access_token=settings.ynab_api_key.get_secret_value()
)
my_budget_id = settings.ynab_budget_id
rprint(settings.amazon_user)


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
        value=settings.ynab_payee_name_to_be_processed,
    )
    amazon_with_memo_payee = find_item_by_attribute(
        items=payees,
        attribute="name",
        value=settings.ynab_payee_name_processing_completed,
    )
    if not (amazon_needs_memo_payee and amazon_with_memo_payee):
        rprint("[bold red]Unable to find payees, exiting.[/]")
        return None, None # returning tuple of None values to maintain type consistency

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
        transaction=ExistingTransaction.model_validate(transaction.to_dict())
    )
    data.transaction.memo = memo
    data.transaction.payee_id = payee_id
    with ynab.ApiClient(configuration=configuration) as api_client:
        ynab.TransactionsApi(api_client=api_client).update_transaction(budget_id=my_budget_id, transaction_id=transaction.id, data=data)


def find_item_by_attribute(items, attribute, value) -> Any | None:
    for item in items:
        item_value = getattr(item, attribute)
        if item_value == value:
            print(f"found {attribute}: {item_value}")
            return item

def print_ynab_transactions(transactions) -> None:
    print(f"found {len(transactions)} transactions with the payee name of {config.ynab_payee_name_to_be_processed}")
    for transaction in transactions:
        print(f'{transaction.var_date}: ${transaction.amount/-1000:.2f}\n')

if __name__ == "__main__":
    ynab_transactions, _ = get_ynab_transactions()
    if not ynab_transactions:
        rprint("[bold red]No transactions found.[/]")
        exit(1)
    print_ynab_transactions(transactions=ynab_transactions)
