import abc
from typing import ClassVar

from pydantic import BaseModel, Field

from ynamazon.models.amazon import SimpleAmazonOrder
from ynamazon.types_pydantic import AmazonItemType

YNAB_MAX_MEMO_LENGTH = 500  # YNAB's character limit


class MultiLineText(BaseModel):
    """A class to handle multi-line text."""

    lines: list[str] = Field(default_factory=list)

    @classmethod
    def from_string(cls, text: str) -> "MultiLineText":
        """Creates an instance from a string."""
        return cls(lines=text.splitlines())

    def __str__(self) -> str:
        """Returns the string representation of the object."""
        return "\n".join(self.lines)

    def append(self, line: str) -> None:
        """Appends a line to the text."""
        self.lines.append(line)

    @property
    def is_empty(self) -> bool:
        """Checks if the text is empty."""
        return not self.lines


class BaseMemoField(BaseModel, abc.ABC):
    header: MultiLineText = MultiLineText()
    items: list[AmazonItemType] = Field(default_factory=list)
    order: SimpleAmazonOrder | None = None

    _use_markdown: ClassVar[bool]

    @abc.abstractmethod
    def render_items(self) -> str:
        """Renders the items in the memo field."""
        pass

    @abc.abstractmethod
    def render_order_info(self) -> str:
        """Renders the order information."""
        pass

    def __str__(self) -> str:
        segments = [str(self.header)] if self.header else []
        segments.append(self.render_items())
        segments.append(self.render_order_info())
        memo = "\n".join(segments)
        return truncate_memo(memo)

    def get_length(self) -> int:
        """Returns the length of the memo."""
        return len(str(self))


class BasicMemoField(BaseMemoField):
    _use_markdown = False

    def render_items(self):
        if len(self.items) > 1:
            item_lines = []
            for idx, item in enumerate(self.items, start=1):
                item_lines.append(f"{idx}. {item.title}")
            return "\n".join(item_lines)
        return f"- {self.items[0].title}"

    def render_order_info(self):
        assert self.order is not None, "Order information is not available."
        return self.order.link


class MarkdownMemoField(BaseMemoField):
    _use_markdown = True

    def render_items(self):
        if len(self.items) > 1:
            item_lines = []
            for idx, item in enumerate(self.items, start=1):
                item_lines.append(f"{idx}. [{item.title}]({item.link})")
            return "\n".join(item_lines)
        return f"- [{self.items[0].title}]({self.items[0].link})"

    def render_order_info(self):
        assert self.order is not None, "Order information is not available."
        return f"[Order #{self.order.number}]({self.order.link})"


def truncate_memo(memo: str, *, max_length: int = YNAB_MAX_MEMO_LENGTH) -> str:
    """Ensure memo doesn't exceed YNAB's character limit by truncating each line proportionally.

    Args:
        memo (str): The full memo text
        max_length (int): The maximum allowed length for the memo

            (default is YNAB_MAX_MEMO_LENGTH)

    Returns:
        str: Truncated memo with each line shortened proportionally if needed
    """
    # Keep this check for function's integrity as a standalone utility
    if len(memo) <= max_length:
        return memo

    # Split the memo into lines
    lines = memo.split("\n")

    # Calculate how many characters need to be removed
    excess_chars = len(memo) - max_length

    # Count total characters in item lines (excluding warning and URL lines)
    item_lines = []
    non_item_lines = []

    for line in lines:
        # Identify item lines (numbered items)
        if line.strip() and (line.strip()[0].isdigit() and ". " in line):
            item_lines.append(line)
        else:
            non_item_lines.append(line)

    # If no item lines found, fall back to simple truncation
    if not item_lines:
        return memo[: max_length - 12] + " [truncated]"

    # Calculate characters to remove from each item line
    chars_per_line = excess_chars // len(item_lines)

    # Truncate each item line
    new_lines = []
    for line in lines:
        if line in item_lines:
            # For numbered items, preserve the numbering, truncate the content
            parts = line.split(". ", 1)
            if len(parts) == 2 and len(parts[1]) > chars_per_line + 3:
                truncated_item = (
                    parts[0] + ". " + parts[1][: -(chars_per_line + 3)] + "..."
                )
                new_lines.append(truncated_item)
            else:
                new_lines.append(line)  # Line too short to truncate
        else:
            new_lines.append(line)  # Don't truncate non-item lines

    result = "\n".join(new_lines)

    # Final check - if we're still over the limit, do a simple truncation
    if len(result) > max_length:
        return result[: max_length - 12] + " [truncated]"

    return result
