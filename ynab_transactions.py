from typing import Any, List
import ynab
from ynab.models.payee import Payee
from ynab.models.put_transaction_wrapper import PutTransactionWrapper
from ynab.models.hybrid_transaction import HybridTransaction

import config

configuration = ynab.Configuration(
    access_token=config.ynab_api_key
)
my_budget_id = config.ynab_budget_id


def get_ynab_transactions() -> tuple[List[HybridTransaction], Payee]:
    with ynab.ApiClient(configuration=configuration) as api_client:
        payees: List[Payee] = (
            ynab.PayeesApi(api_client).get_payees(budget_id=my_budget_id).data.payees
        )
        print(f"Finding payees...")
        amazon_needs_memo_payee: Payee = find_item_by_attribute(
            items=payees, attribute="name", value=config.ynab_payee_name_to_be_processed
        )
        amazon_with_memo_payee: Payee = find_item_by_attribute(
            items=payees, attribute="name", value=config.ynab_payee_name_processing_completed
        )
        if not (amazon_needs_memo_payee and amazon_with_memo_payee):
            print('Unable to find payees, exiting.')
            return None, None

        ynab_transactions: List[HybridTransaction] = (
            ynab.TransactionsApi(api_client)
            .get_transactions_by_payee(
                budget_id=my_budget_id, payee_id=amazon_needs_memo_payee.id
            )
            .data.transactions
        )
    return ynab_transactions, amazon_with_memo_payee

def update_ynab_transaction(transaction, memo, payee_id) -> None:
    data = PutTransactionWrapper(transaction=transaction.to_dict())
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
    print(f"found {len(transactions)} transactions")
    for transaction in transactions:
        print(f'{transaction.var_date} - {transaction.payee_id}: ${transaction.amount/-1000:.2f}\n')

if __name__ == "__main__":
    print_ynab_transactions(transactions=get_ynab_transactions())
