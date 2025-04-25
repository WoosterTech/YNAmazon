from typing import TYPE_CHECKING
from unittest.mock import patch

from ynamazon.ynab_transactions import (  # type: ignore[import-untyped]
    markdown_formatted_link,
    markdown_formatted_title,
)

if TYPE_CHECKING:
    from ynamazon.settings import Settings  # type: ignore[import-untyped]


@patch("ynamazon.ynab_transactions.settings")
def test_markdown_formatted_link_use_markdown(mock_settings: "Settings"):
    mock_settings.ynab_use_markdown = True

    title = "Test Title"
    url = "https://example.com"
    expected_result = f"[{title}]({url})"

    assert markdown_formatted_link(title, url) == expected_result


@patch("ynamazon.ynab_transactions.settings")
def test_markdown_formatted_link_no_markdown(mock_settings: "Settings"):
    mock_settings.ynab_use_markdown = False

    title = "Test Title"
    url = "https://example.com"
    expected_result = url

    assert markdown_formatted_link(title, url) == expected_result


@patch("ynamazon.ynab_transactions.settings")
def test_markdown_formatted_title_use_markdown(mock_settings: "Settings"):
    mock_settings.ynab_use_markdown = True

    title = "Test Title"
    url = "https://example.com"
    expected_result = f"[{title}]({url})"

    assert markdown_formatted_title(title, url) == expected_result


@patch("ynamazon.ynab_transactions.settings")
def test_markdown_formatted_title_no_markdown(mock_settings: "Settings"):
    mock_settings.ynab_use_markdown = False

    title = "Test Title"
    url = "https://example.com"
    expected_result = title

    assert markdown_formatted_title(title, url) == expected_result
