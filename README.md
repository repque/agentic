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

- **LangGraph Foundation** - Built on proven enterprise orchestration  
- **LLM-Based Classification** - Intelligent categorization and validation using your LLM
- **Semantic Knowledge Search** - Embedding-based similarity search with vector storage
- **Framework-Agnostic Knowledge** - Reusable KnowledgeManager for any GenAI framework
- **Automatic Change Detection** - Smart re-vectorization when knowledge updates
- **Simple Conflict Resolution** - One handler per category, no complexity  
- **Automatic Memory** - Conversation persistence with zero config  
- **Confidence Scoring** - Quality control with automatic escalation  
- **MCP Tool Integration** - Automatic discovery and integration with MCP servers  
- **Type Safety** - Pydantic models throughout
- **Async-First** - Modern Python async/await patterns  

## Quick Start

### Installation

```bash
# Basic installation
pip install agentic

# For semantic knowledge search (recommended)
pip install agentic[embeddings]

# For MCP tool support
pip install agentic[mcp]

# Everything included
pip install agentic[all]
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
        return ["./docs/support/", "./kb/billing_procedures.md", "https://api.company.com/docs"]
    
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

### Automatic Workflow

1. **User Input** → Always classified and validated
2. **LLM Classification** → Intelligent categorization into your defined categories  
3. **LLM Requirements Check** → Smart validation of required information
4. **Routing** → Custom handler OR default flow with tools + knowledge
5. **Confidence Check** → Quality scoring with automatic escalation
6. **Response** → User gets helpful response

### What You Get Automatically

- **All routing logic** (automatic decision making)
- **Intelligent LLM-based classification and requirements validation**
- **Framework-agnostic knowledge management** (files, directories, URLs)
- **Context-aware knowledge retrieval** (smart content injection)
- **Confidence scoring and thresholding**  
- **State management and persistence**
- **Multi-user isolation**
- **Error handling and retries**
- **Human-in-the-loop workflows**
- **Streaming and observability**

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
        return ["./policies/", "./procedures/", "https://company.com/api/docs"]
    
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
→ LLM Classification: "ReviewRequest" (intelligent understanding)
→ LLM Requirements: URL and scope detected  
→ Execute: handle_review()
→ Output: "Review JIRA-456 created"
```

### Missing Requirements
```
Input: "Please review my code"
→ LLM Classification: "ReviewRequest" (understands intent)
→ LLM Requirements: Missing URL and scope detected
→ Output: "Need: url, scope"
```

### Default Flow
```
Input: "What's our vacation policy?"
→ LLM Classification: "Query" (no custom handler)
→ Default Flow: Knowledge + LLM + Tools
→ Confidence: High → Return response
```

### Intelligent Classification Examples
```
Input: "Can someone check my PR?"
→ LLM Classification: "ReviewRequest" (understands "check" = "review")

Input: "I need approval for the marketing budget"  
→ LLM Classification: "ApprovalRequest" (understands context)

Input: "Help me understand the deploy process"
→ LLM Classification: "Query" (informational request)
```

### Low Confidence Escalation
```
Input: "Complex technical question"
→ Default Flow: Knowledge + LLM  
→ Confidence: Low (< threshold)
→ Escalation: handle_low_confidence()
→ Output: "Connecting you with an expert..."
```

## Intelligent Classification System

The framework uses your LLM for all classification and requirements validation, providing maximum accuracy and context understanding:

### How It Works

1. **Message Classification**: Your LLM analyzes user input and categorizes it into your defined categories
2. **Requirements Validation**: Your LLM checks if all required information is present in the message
3. **Smart Understanding**: Handles synonyms, context, and intent automatically

### Benefits of LLM-Based Classification

- **Context Aware**: Understands "check my PR" means "ReviewRequest"
- **No Pattern Matching**: No brittle regex or keyword matching
- **Intelligent**: Detects missing requirements with natural language understanding
- **Consistent**: Single approach for all classification needs

### Example Classification Prompts

The framework automatically generates prompts like:

```
Classify the following user message into ONE of these categories: ReviewRequest, Query

Instructions:
- Choose the most appropriate category based on the user's intent
- If the message doesn't clearly fit any category, respond with "default"
- Respond with ONLY the category name, nothing else

User message: "Can someone check my PR?"

Category:
```

Result: `ReviewRequest` (LLM understands "check" = "review")

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

# Custom tools (if needed beyond MCP)
# Most use cases are covered by MCP servers:
# - Filesystem operations: @modelcontextprotocol/server-filesystem  
# - Web scraping: @modelcontextprotocol/server-web
# - Git operations: @modelcontextprotocol/server-git
# - Database: @modelcontextprotocol/server-postgres
# - And many more in the MCP ecosystem

# For specialized business logic, implement custom handlers:
def my_custom_handler(state):
    # Your business logic here
    result = my_business_function(state.messages[-1].content)
    return HandlerResponse(
        messages=[Message(role="assistant", content=result)]
    )

agent.register_handler("CustomCategory", my_custom_handler)
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
- **LLM-based classification** → Intelligent routing and requirements validation
- **Zero-config memory** → Automatic persistence and isolation
- **Built-in quality control** → Confidence scoring and escalation

### Design Principles

1. **Simplicity First** - 80% of use cases with minimal code
2. **LangGraph Foundation** - Don't reinvent proven infrastructure  
3. **One Handler Per Category** - No complex conflict resolution
4. **Escape Hatch Available** - Drop to LangGraph for complex workflows

## License

Apache License 2.0 - see LICENSE file for details.