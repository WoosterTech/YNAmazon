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
Just run `python main.py`!

you can run `python ynab-transaction.py` and `python amazon-transactions.py` directly to test things out and see what it sees.

## How it works

TODO (or just read the source code :P)

## Limitations

This script probably won't be able to handle weird edge cases. The amazon-orders library is only able to handle amazon.com and will not pull data from other countries' amazon. Any transactions in the amazon transaction history that don't relate to an amazon.com order will be ignored. As with any tool that relies on web scraping, things can change at any time and it is up to the maintainers of the amazon-orders library to fix things.