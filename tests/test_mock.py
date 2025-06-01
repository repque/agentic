"""
Test with mocked dependencies to avoid requiring actual LangChain installation.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys

# Mock all the LangChain modules before importing our code
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

# Mock specific classes and functions
sys.modules["langgraph.graph"].StateGraph = MagicMock
sys.modules["langgraph.graph"].START = "START"
sys.modules["langgraph.graph"].END = "END"
sys.modules["langgraph.checkpoint.memory"].MemorySaver = MagicMock
sys.modules["langchain_openai"].ChatOpenAI = MagicMock


def test_basic_mock_import():
    """Test that we can import our agent with mocked dependencies."""
    from src.agentic import Agent, CategoryRequirement

    # This should work now
    assert Agent is not None
    assert CategoryRequirement is not None


@pytest.mark.asyncio
async def test_agent_creation_with_mocks():
    """Test agent creation with fully mocked LangChain."""
    from src.agentic import Agent, CategoryRequirement

    class TestAgent(Agent):
        def get_classification_categories(self):
            return ["ReviewRequest", "Query"]

        def get_category_requirements(self):
            return [
                CategoryRequirement(category="ReviewRequest", required_fields=["url"])
            ]

    # Mock the StateGraph workflow compilation
    mock_workflow = MagicMock()
    
    async def mock_ainvoke(*args, **kwargs):
        return {
            "messages": [{"role": "assistant", "content": "Test response"}]
        }
    
    mock_workflow.ainvoke = mock_ainvoke

    with patch("src.agentic.agent.StateGraph") as mock_state_graph, \
         patch("src.agentic.agent.load_mcp_tools", return_value=[]), \
         patch("src.agentic.agent.get_tools_by_names", return_value=[]):
        mock_graph_instance = MagicMock()
        mock_graph_instance.compile.return_value = mock_workflow
        mock_state_graph.return_value = mock_graph_instance

        agent = TestAgent()
        assert agent.name == "agent"
        assert len(agent.get_classification_categories()) == 2

        # Test chat with mocked workflow
        response = await agent.chat("Hello", "user123")
        assert response == "Test response"


def test_handler_registration_with_mocks():
    """Test handler registration works with mocked system."""
    from src.agentic import Agent
    from src.agentic.models import Message, HandlerResponse

    class TestAgent(Agent):
        def get_classification_categories(self):
            return ["ReviewRequest"]

        def handle_review(self, state):
            return HandlerResponse(
                messages=[Message(role="assistant", content="Review created")]
            )

    with patch("src.agentic.agent.StateGraph"), \
         patch("src.agentic.agent.load_mcp_tools", return_value=[]), \
         patch("src.agentic.agent.get_tools_by_names", return_value=[]):
        agent = TestAgent()

        # Test handler registration
        agent.register_handler("ReviewRequest", agent.handle_review)
        assert "ReviewRequest" in agent.handlers

        # Test duplicate registration fails
        with pytest.raises(ValueError, match="already registered"):
            agent.register_handler("ReviewRequest", agent.handle_review)
