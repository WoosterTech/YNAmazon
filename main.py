import amazon_transactions
import ynab_transactions
from typing import List
from amazon_transactions import TransactionWithOrderInfo


def process_transactions() -> None:
    print('please wait...')
    ynab_trans, amazon_with_memo_payee = ynab_transactions.get_ynab_transactions()
    amazon_trans: List[TransactionWithOrderInfo] = amazon_transactions.get_amazon_transactions()
    if not ynab_trans:
        print('No matching Transactions foound in YNAB. Exiting.')
        return
    print('\n\n\nStarting to look for matching transactions...\n')
    for ynab_tran in ynab_trans:
        print(
            f"\n\nLooking for an Amazon Transaction that matches this YNAB transaction: {ynab_tran.var_date} ${ynab_tran.amount/-1000:.2f}"
        )
        amazon_tran: TransactionWithOrderInfo | None = find_matching_amazon_transaction(amazon_trans=amazon_trans, amount=ynab_tran.amount)
        if not amazon_tran:
            print(f"**** Could not find a matching Amazon Transaction!")
            continue
        print(f"Found a matching Amazon Transaction!")
        print(f"Matching Amazon Transaction: {amazon_tran.completed_date} ${amazon_tran.transaction_total/1000:.2f}")

        memo: str = ""
        if amazon_tran.transaction_total != amazon_tran.order_total:
            memo += f"-This transaction doesn't represent the entire order. The order total is ${amazon_tran.order_total/1000:.2f}-    \n\n"
        if len(amazon_tran.item_names) > 1:
            for i, item in enumerate(amazon_tran.item_names, start=1):
                memo += f"{i}. {item}  \n"
        else:
            memo += amazon_tran.item_names[0] + "  \n"
        memo += amazon_tran.order_link
        print('\nMemo:')
        print(memo)

        no: str = input(prompt='\nupdate transaction? press enter to continue, type anything and press enter to skip...')
        if no:
            print('skipping...\n\n')
        else:
            print('updating...')
            ynab_transactions.update_ynab_transaction(transaction=ynab_tran, memo=memo, payee_id=amazon_with_memo_payee.id)
            print('\n\n')

def find_matching_amazon_transaction(amazon_trans, amount) -> TransactionWithOrderInfo | None:
    amount = amount * -1
    for a_tran in amazon_trans:
        if a_tran.transaction_total == amount:
            return a_tran

if __name__ == '__main__':
    process_transactions()
