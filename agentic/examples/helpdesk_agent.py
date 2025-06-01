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
            "company_policies.md",
            "troubleshooting_guides/",
            "product_documentation/",
            "billing_procedures.md"
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
**Priority:** Standard
**Status:** Open

**Next Steps:**
1. I've created your support ticket and documented your issue
2. Our technical team will review within 2 business hours
3. You'll receive email updates at your registered address
4. Average resolution time: 24-48 hours

**Immediate Suggestions:**
• Try restarting the application
• Check if your software is up to date
• Clear browser cache if it's a web application

**Reference Information:**
• Ticket ID: {ticket_id}
• Issue: {current_issue}

Is there anything else I can help you with while we work on resolving this issue?"""
        
        return HandlerResponse(
            messages=[Message(role="assistant", content=response)]
        )
    
    def handle_billing(self, state: AgentState) -> HandlerResponse:
        """Handle billing inquiries."""
        
        # Simulate account lookup
        import random
        account_status = random.choice(["Active", "Past Due", "Suspended"])
        
        response = f"""💳 **Billing Inquiry - Account Located**

I've found your account and can help with your billing question.

**Account Status:** {account_status}
**Last Payment:** December 15, 2024
**Next Bill Date:** January 15, 2025

**Available Actions:**
• View billing history
• Update payment method  
• Set up auto-pay
• Download invoices
• Dispute charges

For security reasons, I can only provide general account information in this chat. 
For detailed billing changes, I'll need to:

1. Verify your identity with additional security questions
2. Transfer you to our billing specialist
3. Send secure links to your registered email

**Would you like me to:**
• Schedule a callback from billing (recommended)
• Send secure account access link to your email
• Provide general billing policy information

What would work best for you?"""
        
        return HandlerResponse(
            messages=[Message(role="assistant", content=response)]
        )
    
    def handle_account_access(self, state: AgentState) -> HandlerResponse:
        """Handle account access issues."""
        
        response = """🔐 **Account Access Support**

I understand you're having trouble accessing your account. Let me help you get back in.

**Common Solutions:**
1. **Password Reset**
   • Visit: company.com/reset-password
   • Enter your username or email
   • Check email for reset link (including spam folder)

2. **Account Locked**
   • Usually unlocks automatically after 30 minutes
   • Or I can unlock it now with identity verification

3. **Username Recovery**
   • Check your welcome email from when you signed up
   • Username is usually your email address

**Security Verification Required:**
For your protection, I'll need to verify your identity before making account changes.

**Next Steps:**
• I can send a secure verification link to your registered email
• Or we can do verification over the phone
• Account unlock typically takes 2-3 minutes once verified

**Emergency Access:**
If this is urgent and you can't access your email, I can escalate to our security team for manual verification.

Would you like me to:
1. Send email verification link
2. Schedule phone verification  
3. Escalate for emergency access

What's your preference?"""
        
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