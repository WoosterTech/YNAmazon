"""AI-powered memo summarization utilities."""
import os
from typing import List
import logging

from openai import OpenAI
from settings import settings
from prompts import (
    AMAZON_SUMMARY_SYSTEM_PROMPT, 
    AMAZON_SUMMARY_PLAIN_PROMPT, 
    AMAZON_SUMMARY_MARKDOWN_PROMPT
)

logger = logging.getLogger(__name__)

def summarize_memo_with_ai(
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
        
        memo += f"{summary}\n{order_url}"
        
        # Final safety check
        if len(memo) > max_length:
            logger.warning(f"AI summary still exceeds {max_length} characters ({len(memo)}). Truncating.")
            memo = memo[:max_length-3] + "..."
            
        return memo
        
    except Exception as e:
        logger.error(f"Error using OpenAI API: {str(e)}")
        return None