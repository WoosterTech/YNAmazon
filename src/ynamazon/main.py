from typing import TYPE_CHECKING

from loguru import logger
from rich.console import Console
from rich.prompt import Confirm

from ynamazon.amazon_transactions import (
    AmazonConfig,
    get_amazon_transactions,
    locate_amazon_transaction_by_amount,
)
from ynamazon.exceptions import YnabSetupError
from ynamazon.models.amazon import SimpleAmazonOrder
from ynamazon.models.memo import (
    BaseMemoField,
    BasicMemoField,
    MarkdownMemoField,
)
from ynamazon.settings import settings
from ynamazon.ynab_transactions import default_configuration as ynab_configuration
from ynamazon.ynab_transactions import (
    get_ynab_transactions,
    update_ynab_transaction,
)

if TYPE_CHECKING:
    from ynab import Configuration


# TODO: reduce complexity of this function
def process_transactions(
    amazon_config: AmazonConfig | None = None,
    ynab_config: "Configuration | None" = None,
    budget_id: str | None = None,
    use_markdown: bool | None = None,
) -> None:
    """Match YNAB transactions to Amazon Transactions and optionally update YNAB Memos."""
    amazon_config = amazon_config or AmazonConfig()
    ynab_config = ynab_config or ynab_configuration
    budget_id = budget_id or settings.ynab_budget_id.get_secret_value()
    use_markdown = (
        use_markdown if use_markdown is not None else settings.ynab_use_markdown
    )

    console = Console()

    try:
        ynab_trans, amazon_with_memo_payee = get_ynab_transactions(
            configuration=ynab_config, budget_id=budget_id
        )
    except YnabSetupError:
        console.print("[bold red]No matching Transactions found in YNAB. Exiting.[/]")
        return

    console.print("[cyan]Starting search for Amazon transactions...[/]")
    amazon_trans = get_amazon_transactions()
    console.print(
        f"[green]{len(amazon_trans)} Amazon transactions retrieved successfully.[/]"
    )

    console.print("[cyan]Starting to look for matching transactions...[/]")
    for ynab_tran in ynab_trans:
        console.print(
            f"[cyan]Looking for an Amazon Transaction that matches this YNAB transaction:[/] {ynab_tran.var_date} ${ynab_tran.amount_decimal:.2f}"
        )
        # because YNAB uses "milliunits" for amounts, we need to convert to dollars
        logger.debug(f"YNAB transaction amount [dollars]: {ynab_tran.amount_decimal}")
        amazon_tran_index = locate_amazon_transaction_by_amount(
            amazon_trans=amazon_trans, amount=ynab_tran.amount_decimal
        )
        if not amazon_tran_index:
            console.print(
                "[bold yellow]**** Could not find a matching Amazon Transaction![/]"
            )
            continue

        amazon_tran = amazon_trans[amazon_tran_index]
        console.print(
            f"[green]Matching Amazon Transaction:[/] {amazon_tran.completed_date} ${amazon_tran.transaction_total:.2f}"
        )

        if use_markdown:
            memo_cls: type[BaseMemoField] = MarkdownMemoField
        else:
            memo_cls = BasicMemoField
        memo = memo_cls()
        if amazon_tran.transaction_total != amazon_tran.order_total:
            memo.header.append(
                f"-This transaction doesn't represent the entire order. The order total is ${amazon_tran.order_total:.2f}-"
            )
        memo.items.extend(amazon_tran.items)
        memo.order = SimpleAmazonOrder(
            number=amazon_tran.order_number,
            link=amazon_tran.order_link,
            total=amazon_tran.order_total,
        )

        console.print("[bold u green]Memo:[/]")
        console.print(str(memo))

        if amazon_tran.completed_date != ynab_tran.var_date:
            console.print(
                f"[yellow]**** The dates don't match! YNAB: {ynab_tran.var_date} Amazon: {amazon_tran.completed_date}[/]"
            )
            continue_match = Confirm.ask(
                "[bold red]Continue matching this transaction anyway?[/]",
                console=console,
            )
            if not continue_match:
                console.print("[yellow]Skipping this transaction...[/]")
                continue
            else:
                _ = amazon_trans.pop(amazon_tran_index)
                console.log("Removing matched transaction from search")

        update_transaction = Confirm.ask(
            "[bold cyan]Update YNAB transaction memo?[/]", console=console
        )
        if not update_transaction:
            console.print("[yellow]Skipping YNAB transaction update...[/]\n\n")
            console.print("[cyan i]Memo Preview[/]:")
            console.print(str(memo))
            continue

        console.print("[green]Updating YNAB transaction memo...[/]")

        update_ynab_transaction(
            transaction=ynab_tran,
            memo=str(memo),
            payee_id=amazon_with_memo_payee.id,
        )
        console.print("\n\n")


if __name__ == "__main__":
    process_transactions()
