from typing import Union

from pydantic import BaseModel

from ynamazon.wrappers.ynab import MemoField


class TransactionMemo(BaseModel):
    _value: Union[str, None] = None
