# 🔄 Agentic Framework Data Flow

This document visualizes how user input flows through the framework, highlighting where system prompts, memory, and knowledge base components are used.

## 📊 High-Level Flow

```
User Message → Memory → Classification → Requirements → Routing → Response → Memory
     ↓           ↓           ↓              ↓           ↓          ↓         ↓
   Input     Load State   Categorize    Validate    Handler   Generate   Save State
```

## 🔍 Detailed Data Flow

```
┌─────────────────┐
│  User Message   │
│  "I need help"  │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐    🧠 MEMORY COMPONENT
│   Memory Load   │    ├─ LangGraph MemorySaver
│                 │    ├─ Thread ID = user_id  
│ get_state(cfg)  │    ├─ Loads: AgentState with messages[]
└─────────┬───────┘    └─ Context: Previous conversation history
          │
          ▼
┌─────────────────┐    🧵 CONVERSATION THREADING
│ Thread Detection│    ├─ Uses: CONVERSATION_THREAD_PROMPT
│                 │    ├─ Input: {recent_context}, {current_message}
│ NEW/CONTINUE?   │    ├─ LLM Call: "NEW" or "CONTINUE"
└─────────┬───────┘    └─ Effect: Reset state if NEW topic
          │
          ▼
┌─────────────────┐    🎯 CLASSIFICATION PROMPT
│ Classification  │    ├─ Uses: CLASSIFICATION_PROMPT  
│                 │    ├─ Input: {categories}, {message}
│ Categorize      │    ├─ LLM Call: Returns category name
└─────────┬───────┘    └─ Output: "TechnicalSupport", "BillingInquiry", etc.
          │
          ▼
┌─────────────────┐    📋 REQUIREMENTS PROMPT
│ Requirements    │    ├─ Uses: REQUIREMENTS_PROMPT
│ Check           │    ├─ Input: {required_fields}, {recent_context}, {message}
│                 │    ├─ LLM Call: Returns missing fields or "NONE"
│ Missing info?   │    └─ Memory: Uses last 2 user messages for context
└─────────┬───────┘
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
│Field-       │ │          │Handler vs   │   │
│specific     │ │          │Default?     │   │
│prompts      │ │          └─────┬───────┘   │
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
                │   │Custom       │     │    │
                │   │Handler      │     │    │
                │   │             │     │    │
                │   │Execute      │     │    │
                │   │Business     │     │    │
                │   │Logic        │     │    │
                │   └─────┬───────┘     │    │
                │         │             │    │
                │         │      ┌──────▼────▼──┐
                │         │      │     NO        │
                │         │      │               │
                │         │      ▼               │
                │         │ ┌─────────────┐     │
                │         │ │Default LLM  │     │ 🧠 KNOWLEDGE BASE
                │         │ │Response     │     │ ├─ Uses: DEFAULT_RESPONSE_PROMPT
                │         │ │             │     │ ├─ Input: {personality}, {knowledge_section},
                │         │ │Generate     │     │ │        {tools_section}, {conversation_history}
                │         │ └─────┬───────┘     │ ├─ Knowledge: get_knowledge() files/URLs
                │         │       │             │ ├─ Tools: Available MCP tools
                │         │       │             │ └─ Memory: Full conversation context
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
                               ┌─────────────┐    🧠 MEMORY COMPONENT
                               │Memory Save  │    ├─ LangGraph MemorySaver
                               │             │    ├─ Saves: Updated AgentState
                               │Update State │    ├─ Persists: Full conversation
                               └─────┬───────┘    └─ Thread: user_id based
                                     │
                                     ▼
                               ┌─────────────┐
                               │  Response   │
                               │ to User     │
                               └─────────────┘
```

## 🎯 System Prompts Usage Points

