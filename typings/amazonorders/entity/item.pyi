from typing import TypeVar, override

from amazonorders.conf import AmazonOrdersConfig
from amazonorders.entity.parsable import Parsable
from bs4 import Tag

ItemEntity = TypeVar("ItemEntity", bound="Item")

class Item(Parsable):
    def __init__(self, parsed: Tag, config: AmazonOrdersConfig) -> None: ...
    @override
    def __repr__(self) -> str: ...
    @override
    def __str__(self) -> str: ...
    def __lt__(self, other: Item) -> bool: ...
