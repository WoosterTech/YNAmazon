"""Functions for truncating and summarizing memos to fit YNAB's character limit."""

from loguru import logger
import re
from typing import List
from openai import OpenAI
from ynamazon.settings import settings
from ynamazon.prompts import (
    AMAZON_SUMMARY_SYSTEM_PROMPT, 
    AMAZON_SUMMARY_PLAIN_PROMPT, 
    AMAZON_SUMMARY_MARKDOWN_PROMPT
)
from rich.console import Console

# Constants
YNAB_MEMO_LIMIT = 500  # YNAB's character limit for memos


def generate_ai_summary(
    items: List[str],
    order_url: str,
    order_total: str = None,
    transaction_amount: str = None,
    max_length: int = 500
) -> str:
    """
    Uses OpenAI to generate a concise human-readable memo that fits within the character limit.
    
    Args:
        items: List of item descriptions
        order_url: Amazon order URL
        order_total: Total order amount (if different from transaction)
        transaction_amount: Current transaction amount
        max_length: Maximum allowed characters (default: 500)
    
    Returns:
        A human-readable memo summarized by AI
    """
    # Check if OpenAI key is available
    if not settings.openai_api_key.get_secret_value():
        logger.warning("OpenAI API key not found. Skipping AI summarization.")
        return None
    
    # Create client
    client = OpenAI(api_key=settings.openai_api_key.get_secret_value())
    
    # Prepare content for summarization
    partial_order_note = ""
    if order_total and transaction_amount and order_total != transaction_amount:
        partial_order_note = (f"-This transaction doesn't represent the entire order. The order total is ${order_total}-")
    
    # Format items as text for the prompt
    items_text = "\n".join([f"- {item}" for item in items])
    
    # Select the appropriate prompt based on markdown setting
    user_prompt = AMAZON_SUMMARY_MARKDOWN_PROMPT if settings.ynab_use_markdown else AMAZON_SUMMARY_PLAIN_PROMPT
    
    # Add the items to the prompt
    full_prompt = f"{user_prompt}\n\nOrder Details:\n{items_text}"
    
    try:
        # Get the response from OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": AMAZON_SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": full_prompt}
            ]
        )
        
        summary = response.choices[0].message.content.strip()
        
        # Combine all parts
        memo = ""
        if partial_order_note and not settings.suppress_partial_order_warning:
            memo += f"{partial_order_note}\n\n"
        
        # Calculate available space for summary (leaving room for URL)
        url_length = len(order_url) + 1  # +1 for newline
        available_space = max_length - url_length
        if partial_order_note:
            available_space -= len(partial_order_note) + 2  # +2 for newlines
        
        # If summary is too long, truncate it
        if len(summary) > available_space:
            summary = summary[:available_space-3] + "..."
        
        memo += f"{summary}\n{order_url}"
            
        return memo
        
    except Exception as e:
        logger.error(f"Error using OpenAI API: {str(e)}")
        return None


def normalize_memo(memo: str) -> str:
    """Normalize a memo by joining any split lines that contain a URL."""
    lines = memo.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    result = []
    current_line = ""
    in_url = False
    
    for line in lines:
        stripped = line.strip()
        if "amazon.com" in line:
            current_line += stripped
            in_url = True
        elif in_url and (stripped.endswith("-") or stripped.endswith(")")):
            # If we're in a URL and the line ends with a hyphen or closing parenthesis
            current_line += stripped
            if stripped.endswith(")"):
                in_url = False
                result.append(current_line)
                current_line = ""
        elif in_url:
            # If we're in a URL but the line doesn't end with a hyphen
            current_line += stripped
        else:
            if current_line:
                result.append(current_line)
                current_line = ""
            result.append(line)
    
    if current_line:
        result.append(current_line)
    
    return "\n".join(result)


def extract_order_url(memo: str) -> str:
    """Extract the Amazon order URL from a memo, handling both markdown and non-markdown formats."""
    # First normalize the memo to handle split lines
    normalized_memo = normalize_memo(memo)
    
    # First try to find a markdown URL
    markdown_url_match = re.search(r'\[Order\s*#[\w-]+\]\((https://www\.amazon\.com/gp/your-account/order-details\?orderID=[\w-]+)\)', normalized_memo)
    if markdown_url_match:
        return markdown_url_match.group(1)
    
    # If no markdown URL found, look for a plain URL
    plain_url_match = re.search(r'https://www\.amazon\.com/gp/your-account/order-details\?orderID=[\w-]+', normalized_memo)
    if plain_url_match:
        return plain_url_match.group(0)
    
    return None


