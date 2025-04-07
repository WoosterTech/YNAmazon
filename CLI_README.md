# `YNAmazon`

**Usage**:

```console
$ YNAmazon [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `print-ynab-transactions`: Prints YNAB transactions.
* `print-amazon-transactions`: Prints Amazon transactions.
* `ynamazon`: Match YNAB transactions to Amazon...

## `YNAmazon print-ynab-transactions`

Prints YNAB transactions.

All arguments will use defaults in .env file if not provided.

Arguments:
    api_key: YNAB API key.
    budget_id: YNAB Budget ID.
    needs_memo_payee: YNAB Payee Name to be processed.
    completed_payee: YNAB Payee Name completed.

**Usage**:

```console
$ YNAmazon print-ynab-transactions [OPTIONS] [API_KEY] [BUDGET_ID]
```

**Arguments**:

* `[API_KEY]`: YNAB API key  [default: (dynamic)]
* `[BUDGET_ID]`: YNAB Budget ID  [default: (dynamic)]

**Options**:

* `--help`: Show this message and exit.

## `YNAmazon print-amazon-transactions`

Prints Amazon transactions.

All required arguments will use defaults in .env file if not provided.

Arguments:
    user_email: Amazon username.
    user_password: Amazon password.
    order_years: Order years; leave empty for current year.
    transaction_days: Days of transactions to retrieve.

**Usage**:

```console
$ YNAmazon print-amazon-transactions [OPTIONS] [USER_EMAIL] [USER_PASSWORD]
```

**Arguments**:

* `[USER_EMAIL]`: Amazon username  [default: (dynamic)]
* `[USER_PASSWORD]`: Amazon password  [default: (dynamic)]

**Options**:

* `-y, --years INTEGER`: Order years; leave empty for current year
* `-d, --days INTEGER`: Days of transactions to retrieve  [default: 31]
* `--help`: Show this message and exit.

## `YNAmazon ynamazon`

Match YNAB transactions to Amazon Transactions and optionally update YNAB Memos.

All required arguments will use defaults in .env file if not provided.

Arguments:
    ynab_api_key: YNAB API key.
    ynab_budget_id: YNAB Budget ID.
    amazon_user: Amazon username.
    amazon_password: Amazon password.

**Usage**:

```console
$ YNAmazon ynamazon [OPTIONS] [YNAB_API_KEY] [YNAB_BUDGET_ID] [AMAZON_USER] [AMAZON_PASSWORD]
```

**Arguments**:

* `[YNAB_API_KEY]`: YNAB API key  [default: (dynamic)]
* `[YNAB_BUDGET_ID]`: YNAB Budget ID  [default: (dynamic)]
* `[AMAZON_USER]`: Amazon username  [default: (dynamic)]
* `[AMAZON_PASSWORD]`: Amazon password  [default: (dynamic)]

**Options**:

* `--help`: Show this message and exit.
