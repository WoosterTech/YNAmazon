from pydantic import StrictStr

from ynamazon.wrappers.ynab.common import YnabBase


class Payee(YnabBase):
    id: StrictStr
    name: StrictStr
