# Customizing System Prompts

Change how your agent thinks by modifying prompts.

## Default Behavior

The framework uses these prompts automatically:
- **Classification**: How to categorize user messages
- **Requirements**: What info is needed for each category  
- **Responses**: How to generate helpful answers

## Customizing Prompts

```python
# 1. Import the prompts module
from agentic import system_prompts

# 2. Modify prompts for your domain
system_prompts.CLASSIFICATION_PROMPT = """
Classify this customer message into: {categories}

For e-commerce context:
- "OrderIssue": Problems with orders, shipping, delivery
- "ProductQuestion": Questions about products, features, specs
- "Returns": Return requests, exchanges, refunds

Message: "{message}"
Category:"""

# 3. Use your agent normally - it will use the updated prompts
```

## Available Prompts

| Prompt | Purpose | When Used |
|--------|---------|-----------|
| `CLASSIFICATION_PROMPT` | Categorize user messages | Every message |
| `REQUIREMENTS_PROMPT` | Check if required info is present | When category has requirements |
| `CONVERSATION_THREAD_PROMPT` | Detect new conversation topics | Every message |
| `DEFAULT_RESPONSE_PROMPT` | Generate helpful responses | When no custom handler exists |

## Real Example

```python
# Customize for a restaurant booking system
system_prompts.CLASSIFICATION_PROMPT = """
Classify this message into: {categories}

Restaurant booking context:
- "Reservation": Making, changing, or canceling bookings
- "MenuQuestion": Questions about food, drinks, dietary restrictions
- "Hours": Questions about opening times, locations

Message: "{message}"
Category:"""

system_prompts.REQUIREMENTS_PROMPT = """
For restaurant reservations, check if customer provided:
- party_size: How many people
- preferred_date: When they want to dine  
- preferred_time: What time

Message: "{message}"
Missing info:"""

class RestaurantBot(Agent):
    def get_classification_categories(self):
        return ["Reservation", "MenuQuestion", "Hours"]
    
    def get_category_requirements(self):
        return [CategoryRequirement(
            category="Reservation", 
            required_fields=["party_size", "preferred_date", "preferred_time"]
        )]
```

## Tips

- **Be specific**: Include domain context in your prompts  
- **Test changes**: Use `agentic chat` to see how it behaves  
- **Keep it simple**: Don't over-engineer the prompts  
- **Match your categories**: Ensure prompt categories match your `get_classification_categories()`