import abc
from typing import ClassVar

from pydantic import BaseModel, Field

from ynamazon.models.amazon import SimpleAmazonOrder
from ynamazon.types_pydantic import AmazonItemType


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
        return "\n".join(segments)


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
