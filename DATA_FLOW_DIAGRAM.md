# Agentic Framework Data Flow

This diagram shows the complete data flow through the Agentic framework with enhanced knowledge integration.

## Interactive Data Flow Diagram

```mermaid
flowchart TD
    A[User Message<br/>What payment methods do you accept?] --> B
    
    B[Memory Load<br/>get_state config] --> |LangGraph MemorySaver<br/>Load existing state for user_id<br/>Get previous conversation| C
    
    C[Thread Detection<br/>NEW/CONTINUE?] --> |CONVERSATION_THREAD_PROMPT<br/>Input: recent_context, current_message<br/>LLM Call: Thread detection logic<br/>Output: NEW or CONTINUE| D
    
    D[Classification<br/>Categorize] --> |CLASSIFICATION_PROMPT<br/>Input: categories, message<br/>Categories from get_classification_categories<br/>LLM Call: TechnicalSupport or BillingInquiry| E
    
    E[Requirements Check<br/>Missing info?] --> |REQUIREMENTS_PROMPT<br/>Input: required_fields, recent_context, message<br/>Context from MEMORY last 2 user messages<br/>LLM Call: Returns missing fields or NONE| F
    
    F{Missing Requirements?} --> |YES| G[Ask for Info<br/>Category-specific prompts]
    F --> |NO| H[Routing<br/>Handler vs Default?]
    
    H --> I{Handler Found?}
    I --> |YES| J[Custom Handler<br/>Execute Business Logic]
    I --> |NO| K[Default LLM Response]
    
    J --> |Custom Handlers:<br/>• Use business logic<br/>• Access databases<br/>• Call external APIs<br/>• No knowledge injection| P
    
    K --> |KNOWLEDGEMANAGER INTEGRATION:<br/>1. get_personality → personality<br/>2. KnowledgeManager.retrieve_for_query<br/>3. available_tools → tools_section<br/>4. MEMORY → conversation_history<br/>All injected into DEFAULT_RESPONSE_PROMPT| L
    
    L[Confidence Scoring<br/>High enough?] --> M{Confidence Check}
    M --> |YES| N[Return Response]
    M --> |NO| O[Escalation<br/>handle_low_confidence]
    
    G --> P[Memory Save<br/>Update State]
    N --> P
    O --> P
    
    P --> |Save to LangGraph memory:<br/>• Updated message history<br/>• Requirements attempts<br/>• Workflow state| Q[Response to User]
    
    style A fill:#e1f5fe
    style K fill:#fff3e0
    style J fill:#f3e5f5
    style P fill:#e8f5e8
    style Q fill:#fce4ec
```

## Knowledge System Flow

```mermaid
flowchart LR
    subgraph "Initialization Phase"
        A1[Agent.__init__] --> A2[get_knowledge sources]
        A2 --> A3[KnowledgeManager.load_sources]
        A3 --> A4[FileLoader/URLLoader]
        A4 --> A5[EmbeddingRetriever]
        A5 --> A6[Chroma Vector DB]
    end
    
    subgraph "Runtime Phase"
        B1[User Query] --> B2[retrieve_for_query]
        B2 --> B3[Convert to embeddings]
        B3 --> B4[Semantic similarity search]
        B4 --> B5[Return relevant content]
        B5 --> B6[Inject into LLM prompt]
    end
    
    A6 --> B2
    
    style A3 fill:#e3f2fd
    style B2 fill:#fff3e0
    style A6 fill:#f3e5f5
    style B6 fill:#e8f5e8
```

## System Prompts Integration

```mermaid
flowchart TD
    A[system_prompts.py] --> B[CONVERSATION_THREAD_PROMPT]
    A --> C[CLASSIFICATION_PROMPT] 
    A --> D[REQUIREMENTS_PROMPT]
    A --> E[DEFAULT_RESPONSE_PROMPT]
    
    B --> F[Thread Detection Node]
    C --> G[Classification Node]
    D --> H[Requirements Node]
    E --> I[Response Generation Node]
    
    I --> J[KnowledgeManager Integration]
    J --> K[get_personality]
    J --> L[retrieve_for_query]
    J --> M[conversation_history]
    J --> N[available_tools]
    
    style A fill:#e8f5e8
    style I fill:#fff3e0
    style J fill:#f3e5f5
```

## Key Features

- **Interactive Mermaid Diagrams** - Clean, scalable, and easy to read  
- **GitHub Compatible** - Renders perfectly in GitHub and most markdown viewers  
- **Maintainable** - Easy to update and modify  
- **Multiple Views** - Main flow, knowledge system, and prompts integration  
- **Color Coded** - Different components have distinct colors for clarity