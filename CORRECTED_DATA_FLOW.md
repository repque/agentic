# 🔄 Agentic Framework Data Flow - With Knowledge Base

This visualization shows exactly where **System Prompts**, **Memory**, and **Knowledge Base** are used in the data flow.

## 📊 Complete Data Flow with Knowledge Integration

```
┌─────────────────┐
│  User Message   │ "I need help with my order"
│                 │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐    🧠 MEMORY: LangGraph MemorySaver
│   Memory Load   │    ├─ Load existing state for user_id
│                 │    ├─ Get previous conversation: state.messages[]
│ get_state(cfg)  │    └─ Restore context: category, requirements, etc.
└─────────┬───────┘
          │
          ▼
┌─────────────────┐    🎛️ SYSTEM PROMPT #1: CONVERSATION_THREAD_PROMPT
│ Thread Detection│    ┌─────────────────────────────────────────────┐
│                 │    │ Input: {recent_context}, {current_message}   │
│ NEW/CONTINUE?   │    │ LLM Call: Thread detection logic            │
│                 │    │ Output: "NEW" or "CONTINUE"                 │
└─────────┬───────┘    └─────────────────────────────────────────────┘
          │
          ▼
┌─────────────────┐    🎛️ SYSTEM PROMPT #2: CLASSIFICATION_PROMPT
│ Classification  │    ┌─────────────────────────────────────────────┐
│                 │    │ Input: {categories}, {message}               │
│ Categorize      │    │ Categories from: get_classification_categories() │
│                 │    │ LLM Call: "TechnicalSupport" or "BillingInquiry" │
└─────────┬───────┘    └─────────────────────────────────────────────┘
          │
          ▼
┌─────────────────┐    🎛️ SYSTEM PROMPT #3: REQUIREMENTS_PROMPT
│ Requirements    │    ┌─────────────────────────────────────────────┐
│ Check           │    │ Input: {required_fields}, {recent_context}, {message} │
│                 │    │ Context from: MEMORY (last 2 user messages) │
│ Missing info?   │    │ LLM Call: Returns missing fields or "NONE"  │
└─────────┬───────┘    └─────────────────────────────────────────────┘
          │
          ▼
     ┌─────────┐
     │Missing? │
     └────┬────┘
          │
    ┌─────▼─────┐              ┌──────────────┐
    │    YES    │              │     NO       │
    │           │              │              │
    ▼           │              ▼              │
┌─────────────┐ │          ┌─────────────┐   │
│Ask for Info │ │          │   Routing   │   │
│             │ │          │             │   │
│Simple field │ │          │Handler vs   │   │
│prompts      │ │          │Default?     │   │
│             │ │          │             │   │
│No LLM call  │ │          └─────┬───────┘   │
└─────────────┘ │                │           │
                │                ▼           │
                │          ┌─────────────┐   │
                │          │   Handler   │   │
                │          │   Found?    │   │
                │          └─────┬───────┘   │
                │                │           │
                │         ┌──────▼──────┐    │
                │         │    YES      │    │
                │         │             │    │
                │         ▼             │    │
                │   ┌─────────────┐     │    │
                │   │Custom       │     │    │ 📚 KNOWLEDGE: Custom Handlers
                │   │Handler      │     │    │ ┌─────────────────────────┐
                │   │             │     │    │ │ Use business logic       │
                │   │Execute      │     │    │ │ Access databases         │
                │   │Business     │     │    │ │ Call external APIs       │
                │   │Logic        │     │    │ │ No knowledge injection   │
                │   └─────┬───────┘     │    │ └─────────────────────────┘
                │         │             │    │
                │         │      ┌──────▼────▼──┐
                │         │      │     NO        │
                │         │      │               │
                │         │      ▼               │
                │         │ ┌─────────────┐     │
                │         │ │             │     │ 🎛️ SYSTEM PROMPT #4: DEFAULT_RESPONSE_PROMPT
                │         │ │Default LLM  │     │ ┌───────────────────────────────────────────┐
                │         │ │Response     │     │ │ 📚 KNOWLEDGE BASE INJECTION:              │
                │         │ │             │     │ │                                           │
                │         │ │             │     │ │ 1. get_personality() → {personality}      │
                │         │ │             │     │ │    "You are helpful support agent..."     │
                │         │ │             │     │ │                                           │
                │         │ │             │     │ │ 2. get_knowledge() → {knowledge_section}  │
                │         │ │             │     │ │    "Knowledge: policies.md, guides/"     │
                │         │ │             │     │ │                                           │
                │         │ │             │     │ │ 3. available_tools → {tools_section}     │
                │         │ │             │     │ │    "Tools: search_db, send_email"        │
                │         │ │             │     │ │                                           │
                │         │ │             │     │ │ 4. MEMORY → {conversation_history}       │
                │         │ │             │     │ │    "User: help\nAssistant: Sure..."      │
                │         │ └─────┬───────┘     │ │                                           │
                │         │       │             │ │ → All injected into prompt template      │
                │         │       │             │ └───────────────────────────────────────────┘
                │         └───────┼─────────────┘
                │                 │
                └─────────────────┼─────────────────┐
                                  │                 │
                                  ▼                 │
                            ┌─────────────┐         │
                            │Confidence   │         │
                            │Scoring      │         │
                            │             │         │
                            │High enough? │         │
                            └─────┬───────┘         │
                                  │                 │
                             ┌────▼────┐            │
                             │  YES    │            │
                             │         │            │
                             ▼         │            │
                       ┌─────────────┐ │            │
                       │   Return    │ │            │
                       │  Response   │ │            │
                       └─────┬───────┘ │            │
                             │         │            │
                             │  ┌──────▼──────┐     │
                             │  │     NO      │     │
                             │  │             │     │
                             │  ▼             │     │
                             │ ┌─────────────┐│     │
                             │ │ Escalation  ││     │
                             │ │             ││     │
                             │ │handle_low_  ││     │
                             │ │confidence() ││     │
                             │ └─────┬───────┘│     │
                             │       │        │     │
                             └───────┼────────┘     │
                                     │              │
                                     └──────────────┘
                                     │
                                     ▼
                               ┌─────────────┐    🧠 MEMORY: Save Updated State
                               │Memory Save  │    ┌─────────────────────────────┐
                               │             │    │ Save to LangGraph memory:    │
                               │Update State │    │ - Updated message history    │
                               └─────┬───────┘    │ - Requirements attempts      │
                                     │            │ - Workflow state             │
                                     ▼            └─────────────────────────────┘
                               ┌─────────────┐
                               │  Response   │
                               │ to User     │
                               └─────────────┘
```

