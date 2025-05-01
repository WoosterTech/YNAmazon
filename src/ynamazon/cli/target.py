from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from target_orders import get_orders

app = typer.Typer(rich_markup_mode="rich")


@app.command()
def print_transactions(
    cookies_path: Annotated[
        Path | None,
        typer.Option(
            "--cookies-path",
            help="Path to the json file.",
            exists=True,
            dir_okay=False,
        ),
    ] = None,
    delay: Annotated[
        int,
        typer.Option(
            "--delay", help="Number of seconds to wait for Orders page to laod."
        ),
    ] = 5,
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            help="Enable debug mode.",
            is_eager=True,
            is_flag=True,
        ),
    ] = False,
) -> None:
    """Print transactions from the cookies file."""
    console = Console()
    orders = get_orders(cookies_path=cookies_path, loading_delay=delay)

    console.print(orders)
