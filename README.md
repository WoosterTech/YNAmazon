# YNAmazon
A program to annotate YNAB transactions with Amazon order info

## Setup/Prerequistes
1. Have a YNAB and Amazon Account (thank you Captain Obvious)
2. Create a Renaming Rule in YNAB (in the Manage Payees menu) to automatically rename any transactions containing "Amazon" to the payee you want to use to indicate that this transaction should be looked at. The default I chose is "Amazon - Needs Memo"
3. Create a Payee to act as the payee to indicate that a transaction has already been processed and does not need to be processed again. Create this payee before running this script
4. Create the config file
   1. Make a copy of `config-template.py` named `config.py`
       - `config.py` is already in the `.gitignore`
   2. Add the two payee names in the appropriate lines
   3. Add your YNAB API key in the appropriate line. It can be found by going to your YNAB Account Settings and clicking on Developer Settings
   4. Add your YNAB Budget ID. This can be found in the URL of your budget page 
   5. Add your Amazon username (email) and password
5. Run `pip install amazon-orders ynab` or `pip install -r requirements.txt` to install dependencies

## Running the script
Just run `python main.py`

you can run `python ynab-transaction.py` and `python amazon-transactions.py` directly to test things out and see what it sees.

## How it works
This program automates the process of annotating YNAB transactions with detailed Amazon order information. Here's how it works:

1. **Amazon Transactions Retrieval**: The program logs into your Amazon account using the `amazon-orders` library and retrieves your recent order history and transactions. It matches transactions with corresponding orders based on order numbers.

2. **YNAB Transactions Retrieval**: It connects to your YNAB account via the YNAB API and identifies transactions with a specific payee name (e.g., "Amazon - Needs Memo") that require annotation.

3. **Transaction Matching**: The program compares YNAB transactions with Amazon transactions by matching amounts to find corresponding orders.

4. **Memo Annotation**: For each matched transaction, it generates a detailed memo that includes:
   - A note if the transaction does not represent the full order total.
   - A list of items in the order.
   - A link to the Amazon order details.

5. **Transaction Update**: The program updates the YNAB transaction with the generated memo and changes its payee to a designated name (e.g., "Amazon") to mark it as processed.

6. **Automation**: This process is fully automated, reducing manual effort and ensuring accurate reconciliation of Amazon purchases in your YNAB budget.

The script relies on the `amazon-orders` library for Amazon data and the YNAB API for transaction updates.

There is an important distinction between an Amazon order and an Amazon transaction. When you check out, that is a single order. Often, one order will be fulfilled together, creating a single transaction. However, some orders will generate more than one transaction, which will show up in YNAB separately. This program handles this by adding the same memo to each transaction of that order, which includes a note that the transaction doesn't reflect the entire order.

## Limitations
This script probably won't be able to handle weird edge cases. The amazon-orders library is only able to handle amazon.com and will not pull data from other countries' amazon. Any transactions in the amazon transaction history that don't relate to an amazon.com order will be ignored. As with any tool that relies on web scraping, things can change at any time and it is up to the maintainers of the amazon-orders library to fix things.

## Disclaimer
This script requires your Amazon and YNAB credentials. Use at your own risk and ensure you store your credentials securely. The author is not responsible for any misuse or data breaches.