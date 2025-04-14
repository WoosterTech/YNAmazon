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
from ynamazon.ynab_memo import process_memo, truncate_memo
from ynamazon.settings import settings

def test_memo_truncation():
    """Test memo truncation functionality."""
    console = Console()
    
    # Store original settings to restore later
    original_ai = settings.use_ai_summarization
    original_markdown = settings.ynab_use_markdown
    
    # Check if OpenAI key is available
    has_openai_key = bool(settings.openai_api_key.get_secret_value())
    if not has_openai_key:
        console.print("[yellow]OpenAI API key not found. Skipping AI summarization tests.[/]")
    
    try:
        # Test without markdown
        test_memo = """
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
"""
        console.print("\n[bold]Testing Plain Text Memo[/]")
        console.print(Panel(test_memo, title="Original"))
        
        # Test with AI summarization if available
        if has_openai_key:
            settings.use_ai_summarization = True
            settings.ynab_use_markdown = False
            console.print("\n[bold cyan]AI Summarized Version (Plain Text):[/]")
            processed = process_memo(test_memo)
            console.print(Panel(processed, title="AI Summarized"))
        
        # Test truncation
        settings.use_ai_summarization = False
        console.print("\n[bold cyan]Truncated Version (Plain Text):[/]")
        truncated = process_memo(test_memo)
        console.print(Panel(truncated, title="Truncated"))
        
        # Test with markdown
        test_memo_markdown = """
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
        console.print("\n[bold]Testing Markdown Memo[/]")
        console.print(Panel(test_memo_markdown, title="Original"))
        
        # Test with AI summarization if available
        if has_openai_key:
            settings.use_ai_summarization = True
            settings.ynab_use_markdown = True
            console.print("\n[bold cyan]AI Summarized Version (Markdown):[/]")
            processed_markdown = process_memo(test_memo_markdown)
            console.print(Panel(processed_markdown, title="AI Summarized"))
        
        # Test truncation
        settings.use_ai_summarization = False
        console.print("\n[bold cyan]Truncated Version (Markdown):[/]")
        truncated_markdown = process_memo(test_memo_markdown)
        console.print(Panel(truncated_markdown, title="Truncated"))
        
    finally:
        # Restore original settings
        settings.use_ai_summarization = original_ai
        settings.ynab_use_markdown = original_markdown

if __name__ == "__main__":
    test_memo_truncation() 