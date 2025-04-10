from datetime import date, timedelta
from typing import Union
from unittest.mock import MagicMock

import pytest
from amazonorders.entity.item import Item
from amazonorders.entity.order import Order
from faker import Faker

from ynamazon.models.memo import (  # type: ignore[import-untyped]
    BasicMemoField,
    MarkdownMemoField,
    truncate_memo,
)

fake = Faker()

ITEM_TITLE_LIST = [
    "AIRMEGA Max 2 Air Purifier Replacement Filter Set for 300/300S",
    "COWAY AP-1512HH & 200M Air Purifier Filter Replacement, Fresh Starter Pack, 2 Fresh Starter Deodorization Filters and 1 True HEPA Filter, 1 Pack, Black",
    "Chemical Guys ACC138 Secondary Container Dilution Bottle with Heavy Duty Sprayer, 16 oz, 3 Pack",
    "Coway Airmega 150 Air Purifier Replacement Filter Set, Green True HEPA and Active Carbon Filter, AP-1019C-FP",
    "Coway Airmega 230/240 Air Purifier Replacement Filter Set, Max 2 Green True HEPA and Active Carbon Filter",
    "Nakee Butter Focus Nut Butter: High-Protein, Low-Carb Keto Peanut Butter with Cacao & MCT Oil, 12g Protein - On-The-Go, 6 Packs.",
    "ScanSnap iX1600 Wireless or USB High-Speed Cloud Enabled Document, Photo & Receipt Scanner with Large Touchscreen and Auto Document Feeder for Mac or PC, 17 watts, Black",
]


@pytest.fixture
def mock_order():
    order = MagicMock(spec=Order)
    order.number = "123-4567890-1234567"
    order.link = "https://www.amazon.com/gp/your-account/order-details?orderID=123-4567890-1234567"

    return order


@pytest.fixture
def mock_long_items():
    """Create a list of mock items with long titles."""
    return [mock_item(title=title) for title in ITEM_TITLE_LIST]


@pytest.fixture
def mock_basic_memo_field(
    mock_order: Order, mock_long_items: list[Item]
) -> BasicMemoField:
    """Create a mock BasicMemoField with a header and items."""
    memo = BasicMemoField()
    memo.header = "-This transaction doesn't represent the entire order. The order total is $603.41-"
    memo.items = mock_long_items
    memo.order = mock_order

    return memo


@pytest.fixture
def mock_markdown_memo_field(
    mock_order: Order, mock_long_items: list[Item]
) -> MarkdownMemoField:
    """Create a mock MarkdownMemoField with a header and items."""
    memo = MarkdownMemoField()
    memo.header = "-This transaction doesn't represent the entire order. The order total is $603.41-"
    memo.items = mock_long_items
    memo.order = mock_order

    return memo


LONG_STRING = """-This transaction doesn't represent the entire order. The order total is $603.41-
**Items**
1. AIRMEGA Max 2 Air Purifier Replacement Filter Set for 300/300S
2. COWAY AP-1512HH & 200M Air Purifier Filter Replacement, Fresh Starter Pack, 2 Fresh Starter Deodorization Filters and 1 True HEPA Filter, 1 Pack, Black
3. Chemical Guys ACC138 Secondary Container Dilution Bottle with Heavy Duty Sprayer, 16 oz, 3 Pack
4. Coway Airmega 150 Air Purifier Replacement Filter Set, Green True HEPA and Active Carbon Filter, AP-1019C-FP
5. Coway Airmega 230/240 Air Purifier Replacement Filter Set, Max 2 Green True HEPA and Active Carbon Filter
6. Nakee Butter Focus Nut Butter: High-Protein, Low-Carb Keto Peanut Butter with Cacao & MCT Oil, 12g Protein - On-The-Go, 6 Packs.
7. ScanSnap iX1600 Wireless or USB High-Speed Cloud Enabled Document, Photo & Receipt Scanner with Large Touchscreen and Auto Document Feeder for Mac or PC, 17 watts, Black
https://www.amazon.com/gp/your-account/order-details?orderID=113-2607960-6193002"""


def mock_item(title: Union[str, None] = None) -> Item:
    item = MagicMock(spec=Item)
    item.title = title or fake.sentence()
    item.link = fake.url()
    item.price = fake.random_number(digits=2) + 0.99
    item.seller = "Fake Seller"
    item.condition = "New"
    item.return_eligible_date = date(2023, 1, 1) + timedelta(days=30)
    item.image_link = fake.image_url()
    item.quantity = fake.random_int(min=1, max=5)
    return item


def test_truncate_memo():
    """Test the truncate_memo function."""
    assert len(truncate_memo(LONG_STRING, max_length=500)) == 500, (
        "Memo should be truncated to 500 characters"
    )


def test_truncate_basic_memo_field(mock_basic_memo_field: BasicMemoField):
    """Test the truncate_memo function with a BasicMemoField."""
    assert len(str(mock_basic_memo_field)) == 500, (
        "Memo should be truncated to 500 characters"
    )


def test_truncate_markdown_memo_field(mock_markdown_memo_field: MarkdownMemoField):
    """Test the truncate_memo function with a MarkdownMemoField."""
    assert len(str(mock_markdown_memo_field)) == 500, (
        "Memo should be truncated to 500 characters"
    )
