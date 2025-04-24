import abc
from decimal import Decimal
import enum
from typing import Annotated, Any, Generic, TypeVar
from pydantic import (
    BaseModel,
    ConfigDict,
    StrictBool,
    StrictInt,
    StrictStr,
    model_validator,
)
import datetime as dt


class YnabBase(BaseModel, abc.ABC):
    """Base class for YNAB."""

    model_config = ConfigDict(from_attributes=True)


_F = TypeVar("_F")


class Field(BaseModel, Generic[_F], abc.ABC):
    value: _F

    @model_validator(mode="before")
    @classmethod
    def from_value(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return {"value": data}
        return data


class AccountType(enum.StrEnum):
    """The type of account."""

    CHECKING = "checking"
    SAVINGS = "savings"
    CASH = "cash"
    CREDIT_CARD = "creditCard"
    LOAN = "loan"
    INVESTMENT = "investment"
    OTHER_ASSET = "otherAsset"
    OTHER_LIABILITY = "otherLiability"
    MORTGAGE = "mortgage"
    AUTO_LOAN = "autoLoan"
    STUDENT_LOAN = "studentLoan"
    PERSONAL_LOAN = "personalLoan"
    MEDICAL_DEBT = "medicalDebt"
    OTHER_DEBUG = "otherDebt"


class Account(YnabBase):
    id: StrictStr
    name: StrictStr
    account_type: Annotated[AccountType, Field(validation_alias="type")]
    on_budget: StrictBool
    closed: StrictBool
    note: StrictStr | None = None
    balance: StrictInt
    cleared_balance: StrictInt
    uncleared_balance: StrictInt
    transfer_payee: "Payee" | None = None
    direct_import_linked: StrictBool | None = None
    direct_import_in_error: StrictBool | None = None
    last_reconciled_at: dt.datetime | None = None
    debt_original_balance: StrictInt | None = None

    def _milliunit_to_decimal(self, field_name: str) -> Decimal:
        """Convert milliunit to decimal."""
        return getattr(self, field_name) / Decimal("1000")

    @property
    def balance_decimal(self) -> Decimal:
        """Returns the balance in currency."""
        return self._milliunit_to_decimal("balance")

    @property
    def cleared_balance_decimal(self) -> Decimal:
        """Returns the cleared balance in currency."""
        return self._milliunit_to_decimal("cleared_balance")

    @property
    def uncleared_balance_decimal(self) -> Decimal:
        """Returns the uncleared balance in currency."""
        return self._milliunit_to_decimal("uncleared_balance")


class Payee(YnabBase):
    id: StrictStr
    name: StrictStr


class MemoField(Field[str]):
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
