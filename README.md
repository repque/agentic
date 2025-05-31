# Agentic AI Framework

A simplified framework for building agentic AI systems built on **LangGraph**. Provides "batteries included, zero boilerplate" development experience.

## Why Agentic?

**Before:** Building AI agents requires 100+ lines of orchestration code, state management, routing logic, memory handling, etc.

**After:** Override 5 optional methods, get everything else for free.

```python
# Traditional approach: 100+ lines of complex orchestration
# Our approach: 5 simple methods

class MyAgent(Agent):
    def get_classification_categories(self):
        return ["ReviewRequest", "Query"]
    
    def get_category_requirements(self):
        return [CategoryRequirement(category="ReviewRequest", required_fields=["url"])]
    
    def handle_review_request(self, state):
        return HandlerResponse(messages=[Message(role="assistant", content="Review created")])

# That's it! Framework handles the complex workflow automatically.
```

## Features

✅ **LangGraph Foundation** - Built on proven enterprise orchestration  
✅ **Always-On Classification** - Every input categorized and validated  
✅ **Simple Conflict Resolution** - One handler per category, no complexity  
✅ **Automatic Memory** - Conversation persistence with zero config  
✅ **Confidence Scoring** - Quality control with automatic escalation  
✅ **MCP Tool Integration** - Automatic discovery and integration with MCP servers  
✅ **Type Safety** - Pydantic models throughout  

## Quick Start

### Installation

```bash
pip install agentic

# For MCP tool support (recommended)
pip install mcp
```

### Basic Agent

```python
from agentic import Agent, CategoryRequirement, Message, HandlerResponse

class HelpDeskAgent(Agent):
    def get_classification_categories(self):
        return ["TechSupport", "Billing", "General"]
    
    def get_category_requirements(self):
        return [
            CategoryRequirement(category="TechSupport", required_fields=["issue_type"]),
            CategoryRequirement(category="Billing", required_fields=["account_id"])
        ]
    
    def get_knowledge(self):
        return ["./docs/support/", "./kb/"]
    
    def handle_tech_support(self, state):
        # Your custom business logic
        ticket_id = self.create_support_ticket(state.messages[-1].content)
        return HandlerResponse(
            messages=[Message(role="assistant", content=f"Support ticket {ticket_id} created")]
        )

# Usage
agent = HelpDeskAgent()
agent.register_handler("TechSupport", agent.handle_tech_support)

# Usage (async by default)
import asyncio
response = await agent.chat("I need help with login issues", "user123")
# Or: response = asyncio.run(agent.chat("message", "user123"))
```

## How It Works

![Workflow Diagram](workflow-diagram.png)

### Automatic Workflow

1. **User Input** → Always classified and validated
2. **Classification** → LLM categorizes into your defined categories  
3. **Requirements Check** → Validates required fields are present
4. **Routing** → Custom handler OR default flow with tools + knowledge
5. **Confidence Check** → Quality scoring with automatic escalation
6. **Response** → User gets helpful response

### What You Get Automatically

- ✅ **All routing logic** (diamond decision points in flowchart)
- ✅ **Classification and completeness checking**
- ✅ **Confidence scoring and thresholding**  
- ✅ **State management and persistence**
- ✅ **Multi-user isolation**
- ✅ **Error handling and retries**
- ✅ **Human-in-the-loop workflows**
- ✅ **Streaming and observability**

## Examples

### Enterprise Review Agent

```python
class EnterpriseAgent(Agent):
    def __init__(self):
        super().__init__(
            name="enterprise_assistant",
            llm="openai/gpt-4", 
            tools=["jira_client", "email_sender", "web_scraper"],
            confidence_threshold=0.75
        )
        
        self.register_handler("ReviewRequest", self.handle_review)
        self.register_handler("Approval", self.handle_approval)
    
    def get_classification_categories(self):
        return ["ReviewRequest", "Approval", "Query"]
    
    def get_category_requirements(self):
        return [
            CategoryRequirement("ReviewRequest", ["url", "scope"]),
            CategoryRequirement("Approval", ["amount", "project"])
        ]
    
    def get_knowledge(self):
        return ["./policies/", "./procedures/"]
    
    def handle_review(self, state):
        # Extract review details
        review_details = self.extract_review_info(state.messages[-1].content)
        
        # Create Jira ticket
        ticket = self.tools.get("jira_client").execute(
            action="create",
            title=f"Review: {review_details['title']}",
            description=review_details['description']
        )
        
        # Send notification
        self.tools.get("email_sender").execute(
            to="review-team@company.com",
            subject=f"New Review Request: {ticket}",
            body=f"Review requested: {review_details['url']}"
        )
        
        return HandlerResponse(
            messages=[Message(role="assistant", content=f"Review {ticket} created and team notified")]
        )

# Usage examples
agent = EnterpriseAgent()

# Complete request → Custom handler
response = agent.chat("Review PR #123 at https://github.com/repo/pull/123 for security", "user123")
# → "Review JIRA-456 created and team notified"

# Incomplete request → Missing requirements
response = agent.chat("Please review my code", "user123")  
# → "Need: url, scope"

# General query → Default flow  
response = agent.chat("What's our code review policy?", "user123")
# → Uses knowledge base + LLM
```

### Testing Your Agent

