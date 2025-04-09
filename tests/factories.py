from polyfactory.factories.pydantic_factory import ModelFactory
from ynab.models.budget_detail import BudgetDetail
from ynab.models.hybrid_transaction import HybridTransaction
from ynab.models.payee import Payee


class PayeeFactory(ModelFactory[Payee]): ...


amazon_payee = PayeeFactory.build(name="Amazon")
amazon_needs_memo_payee = PayeeFactory.build(name="Amazon Needs Memo")


class BudgetFactory(ModelFactory[BudgetDetail]):
    payees = [amazon_payee, amazon_needs_memo_payee]  # noqa: RUF012


class HybridTransactionFactory(ModelFactory[HybridTransaction]): ...


class NeedsMemoHybridTransactionFactory(HybridTransactionFactory):
    payee_id: str = amazon_needs_memo_payee.id


class AmazonTransactionFactory(HybridTransactionFactory):
    payee_id: str = amazon_payee.id