## 📚 Knowledge Base Components Detailed

### **Where Knowledge is NOT Used**
- ❌ Classification (only uses categories from agent)
- ❌ Requirements checking (only validates fields)
- ❌ Custom handlers (use their own business logic)
- ❌ Thread detection (only uses conversation context)

### **Where Knowledge IS Used**
- ✅ **Default Response Generation ONLY**

### **Knowledge Injection Process**

```python
# In agent.py:_generate_response()

# 1. Get personality from agent
personality = self.get_personality()
# Result: "You are a helpful customer service agent..."

# 2. Get knowledge sources 
knowledge_section = ""
if self.get_knowledge():
    knowledge_section = f"\n\nKnowledge: {', '.join(self.get_knowledge())}"
# Result: "\n\nKnowledge: policies.md, troubleshooting_guides/, faq.txt"

# 3. Get available tools
tools_section = ""
if self.available_tools:
    tools = ", ".join([t['name'] for t in self.available_tools])
    tools_section = f"\n\nTools: {tools}"
# Result: "\n\nTools: search_database, send_email, create_ticket"

# 4. Build conversation history from memory
conversation_history = ""
for msg in messages:  # From memory
    role = "User" if msg.role == "user" else "Assistant"
    conversation_history += f"\n{role}: {msg.content}"
# Result: "\nUser: I need help\nAssistant: How can I help you?"

# 5. Inject all into DEFAULT_RESPONSE_PROMPT
prompt = DEFAULT_RESPONSE_PROMPT.format(
    personality=personality,
    knowledge_section=knowledge_section,
    tools_section=tools_section,
    conversation_history=conversation_history
)
```

## 🎯 Example Knowledge Integration

### **HelpDeskAgent Example**
```python
def get_knowledge(self) -> list[str]:
    return [
        "company_policies.md",           # ← Becomes part of prompt
        "troubleshooting_guides/",       # ← Becomes part of prompt  
        "product_documentation/",        # ← Becomes part of prompt
        "billing_procedures.md"          # ← Becomes part of prompt
    ]

def get_personality(self) -> str:
    return """You are a professional help desk agent for Acme Corporation. 
    You are helpful, patient, and always follow proper support procedures."""
```

### **Resulting DEFAULT_RESPONSE_PROMPT**
```
You are a professional help desk agent for Acme Corporation. 
You are helpful, patient, and always follow proper support procedures.

Knowledge: company_policies.md, troubleshooting_guides/, product_documentation/, billing_procedures.md

Tools: search_database, create_ticket, send_email

Conversation history (use this context to provide relevant responses):
User: I need help with my order
Assistant: I can help you with your order. What specific issue are you experiencing?
User: It's not working

Important: If the user asks about request status, ticket status, or 'my request', refer to any tickets mentioned in the conversation history above. Be helpful and reference specific ticket IDs if they were mentioned.
Assistant:
```

## 🔑 Key Insight

**Knowledge Base is ONLY used in the Default Response Generation step** - it's not used for classification, requirements checking, or custom handlers. The knowledge gets injected into the DEFAULT_RESPONSE_PROMPT to give the LLM context about available resources, but the actual knowledge content is not loaded or processed by the framework itself.