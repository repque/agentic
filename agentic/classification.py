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
    requirements: List[CategoryRequirement],
    conversation_history: List[Any] = None
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
    
    # Use LLM to analyze all required fields considering conversation history
    fields_str = ", ".join(category_reqs.required_fields)
    
    # Build conversation context
    conversation_context = ""
    if conversation_history:
        context_messages = []
        for msg in conversation_history[-5:]:  # Look at last 5 messages for context
            if hasattr(msg, 'role') and hasattr(msg, 'content'):
                if msg.role == "user":
                    context_messages.append(f"User: {msg.content}")
                elif msg.role == "assistant":
                    context_messages.append(f"Assistant: {msg.content}")
        if context_messages:
            conversation_context = f"\nConversation history:\n" + "\n".join(context_messages) + "\n"
    
    analysis_prompt = f"""Analyze the conversation to determine which required information is present or missing.

Required fields: {fields_str}{conversation_context}
Current message: "{message}"

Instructions:
- Look at the ENTIRE conversation history, not just the current message
- For each required field, determine if ANY message in the conversation contains that information
- Be strict about requiring actionable troubleshooting information
- Examples of sufficient problem_details (CREATE TICKET):
  * Includes error messages: "shows error code 0x123", "displays 'disk not found'"
  * Includes troubleshooting steps tried: "won't turn on, no lights, tried different power cable"
  * Includes specific triggers: "crashes every time I click File menu"
- Examples of insufficient problem_details (ASK FOR MORE):
  * Basic symptoms only: "won't turn on", "isn't blowing cold air", "not working", "runs slow"
  * Missing context: "keeps crashing", "overheating", "making noise"
- ALWAYS ask for more details unless the message includes error messages, troubleshooting steps, or specific triggers
  * account_number: any account identifier or number
  * username: any username, email, or user identifier
- List only the MISSING fields (fields not present anywhere in the conversation)
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


