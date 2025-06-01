"""
LLM-based classification and requirements validation.

Uses the agent's LLM for intelligent message categorization and requirements checking.
All classification and validation is done through LLM calls for maximum accuracy.
"""

from typing import List, Any
from .models import CategoryRequirement


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
    
    # Use LLM to analyze all required fields at once
    fields_str = ", ".join(category_reqs.required_fields)
    
    analysis_prompt = f"""Analyze the following message to determine which required information is present or missing.

Required fields: {fields_str}
Message: "{message}"

Instructions:
- For each required field, determine if the message contains that information
- List only the MISSING fields (fields not present in the message)
- If all fields are present, respond with "NONE"
- Respond with missing field names separated by commas, or "NONE"

Missing fields:"""

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


