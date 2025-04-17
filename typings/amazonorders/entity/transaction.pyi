"""This type stub file was generated by pyright."""

from datetime import date
from bs4 import Tag
from amazonorders.conf import AmazonOrdersConfig
from amazonorders.entity.parsable import Parsable

__copyright__ = ...
__license__ = ...
logger = ...

class Transaction(Parsable):
    """An Amazon Transaction."""
    def __init__(
        self, parsed: Tag, config: AmazonOrdersConfig, completed_date: date
    ) -> None: ...
    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...
