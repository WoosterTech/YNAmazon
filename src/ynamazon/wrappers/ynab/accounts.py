import datetime as dt
import enum
from decimal import Decimal
from typing import Annotated, Union

from pydantic import Field, StrictBool, StrictInt, StrictStr

from ynamazon.wrappers.ynab.common import YnabBase
from ynamazon.wrappers.ynab.payees import Payee


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
    transfer_payee: Union[Payee, None] = None
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
