"""Test script for memo truncation and summarization.

To run this test:
    python -m tests.test_memo_truncation

This script tests how memos are truncated and summarized, with examples of both
markdown and non-markdown formatted memos.

Example Memos:

1. Without Markdown:
-This transaction doesn't represent the entire order. The order total is $603.41-
**Items**
1. AIRMEGA Max 2 Air Purifier Replacement Filter Set for 300/300S
2. COWAY AP-1512HH & 200M Air Purifier Filter Replacement, Fresh Starter Pack, 2 Fresh Starter 
Deodorization Filters and 1 True HEPA Filter, 1 Pack, Black
3. Chemical Guys ACC138 Secondary Container Dilution Bottle with Heavy Duty Sprayer, 16 oz, 3 
Pack
4. Coway Airmega 150 Air Purifier Replacement Filter Set, Green True HEPA and Active Carbon 
Filter, AP-1019C-FP
5. Coway Airmega 230/240 Air Purifier Replacement Filter Set, Max 2 Green True HEPA and Active 
Carbon Filter
6. Nakee Butter Focus Nut Butter: High-Protein, Low-Carb Keto Peanut Butter with Cacao & MCT 
Oil, 12g Protein - On-The-Go, 6 Packs.
7. ScanSnap iX1600 Wireless or USB High-Speed Cloud Enabled Document, Photo & Receipt Scanner 
with Large Touchscreen and Auto Document Feeder for Mac or PC, 17 watts, Black
https://www.amazon.com/gp/your-account/order-details?orderID=113-2607970-8010001

2. With Markdown:
-This transaction doesn't represent the entire order. The order total is $603.41-

**Items**
1. [AIRMEGA Max 2 Air Purifier Replacement Filter Set for 
300/300S](https://www.amazon.com/dp/B01C9RIAEE?ref=ppx_yo2ov_dt_b_fed_asin_title)
2. [COWAY AP-1512HH & 200M Air Purifier Filter Replacement, Fresh Starter Pack, 2 Fresh Starter
Deodorization Filters and 1 True HEPA Filter, 1 Pack, 
Black](https://www.amazon.com/dp/B00C7WMQTW?ref=ppx_yo2ov_dt_b_fed_asin_title)
3. [Chemical Guys ACC138 Secondary Container Dilution Bottle with Heavy Duty Sprayer, 16 oz, 3 
Pack](https://www.amazon.com/dp/B06WVJG4H8?ref=ppx_yo2ov_dt_b_fed_asin_title)
4. [Coway Airmega 150 Air Purifier Replacement Filter Set, Green True HEPA and Active Carbon 
Filter, AP-1019C-FP](https://www.amazon.com/dp/B08JPCDVK8?ref=ppx_yo2ov_dt_b_fed_asin_title)
5. [Coway Airmega 230/240 Air Purifier Replacement Filter Set, Max 2 Green True HEPA and Active
Carbon Filter](https://www.amazon.com/dp/B0B9WX6L97?ref=ppx_yo2ov_dt_b_fed_asin_title)
6. [Nakee Butter Focus Nut Butter: High-Protein, Low-Carb Keto Peanut Butter with Cacao & MCT 
Oil, 12g Protein - On-The-Go, 6 
Packs.](https://www.amazon.com/dp/B072FGTT8P?ref=ppx_yo2ov_dt_b_fed_asin_title)
7. [ScanSnap iX1600 Wireless or USB High-Speed Cloud Enabled Document, Photo & Receipt Scanner 
with Large Touchscreen and Auto Document Feeder for Mac or PC, 17 watts, 
Black](https://www.amazon.com/dp/B08PH5Q51P?ref=ppx_yo2ov_dt_b_fed_asin_title)
[Order 
#113-2607960-6193002](https://www.amazon.com/gp/your-account/order-details?orderID=113-2607960-
6193002)
"""

from rich.console import Console
from rich.panel import Panel
import re

from ynamazon.memo_truncation import truncate_memo, summarize_memo_with_ai

console = Console()
YNAB_MEMO_LIMIT = 500  # YNAB's character limit for memos

def extract_url(memo: str) -> str:
    """Extract the Amazon order URL from the memo."""
    # Look for URLs in the format of Amazon order details
    url_pattern = r'https://www\.amazon\.com/gp/your-account/order-details\?orderID=[\w-]+'
    match = re.search(url_pattern, memo)
    if match:
        return match.group(0)
    return ""

