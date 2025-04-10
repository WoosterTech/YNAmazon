from typing import Annotated, Any

from amazonorders.entity.item import Item  # type: ignore[import-untyped]
from amazonorders.entity.order import Order  # type: ignore[import-untyped]
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema


class _AmazonItem:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: "GetCoreSchemaHandler"
    ) -> CoreSchema:
        return core_schema.is_instance_schema(Item)


AmazonItemType = Annotated[Item, _AmazonItem]

__all__ = ["AmazonItemType"]


class _AmazonOrder:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: "GetCoreSchemaHandler"
    ) -> CoreSchema:
        return core_schema.is_instance_schema(Order)


AmazonOrderType = Annotated[Order, _AmazonOrder]
