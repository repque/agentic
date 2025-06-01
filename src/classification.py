"""
LLM-based classification and requirements validation.

Uses the agent's LLM for intelligent message categorization and requirements checking.
All classification and validation is done through LLM calls for maximum accuracy.
"""

from typing import List, Any
from .models import CategoryRequirement
from .system_prompts import CLASSIFICATION_PROMPT, REQUIREMENTS_PROMPT


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
    
    # Use system prompt (can be modified by developer)
    categories_str = ", ".join(categories)
    classification_prompt = CLASSIFICATION_PROMPT.format(
        categories=categories_str,
        message=message
    )

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
    requirements: List[CategoryRequirement],
    conversation_history: List[Any] = None
) -> tuple[bool, List[str]]:
    """
    Simplified requirements checking focusing on current message + recent context.
    
    Args:
        llm: The language model instance
        message: User message to analyze
        category: The classified category
        requirements: List of category requirements
        conversation_history: Recent conversation (optional, limited to last 2-3 messages)
        
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
    
    # Simple approach: focus on current message with minimal context
    fields_str = ", ".join(category_reqs.required_fields)
    
    # Only use last 2 user messages for context (avoid confusion from long conversations)
    recent_context = ""
    if conversation_history:
        recent_user_messages = []
        for msg in reversed(conversation_history):
            if hasattr(msg, 'role') and msg.role == "user":
                recent_user_messages.append(msg.content)
                if len(recent_user_messages) >= 2:  # Only last 2 user messages
                    break
        
        if len(recent_user_messages) > 1:
            recent_context = f"\nPrevious user message: \"{recent_user_messages[1]}\"\n"
    
    # Use system prompt (can be modified by developer)
    analysis_prompt = REQUIREMENTS_PROMPT.format(
        required_fields=fields_str,
        recent_context=recent_context,
        message=message
    )

    try:
        response = await llm.ainvoke(analysis_prompt)
        result = response.content.strip() if hasattr(response, 'content') else str(response).strip()
        
        if result.upper() == "NONE":
            return True, []
        
        # Parse missing fields
        missing_fields = [field.strip() for field in result.split(",") if field.strip()]
        
        # Validate that returned fields are actually in our requirements
        valid_missing = []
        for field in missing_fields:
            if field in category_reqs.required_fields:
                valid_missing.append(field)
        
        return len(valid_missing) == 0, valid_missing
        
    except Exception as e:
        import logging
        logging.warning(f"LLM requirements check failed: {e}")
        
        # Fallback: assume all fields are missing for safety
        return False, category_reqs.required_fields