def test_memo_truncation(memo: str, memo_type: str) -> None:
    """Test memo truncation with the given memo text.
    
    Args:
        memo: The memo text to test
        memo_type: Description of the memo type (e.g., "Without Markdown", "With Markdown")
    """
    console.print(f"\n[bold cyan]Testing {memo_type} Memo:[/]")
    console.print("\n[bold cyan]Original Memo:[/]")
    console.print(Panel(memo, title="Original", border_style="cyan"))
    
    console.print("\n[bold green]After Truncation:[/]")
    truncated = truncate_memo(memo)
    console.print(Panel(truncated, title="Truncated", border_style="green"))
    
    console.print("\n[bold yellow]After AI Summarization:[/]")
    order_url = extract_url(memo)
    summarized = summarize_memo_with_ai(memo, order_url)
    console.print(Panel(summarized, title="AI Summarized", border_style="yellow"))
    
    console.print(f"\n[bold]Lengths:[/]")
    console.print(f"Original: {len(memo)} characters")
    console.print(f"Truncated: {len(truncated)} characters")
    console.print(f"Summarized: {len(summarized)} characters")

if __name__ == "__main__":
    # Test memos
    memo_without_markdown = """-This transaction doesn't represent the entire order. The order total is $603.41-
**Items**
1. AIRMEGA Max 2 Air Purifier Replacement Filter Set for 300/300S
2. COWAY AP-1512HH & 200M Air Purifier Filter Replacement, Fresh Starter Pack, 2 Fresh Starter 
Deodorization Filters and 1 True HEPA Filter, 1 Pack, Black
3. Chemical Guys ACC138 Secondary Container Dilution Bottle with Heavy Duty Sprayer, 16 oz, 3 
Pack
4. Coway Airmega 150 Air Purifier Replacement Filter Set, Green True HEPA and Active Carbon 
Filter, AP-1019C-FP
5. Coway Airmega 230/240 Air Purifier Replacement Filter Set, Max 2 Green True HEPA and Active 
Carbon Filter
6. Nakee Butter Focus Nut Butter: High-Protein, Low-Carb Keto Peanut Butter with Cacao & MCT 
Oil, 12g Protein - On-The-Go, 6 Packs.
7. ScanSnap iX1600 Wireless or USB High-Speed Cloud Enabled Document, Photo & Receipt Scanner 
with Large Touchscreen and Auto Document Feeder for Mac or PC, 17 watts, Black
https://www.amazon.com/gp/your-account/order-details?orderID=113-2607970-8010001"""

    memo_with_markdown = """-This transaction doesn't represent the entire order. The order total is $603.41-

**Items**
1. [AIRMEGA Max 2 Air Purifier Replacement Filter Set for 
300/300S](https://www.amazon.com/dp/B01C9RIAEE?ref=ppx_yo2ov_dt_b_fed_asin_title)
2. [COWAY AP-1512HH & 200M Air Purifier Filter Replacement, Fresh Starter Pack, 2 Fresh Starter
Deodorization Filters and 1 True HEPA Filter, 1 Pack, 
Black](https://www.amazon.com/dp/B00C7WMQTW?ref=ppx_yo2ov_dt_b_fed_asin_title)
3. [Chemical Guys ACC138 Secondary Container Dilution Bottle with Heavy Duty Sprayer, 16 oz, 3 
Pack](https://www.amazon.com/dp/B06WVJG4H8?ref=ppx_yo2ov_dt_b_fed_asin_title)
4. [Coway Airmega 150 Air Purifier Replacement Filter Set, Green True HEPA and Active Carbon 
Filter, AP-1019C-FP](https://www.amazon.com/dp/B08JPCDVK8?ref=ppx_yo2ov_dt_b_fed_asin_title)
5. [Coway Airmega 230/240 Air Purifier Replacement Filter Set, Max 2 Green True HEPA and Active
Carbon Filter](https://www.amazon.com/dp/B0B9WX6L97?ref=ppx_yo2ov_dt_b_fed_asin_title)
6. [Nakee Butter Focus Nut Butter: High-Protein, Low-Carb Keto Peanut Butter with Cacao & MCT 
Oil, 12g Protein - On-The-Go, 6 
Packs.](https://www.amazon.com/dp/B072FGTT8P?ref=ppx_yo2ov_dt_b_fed_asin_title)
7. [ScanSnap iX1600 Wireless or USB High-Speed Cloud Enabled Document, Photo & Receipt Scanner 
with Large Touchscreen and Auto Document Feeder for Mac or PC, 17 watts, 
Black](https://www.amazon.com/dp/B08PH5Q51P?ref=ppx_yo2ov_dt_b_fed_asin_title)
[Order 
#113-2607960-6193002](https://www.amazon.com/gp/your-account/order-details?orderID=113-2607960-
6193002)"""

    # Test both memos
    test_memo_truncation(memo_without_markdown, "Without Markdown")
    test_memo_truncation(memo_with_markdown, "With Markdown") 