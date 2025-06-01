"""
Custom test agent demonstrating how to create your own agent for the CLI.

This shows how users can create their own agents and plug them into the chat interface.
"""

from agentic import Agent, CategoryRequirement, Message, HandlerResponse
from agentic.models import AgentState


class MyTestAgent(Agent):
    """
    A simple test agent that demonstrates custom functionality.
    
    This agent can handle greetings and provide information about itself.
    """
    
    def __init__(self):
        super().__init__(
            name="my_test_agent",
            llm="openai/gpt-4",
            confidence_threshold=0.5
        )
        
        # Register custom handlers
        self.register_handler("Greeting", self.handle_greeting)
        self.register_handler("AboutMe", self.handle_about_me)
    
    def get_personality(self) -> str:
        """Define the agent's personality."""
        return """You are a friendly and helpful test agent. You love to demonstrate 
        the capabilities of the Agentic framework and help users understand how to 
        build their own agents. You're enthusiastic about AI and agent development."""
    
    def get_classification_categories(self) -> list[str]:
        """Define what types of messages this agent can handle."""
        return ["Greeting", "AboutMe", "Question", "Help"]
    
    def get_category_requirements(self) -> list[CategoryRequirement]:
        """Define required information for each category."""
        return [
            # No special requirements for this simple agent
        ]
    
    def handle_greeting(self, state: AgentState) -> HandlerResponse:
        """Handle greeting messages."""
        response = """Hello! 👋 I'm your custom test agent!

🎉 **Success!** You've successfully:
   • Created a custom agent
   • Plugged it into the Agentic CLI
   • Started an interactive conversation

🔧 **What I can do:**
   • Respond to greetings (like this!)
   • Tell you about myself (/info or ask "tell me about yourself")
   • Answer general questions using the default LLM flow
   • Demonstrate the framework's multi-node workflow

💡 **Try asking me:**
   • "Tell me about yourself" (triggers AboutMe handler)
   • "What is machine learning?" (default LLM flow)
   • Or just chat with me naturally!

What would you like to explore?"""
        
        return HandlerResponse(
            messages=[Message(role="assistant", content=response)]
        )
    
    def handle_about_me(self, state: AgentState) -> HandlerResponse:
        """Provide information about this agent."""
        response = """🤖 **About Me - Custom Test Agent**

**Identity:**
• Name: MyTestAgent
• Framework: Agentic v0.1.0
• Purpose: Demonstrate custom agent creation

**Capabilities:**
• Multi-node LangGraph workflow
• LLM-based classification
• Custom handler registration
• Confidence scoring with escalation
• Conversation memory and state management

**Architecture:**
```
User Input → Classify → Requirements → Route → Handler/LLM → Confidence → Response
```

**Custom Handlers:**
• Greeting - Welcomes users enthusiastically
• AboutMe - Provides detailed agent information (this one!)

**Configuration:**
• LLM: GPT-4
• Confidence Threshold: 0.5 (relatively permissive)
• Categories: Greeting, AboutMe, Question, Help

**Framework Features I Demonstrate:**
✅ Custom personality and behavior
✅ Intelligent message classification  
✅ Business logic in custom handlers
✅ Graceful fallback to default LLM flow
✅ CLI integration for easy testing

**Development Tips:**
• Override the 5 key methods to customize behavior
• Register handlers for specific business logic
• Use CategoryRequirement for data validation
• Test with the CLI before production deployment

Want to see how I handle other types of messages?"""
        
        return HandlerResponse(
            messages=[Message(role="assistant", content=response)]
        )


# You can also create multiple agents in one file
class SimpleTestAgent(Agent):
    """An even simpler agent for comparison."""
    
    def get_personality(self) -> str:
        return "You are a simple, minimal agent for testing."
    
    def get_classification_categories(self) -> list[str]:
        return ["Question"]