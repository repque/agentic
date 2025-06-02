# Agentic AI Framework

Build AI agents with 5 simple methods instead of 100+ lines of complex code.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/repque/agentic.git
cd agentic

# Install in development mode
pip install -e .
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

**Custom Handlers** = Branch from main execution path
- Take full control for specific categories
- Skip normal AI response generation
- Return exactly what you want
- Example: "PlaceOrder" → create order, return confirmation

**Tools** = Encapsulated capabilities for AI
- API calls, database access, sending emails
- AI decides when and how to use them
- AI can combine multiple tools in responses
- Example: AI uses email tool + database tool to answer "Send me my order status"

**Knowledge** = Information for AI responses
- AI uses context to answer questions
- No code execution, just enhanced responses
- Best for Q&A and documentation
- Example: Company policies, product info

```python
class OrderBot(Agent):
    def __init__(self):
        # Tools: AI can use database, email, etc. in its responses
        super().__init__(tools=["database_lookup", "send_email", "calculator"])
    
    def get_knowledge(self):
        # Knowledge: AI always has access to answer questions
        return ["./product_catalog.md", "./shipping_policy.md"]
    
    def handle_place_order(self, state):
        # Handler: Branches from main path, takes full control
        order = create_order_from_message(state.messages[-1].content)
        return HandlerResponse(messages=[
            Message(role="assistant", content=f"Order {order.id} created! You'll receive email confirmation.")
        ])
        # Note: Skips normal AI response, returns exactly this message
    
    # User: "What's my order status for #12345?"
    # → AI uses database_lookup tool + generates helpful response
    
    # User: "I want to place an order" 
    # → Handler takes over, bypasses AI, returns specific confirmation
    
    # User: "What's your return policy?"
    # → AI uses knowledge to generate informed response
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