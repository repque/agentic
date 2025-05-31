"""
Core Agent class - the main framework interface.

This is what developers inherit from to build their agents.
"""

from typing import List, Dict, Optional, Callable
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from .models import AgentState, Message, CategoryRequirement, HandlerResponse
from .classification import check_field_present
from .tools import get_tools_by_names, get_tools_by_names_async, load_mcp_tools


class Agent:
    """
    Base class for building agentic AI systems.

    Developers override 5 optional methods to define their agent:
    - get_knowledge(): Knowledge sources
    - get_personality(): System prompt
    - get_classification_categories(): Input categories
    - get_category_requirements(): Required fields per category
    - handle_low_confidence(): Custom escalation logic

    The framework handles all orchestration, routing, and LangGraph integration.
    """

    def __init__(
        self,
        name: str = "agent",
        llm: str = "openai/gpt-4",
        tools: Optional[List[str]] = None,
        confidence_threshold: float = 0.7,
    ):
        self.name = name
        self.llm_name = llm
        self.tools = tools or []
        self.confidence_threshold = confidence_threshold
        self.handlers: Dict[str, Callable[[AgentState], HandlerResponse]] = {}

        # Initialize LLM and tools
        self.llm = self._create_llm(llm)
        self.available_tools = get_tools_by_names(self.tools) if self.tools else load_mcp_tools()

        # Build LangGraph workflow
        self._workflow = None
        self._memory = MemorySaver()  # In-memory for now
        self._build_workflow()

    # ===== Developer API (5 optional methods) =====

    def get_knowledge(self) -> List[str]:
        """Return list of knowledge sources (files, directories, URLs)."""
        return []

    def get_personality(self) -> str:
        """Return system prompt describing agent behavior."""
        return "You are a helpful assistant."

    def get_classification_categories(self) -> List[str]:
        """Return categories for input classification."""
        return []

    def get_category_requirements(self) -> List[CategoryRequirement]:
        """Define required information for each category."""
        return []

    def handle_low_confidence(self, state: AgentState) -> HandlerResponse:
        """Handle low confidence responses."""
        return HandlerResponse(
            messages=[
                Message(
                    role="assistant", content="Let me connect you with a human expert."
                )
            ]
        )

    # ===== Handler Registration =====

    def register_handler(
        self, category: str, handler: Callable[[AgentState], HandlerResponse]
    ) -> None:
        """Register a custom handler for a category."""
        # Validation
        if not category or not isinstance(category, str):
            raise ValueError("Category must be a non-empty string")

        if not callable(handler):
            raise ValueError("Handler must be callable")

        if category in self.handlers:
            raise ValueError(
                f"Handler for category '{category}' already registered. "
                f"Use a different category name or unregister first."
            )

        # Check if category is in classification categories
        if (
            self.get_classification_categories()
            and category not in self.get_classification_categories()
        ):
            import warnings

            warnings.warn(
                f"Handler registered for category '{category}' but it's not in "
                f"get_classification_categories(). It may never be called.",
                UserWarning,
            )

        self.handlers[category] = handler

        # Rebuild workflow to include new handler
        self._build_workflow()

    def unregister_handler(self, category: str) -> None:
        """Remove handler for category."""
        self.handlers.pop(category, None)

    # ===== Main Interface =====

    async def chat(self, message: str, user_id: str) -> str:
        """
        Main interface for chatting with the agent.

        Executes the LangGraph workflow with automatic state management.
        """
        # Input validation
        if not isinstance(message, str) or not message.strip():
            raise ValueError("Message must be a non-empty string")

        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("User ID must be a non-empty string")

        if not self._workflow:
            raise RuntimeError(
                "Workflow not initialized. Call _build_workflow() first."
            )

        # Create initial state
        initial_state = AgentState(
            messages=[Message(role="user", content=message.strip())]
        )

        # Execute workflow with thread-based memory
        try:
            result = await self._workflow.ainvoke(
                initial_state.model_dump(),
                config={"configurable": {"thread_id": user_id}},
            )

            # Extract the assistant's response
            if result.get("messages"):
                last_message = result["messages"][-1]
                if (
                    isinstance(last_message, dict)
                    and last_message.get("role") == "assistant"
                ):
                    return last_message["content"]
                elif hasattr(last_message, "content"):
                    return last_message.content

            return "I apologize, but I couldn't process your request."

        except Exception as e:
            # Log the error for debugging but return user-friendly message
            import logging

            logging.error(f"Agent workflow error: {str(e)}")
            return "I apologize, but I encountered an error while processing your request. Please try again."

    # ===== Internal Methods (Framework Implementation) =====

    def _create_llm(self, llm_name: str) -> BaseChatModel:
        """Create LLM instance from name."""
        if llm_name.startswith("openai/"):
            model = llm_name.replace("openai/", "")
            return ChatOpenAI(model=model, temperature=0)
        else:
            # Default to OpenAI GPT-4
            return ChatOpenAI(model="gpt-4", temperature=0)

    def _build_workflow(self) -> None:
        """Build simple LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Single main node that handles everything
        workflow.add_node("process", self._process_message)
        workflow.add_edge(START, "process")
        workflow.add_edge("process", END)
        
        self._workflow = workflow.compile(checkpointer=self._memory)

    async def _process_message(self, state: AgentState) -> AgentState:
        """Process a message through classification, requirements, and handlers."""
        last_message = state.messages[-1].content
        
        # Classify if categories are defined
        if self.get_classification_categories():
            state = self._classify_message(state)
            
            # Check requirements
            if not self._check_requirements(state):
                missing = ", ".join(state.missing_requirements)
                state.messages.append(Message(role="assistant", content=f"Need: {missing}"))
                return state
            
            # Try custom handler
            if state.category in self.handlers:
                response = self.handlers[state.category](state)
                state.messages.extend(response.messages)
                return state
        
        # Default LLM response
        response = await self._generate_response(last_message)
        confidence = len(response) / 100  # Simple confidence: longer = more confident
        
        if confidence < self.confidence_threshold:
            escalation_response = self.handle_low_confidence(state)
            state.messages.extend(escalation_response.messages)
        else:
            state.messages.append(Message(role="assistant", content=response))
            
        return state

    def _classify_message(self, state: AgentState) -> AgentState:
        """Simple message classification."""
        message = state.messages[-1].content
        categories = self.get_classification_categories()
        
        # Simple keyword-based classification (could use LLM if needed)
        for category in categories:
            if category.lower() in message.lower():
                state.category = category
                return state
        
        state.category = "default"
        return state
    
    def _check_requirements(self, state: AgentState) -> bool:
        """Check if required fields are present."""
        requirements = self.get_category_requirements()
        message = state.messages[-1].content.lower()
        
        for req in requirements:
            if req.category == state.category:
                missing = []
                for field in req.required_fields:
                    if not check_field_present(message, field):
                        missing.append(field)
                
                if missing:
                    state.missing_requirements = missing
                    return False
        
        return True
    
    async def _generate_response(self, message: str) -> str:
        """Generate LLM response with context."""
        prompt = self.get_personality()
        
        # Add knowledge
        if self.get_knowledge():
            prompt += f"\n\nKnowledge: {', '.join(self.get_knowledge())}"
        
        # Add tools
        if self.available_tools:
            tools = ", ".join([t['name'] for t in self.available_tools])
            prompt += f"\n\nTools: {tools}"
        
        prompt += f"\n\nUser: {message}\nAssistant:"
        
        try:
            response = await self.llm.ainvoke(prompt)
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            return f"Error: {str(e)}"

    # Removed: Complex confidence, escalation, and handler wrapper methods
    # Now handled inline in _process_message for simplicity
