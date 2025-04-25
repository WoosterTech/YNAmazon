from ynamazon.ynab_transactions import (  # type: ignore[import-untyped]
    markdown_formatted_link,
    markdown_formatted_title,
)


def test_markdown_formatted_link_use_markdown(monkeypatch):
    monkeypatch.setenv("YNAB_USE_MARKDOWN", "True")

    title = "Test Title"
    url = "https://example.com"
    expected_result = f"[{title}]({url})"

    assert markdown_formatted_link(title, url) == expected_result


def test_markdown_formatted_link_no_markdown(monkeypatch):
    monkeypatch.setenv("YNAB_USE_MARKDOWN", "False")

    title = "Test Title"
    url = "https://example.com"
    expected_result = url

    assert markdown_formatted_link(title, url) == expected_result


def test_markdown_formatted_title_use_markdown(monkeypatch):
    monkeypatch.setenv("YNAB_USE_MARKDOWN", "True")

    title = "Test Title"
    url = "https://example.com"
    expected_result = f"[{title}]({url})"

    assert markdown_formatted_title(title, url) == expected_result


def test_markdown_formatted_title_no_markdown(monkeypatch):
    monkeypatch.setenv("YNAB_USE_MARKDOWN", "False")

    title = "Test Title"
    url = "https://example.com"
    expected_result = title

    assert markdown_formatted_title(title, url) == expected_result
