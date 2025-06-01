# 🎛️ System Prompts Guide

The Agentic Framework uses 4 core prompts to drive its workflow. All prompts are centralized in `system_prompts.py` for easy customization.

## 📍 Where to Find the Prompts

```python
from agentic import system_prompts

# View current prompts
print(system_prompts.CLASSIFICATION_PROMPT)
print(system_prompts.REQUIREMENTS_PROMPT)
print(system_prompts.CONVERSATION_THREAD_PROMPT)
print(system_prompts.DEFAULT_RESPONSE_PROMPT)
```

## 🔧 How to Customize

Simply modify the prompt strings for your domain:

```python
from agentic import system_prompts

# Customize classification for your domain
system_prompts.CLASSIFICATION_PROMPT = """Classify this customer message: {categories}

E-commerce Guidelines:
- OrderStatus: Order tracking, shipping
- Returns: Return requests, refunds
- Support: General customer service

Message: "{message}"
Category:"""

# Your agent will automatically use the new prompt
```

## 📋 The 4 Core Prompts

### 1. **CLASSIFICATION_PROMPT**
**Purpose**: Categorize user messages to determine routing  
**Used in**: `classification.py:classify_message_with_llm()`  
**Variables**: `{categories}`, `{message}`

**Default behavior**: Classifies into TechnicalSupport, BillingInquiry, AccountAccess, etc.

**Customize for your domain**:
```python
system_prompts.CLASSIFICATION_PROMPT = """Classify this message: {categories}

Healthcare Guidelines:
- Appointment: Scheduling, rescheduling
- Medical: Health questions, symptoms  
- Emergency: Urgent situations

Patient message: "{message}"
Category:"""
```

### 2. **REQUIREMENTS_PROMPT**
**Purpose**: Check if required information is present  
**Used in**: `classification.py:check_requirements_with_llm()`  
**Variables**: `{required_fields}`, `{recent_context}`, `{message}`

**Default behavior**: Practical validation for account numbers, usernames, problem details

**Customize for your fields**:
```python
system_prompts.REQUIREMENTS_PROMPT = """Check for required info: {required_fields}

Pizza Shop Rules:
- pizza_size: Small/Medium/Large (be flexible)
- toppings: Any pizza toppings
- address: Delivery location

Message: "{message}"
Missing fields or "NONE":"""
```

### 3. **CONVERSATION_THREAD_PROMPT**
**Purpose**: Detect when user starts a new topic vs continuing current one  
**Used in**: `agent.py:_is_new_conversation_thread()`  
**Variables**: `{recent_context}`, `{current_message}`

**Default behavior**: Conservative - prefers to continue conversations

**Customize for your context**:
```python
system_prompts.CONVERSATION_THREAD_PROMPT = """New order or same order?

Previous: {recent_context}
Current: {current_message}

NEW: Starting fresh order
CONTINUE: Adding to same order

Response: NEW or CONTINUE"""
```

### 4. **DEFAULT_RESPONSE_PROMPT**
**Purpose**: Generate conversational responses when no custom handler exists  
**Used in**: `agent.py:_generate_response()`  
**Variables**: `{personality}`, `{knowledge_section}`, `{tools_section}`, `{conversation_history}`

**Default behavior**: Professional assistant with context awareness

**Customize for your personality**:
```python
system_prompts.DEFAULT_RESPONSE_PROMPT = """You are Mario from Mario's Pizza!

{conversation_history}

Mario's Style:
- Enthusiastic about pizza
- Use Italian expressions occasionally  
- Always suggest popular combinations

Mario:"""
```

## 🎯 Complete Example

```python
from agentic import Agent, system_prompts

# 1. Customize all prompts for pizza ordering
system_prompts.CLASSIFICATION_PROMPT = """Classify: {categories}
Pizza: OrderPizza, TrackOrder, MenuQuestion
Message: "{message}"
Category:"""

system_prompts.REQUIREMENTS_PROMPT = """Pizza info needed: {required_fields}
Customer: "{message}"
Missing or "NONE":"""

system_prompts.CONVERSATION_THREAD_PROMPT = """Same pizza order?
Before: {recent_context}
Now: {current_message}
NEW or CONTINUE:"""

system_prompts.DEFAULT_RESPONSE_PROMPT = """You are Tony's Pizza!
{conversation_history}
Tony:"""

# 2. Create agent (automatically uses customized prompts)
class PizzaAgent(Agent):
    def get_classification_categories(self):
        return ["OrderPizza", "TrackOrder", "MenuQuestion"]

agent = PizzaAgent()
# Agent now uses your customized prompts!
```

## 💡 Best Practices

1. **Keep the variable names** - Don't change `{categories}`, `{message}`, etc.
2. **Test with real messages** - Verify your prompts work with actual user input
3. **Be specific to your domain** - Generic prompts won't perform as well
4. **Document your changes** - Comment why you made specific modifications
5. **Start simple** - Modify one prompt at a time and test

## 🔍 Debugging

To see what prompt is being used:

```python
# Print the formatted prompt before sending to LLM
prompt = system_prompts.CLASSIFICATION_PROMPT.format(
    categories="OrderPizza, TrackOrder", 
    message="I want pizza"
)
print(prompt)
```

## 🎨 Domain Examples

### E-commerce
```python
system_prompts.CLASSIFICATION_PROMPT = """Classify: {categories}
- OrderStatus: Tracking, shipping
- Returns: Refunds, exchanges  
- Products: Questions, availability
Message: "{message}" → Category:"""
```

### Healthcare  
```python
system_prompts.CLASSIFICATION_PROMPT = """Classify: {categories}
- Appointment: Scheduling care
- Medical: Health questions
- Insurance: Coverage, billing
Patient: "{message}" → Category:"""
```

### Support Desk
```python
system_prompts.CLASSIFICATION_PROMPT = """Classify: {categories}
- TechIssue: Software problems
- Account: Login, access issues
- Billing: Payment, charges
User: "{message}" → Category:"""
```

The system is designed to be **simple and direct** - just modify the strings to match your domain, and your agent will immediately behave better for your specific use case!