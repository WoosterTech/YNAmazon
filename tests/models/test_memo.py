from ynamazon.models.memo import truncate_memo  # type: ignore[import-untyped]

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


def test_truncate_memo():
    """Test the truncate_memo function."""
    assert len(truncate_memo(LONG_STRING, max_length=500)) == 500, (
        "Memo should be truncated to 500 characters"
    )
