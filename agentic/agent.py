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
        if await self._is_new_conversation_thread(state):
            # Reset classification state for new conversation thread, but preserve message history
            state.missing_requirements = []
            state.category = None  # Will be reclassified
        else:
            # Reset requirements for continuing conversation
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
            # Count how many times we've asked for requirements by counting assistant messages
            # that are asking for information (not just containing field names)
            requirement_requests = 0
            for msg in state.messages:
                if msg.role == "assistant":
                    # Check if the message is asking for information (contains question words)
                    content_lower = msg.content.lower()
                    if any(word in content_lower for word in ["could you", "please tell", "can you provide", "what", "which", "need"]):
                        requirement_requests += 1
            
            # If we've asked 2+ times, escalate instead of asking again
            if requirement_requests >= 2:
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
        
        prompt = f"""Determine if the current message starts a NEW conversation topic or continues the EXISTING topic.

Recent conversation context: {recent_context}
Current message: {current_message}

Rules:
- If the current message introduces a COMPLETELY DIFFERENT problem/service area, respond "NEW"
- If the current message continues the same issue, provides requested information, or gives more details, respond "CONTINUE"
- Be CONSERVATIVE - when in doubt, choose "CONTINUE"
- Examples of NEW: switching from billing issues to technical support, from AC problems to computer problems
- Examples of CONTINUE: providing account numbers, describing symptoms, giving error details, clarifying previous statements

Respond with only "NEW" or "CONTINUE":"""

        try:
            response = await self.llm.ainvoke(prompt)
            result = response.content.strip().upper()
            return result == "NEW"
        except:
            # Fallback: assume continuing conversation
            return False
    
    async def _generate_response(self, messages: list) -> str:
        """Generate LLM response with full conversation context."""
        prompt = self.get_personality()
        
        # Add knowledge
        if self.get_knowledge():
            prompt += f"\n\nKnowledge: {', '.join(self.get_knowledge())}"
        
        # Add tools
        if self.available_tools:
            tools = ", ".join([t['name'] for t in self.available_tools])
            prompt += f"\n\nTools: {tools}"
        
        # Add conversation history with emphasis on context awareness
        prompt += "\n\nConversation history (use this context to provide relevant responses):"
        for msg in messages:
            if hasattr(msg, 'role') and hasattr(msg, 'content'):
                role = "User" if msg.role == "user" else "Assistant"
                prompt += f"\n{role}: {msg.content}"
            elif isinstance(msg, dict):
                role = "User" if msg.get('role') == "user" else "Assistant"
                prompt += f"\n{role}: {msg.get('content', '')}"
        
        # Add specific guidance for status requests
        prompt += "\n\nImportant: If the user asks about request status, ticket status, or 'my request', refer to any tickets mentioned in the conversation history above. Be helpful and reference specific ticket IDs if they were mentioned."
        prompt += "\nAssistant:"
        
        try:
            response = await self.llm.ainvoke(prompt)
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            return f"Error: {str(e)}"

    async def _generate_missing_requirements_response(
        self, category: str, missing_fields: list[str], user_message: str
    ) -> str:
        """Generate a conversational response for missing requirements."""
        
        # Create a conversational prompt for the LLM
        personality = self.get_personality()
        
        prompt = f"""You are a helpful assistant in a casual chat conversation.

The user said: "{user_message}"
You need this missing info: {', '.join(missing_fields)}

Respond in 1-2 short sentences asking for what you need. Be direct and professional. Don't use phrases like "Oh no", "that's frustrating", or other emotional reactions. Just ask for the information you need.

Response:"""

        try:
            response = await self.llm.ainvoke(prompt)
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            # Fallback to brief chat-style responses
            if len(missing_fields) == 1:
                field = missing_fields[0]
                return f"I can help with that! What's your {field}?"
            else:
                fields_text = ", ".join(missing_fields[:-1]) + f", and {missing_fields[-1]}" if len(missing_fields) > 1 else missing_fields[0]
                return f"I can help! I just need your {fields_text}."
