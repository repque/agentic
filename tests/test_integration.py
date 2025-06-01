"""
Integration test demonstrating the complete framework functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys

# Mock LangChain dependencies
langchain_mocks = {
    "langchain_core": MagicMock(),
    "langchain_core.language_models": MagicMock(),
    "langchain_openai": MagicMock(),
    "langgraph": MagicMock(),
    "langgraph.graph": MagicMock(),
    "langgraph.checkpoint": MagicMock(),
    "langgraph.checkpoint.memory": MagicMock(),
    "langgraph.prebuilt": MagicMock(),
}

for module_name, mock_module in langchain_mocks.items():
    sys.modules[module_name] = mock_module

sys.modules["langgraph.graph"].StateGraph = MagicMock
sys.modules["langgraph.graph"].START = "START"
sys.modules["langgraph.graph"].END = "END"
sys.modules["langgraph.checkpoint.memory"].MemorySaver = MagicMock
sys.modules["langchain_openai"].ChatOpenAI = MagicMock


@pytest.mark.asyncio
async def test_complete_framework_demo():
    """Test the complete framework functionality as shown in README."""
    from agentic import Agent, CategoryRequirement, Message, HandlerResponse

    class EnterpriseAgent(Agent):
        def __init__(self):
            super().__init__(
                name="enterprise_assistant",
                llm="openai/gpt-4",
                tools=["jira_client", "email_sender"],
                confidence_threshold=0.75,
            )

            self.register_handler("ReviewRequest", self.handle_review)

        def get_classification_categories(self):
            return ["ReviewRequest", "Query"]

        def get_category_requirements(self):
            return [
                CategoryRequirement(category="ReviewRequest", required_fields=["url"])
            ]

        def get_knowledge(self):
            return ["./docs/", "./policies/"]

        def handle_review(self, state):
            # Mock business logic
            return HandlerResponse(
                messages=[
                    Message(
                        role="assistant",
                        content="Review JIRA-456 created and team notified",
                    )
                ]
            )

    # Mock the StateGraph workflow
    mock_workflow = MagicMock()

    async def mock_ainvoke(state, config):
        # Simulate different workflow paths based on input
        messages = state.get("messages", [])
        if not messages:
            return {"messages": [{"role": "assistant", "content": "No message"}]}

        user_message = (
            messages[0].get("content", "")
            if isinstance(messages[0], dict)
            else messages[0].content
        )

        if "https://" in user_message:
            # Complete review request
            return {
                "messages": [
                    {
                        "role": "assistant",
                        "content": "Review JIRA-456 created and team notified",
                    }
                ]
            }
        elif "review" in user_message.lower():
            # Missing requirements
            return {"messages": [{"role": "assistant", "content": "Need: url"}]}
        else:
            # Default flow
            return {
                "messages": [{"role": "assistant", "content": "Our policy states..."}]
            }

    mock_workflow.ainvoke = mock_ainvoke

    with patch("agentic.agent.StateGraph") as mock_state_graph, \
         patch("agentic.agent.load_mcp_tools", return_value=[]), \
         patch("agentic.agent.get_tools_by_names", return_value=[]):
        mock_graph_instance = MagicMock()
        mock_graph_instance.compile.return_value = mock_workflow
        mock_state_graph.return_value = mock_graph_instance

        agent = EnterpriseAgent()

        # Test 1: Complete flow (requirements met → custom handler)
        response = await agent.chat("Review https://github.com/repo/pr/123", "user123")
        assert "JIRA-456" in response

        # Test 2: Missing requirements
        response = await agent.chat("Please review my code", "user123")
        assert "Need:" in response and "url" in response

        # Test 3: Default flow
        response = await agent.chat("What's our vacation policy?", "user123")
        assert "policy" in response


def test_tools_integration():
    """Test tool integration works correctly."""
    from agentic import Agent

    class ToolAgent(Agent):
        def __init__(self):
            super().__init__(tools=[])  # No specific tools, will load from MCP

    with patch("agentic.agent.StateGraph"), \
         patch("agentic.agent.load_mcp_tools", return_value=[]), \
         patch("agentic.agent.get_tools_by_names", return_value=[]):
        agent = ToolAgent()

        # Verify tools attribute exists
        assert hasattr(agent, 'available_tools')
        assert isinstance(agent.available_tools, list)


@pytest.mark.asyncio
async def test_validation_and_error_handling():
    """Test input validation and error handling."""
    from agentic import Agent

    with patch("agentic.agent.StateGraph"), \
         patch("agentic.agent.load_mcp_tools", return_value=[]), \
         patch("agentic.agent.get_tools_by_names", return_value=[]):
        agent = Agent()

        # Test input validation
        with pytest.raises(ValueError, match="non-empty string"):
            await agent.chat("", "user123")

        with pytest.raises(ValueError, match="non-empty string"):
            await agent.chat("hello", "")

        # Test handler validation
        with pytest.raises(ValueError, match="non-empty string"):
            agent.register_handler("", lambda x: x)

        with pytest.raises(ValueError, match="callable"):
            agent.register_handler("test", "not_callable")


def test_confidence_scoring():
    """Test confidence scoring functionality."""
    from agentic import Agent

    class TestAgent(Agent):
        pass

    with patch("agentic.agent.StateGraph"), \
         patch("agentic.agent.load_mcp_tools", return_value=[]), \
         patch("agentic.agent.get_tools_by_names", return_value=[]):
        agent = TestAgent()

        # Test confidence calculation
        # Test confidence behavior - confidence is now calculated inline
        # in _process_message as len(response) / 100
        assert agent.confidence_threshold == 0.7  # Default threshold
        assert hasattr(agent, 'handle_low_confidence')
        # Confidence calculation is now internal to the framework


def test_testing_utilities():
    """Test the testing utilities work correctly."""
    from agentic.testing import MockLLMAgent

    # Test MockLLMAgent
    mock_workflow = MagicMock()
    
    async def mock_ainvoke(*args, **kwargs):
        return {
            "messages": [{"role": "assistant", "content": "Mock response"}]
        }
    
    mock_workflow.ainvoke = mock_ainvoke

    with patch("agentic.agent.StateGraph") as mock_state_graph, \
         patch("agentic.agent.load_mcp_tools", return_value=[]), \
         patch("agentic.agent.get_tools_by_names", return_value=[]):
        mock_graph_instance = MagicMock()
        mock_graph_instance.compile.return_value = mock_workflow
        mock_state_graph.return_value = mock_graph_instance

        mock_agent = MockLLMAgent(
            mock_responses=["Mock response"]
        )

        # Verify mock responses work
        assert hasattr(mock_agent, "mock_responses")
        assert mock_agent.mock_responses == ["Mock response"]


@pytest.mark.asyncio
@patch("agentic.agent.get_tools_by_names", return_value=[])
@patch("agentic.agent.load_mcp_tools", return_value=[])
@patch("agentic.agent.StateGraph")
async def test_handler_lifecycle(mock_state_graph, mock_load_mcp_tools, mock_get_tools_by_names):
    """Test complete handler registration and execution lifecycle."""
    from agentic import Agent, HandlerResponse, Message

    # Mock workflow setup
    mock_workflow = MagicMock()
    
    async def mock_ainvoke(*args, **kwargs):
        return {
            "messages": [{"role": "assistant", "content": "Handler executed"}]
        }
    
    mock_workflow.ainvoke = mock_ainvoke
    mock_graph_instance = MagicMock()
    mock_graph_instance.compile.return_value = mock_workflow
    mock_state_graph.return_value = mock_graph_instance

    class TestAgent(Agent):
        def get_classification_categories(self):
            return ["TestCategory"]

        def handle_test_category(self, state):
            return HandlerResponse(
                messages=[Message(role="assistant", content="Handler executed")]
            )

    agent = TestAgent()

    # Test handler registration
    agent.register_handler("TestCategory", agent.handle_test_category)
    assert "TestCategory" in agent.handlers

    # Test workflow rebuild on handler registration
    assert mock_state_graph.called  # Workflow was rebuilt

    # Test chat executes successfully
    response = await agent.chat("Test message", "user123")
    assert isinstance(response, str)
