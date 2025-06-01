"""
LLM-based classification for intelligent input categorization.

Uses the agent's LLM to classify user messages into developer-defined categories.
"""

import re
from typing import List, Any, Optional
from .models import AgentState, CategoryRequirement


async def classify_message_with_llm(
    llm: Any, 
    message: str, 
    categories: List[str]
) -> str:
    """
    Use LLM to classify a message into one of the defined categories.
    
    Args:
        llm: The language model instance
        message: User message to classify
        categories: List of available categories
        
    Returns:
        Classified category name or "default" if no match
    """
    if not categories:
        return "default"
    
    # Create classification prompt
    categories_str = ", ".join(categories)
    classification_prompt = f"""Classify the following user message into ONE of these categories: {categories_str}

Instructions:
- Choose the most appropriate category based on the user's intent
- If the message doesn't clearly fit any category, respond with "default"
- Respond with ONLY the category name, nothing else

User message: "{message}"

Category:"""

    try:
        # Get LLM classification
        response = await llm.ainvoke(classification_prompt)
        
        # Extract and clean the response
        classified_category = response.content.strip() if hasattr(response, 'content') else str(response).strip()
        
        # Validate it's one of our categories (case-insensitive)
        classified_lower = classified_category.lower()
        for category in categories:
            if category.lower() == classified_lower:
                return category
        
        # If not found, return default
        return "default"
        
    except Exception as e:
        # If classification fails, default to "default"
        import logging
        logging.warning(f"LLM classification failed: {e}")
        return "default"


async def check_requirements_with_llm(
    llm: Any,
    message: str,
    category: str,
    requirements: List[CategoryRequirement]
) -> tuple[bool, List[str]]:
    """
    Use LLM to check if required information is present in the message.
    
    Args:
        llm: The language model instance
        message: User message to analyze
        category: The classified category
        requirements: List of category requirements
        
    Returns:
        Tuple of (requirements_met: bool, missing_fields: List[str])
    """
    # Find requirements for this category
    category_reqs = None
    for req in requirements:
        if req.category == category:
            category_reqs = req
            break
    
    if not category_reqs or not category_reqs.required_fields:
        return True, []
    
    # Use basic field detection for common patterns, LLM for complex cases
    missing_fields = []
    
    for field in category_reqs.required_fields:
        if not await _check_field_present_smart(llm, message, field):
            missing_fields.append(field)
    
    return len(missing_fields) == 0, missing_fields


async def _check_field_present_smart(llm: Any, message: str, field: str) -> bool:
    """
    Smart field detection using patterns + LLM fallback.
    
    Uses fast pattern matching for common fields (URL, amount) and
    LLM analysis for more complex or ambiguous fields.
    """
    field_lower = field.lower()
    message_lower = message.lower()
    
    # Fast pattern matching for common fields
    if field_lower in ["url", "link", "repository", "repo"]:
        return bool(re.search(r"https?://[^\s]+", message))
    
    if field_lower in ["amount", "cost", "price", "budget"]:
        return bool(re.search(r"[\$€£¥][\d,.]+|\b\d+\s*(?:dollars?|euros?|pounds?|yen|usd|eur|gbp)\b", message, re.IGNORECASE))
    
    if field_lower in ["email", "email_address"]:
        return bool(re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", message))
    
    if field_lower in ["phone", "phone_number", "telephone"]:
        return bool(re.search(r"[\+]?[\d\s\-\(\)]{10,}", message))
    
    # Simple word presence for basic fields
    if field_lower in message_lower:
        return True
    
    # For complex fields, use LLM analysis
    try:
        analysis_prompt = f"""Does the following message contain information about "{field}"?

Message: "{message}"

Instructions:
- Answer with only "YES" or "NO"
- YES if the message contains any information related to {field}
- NO if the message does not contain information about {field}

Answer:"""

        response = await llm.ainvoke(analysis_prompt)
        result = response.content.strip().upper() if hasattr(response, 'content') else str(response).strip().upper()
        
        return result == "YES"
        
    except Exception:
        # If LLM analysis fails, fall back to simple word presence
        return field_lower in message_lower


def check_field_present(message: str, field: str) -> bool:
    """
    Synchronous field detection for backwards compatibility.
    
    Uses basic pattern matching without LLM calls.
    """
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