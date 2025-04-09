# `yna`

**Usage**:

```console
$ yna [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `print-ynab`: <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">Prints YNAB transactions.</span>
* `print-amazon`: <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">Prints Amazon transactions.</span>
* `ynamazon`: <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">Match YNAB transactions to...</span>

## `yna print-ynab`

<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">Prints YNAB transactions.</span>

<span style="color: #808000; text-decoration-color: #808000; font-style: italic">All arguments will use defaults in .env file if not provided.</span>

**Usage**:

```console
$ yna print-ynab [OPTIONS] [API_KEY] [BUDGET_ID]
```

**Arguments**:

* `[API_KEY]`: YNAB API key  [default: (dynamic)]
* `[BUDGET_ID]`: YNAB Budget ID  [default: (dynamic)]

**Options**:

* `--help`: Show this message and exit.

## `yna print-amazon`

<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">Prints Amazon transactions.</span>

<span style="color: #808000; text-decoration-color: #808000; font-style: italic">All required arguments will use defaults in .env file if not provided.</span>

**Usage**:

```console
$ yna print-amazon [OPTIONS] [USER_EMAIL] [USER_PASSWORD]
```

**Arguments**:

* `[USER_EMAIL]`: Amazon username  [default: (dynamic)]
* `[USER_PASSWORD]`: Amazon password  [default: (dynamic)]

**Options**:

* `-y, --years INTEGER`: Order years; leave empty for current year
* `-d, --days INTEGER`: Days of transactions to retrieve  [default: 31]
* `--help`: Show this message and exit.

## `yna ynamazon`

<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">Match YNAB transactions to Amazon Transactions and optionally update YNAB Memos.</span>

<span style="color: #808000; text-decoration-color: #808000; font-style: italic">All required arguments will use defaults in .env file if not provided.</span>

**Usage**:

```console
$ yna ynamazon [OPTIONS] [YNAB_API_KEY] [YNAB_BUDGET_ID] [AMAZON_USER] [AMAZON_PASSWORD]
```

**Arguments**:

* `[YNAB_API_KEY]`: YNAB API key  [default: (dynamic)]
* `[YNAB_BUDGET_ID]`: YNAB Budget ID  [default: (dynamic)]
* `[AMAZON_USER]`: Amazon username  [default: (dynamic)]
* `[AMAZON_PASSWORD]`: Amazon password  [default: (dynamic)]

**Options**:

* `--help`: Show this message and exit.
