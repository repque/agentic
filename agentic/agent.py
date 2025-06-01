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
from .classification import classify_message_with_llm, check_requirements_with_llm
from .tools import get_tools_by_names, get_tools_by_names_async, load_mcp_tools
from .system_prompts import CONVERSATION_THREAD_PROMPT, DEFAULT_RESPONSE_PROMPT
from .knowledge import create_default_knowledge_manager


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

        # Initialize knowledge management system
        self.knowledge_manager = create_default_knowledge_manager()
        self._load_knowledge_sources()

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
                    role="assistant", content="Your request is being reviewed by our team and we'll get back to you shortly."
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

        # Get existing state from memory or create new one
        config = {"configurable": {"thread_id": user_id}}
        
        try:
            # Try to get existing state
            existing_state = await self._workflow.aget_state(config)
            if existing_state.values:
                # Append new message to existing conversation
                current_state = AgentState(**existing_state.values)
                current_state.messages.append(Message(role="user", content=message.strip()))
            else:
                # No existing state, create fresh one
                current_state = AgentState(
                    messages=[Message(role="user", content=message.strip())]
                )
        except:
            # Fallback to fresh state if memory access fails
            current_state = AgentState(
                messages=[Message(role="user", content=message.strip())]
            )

        # Execute workflow with updated state
        try:
            result = await self._workflow.ainvoke(
                current_state.model_dump(),
                config=config,
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
        """Build multi-node LangGraph workflow with conditional routing."""
        workflow = StateGraph(AgentState)
        
        # Add all workflow nodes
        workflow.add_node("classify", self._classify_node)
        workflow.add_node("check_requirements", self._check_requirements_node)
        workflow.add_node("route", self._route_node)
        workflow.add_node("execute_handler", self._execute_handler_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("score_confidence", self._score_confidence_node)
        workflow.add_node("escalate", self._escalate_node)
        
        # Define workflow entry point
        workflow.add_edge(START, "classify")
        
        # Add conditional edges for routing
        workflow.add_conditional_edges(
            "classify",
            self._should_check_requirements,
            {
                "check_requirements": "check_requirements",
                "generate_response": "generate_response"
            }
        )
        
        workflow.add_conditional_edges(
            "check_requirements",
            self._requirements_met,
            {
                "route": "route",
                "__end__": END
            }
        )
        
        workflow.add_conditional_edges(
            "route",
            self._has_custom_handler,
            {
                "execute_handler": "execute_handler",
                "generate_response": "generate_response"
            }
        )
        
        # Custom handlers go directly to end
        workflow.add_edge("execute_handler", END)
        
        # Default responses go through confidence scoring
        workflow.add_edge("generate_response", "score_confidence")
        
        workflow.add_conditional_edges(
            "score_confidence",
            self._confidence_check,
            {
                "escalate": "escalate",
                "__end__": END
            }
        )
        
        # Escalation goes to end
        workflow.add_edge("escalate", END)
        
        self._workflow = workflow.compile(checkpointer=self._memory)

    # ===== Individual Workflow Nodes =====

    async def _classify_node(self, state: AgentState) -> AgentState:
        """Classify the user message using LLM."""
        state.workflow_step = "classify"
        
        last_message = state.messages[-1].content
        
        # Check if this is a new conversation thread (different topic/issue)
        # Only reset state for truly different problem domains, not natural topic shifts
        if await self._is_new_conversation_thread(state):
            # Reset classification state for new conversation thread, but preserve message history
            state.missing_requirements = []
            # Reset requirement attempts when switching to truly different topics
            state.requirement_attempts = {}
        else:
            # Reset requirements for continuing conversation (but keep attempt counts)
            state.missing_requirements = []
        
        if not self.get_classification_categories():
            state.category = "default"
            return state
        
        state.category = await classify_message_with_llm(
            self.llm, 
            last_message, 
            self.get_classification_categories()
        )
        
        return state

    async def _check_requirements_node(self, state: AgentState) -> AgentState:
        """Check if required information is present in the message."""
        state.workflow_step = "check_requirements"
        
        last_message = state.messages[-1].content
        requirements_met, missing_fields = await check_requirements_with_llm(
            self.llm,
            last_message,
            state.category,
            self.get_category_requirements(),
            state.messages  # Pass conversation history
        )
        
        state.missing_requirements = missing_fields
        
        if not requirements_met:
            # Simple session-based tracking: track attempts per category per user
            session_key = f"{state.workflow_step}_{state.category}_requirements"
            
            # Initialize attempt tracking if not exists
            if not hasattr(state, 'requirement_attempts'):
                state.requirement_attempts = {}
            
            # Increment attempts for this category
            if session_key not in state.requirement_attempts:
                state.requirement_attempts[session_key] = 0
            state.requirement_attempts[session_key] += 1
            
            # Escalate if we've tried too many times (simple counter)
            max_attempts = 2
            if state.requirement_attempts[session_key] > max_attempts:
                state.needs_escalation = True
                escalation_response = self.handle_low_confidence(state)
                state.messages.extend(escalation_response.messages)
            else:
                # Generate conversational response for missing requirements
                conversational_response = await self._generate_missing_requirements_response(
                    state.category, missing_fields, last_message
                )
                state.messages.append(Message(role="assistant", content=conversational_response))
        
        return state

    async def _route_node(self, state: AgentState) -> AgentState:
        """Determine routing based on category and available handlers."""
        state.workflow_step = "route"
        # This is a decision node - actual routing handled by conditional edges
        return state

    async def _execute_handler_node(self, state: AgentState) -> AgentState:
        """Execute custom handler for the classified category."""
        state.workflow_step = "execute_handler"
        
        if state.category in self.handlers:
            response = self.handlers[state.category](state)
            state.messages.extend(response.messages)
        
        return state

    async def _generate_response_node(self, state: AgentState) -> AgentState:
        """Generate default LLM response with context."""
        state.workflow_step = "generate_response"
        
        response = await self._generate_response(state.messages)
        state.messages.append(Message(role="assistant", content=response))
        
        return state

    async def _score_confidence_node(self, state: AgentState) -> AgentState:
        """Calculate confidence score for the generated response."""
        state.workflow_step = "score_confidence"
        
        if state.messages:
            last_response = state.messages[-1].content
            state.confidence = len(last_response) / 100  # Simple confidence: longer = more confident
            state.needs_escalation = state.confidence < self.confidence_threshold
        
        return state

    async def _escalate_node(self, state: AgentState) -> AgentState:
        """Handle low confidence responses with escalation."""
        state.workflow_step = "escalate"
        
        escalation_response = self.handle_low_confidence(state)
        # Replace the low-confidence response with escalation response
        state.messages[-1:] = escalation_response.messages
        
        return state

    # ===== Conditional Routing Functions =====

    def _should_check_requirements(self, state: AgentState) -> str:
        """Route to requirements check or skip to default flow."""
        if (self.get_classification_categories() and 
            state.category and 
            state.category not in ["default", ""]):
            return "check_requirements"
        else:
            return "generate_response"

    def _requirements_met(self, state: AgentState) -> str:
        """Route based on whether requirements are satisfied."""
        if state.missing_requirements:
            return "__end__"  # End workflow - requirements message already added
        else:
            return "route"

    def _has_custom_handler(self, state: AgentState) -> str:
        """Route to custom handler or default response generation."""
        if state.category and state.category in self.handlers:
            return "execute_handler"
        else:
            return "generate_response"

    def _needs_confidence_check(self, state: AgentState) -> str:
        """Determine if confidence scoring is needed."""
        # Only score confidence for default responses, not custom handlers
        return "score_confidence"

    def _confidence_check(self, state: AgentState) -> str:
        """Route based on confidence score."""
        if state.needs_escalation:
            return "escalate"
        else:
            return "__end__"
    
    async def _is_new_conversation_thread(self, state: AgentState) -> bool:
        """Determine if the current message starts a new conversation thread."""
        
        if len(state.messages) <= 1:
            return True  # First message is always a new thread
        
        current_message = state.messages[-1].content
        
        # Look at recent conversation context (last few messages)
        recent_messages = []
        for msg in state.messages[-4:-1]:  # Previous 3 messages (excluding current)
            if msg.role == "user":
                recent_messages.append(msg.content)
        
        if not recent_messages:
            return True  # No recent user messages
        
        # Use LLM to determine if this is a new topic
        recent_context = " | ".join(recent_messages)
        
        prompt = CONVERSATION_THREAD_PROMPT.format(
            recent_context=recent_context,
            current_message=current_message
        )

        try:
            response = await self.llm.ainvoke(prompt)
            result = response.content.strip().upper()
            return result == "NEW"
        except:
            # Fallback: assume continuing conversation
            return False
    
    async def _generate_response(self, messages: list) -> str:
        """Generate LLM response with full conversation context and knowledge retrieval."""
        personality = self.get_personality()
        
        # Get current user query for knowledge retrieval
        current_query = ""
        if messages:
            last_msg = messages[-1]
            if hasattr(last_msg, 'content'):
                current_query = last_msg.content
            elif isinstance(last_msg, dict):
                current_query = last_msg.get('content', '')
        
        # Build knowledge section with context-aware retrieval
        knowledge_section = ""
        if current_query:
            relevant_knowledge = self.knowledge_manager.retrieve_for_query(current_query, max_results=3)
            if relevant_knowledge:
                knowledge_section = f"\n\nRelevant Knowledge:\n{relevant_knowledge}"
        
        # Build tools section
        tools_section = ""
        if self.available_tools:
            tools = ", ".join([t['name'] for t in self.available_tools])
            tools_section = f"\n\nTools: {tools}"
        
        # Build conversation history
        conversation_history = ""
        for msg in messages:
            if hasattr(msg, 'role') and hasattr(msg, 'content'):
                role = "User" if msg.role == "user" else "Assistant"
                conversation_history += f"\n{role}: {msg.content}"
            elif isinstance(msg, dict):
                role = "User" if msg.get('role') == "user" else "Assistant"
                conversation_history += f"\n{role}: {msg.get('content', '')}"
        
        # Use system prompt (can be modified by developer)
        prompt = DEFAULT_RESPONSE_PROMPT.format(
            personality=personality,
            knowledge_section=knowledge_section,
            tools_section=tools_section,
            conversation_history=conversation_history
        )
        
        try:
            response = await self.llm.ainvoke(prompt)
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            return f"Error: {str(e)}"

    async def _generate_missing_requirements_response(
        self, category: str, missing_fields: list[str], user_message: str
    ) -> str:
        """Generate a conversational response for missing requirements with field-specific prompts."""
        
        if not missing_fields:
            return "I have all the information I need. Let me help you with that."
        
        # Use field-specific prompts for better user guidance
        field = missing_fields[0]  # Focus on one field at a time
        field_display = field.replace("_", " ")
        
        # Category-specific prompts
        if category == "TechnicalSupport" and field == "problem_details":
            return "Could you describe the technical issue you're experiencing? Please include any error messages or specific symptoms."
        elif category == "BillingInquiry" and field == "account_number":
            return "I'll need your account number to assist with billing matters. You can find this on your billing statement or customer portal."
        elif category == "AccountAccess" and field == "username":
            return "What username are you having trouble accessing?"
        
        # Fallback to generic prompt
        return f"Could you please provide your {field_display}?"
    
    def _load_knowledge_sources(self) -> None:
        """
        Load knowledge sources into the knowledge manager.
        
        This method is called during initialization to load all knowledge sources
        defined by get_knowledge() into the KnowledgeManager for efficient retrieval.
        """
        knowledge_sources = self.get_knowledge()
        if knowledge_sources:
            try:
                stats = self.knowledge_manager.load_sources(knowledge_sources)
                if stats['errors']:
                    import logging
                    logging.warning(f"Knowledge loading errors: {stats['errors']}")
            except Exception as e:
                import logging
                logging.error(f"Failed to load knowledge sources: {str(e)}")
    
    def reload_knowledge(self) -> Dict[str, any]:
        """
        Reload knowledge sources - useful for development/testing.
        
        Returns:
            Dictionary with loading statistics
        """
        return self.knowledge_manager.load_sources(self.get_knowledge())
