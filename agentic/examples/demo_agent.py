"""
Demo agent showcasing the framework's basic capabilities.

This agent demonstrates classification, requirements checking, and custom handlers.
"""

from agentic.agent import Agent
from agentic.models import AgentState, Message, CategoryRequirement, HandlerResponse


class DemoAgent(Agent):
    """
    Demo agent that handles greetings, questions, and help requests.
    
    Shows basic framework features like classification and requirements.
    """
    
    def __init__(self):
        super().__init__(
            name="demo_agent",
            llm="openai/gpt-4",
            confidence_threshold=0.6
        )
        
        # Register custom handlers
        self.register_handler("Greeting", self.handle_greeting)
        self.register_handler("Help", self.handle_help)
    
    def get_personality(self) -> str:
        """Friendly and helpful demo personality."""
        return """You are a friendly demo agent built with the Agentic framework. 
        You help users understand how the framework works by demonstrating 
        classification, requirements checking, and custom handlers. 
        Be encouraging and explain what's happening behind the scenes."""
    
    def get_classification_categories(self) -> list[str]:
        """Define the types of requests this agent can handle."""
        return ["Greeting", "Question", "Help", "Feedback"]
    
    def get_category_requirements(self) -> list[CategoryRequirement]:
        """Define what information is needed for each category."""
        return [
            CategoryRequirement(
                category="Feedback", 
                required_fields=["feedback_type", "details"]
            )
        ]
    
    def handle_greeting(self, state: AgentState) -> HandlerResponse:
        """Handle greeting messages with enthusiasm."""
        user_message = state.messages[-1].content.lower()
        
        if "morning" in user_message:
            greeting = "Good morning! 🌅"
        elif "afternoon" in user_message:
            greeting = "Good afternoon! ☀️"
        elif "evening" in user_message:
            greeting = "Good evening! 🌆"
        else:
            greeting = "Hello there! 👋"
        
        response = f"""{greeting} 

I'm the Agentic Framework Demo Agent! I'm here to show you how this framework works.

🔧 **What just happened:**
   • Your message was classified as a "Greeting"
   • This triggered my custom greeting handler
   • No requirements needed for greetings, so we proceeded directly

💡 **Try asking me:**
   • "Can you help me?" (triggers Help handler)
   • "What is Python?" (goes to default LLM flow)
   • "I have feedback about the bugs in your system" (requires more info)

What would you like to explore?"""
        
        return HandlerResponse(
            messages=[Message(role="assistant", content=response)]
        )
    
    def handle_help(self, state: AgentState) -> HandlerResponse:
        """Provide help about the framework and demo agent."""
        
        response = """🆘 **Agentic Framework Help**

I'm a demo agent showing off the framework's capabilities:

🏗️ **Framework Features:**
   • **Smart Classification** - I understand your intent using LLM
   • **Requirements Checking** - I ask for missing information
   • **Custom Handlers** - Special logic for specific scenarios  
   • **Default Flow** - LLM + tools for everything else
   • **Confidence Scoring** - Quality control with escalation

🎯 **What I Can Do:**
   • Greetings (custom handler) 
   • Questions (default LLM flow)
   • Help (this custom handler)
   • Feedback (requires feedback_type + details)

🧪 **Test Ideas:**
   • Try: "Hello!" → Custom greeting handler
   • Try: "What is machine learning?" → Default LLM response  
   • Try: "I have feedback" → Requirements checking
   • Try: "I have feedback about bugs in the UI" → Complete flow

Type /info to see my configuration or /stats for session metrics!"""
        
        return HandlerResponse(
            messages=[Message(role="assistant", content=response)]
        )
    
    def handle_low_confidence(self, state: AgentState) -> HandlerResponse:
        """Custom escalation for low confidence responses."""
        return HandlerResponse(
            messages=[Message(
                role="assistant", 
                content="Your request is being reviewed by our team and we'll get back to you shortly."
            )]
        )


# Alternative way to create agents - using a factory function
def create_simple_demo_agent():
    """Factory function to create a simpler demo agent."""
    
    class SimpleDemoAgent(Agent):
        def get_classification_categories(self):
            return ["Question", "Greeting"]
        
        def get_personality(self):
            return "You are a simple, friendly assistant created with the Agentic framework."
    
    return SimpleDemoAgent()