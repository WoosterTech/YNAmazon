from decimal import Decimal

from pydantic import AnyUrl, BaseModel


class SimpleAmazonOrder(BaseModel):
    number: str
    link: AnyUrl
    total: Decimal
