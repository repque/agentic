# Agentic AI Framework

Build AI agents with 5 simple methods instead of 100+ lines of complex code.

## Quick Start

```bash
pip install agentic
```

```python
from agentic import Agent, CategoryRequirement, HandlerResponse, Message

class SupportAgent(Agent):
    def get_classification_categories(self):
        return ["TechnicalIssue", "BillingQuestion", "GeneralInquiry"]
    
    def get_category_requirements(self):
        return [
            CategoryRequirement(category="TechnicalIssue", required_fields=["problem_details"]),
            CategoryRequirement(category="BillingQuestion", required_fields=["account_number"])
        ]
    
    def handle_technical_issue(self, state):
        # Your business logic here
        return HandlerResponse(messages=[
            Message(role="assistant", content="I've created a support ticket for your technical issue.")
        ])

# That's it! Use it:
agent = SupportAgent()
response = await agent.chat("My app won't start", user_id="user123")
```

## Common Use Cases

### 1. Customer Support Bot

```python
class SupportBot(Agent):
    def get_knowledge(self):
        return ["./support_docs/", "./faq.md"]  # Auto-loaded knowledge
    
    def get_personality(self):
        return "You are a helpful customer support agent."
    
    def get_classification_categories(self):
        return ["TechnicalSupport", "Billing", "Returns"]
```

### 2. Code Review Assistant

```python
class CodeReviewer(Agent):
    def get_classification_categories(self):
        return ["ReviewRequest", "Question"]
    
    def get_category_requirements(self):
        return [CategoryRequirement(category="ReviewRequest", required_fields=["code_url"])]
    
    def handle_review_request(self, state):
        # Implement code review logic
        return HandlerResponse(messages=[
            Message(role="assistant", content="Code review completed. Found 3 suggestions.")
        ])
```

### 3. Document Q&A

```python
class DocumentBot(Agent):
    def get_knowledge(self):
        return ["./documents/", "https://api.company.com/docs"]  # Any files or URLs
    
    def get_personality(self):
        return "You answer questions based on company documents."
    
    # No handlers needed - uses knowledge automatically
```

## Interactive Testing

```bash
# Test your agent interactively
agentic chat --example helpdesk_agent

# List available examples  
agentic list-examples
```

## Handlers vs Tools vs Knowledge

**Custom Handlers** = Your business logic
- You write the code that executes
- Direct control over what happens
- Returns specific responses
- Example: Create database records, call your APIs

**Tools** = AI-accessible utilities  
- AI decides when and how to use them
- AI can combine multiple tools
- More flexible but less predictable
- Example: File operations, web search, calculators

**Knowledge** = Information for AI responses
- AI uses context to answer questions
- No code execution, just enhanced responses
- Best for Q&A and documentation
- Example: Company policies, product info

```python
class OrderBot(Agent):
    def __init__(self):
        # Tools: AI can use these when it thinks they're helpful
        super().__init__(tools=["file_search", "calculator", "web_search"])
    
    def get_knowledge(self):
        # Knowledge: AI always has access to answer questions
        return ["./product_catalog.md", "./shipping_policy.md"]
    
    def handle_place_order(self, state):
        # Handler: You control exactly what happens
        order = create_order_from_message(state.messages[-1].content)
        send_confirmation_email(order.customer_email)
        return HandlerResponse(messages=[
            Message(role="assistant", content=f"Order {order.id} created and confirmation sent!")
        ])
    
    # AI automatically:
    # - Uses knowledge to answer "What's your return policy?"
    # - Uses calculator tool for "What's 15% tip on $67?"
    # - Calls your handler for "I want to place an order"
```

## That's It!

The framework handles:
- Message routing and classification
- Conversation memory and context
- Knowledge integration and search
- Requirements validation
- Error handling and escalation
- Multi-user conversations

You focus on your business logic.

## Need More?

- **Knowledge Integration**: [KNOWLEDGE_GUIDE.md](KNOWLEDGE_GUIDE.md)
- **System Prompts**: [PROMPTS_GUIDE.md](PROMPTS_GUIDE.md)  
- **Architecture**: [DATA_FLOW_DIAGRAM.md](DATA_FLOW_DIAGRAM.md)