def truncate_memo(memo: str) -> str:
    """Truncate a memo to fit within YNAB's character limit while preserving important information."""
    if len(memo) <= YNAB_MEMO_LIMIT:
        return memo

    # Extract the URL first
    url_line = extract_order_url(memo)
    
    # Strip all markdown formatting
    clean_memo = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', memo)  # Remove markdown links
    clean_memo = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean_memo)  # Remove bold
    
    # Normalize line endings and split into lines
    lines = [line.strip() for line in clean_memo.replace("\r\n", "\n").split("\n") if line.strip()]
    
    multi_order_line = next((line for line in lines if line.startswith("-This transaction")), None)
    items_header = next((line for line in lines if line == "Items"), None)
    
    # Process item lines
    item_lines = []
    for line in lines:
        if line[0].isdigit() and ". " in line:
            item_lines.append(line)
    
    # Calculate how many characters we need to remove, excluding the URL
    current_length = sum(len(line) + 1 for line in [multi_order_line, items_header] + item_lines if line)
    
    if current_length > YNAB_MEMO_LIMIT - len(url_line) - 1:  # -1 for newline
        # Calculate how many characters to remove from each item line
        chars_to_remove = current_length - (YNAB_MEMO_LIMIT - len(url_line) - 1)
        chars_per_line = chars_to_remove // len(item_lines)
        
        # Truncate each item line
        truncated_items = []
        for line in item_lines:
            num, text = line.split(". ", 1)
            truncated_text = text[:len(text)-chars_per_line] + "..."
            truncated_items.append(f"{num}. {truncated_text}")
        
        # Build the result
        result = []
        if multi_order_line:
            result.append(multi_order_line)
        if items_header:
            result.append(items_header)
        result.extend(truncated_items)
        if url_line:
            result.append(url_line)
        
        return "\n".join(result)
    
    # If we're under the limit, return the cleaned memo
    result = []
    if multi_order_line:
        result.append(multi_order_line)
    if items_header:
        result.append(items_header)
    result.extend(item_lines)
    if url_line:
        result.append(url_line)
    
    return "\n".join(result)


def summarize_memo_with_ai(memo: str, order_url: str) -> str:
    """Summarize a memo using AI, ensuring it fits within YNAB's character limit."""
    # Strip markdown formatting
    clean_memo = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', memo)  # Remove markdown links
    clean_memo = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean_memo)  # Remove bold
    
    # Extract items and order URL from memo
    lines = clean_memo.split("\n")
    items = []
    order_total = None
    transaction_amount = None
    
    for line in lines:
        if line.strip() and line.strip()[0].isdigit() and ". " in line:
            items.append(line)
        elif "order total is $" in line:
            order_total = line.split("$")[-1].strip()
        elif "transaction doesn't represent" in line:
            transaction_amount = line.split("$")[-1].strip()
    
    # Generate AI summary
    summary = generate_ai_summary(
        items=items,
        order_url=order_url,
        order_total=order_total,
        transaction_amount=transaction_amount
    )
    
    # If summary is still too long, truncate it
    if len(summary) > YNAB_MEMO_LIMIT:
        logger.warning(f"AI summary still exceeds {YNAB_MEMO_LIMIT} characters ({len(summary)}). Truncating.")
        return truncate_memo(summary)
    
    return summary


def summarize_memo(memo: str) -> str:
    """Summarize a memo using AI if enabled, otherwise use truncation."""
    if settings.use_ai_summarization:
        logger.info("Using AI summarization for memo")
        # Extract order URL from memo
        order_url = extract_order_url(memo)
        
        if not order_url:
            logger.warning("Could not find order URL in memo, falling back to truncation")
            return truncate_memo(memo)
            
        # Strip all markdown formatting
        clean_memo = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', memo)  # Remove markdown links
        clean_memo = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean_memo)  # Remove bold
        return summarize_memo_with_ai(clean_memo, order_url)
    else:
        logger.info("Using truncation summarization for memo")
        return truncate_memo(memo)


def process_memo(memo: str) -> str:
    """Process a memo using AI summarization if enabled, otherwise use truncation if needed.
    
    This function handles both markdown and non-markdown memos based on the settings.ynab_use_markdown setting:
    - If markdown is enabled, it preserves markdown formatting in the output
    - If markdown is disabled, it strips all markdown formatting
    
    The processing strategy is:
    1. If AI summarization is enabled (settings.use_ai_summarization):
       - Uses OpenAI to generate a concise summary
       - Preserves markdown formatting if enabled
       - Ensures the summary fits within YNAB's character limit
    
    2. If AI summarization is disabled:
       - Checks if memo exceeds YNAB's character limit
       - If it does, uses truncation to shorten while preserving important information
       - If not, returns the original memo
    
    Returns:
        str: The processed memo, either AI-summarized or truncated, with appropriate markdown formatting
    """
    console = Console()
    original_memo = str(memo)
    
    if settings.use_ai_summarization:
        console.print("[yellow]Using AI summarization for memo[/]")
        processed_memo = summarize_memo(original_memo)
        console.print("[bold cyan]Memo after AI summarization:[/]")
        console.print(processed_memo)
        console.print(
            f"[green]Summarized from {len(original_memo)} to {len(processed_memo)} characters[/]"
        )
    elif len(original_memo) > YNAB_MEMO_LIMIT:
        console.print(
            f"[yellow]Warning: Memo exceeds YNAB's {YNAB_MEMO_LIMIT} character limit ({len(original_memo)} characters)[/]"
        )
        processed_memo = summarize_memo(original_memo)
        console.print("[bold cyan]Memo after truncation:[/]")
        console.print(processed_memo)
        console.print(
            f"[green]Truncated from {len(original_memo)} to {len(processed_memo)} characters[/]"
        )
    else:
        processed_memo = original_memo
        
    return processed_memo 