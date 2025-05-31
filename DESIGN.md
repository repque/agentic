# Agentic AI Framework Design Document

## Overview

A simplified framework for building agentic AI systems built on **LangGraph**. The framework follows a "batteries included, zero boilerplate" philosophy where developers override 5 optional methods and get a complete AI agent.

**Why LangGraph?** We use LangGraph's proven state management and persistence while keeping the implementation extremely simple.

## Core Architecture: Simplified Design

### Single-Node Workflow

Instead of complex multi-node workflows, we use a single LangGraph node that handles everything:

```python
def _build_workflow(self) -> None:
    """Build simple LangGraph workflow."""
    workflow = StateGraph(AgentState)
    
    # Single main node that handles everything
    workflow.add_node("process", self._process_message)
    workflow.add_edge(START, "process")
    workflow.add_edge("process", END)
    
    self._workflow = workflow.compile(checkpointer=self._memory)
```

### Processing Flow

The `_process_message` method handles the complete workflow inline:

1. **Classification** (if categories defined) - Simple keyword matching
2. **Requirements Check** - Basic field presence validation  
3. **Handler Routing** - Direct function calls to custom handlers
4. **Default LLM** - Fallback to LLM with context (knowledge + tools)
5. **Confidence Check** - Simple length-based confidence scoring
6. **Escalation** - Call `handle_low_confidence()` if needed

## Key Design Principles

1. **Simplicity First** - Single workflow node vs complex routing
2. **Inline Processing** - No separate classification engine or routing functions
3. **Direct Integration** - MCP tools loaded as simple dicts
4. **Minimal Abstraction** - Fewer classes, more direct function calls
5. **Essential Models Only** - Stripped down Pydantic models

## Developer API (Unchanged)

Developers still override the same 5 optional methods:

```python
class MyAgent(Agent):
    def get_knowledge(self) -> List[str]:
        """Knowledge sources automatically loaded into context"""
        return ["./docs/"]
    
    def get_personality(self) -> str:
        """System prompt for LLM"""
        return "You are a helpful assistant."
    
    def get_classification_categories(self) -> List[str]:
        """Categories for simple keyword classification"""
        return ["ReviewRequest", "Query"]
    
    def get_category_requirements(self) -> List[CategoryRequirement]:
        """Requirements checked via field presence"""
        return [CategoryRequirement("ReviewRequest", ["url"])]
    
    def handle_low_confidence(self, state: AgentState) -> HandlerResponse:
        """Custom logic for low confidence responses"""
        return HandlerResponse(messages=[Message(role="assistant", content="Escalating...")])

# Custom handlers registered directly
agent.register_handler("ReviewRequest", my_review_handler)
```

## Implementation Simplifications

### Before vs After

**Before**: Complex multi-node LangGraph workflow
- Classification engine with LLM calls
- Separate routing functions 
- Confidence scoring with complex heuristics
- Handler wrappers and node creators
- Tool registry with complex management

**After**: Single processing function
- Simple keyword-based classification
- Inline requirement checking with basic field detection
- Direct handler execution
- Simple confidence scoring (response length)
- MCP tools as plain dicts

### Code Reduction

- `agent.py`: 373 lines → ~150 lines (60% reduction)
- `classification.py`: 163 lines → 26 lines (84% reduction)  
- `testing.py`: 144 lines → 34 lines (76% reduction)
- `tools.py`: 300 lines → 145 lines (52% reduction)

**Total**: ~980 lines → ~355 lines (64% reduction)

## Framework Benefits

**For Developers:**
- Same simple 5-method API
- All the same functionality
- Much easier to debug and understand

**For Maintenance:**
- Significantly less code to maintain
- Fewer abstractions = fewer bugs
- Simpler testing and deployment

**For Performance:**
- Single LangGraph node = faster execution
- Less object creation and method calls
- Simpler state management

## MCP Integration

Tools are loaded as simple dicts from MCP servers:

```python
# Simple function calls instead of complex registry
tools = load_mcp_tools()  # Returns List[Dict]
filtered_tools = get_tools_by_names(["filesystem", "web"])

# Tools passed directly to LLM context
if self.available_tools:
    tools_desc = ", ".join([t['name'] for t in self.available_tools])
    prompt += f"\n\nTools: {tools_desc}"
```

## Philosophy: Maximum Simplicity

The framework now embodies **maximum simplicity while maintaining functionality**:

- **One workflow node** instead of 10+ nodes
- **Inline processing** instead of separate engines  
- **Direct function calls** instead of complex routing
- **Simple dicts** instead of complex registries
- **Essential models** instead of over-engineered classes

Developers get the same "batteries included" experience with dramatically simpler, more maintainable code underneath.