| **Prompt** | **Location** | **Purpose** | **Input** | **Output** |
|------------|--------------|-------------|-----------|------------|
| `CONVERSATION_THREAD_PROMPT` | Thread Detection | Detect topic changes | `{recent_context}`, `{current_message}` | "NEW" or "CONTINUE" |
| `CLASSIFICATION_PROMPT` | Classification | Route to category | `{categories}`, `{message}` | Category name |
| `REQUIREMENTS_PROMPT` | Requirements Check | Validate info | `{required_fields}`, `{recent_context}`, `{message}` | Missing fields or "NONE" |
| `DEFAULT_RESPONSE_PROMPT` | Default Response | Generate answer | `{personality}`, `{knowledge_section}`, `{tools_section}`, `{conversation_history}` | Conversational response |

## 🧠 Memory Components Usage

| **Component** | **When Used** | **What's Stored** | **How Accessed** |
|---------------|---------------|-------------------|------------------|
| **LangGraph MemorySaver** | Every chat() call | Full AgentState with messages, metadata | Thread ID = user_id |
| **Message History** | Load/Save state | User + Assistant messages | `state.messages[]` |
| **Requirement Attempts** | Requirements tracking | Count per category | `state.requirement_attempts{}` |
| **Conversation Context** | Thread detection | Last 3-4 user messages | Extracted from `state.messages` |

## 📚 Knowledge Base Usage

| **Component** | **When Used** | **How Integrated** | **Example** |
|---------------|---------------|-------------------|-------------|
| **Knowledge Sources** | Default Response | `get_knowledge()` → knowledge_section | "customer_policies.md, faq.txt" |
| **Tools** | Default Response | `self.available_tools` → tools_section | "search_orders, send_email" |
| **Personality** | Default Response | `get_personality()` → personality | "You are a helpful support agent..." |

## 🔀 Decision Points & Branches

### 1. **Thread Detection Branch**
```
Thread Detection → NEW? 
├─ YES: Reset requirement_attempts, clear missing_requirements
└─ NO:  Keep existing state, clear missing_requirements
```

### 2. **Classification Branch**
```
Classification → Has categories?
├─ YES: Use CLASSIFICATION_PROMPT → Get category
└─ NO:  Set category = "default"
```

### 3. **Requirements Branch**
```
Requirements Check → Missing fields?
├─ YES: Ask for requirements (field-specific prompts) → END
└─ NO:  Continue to routing
```

### 4. **Routing Branch**
```
Routing → Custom handler exists?
├─ YES: Execute handler → END
└─ NO:  Generate default response
```

### 5. **Confidence Branch**
```
Confidence Check → Above threshold?
├─ YES: Return response → END  
└─ NO:  Escalate → END
```

## 📊 Data Transformations

### **User Input → AgentState**
```python
# Initial state creation
AgentState(
    messages=[Message(role="user", content="help with my order")],
    category=None,
    missing_requirements=[],
    confidence=None,
    needs_escalation=False,
    workflow_step=None,
    requirement_attempts={}
)
```

### **After Classification**
```python
AgentState(
    messages=[...],
    category="BillingInquiry",        # ← From CLASSIFICATION_PROMPT
    missing_requirements=[],
    workflow_step="classify"
)
```

### **After Requirements Check**
```python
AgentState(
    messages=[...],
    category="BillingInquiry",
    missing_requirements=["account_number"],  # ← From REQUIREMENTS_PROMPT
    workflow_step="check_requirements"
)
```

### **Final Response State**
```python
AgentState(
    messages=[
        Message(role="user", content="help with my order"),
        Message(role="assistant", content="I can help! What's your account number?")
    ],
    category="BillingInquiry",
    missing_requirements=[],
    confidence=0.8,
    workflow_step="complete"
)
```

## 🎛️ Key Integration Points

### **Memory ↔ System Prompts**
- Memory provides conversation history to prompts
- Thread detection uses memory to find recent messages
- Requirements checking uses memory for context

### **Knowledge Base ↔ System Prompts** 
- Knowledge sources injected into DEFAULT_RESPONSE_PROMPT
- Tools list included in response generation
- Personality guides all response generation

### **System Prompts ↔ Workflow**
- Classification determines routing path
- Requirements validation controls flow continuation
- Thread detection resets workflow state

This data flow shows how the framework orchestrates **memory**, **knowledge**, and **system prompts** to create intelligent, context-aware conversations while maintaining state across interactions.