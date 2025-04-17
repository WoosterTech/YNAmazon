"""This type stub file was generated by pyright."""

from typing import TypeVar
from bs4 import Tag
from amazonorders.conf import AmazonOrdersConfig
from amazonorders.entity.parsable import Parsable

__copyright__ = ...
__license__ = ...
logger = ...
ItemEntity = TypeVar("ItemEntity", bound="Item")

class Item(Parsable):
    """An Item in an Amazon :class:`~amazonorders.entity.order.Order`."""
    def __init__(self, parsed: Tag, config: AmazonOrdersConfig) -> None: ...
    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...
    def __lt__(self, other: ItemEntity) -> bool: ...
