from typing import TYPE_CHECKING

from loguru import logger
from pydantic import BaseModel, Field
from rich.console import Console
from rich.prompt import Confirm

from ynamazon.amazon_transactions import (
    AmazonConfig,
    AmazonTransactionRetriever,
    locate_amazon_transaction_by_amount,
)
from ynamazon.exceptions import YnabSetupError
from ynamazon.settings import settings
from ynamazon.ynab_transactions import default_configuration as ynab_configuration
from ynamazon.ynab_transactions import (
    get_ynab_transactions,
    markdown_formatted_link,
    markdown_formatted_title,
    update_ynab_transaction,
)
try:
    from ynamazon.ynab_memo import process_memo
except ImportError:
    pass

if TYPE_CHECKING:
    from ynab import Configuration


class MultiLineText(BaseModel):
    """A class to handle multi-line text."""

    lines: list[str] = Field(default_factory=list)

    def __str__(self) -> str:
        """Returns the string representation of the object."""
        return "\n".join(self.lines)

    def append(self, line: str) -> None:
        """Appends a line to the text."""
        self.lines.append(line)


# TODO: reduce complexity of this function
def process_transactions(  # noqa: C901
    amazon_config: AmazonConfig | None = None,
    ynab_config: "Configuration | None" = None,
    budget_id: str | None = None,
    force_refresh_amazon: bool = False
) -> None:
    """Match YNAB transactions to Amazon Transactions and optionally update YNAB Memos."""
    amazon_config = amazon_config or AmazonConfig()
    ynab_config = ynab_config or ynab_configuration
    budget_id = budget_id or settings.ynab_budget_id.get_secret_value()

    console = Console()

    try:
        ynab_trans, amazon_with_memo_payee = get_ynab_transactions(
            configuration=ynab_config, budget_id=budget_id
        )
    except YnabSetupError:
        console.print("[bold red]No matching Transactions found in YNAB. Exiting.[/]")
        return

    console.print("[cyan]Starting search for Amazon transactions...[/]")
    amazon_trans = AmazonTransactionRetriever(
        amazon_config=amazon_config,
        force_refresh_amazon=force_refresh_amazon
    ).get_amazon_transactions()

    console.print(
        f"[green]{len(amazon_trans)} Amazon transactions retrieved successfully.[/]"
    )

    console.print("[cyan]Starting to look for matching transactions...[/]")
    for ynab_tran in ynab_trans:
        console.print(
            f"[cyan]Looking for an Amazon Transaction that matches this YNAB transaction:[/] {ynab_tran.var_date} ${ynab_tran.amount / -1000:.2f}"
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

        memo = MultiLineText()
        if amazon_tran.transaction_total != amazon_tran.order_total:
            memo.append(
                f"-This transaction doesn't represent the entire order. The order total is ${amazon_tran.order_total:.2f}-"
            )
        if len(amazon_tran.items) > 1:
            memo.append("**Items**")
            for i, item in enumerate(amazon_tran.items, start=1):
                memo.append(f"{i}. {markdown_formatted_title(item.title, item.link)}")
        elif len(amazon_tran.items) == 1:
            item = amazon_tran.items[0]
            memo.append(f"- {markdown_formatted_title(item.title, item.link)}")

        memo.append(
            markdown_formatted_link(
                f"\nOrder #{amazon_tran.order_number}", amazon_tran.order_link
            )
        )

        console.print("[bold u green]Memo:[/]")
        console.print(str(memo))

        # Only use the AI processing if OpenAI is installed
        if 'process_memo' in globals():
            memo = process_memo(str(memo))

        console.print("[bold u green]Processed Memo:[/]")
        console.print(memo)

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
            memo=memo,
            payee_id=amazon_with_memo_payee.id,
        )
        console.print("\n\n")


if __name__ == "__main__":
    process_transactions()
