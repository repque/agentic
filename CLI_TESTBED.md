# Agentic CLI Testbed

Interactive chat interface for testing agents, similar to Claude Code.

## Quick Start

```bash
# Install the framework
pip install -e .

# Start chat with default demo agent
agentic chat

# Use a specific example agent
agentic chat --example helpdesk_agent

# Use your own custom agent
agentic chat --agent-file my_custom_agent.py

# Enable debug mode
agentic chat --example demo_agent --debug
```

## Available Commands

### Chat Commands (within chat session)

| Command | Description |
|---------|-------------|
| `/help` | Show help message |
| `/info` | Show agent information |
| `/stats` | Show session statistics |
| `/history` | Show conversation history |
| `/clear` | Clear conversation history |
| `/export` | Export chat to JSON file |
| `/quit`, `/exit` | Exit chat |

### CLI Commands

```bash
# List available example agents
agentic list-examples

# Start interactive chat
agentic chat [OPTIONS]
```

## Example Agents

### 🎯 Demo Agent (`demo_agent`)
- **Purpose:** Framework demonstration and learning
- **Categories:** Greeting, Question, Help, Feedback
- **Features:** Interactive tutorials, framework explanations
- **Best for:** Understanding how the framework works

### 🎫 Help Desk Agent (`helpdesk_agent`)
- **Purpose:** Enterprise customer support simulation
- **Categories:** TechnicalSupport, BillingInquiry, AccountAccess, GeneralInquiry
- **Features:** Ticket creation, escalation workflows, realistic business logic
- **Best for:** Testing enterprise workflows

### 🔍 Code Review Agent (`code_review_agent`)
- **Purpose:** Developer workflow automation
- **Categories:** CodeReview, SecurityReview, PerformanceReview
- **Features:** Technical analysis, structured feedback, security scanning
- **Best for:** Testing technical domain expertise

## Creating Custom Agents

### 1. Create Agent File

```python
# my_agent.py
from agentic import Agent, CategoryRequirement, Message, HandlerResponse
from agentic.models import AgentState

class MyAgent(Agent):
    def get_classification_categories(self):
        return ["Greeting", "Question"]
    
    def get_category_requirements(self):
        return [
            CategoryRequirement(
                category="Question", 
                required_fields=["topic"]
            )
        ]
    
    def handle_greeting(self, state: AgentState) -> HandlerResponse:
        return HandlerResponse(
            messages=[Message(role="assistant", content="Hello! 👋")]
        )

# Register handler
agent = MyAgent()
agent.register_handler("Greeting", agent.handle_greeting)
```

### 2. Test with CLI

```bash
agentic chat --agent-file my_agent.py
```

## Features

### 🎯 **Agent Testing**
- **Plugin System:** Load any agent from Python file
- **Hot Swapping:** Easy switching between different agents
- **Real Conversations:** Full interactive chat experience

### 📊 **Debugging & Analytics**
- **Workflow Tracking:** See which nodes execute
- **Conversation History:** Full session replay
- **Performance Stats:** Message counts, session duration
- **Export Capability:** Save conversations for analysis

### 🔧 **Developer Experience**
- **Live Reload:** Modify agents and test immediately
- **Error Handling:** Graceful error display and recovery
- **Debug Mode:** Detailed execution information
- **Cross-Platform:** Works on macOS, Linux, Windows

## Workflow Visualization

The CLI shows you exactly how the framework processes messages:

```
User Input → Classify → Requirements → Route → Handler/LLM → Confidence → Response
     ↓           ↓           ↓          ↓         ↓           ↓         ↓
   "Hello"  → "Greeting" → Met      → Custom  → Success   → High    → "Hi! 👋"
```

Use `/info` in chat to see your agent's:
- Classification categories
- Requirements per category  
- Registered handlers
- Confidence threshold
- Workflow configuration

## Session Management

### Conversation Export

```bash
# Within chat session
> /export
💾 Chat history exported to: chat_export_20241228_143022.json
```

Export includes:
- Full conversation history
- Agent configuration
- Session statistics
- Timestamps and metadata

### Session Statistics

```bash
# Within chat session  
> /stats
📊 Session Statistics:
   Session Duration: 0:05:23
   User Messages: 12
   Agent Messages: 12
   Errors: 0
   Total Exchanges: 12
```

## Best Practices

### 🎯 **Agent Development**
1. **Start Simple:** Begin with basic categories and handlers
2. **Test Early:** Use CLI to validate behavior immediately
3. **Iterate Fast:** Modify agent file and restart chat
4. **Export Sessions:** Save interesting conversations for analysis

### 🔍 **Testing Strategies**
1. **Happy Path:** Test expected workflows first
2. **Edge Cases:** Try incomplete or unusual inputs
3. **Requirements:** Test missing vs. provided information
4. **Confidence:** Trigger both high and low confidence scenarios

### 📊 **Debugging Workflow**
1. **Enable Debug:** Use `--debug` flag for detailed info
2. **Check Classification:** Use `/info` to see categories
3. **Review History:** Use `/history` to see full conversation
4. **Export & Analyze:** Save sessions for deeper analysis

## Advanced Usage

### Multiple Agents in One File

```python
# agents.py
class SupportAgent(Agent):
    # ... implementation

class SalesAgent(Agent):
    # ... implementation

# CLI will detect and use the first Agent subclass
```

### Custom User IDs

```bash
# Test multi-user scenarios
agentic chat --user-id "customer_123" --example helpdesk_agent
```

### Integration Testing

```python
# test_my_agent.py
import asyncio
from my_agent import MyAgent

async def test_agent():
    agent = MyAgent()
    response = await agent.chat("Hello", "test_user")
    print(response)

asyncio.run(test_agent())
```

## Troubleshooting

### Common Issues

**Agent Not Loading:**
- Check Python file syntax
- Ensure Agent subclass exists
- Verify all imports are available

**LLM Errors:**
- Set `OPENAI_API_KEY` environment variable
- Check internet connection
- Verify API key permissions

**Import Errors:**
- Install framework: `pip install -e .`
- Check file paths are correct
- Ensure all dependencies installed

### Debug Mode

```bash
agentic chat --debug --example demo_agent
```

Debug mode shows:
- Detailed error messages
- LLM call information
- Workflow step execution
- Performance timing

## Next Steps

1. **Try Example Agents:** Start with provided examples
2. **Create Custom Agent:** Build your own agent file
3. **Test Workflows:** Explore different message types
4. **Export & Analyze:** Save interesting conversations
5. **Iterate & Improve:** Refine based on testing results

The CLI testbed makes it easy to rapidly prototype, test, and refine your agents before deploying them in production environments.