```python
from agentic.testing import MockLLMAgent

# Test with mocked responses  
mock_agent = MockLLMAgent(
    mock_responses=["Review completed"]
)
response = mock_agent.chat("Review this PR", "test_user")
assert "Review completed" in response

# Test with real agent
agent = MyAgent()
response = agent.chat("Hello", "test_user")
assert len(response) > 0
```

## Framework Flow Examples

### Complete Flow (Requirements Met)
```
Input: "Review https://github.com/repo/pr/123 for security scope"
→ Classification: "ReviewRequest"
→ Requirements: ✅ URL and scope present  
→ Execute: handle_review()
→ Output: "Review JIRA-456 created"
```

### Missing Requirements
```
Input: "Please review my code"
→ Classification: "ReviewRequest"
→ Requirements: ❌ Missing URL and scope
→ Output: "Need: url, scope"
```

### Default Flow
```
Input: "What's our vacation policy?"
→ Classification: "Query" (no custom handler)
→ Default Flow: Knowledge + LLM
→ Confidence: High → Return response
```

### Low Confidence Escalation
```
Input: "Complex technical question"
→ Default Flow: Knowledge + LLM  
→ Confidence: Low (< threshold)
→ Escalation: handle_low_confidence()
→ Output: "Connecting you with an expert..."
```

## Advanced Features

### Async by Default

The framework is async-first for better performance:

```python
# Basic usage
import asyncio

async def main():
    agent = MyAgent()
    response = await agent.chat("Hello", "user123")
    return response

response = asyncio.run(main())

# Web frameworks (FastAPI, etc.)
@app.post("/chat")
async def chat_endpoint(message: str, user_id: str):
    agent = MyAgent()
    response = await agent.chat(message, user_id)
    return {"response": response}
```

### MCP Tool Integration

```python
# Automatic MCP server discovery
agent = MyAgent()
# Framework automatically loads tools from MCP servers

# Manual MCP server configuration
# Create mcp_config.json:
{
  "servers": {
    "filesystem": {
      "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem"],
      "args": ["--root", "/path/to/project"]
    },
    "web": {
      "command": ["npx", "-y", "@modelcontextprotocol/server-web"]
    },
    "git": {
      "command": ["npx", "-y", "@modelcontextprotocol/server-git"]
    }
  }
}

# Custom tools (when MCP tools aren't sufficient)
from agentic.tools import BaseTool

class CustomTool(BaseTool):
    def __init__(self):
        super().__init__("custom_tool", "Custom business logic")
    
    def execute(self, **kwargs) -> str:
        # Your custom logic
        return "Custom result"

# Register custom tool
agent.tool_registry.register(CustomTool())
```

### Memory & Multi-User

```python
# Development (automatic in-memory)
agent = MyAgent()

# Production (automatic PostgreSQL)
# Just set: DATABASE_URL=postgresql://user:pass@localhost/agents
agent = MyAgent()  # Same code, persistent memory

# Each user gets isolated memory automatically
agent.chat("Hello", "user123")  # Separate conversation  
agent.chat("Hi", "user456")     # Separate conversation
```

### Confidence Tuning

```python
class MyAgent(Agent):
    def __init__(self):
        super().__init__(
            confidence_threshold=0.8  # Higher = more escalations
        )
    
    def handle_low_confidence(self, state):
        # Custom escalation logic
        return HandlerResponse(
            messages=[Message(role="assistant", content="Let me get a specialist...")]
        )
```

## Environment Variables

```bash
# LLM API Keys
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Database for persistent memory (optional)
DATABASE_URL=postgresql://user:pass@localhost/agents

# Observability (optional)  
LANGCHAIN_API_KEY=your_key_here
LANGCHAIN_TRACING_V2=true
```

## API Reference

### Agent Class

#### Methods to Override

- `get_knowledge() -> List[str]` - Knowledge sources (files, URLs)
- `get_personality() -> str` - System prompt for LLM
- `get_classification_categories() -> List[str]` - Input categories
- `get_category_requirements() -> List[CategoryRequirement]` - Required fields
- `handle_low_confidence(state) -> HandlerResponse` - Custom escalation

#### Main Interface

- `async chat(message: str, user_id: str) -> str` - Chat with the agent
- `register_handler(category: str, handler: Callable)` - Add custom handler
- `unregister_handler(category: str)` - Remove handler

### Models

- `AgentState` - LangGraph workflow state
- `Message` - Chat message with role and content  
- `CategoryRequirement` - Required fields for a category
- `HandlerResponse` - Response from custom handlers

## Why This Design?

### Problem We Solve

Building production AI agents typically requires:
- 100+ lines of orchestration code
- Complex state management
- Memory and persistence setup
- Routing and classification logic
- Error handling and retries
- Quality control and escalation
- Tool integration and management

### Our Solution

- **5 simple methods** → Complete enterprise workflow
- **LangGraph foundation** → Production-grade orchestration  
- **Always-on classification** → Smart routing with validation
- **Zero-config memory** → Automatic persistence and isolation
- **Built-in quality control** → Confidence scoring and escalation

### Design Principles

1. **Simplicity First** - 80% of use cases with minimal code
2. **LangGraph Foundation** - Don't reinvent proven infrastructure  
3. **One Handler Per Category** - No complex conflict resolution
4. **Escape Hatch Available** - Drop to LangGraph for complex workflows

## Contributing

We welcome contributions! See our development plan in `TODO.md`.

## License

MIT License - see LICENSE file for details.