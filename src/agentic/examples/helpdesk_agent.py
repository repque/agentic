"""
Help desk agent example demonstrating enterprise workflow patterns.

Shows classification, requirements, routing, and escalation in a realistic scenario.
"""

from agentic.agent import Agent
from agentic.models import AgentState, Message, CategoryRequirement, HandlerResponse


class HelpDeskAgent(Agent):
    """
    Enterprise help desk agent handling support tickets, billing, and general inquiries.
    
    Demonstrates:
    - Multiple categories with different requirements
    - Business logic in custom handlers
    - Escalation workflows
    - Knowledge integration
    """
    
    def __init__(self):
        super().__init__(
            name="helpdesk_agent",
            llm="openai/gpt-4",
            confidence_threshold=0.7
        )
        
        # Register handlers for different ticket types
        self.register_handler("TechnicalSupport", self.handle_tech_support)
        self.register_handler("BillingInquiry", self.handle_billing)
        self.register_handler("AccountAccess", self.handle_account_access)
    
    def get_personality(self) -> str:
        """Professional help desk personality."""
        return """You are a professional help desk agent for Acme Corporation. 
        You are helpful, patient, and always follow proper support procedures.
        You prioritize understanding the customer's issue and gathering the necessary 
        information to resolve it efficiently. Be empathetic but maintain professionalism."""
    
    def get_classification_categories(self) -> list[str]:
        """Categories of support requests."""
        return [
            "TechnicalSupport", 
            "BillingInquiry", 
            "AccountAccess", 
            "GeneralInquiry",
            "ProductInfo"
        ]
    
    def get_category_requirements(self) -> list[CategoryRequirement]:
        """Required information for each category."""
        return [
            CategoryRequirement(
                category="TechnicalSupport", 
                required_fields=["problem_details"]
            ),
            CategoryRequirement(
                category="BillingInquiry", 
                required_fields=["account_number"]
            ),
            CategoryRequirement(
                category="AccountAccess", 
                required_fields=["username"]
            )
        ]
    
    def get_knowledge(self) -> list[str]:
        """Knowledge sources for the help desk."""
        return [
            # Add your knowledge sources here:
            # "./docs/company_policies.md",
            # "./docs/billing_procedures.md", 
            # "./docs/troubleshooting_guides/",
            # "https://api.company.com/docs"
        ]
    
    def handle_tech_support(self, state: AgentState) -> HandlerResponse:
        """Handle technical support requests."""
        
        # Simple: use the current user message as the issue description
        current_issue = state.messages[-1].content
        
        # Generate a ticket ID
        import random
        ticket_id = f"TECH-{random.randint(10000, 99999)}"
        
        response = f"""🎫 **Technical Support Ticket Created**

**Ticket ID:** {ticket_id}
**Status:** Open
**Issue:** {current_issue}

**What happens next:**
1. Your issue has been documented and assigned to our technical team
2. You'll receive updates via email as we investigate
3. Our team will work to resolve this as quickly as possible

**While you wait, you might try:**
• Restarting the application
• Checking for software updates
• Clearing browser cache (for web applications)

**Your ticket reference:** {ticket_id}

Is there anything else I can help you with?"""
        
        return HandlerResponse(
            messages=[Message(role="assistant", content=response)]
        )
    
    def handle_billing(self, state: AgentState) -> HandlerResponse:
        """Handle billing inquiries."""
        
        # Simulate account lookup
        import random
        account_status = random.choice(["Active", "Past Due", "Suspended"])
        
        response = f"""💳 **Billing Inquiry - Account Located**

I've located your account and can help with your billing question.

**Account Status:** {account_status}

**Available options:**
• Review billing history
• Update payment information  
• Set up automatic payments
• Download invoices
• Submit billing disputes

**For your security:**
I can provide general billing information here, but account changes require identity verification.

**Next steps:**
I can help you with:
• Scheduling a callback from our billing team
• Sending secure access links to your registered email
• General billing policy questions

What would be most helpful for you?"""
        
        return HandlerResponse(
            messages=[Message(role="assistant", content=response)]
        )
    
    def handle_account_access(self, state: AgentState) -> HandlerResponse:
        """Handle account access issues."""
        
        response = """🔐 **Account Access Support**

I can help you with your login issue. To resolve this properly, I'll need to gather some additional information and verify your identity.

**What I can help with:**
• Password reset assistance
• Account unlock requests  
• Username recovery
• Two-factor authentication issues

**Next steps:**
To proceed safely, I'll need to verify your identity. I can:
1. Send a verification link to your registered email
2. Transfer you to our identity verification team
3. Guide you through self-service options

**For your security:**
I cannot make account changes without proper verification, but I can guide you through the process.

Would you prefer:
• Email verification (if you have email access)
• Phone verification with our security team
• Self-service troubleshooting guidance

What works best for you?"""
        
        return HandlerResponse(
            messages=[Message(role="assistant", content=response)]
        )
    
    def handle_low_confidence(self, state: AgentState) -> HandlerResponse:
        """Escalate unclear or complex issues."""
        return HandlerResponse(
            messages=[Message(
                role="assistant",
                content="Your request is being reviewed by our team and we'll get back to you shortly."
            )]
        )