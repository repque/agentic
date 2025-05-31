"""
Simple classification utilities.

Basic functions for categorizing messages and checking requirements.
"""

import re
from typing import List
from .models import CategoryRequirement


def check_field_present(message: str, field: str) -> bool:
    """Check if a required field is present in the message."""
    field_lower = field.lower()
    message_lower = message.lower()
    
    # Check for URLs
    if field_lower in ["url", "link"]:
        return bool(re.search(r"https?://[^\s]+", message))
    
    # Check for amounts/money
    if field_lower in ["amount", "cost", "price"]:
        return bool(re.search(r"[\$€£¥][\d,.]+|\b\d+\b", message))
    
    # Simple word presence check
    return field_lower in message_lower