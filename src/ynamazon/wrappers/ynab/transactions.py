import datetime as dt
import enum

from pydantic import StrictBool, StrictInt, StrictStr

from ynamazon.wrappers.ynab.common import YnabBase, YnabField


class MemoField(YnabField[str]):
    """Memo field for YNAB."""


class TransactionClearedStatus(enum.StrEnum):
    """The cleared status of the transaction."""

    CLEARED = "cleared"
    UNCLEARED = "uncleared"
    RECONCILED = "reconciled"


class TransactionFlagColor(enum.StrEnum):
    """The flag color of the transaction."""

    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"
    PURPLE = "purple"


class BaseTransaction(YnabBase):
    var_date: dt.date | None = None
    amount: StrictInt
    memo: MemoField | None = None
    cleared: TransactionClearedStatus | None = None
    approved: StrictBool | None = None
    flag_color: TransactionFlagColor | None = None
    account_id: StrictStr | None = None
    payee_id: StrictStr | None = None
