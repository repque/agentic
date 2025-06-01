"""
Integration tests for the Agentic framework.

Focus on the three critical flows:
1. Complete flow (all requirements met -> custom handler)
2. Missing requirements (incomplete input -> "Need: X, Y, Z")
3. Default flow (no custom handler -> default LangGraph agent)
"""

import pytest
from unittest.mock import Mock, patch
from agentic import Agent, CategoryRequirement
from agentic.models import AgentState, Message, HandlerResponse


class ExampleAgent(Agent):
    """Test agent for integration testing."""

    def get_classification_categories(self):
        return ["ReviewRequest", "Query"]

    def get_category_requirements(self):
        return [CategoryRequirement(category="ReviewRequest", required_fields=["url"])]

    def handle_review_request(self, state: AgentState) -> HandlerResponse:
        """Custom handler for review requests."""
        return HandlerResponse(
            messages=[Message(role="assistant", content="Review created")]
        )


@patch("agentic.agent.ChatOpenAI")
def test_agent_instantiation(mock_llm):
    """Test that we can create an agent without errors."""
    # Mock the LLM
    mock_llm.return_value = Mock()
    mock_llm.return_value.invoke.return_value.content = "Test response"

    agent = ExampleAgent()
    assert agent.name == "agent"
    assert agent.confidence_threshold == 0.7
    assert len(agent.get_classification_categories()) == 2
    assert len(agent.get_category_requirements()) == 1
    assert agent._workflow is not None  # Workflow should be built


@patch("agentic.agent.ChatOpenAI")
def test_handler_registration(mock_llm):
    """Test custom handler registration."""
    # Mock the LLM
    mock_llm.return_value = Mock()
    mock_llm.return_value.invoke.return_value.content = "Test response"

    agent = ExampleAgent()

    # Register handler
    agent.register_handler("ReviewRequest", agent.handle_review_request)
    assert "ReviewRequest" in agent.handlers

    # Test duplicate registration fails
    with pytest.raises(ValueError, match="already registered"):
        agent.register_handler("ReviewRequest", agent.handle_review_request)

    # Test unregistration
    agent.unregister_handler("ReviewRequest")
    assert "ReviewRequest" not in agent.handlers


@pytest.mark.asyncio
@patch("agentic.agent.ChatOpenAI")
@patch("agentic.agent.load_mcp_tools", return_value=[])
@patch("agentic.agent.get_tools_by_names", return_value=[])
async def test_basic_chat(mock_tools, mock_mcp, mock_llm):
    """Test basic chat functionality with LangGraph workflow."""
    # Mock the LLM
    mock_llm_instance = Mock()
    mock_llm_instance.ainvoke.return_value.content = "Hello! How can I help you?"
    mock_llm.return_value = mock_llm_instance

    agent = ExampleAgent()

    # This should now use the real LangGraph workflow
    response = await agent.chat("Hello world", "user123")

    assert isinstance(response, str)
    assert len(response) > 0  # Should get some response


@patch("agentic.agent.ChatOpenAI")
def test_framework_methods(mock_llm):
    """Test that framework methods exist and return expected types."""
    # Mock the LLM
    mock_llm.return_value = Mock()
    mock_llm.return_value.invoke.return_value.content = "Test response"

    agent = ExampleAgent()

    # Test developer API methods
    assert isinstance(agent.get_knowledge(), list)
    assert isinstance(agent.get_personality(), str)
    assert isinstance(agent.get_classification_categories(), list)
    assert isinstance(agent.get_category_requirements(), list)

    # Test internal methods exist and workflow is built
    assert hasattr(agent, "_build_workflow")
    assert agent._workflow is not None


# Phase 2 tests - Real workflow integration


@pytest.mark.asyncio
@patch("agentic.agent.ChatOpenAI")
@patch("agentic.agent.load_mcp_tools", return_value=[])
@patch("agentic.agent.get_tools_by_names", return_value=[])
async def test_complete_flow(mock_tools, mock_mcp, mock_llm):
    """Test the main happy path - complete request with custom handler."""
    # Mock LLM to classify as ReviewRequest  
    mock_llm_instance = Mock()
    async def mock_ainvoke(prompt):
        if "Classify" in prompt:
            return Mock(content="ReviewRequest")
        else:
            return Mock(content="NONE")
    mock_llm_instance.ainvoke = mock_ainvoke
    mock_llm.return_value = mock_llm_instance

    agent = ExampleAgent()
    agent.register_handler("ReviewRequest", agent.handle_review_request)

    response = await agent.chat("Review https://github.com/repo/pr/123", "user123")
    assert "Review created" in response


@pytest.mark.asyncio
@patch("agentic.agent.ChatOpenAI")
@patch("agentic.agent.load_mcp_tools", return_value=[])
@patch("agentic.agent.get_tools_by_names", return_value=[])
async def test_missing_requirements(mock_tools, mock_mcp, mock_llm):
    """Test missing requirements handling."""
    # Mock LLM to classify as ReviewRequest but message lacks URL
    mock_llm_instance = Mock()
    async def mock_ainvoke(prompt):
        if "Classify" in prompt:
            return Mock(content="ReviewRequest")
        elif "casual chat conversation" in prompt:
            return Mock(content="What's the URL you want me to review?")
        else:
            return Mock(content="url")  # Missing URL field
    mock_llm_instance.ainvoke = mock_ainvoke
    mock_llm.return_value = mock_llm_instance

    agent = ExampleAgent()
    response = await agent.chat("Please review my code", "user123")
    assert "url" in response.lower()  # Should ask for URL in a conversational way
    # Response should be brief and casual
    assert len(response) < 100  # Should be concise, not verbose


@pytest.mark.asyncio
@patch("agentic.agent.ChatOpenAI")
@patch("agentic.agent.load_mcp_tools", return_value=[])
@patch("agentic.agent.get_tools_by_names", return_value=[])
async def test_default_flow(mock_tools, mock_mcp, mock_llm):
    """Test fallback to default flow."""
    # Mock LLM to classify as "default" and provide response
    mock_llm_instance = Mock()
    mock_llm_instance.ainvoke.side_effect = [Mock(content="default"), Mock(content="Our vacation policy is...")]
    mock_llm.return_value = mock_llm_instance

    agent = ExampleAgent()
    response = await agent.chat("What's our vacation policy?", "user123")
    assert isinstance(response, str)
    assert len(response) > 0
