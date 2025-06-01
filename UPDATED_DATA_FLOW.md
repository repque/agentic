# 🔄 Agentic Framework Data Flow - With KnowledgeManager Integration

This visualization shows the updated data flow with the new **KnowledgeManager** system that provides framework-agnostic knowledge integration.

## 📊 Complete Data Flow with Enhanced Knowledge System

```
┌─────────────────┐
│  User Message   │ "What payment methods do you accept?"
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
│Category-    │ │          │Handler vs   │   │
│specific     │ │          │Default?     │   │
│prompts      │ │          │             │   │
└─────────────┘ │          └─────┬───────┘   │
                │                │           │
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
                │         │ │Default LLM  │     │ ┌─────────────────────────────────────────────┐
                │         │ │Response     │     │ │ 📚 NEW KNOWLEDGEMANAGER INTEGRATION:        │
                │         │ │             │     │ │                                             │
                │         │ │             │     │ │ 1. get_personality() → {personality}         │
                │         │ │             │     │ │    "You are helpful support agent..."       │
                │         │ │             │     │ │                                             │
                │         │ │             │     │ │ 2. KnowledgeManager.retrieve_for_query()    │
                │         │ │             │     │ │    Input: current_query                     │
                │         │ │             │     │ │    Output: {knowledge_section}              │
                │         │ │             │     │ │    "Relevant Knowledge: billing_proc..."    │
                │         │ │             │     │ │                                             │
                │         │ │             │     │ │ 3. available_tools → {tools_section}        │
                │         │ │             │     │ │    "Tools: search_db, send_email"           │
                │         │ │             │     │ │                                             │
                │         │ │             │     │ │ 4. MEMORY → {conversation_history}          │
                │         │ │             │     │ │    "User: help\nAssistant: Sure..."         │
                │         │ └─────┬───────┘     │ │                                             │
                │         │       │             │ │ → All injected into prompt template         │
                │         │       │             │ └─────────────────────────────────────────────┘
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

## 🔧 KnowledgeManager System Architecture

### **Initialization Phase** (Agent Startup)
```python
# During Agent.__init__()
self.knowledge_manager = create_default_knowledge_manager()
self._load_knowledge_sources()

# KnowledgeManager loads and indexes content:
knowledge_sources = self.get_knowledge()  # ["policies.md", "billing.md"]
stats = self.knowledge_manager.load_sources(knowledge_sources)
# Result: Content loaded into FileLoader → SimpleRetriever
```

### **Runtime Phase** (Per User Query)
```python
# In _generate_response()
current_query = messages[-1].content  # "What payment methods do you accept?"
relevant_knowledge = self.knowledge_manager.retrieve_for_query(current_query, max_results=3)

# SimpleRetriever performs keyword matching:
# Query words: ["payment", "methods", "accept"]
# Finds matching content from billing_procedures.md
# Returns formatted knowledge section
```

## 📚 Enhanced Knowledge Components

### **Where Knowledge is Used**
| **Component** | **Usage** | **How** | **Example** |
|---------------|-----------|---------|-------------|
| **FileLoader** | Initialization | Load files/directories into content store | billing_procedures.md → content dictionary |
| **URLLoader** | Initialization | Load web content (if URLs provided) | https://api.docs → content dictionary |
| **SimpleRetriever** | Runtime | Keyword-based content matching | "payment" query → billing content |
| **KnowledgeManager** | Both | Coordinates loading and retrieval | retrieve_for_query() → formatted knowledge |

### **Universal Framework Integration**

```python
# Universal API works with ANY framework - no framework-specific code needed
km = create_default_knowledge_manager()
km.load_sources(["docs/", "policies.md"])

# Same method for all frameworks
knowledge = km.retrieve_for_query(query, max_results=3)

# Use with LangChain
langchain_prompt = f"Context: {knowledge}\nQuery: {query}"

# Use with OpenAI 
openai_messages = [{"role": "system", "content": f"Knowledge: {knowledge}"}]

# Use with LlamaIndex (if you need raw content)
all_content = [c['content'] for c in km.loaded_content if c.get('content')]

# Use with our framework (built-in)
# Already integrated automatically
```

## 🎯 Knowledge Integration Process

### **Before (Broken)**
```python
# Old broken method
def _load_knowledge_content(self) -> str:
    # Just read files directly, no indexing or retrieval
    # LLM couldn't access actual content
    return f"Knowledge: {', '.join(self.get_knowledge())}"
```

### **After (Enhanced)**
```python
# New KnowledgeManager integration
def _generate_response(self, messages: list) -> str:
    current_query = messages[-1].content
    # Context-aware retrieval based on user query
    relevant_knowledge = self.knowledge_manager.retrieve_for_query(current_query, max_results=3)
    knowledge_section = f"\n\nRelevant Knowledge:\n{relevant_knowledge}"
    # Knowledge content actually injected into LLM prompt
```

## 🔍 Real Example: Knowledge in Action

### **User Query**: "What payment methods do you accept?"

**1. Classification**: → "GeneralInquiry" (no requirements needed)
**2. Knowledge Retrieval**: 
   - SimpleRetriever matches ["payment", "methods", "accept"] 
   - Finds content in billing_procedures.md
   - Returns: "Credit Cards (Visa, MasterCard, Amex), ACH Bank Transfer, PayPal, Wire Transfer..."

**3. LLM Response**: Uses retrieved knowledge to provide specific payment method details

### **User Query**: "What are your support response times?"

**1. Classification**: → "GeneralInquiry"
**2. Knowledge Retrieval**:
   - Matches ["support", "response", "times"]
   - Finds content in company_policies.md
   - Returns: "High Priority: 2 hours, Medium Priority: 24 hours, Low Priority: 72 hours"

**3. LLM Response**: "Our support response times vary based on priority: High Priority issues are resolved within 2 hours..."

## 🚀 Key Improvements

✅ **Framework Agnostic**: Can be used with any GenAI framework
✅ **Context-Aware**: Retrieves relevant knowledge based on user queries  
✅ **Efficient**: Content loaded once, retrieved on-demand
✅ **Extensible**: Protocol-based loaders and retrievers
✅ **Scalable**: Handles files, directories, URLs
✅ **Real Knowledge**: LLM now has access to actual file contents
✅ **Reusable Component**: Other frameworks can use the same KnowledgeManager

This solves the critical issue where "LLM doesn't automatically read those knowledge files" and provides a sophisticated, reusable knowledge integration system for any GenAI framework.