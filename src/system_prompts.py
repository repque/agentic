"""
System Prompts for Agentic Framework

This module contains all the prompts used by the framework's core workflow.
Developers can import and modify these prompts to customize their agent's behavior.

Usage:
    from agentic.system_prompts import CLASSIFICATION_PROMPT
    
    # Modify for your domain
    CLASSIFICATION_PROMPT = '''
    Classify this customer message into: {categories}
    Focus on e-commerce context...
    '''

Each prompt includes documentation about:
- Where it's used in the framework
- What variables it expects
- How to customize it for your domain
"""

# =============================================================================
# CLASSIFICATION PROMPT
# =============================================================================

CLASSIFICATION_PROMPT = """Classify the following user message into ONE of these categories: {categories}

Category Guidelines:
- TechnicalSupport: Technical problems, errors, bugs, system issues, software not working
- BillingInquiry: Bills, payments, charges, account balance, billing history, payment methods
- AccountAccess: Login problems, password reset, locked accounts, can't sign in, username issues
- GeneralInquiry: General questions, product info, how-to questions
- ProductInfo: Information about products, features, specifications

Instructions:
- Choose the most appropriate category based on the user's primary intent
- Consider the main topic: billing/money matters vs login/access problems vs technical issues
- If the message doesn't clearly fit any category, respond with "default"
- Respond with ONLY the category name, nothing else

User message: "{message}"

Category:"""

# WHERE USED: classification.py:classify_message_with_llm()
# CALLED: Every user message to determine routing
# VARIABLES: categories (comma-separated), message (user input)


# =============================================================================
# REQUIREMENTS CHECKING PROMPT  
# =============================================================================

REQUIREMENTS_PROMPT = """Check if the user has provided the required information.

Required information: {required_fields}{recent_context}
Current message: "{message}"

For each required field:
- account_number: Look for any number that could be an account (4+ digits)
- username: Look for any username, email, or user identifier  
- problem_details: Look for specific error messages, symptoms, or troubleshooting steps tried
- feedback_type: Look for type of feedback (bug, feature, complaint, etc.)
- details: Look for specific details or explanations

Rules:
- If the current message contains the information, mark it as PROVIDED
- Be practical - "12345" can be an account number, "bob" can be a username
- For problem_details: accept specific symptoms like "shows error X" or "tried restarting but still crashes"
- Don't be overly strict - if user gives reasonable information, accept it

List only the MISSING fields (not provided in current or recent messages).
If all information is provided, respond with "NONE".
Format: comma-separated field names or "NONE"

Missing fields:"""

# WHERE USED: classification.py:check_requirements_with_llm()
# CALLED: After classification, when category has required fields
# VARIABLES: required_fields, recent_context, message


# =============================================================================
# CONVERSATION THREADING PROMPT
# =============================================================================

CONVERSATION_THREAD_PROMPT = """Determine if the current message starts a NEW conversation topic or continues the EXISTING topic.

Recent conversation context: {recent_context}
Current message: {current_message}

Rules:
- If the current message introduces a COMPLETELY DIFFERENT problem/service area, respond "NEW"
- If the current message continues the same issue, provides requested information, or gives more details, respond "CONTINUE"
- Be CONSERVATIVE - when in doubt, choose "CONTINUE"
- Examples of NEW: switching from billing issues to technical support, from AC problems to computer problems
- Examples of CONTINUE: providing account numbers, describing symptoms, giving error details, clarifying previous statements

Respond with only "NEW" or "CONTINUE":"""

# WHERE USED: agent.py:_is_new_conversation_thread()
# CALLED: Before classification to detect topic changes
# VARIABLES: recent_context, current_message


# =============================================================================
# DEFAULT RESPONSE GENERATION PROMPT
# =============================================================================

DEFAULT_RESPONSE_PROMPT = """{personality}

{knowledge_section}

{tools_section}

Conversation history (use this context to provide relevant responses):
{conversation_history}

Important: If the user asks about request status, ticket status, or 'my request', refer to any tickets mentioned in the conversation history above. Be helpful and reference specific ticket IDs if they were mentioned.
Assistant:"""

# WHERE USED: agent.py:_generate_response()
# CALLED: When no custom handler exists for the category
# VARIABLES: personality, knowledge_section, tools_section, conversation_history