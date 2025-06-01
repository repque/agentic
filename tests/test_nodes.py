"""
Unit tests for individual workflow nodes.

Tests each node in isolation to verify correct behavior and state transitions.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from agentic import Agent, CategoryRequirement, Message, HandlerResponse
from agentic.models import AgentState


class NodeTestAgent(Agent):
    """Test agent for node testing."""
    
    def get_classification_categories(self):
        return ["ReviewRequest", "Query"]
    
    def get_category_requirements(self):
        return [CategoryRequirement(category="ReviewRequest", required_fields=["url"])]
    
    def handle_review_request(self, state: AgentState) -> HandlerResponse:
        return HandlerResponse(
            messages=[Message(role="assistant", content="Review created")]
        )


@pytest.fixture
def test_agent():
    """Create test agent with mocked dependencies."""
    with patch("agentic.agent.StateGraph"), \
         patch("agentic.agent.load_mcp_tools", return_value=[]), \
         patch("agentic.agent.get_tools_by_names", return_value=[]):
        agent = NodeTestAgent()
        agent.register_handler("ReviewRequest", agent.handle_review_request)
        return agent


@pytest.fixture
def sample_state():
    """Create fresh sample AgentState for testing."""
    def _create_state():
        return AgentState(
            messages=[Message(role="user", content="Review https://github.com/repo/pr/123")]
        )
    return _create_state


class TestClassifyNode:
    """Test the classify node functionality."""
    
    @pytest.mark.asyncio
    async def test_classify_with_categories(self, test_agent, sample_state):
        """Test classification when categories are defined."""
        state = sample_state()  # Create fresh state
        
        # Mock the LLM classification function
        with patch("agentic.agent.classify_message_with_llm") as mock_classify:
            mock_classify.return_value = "ReviewRequest"
            
            result = await test_agent._classify_node(state)
            
            assert result.workflow_step == "classify"
            assert result.category == "ReviewRequest"
            mock_classify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_classify_no_categories(self, sample_state):
        """Test classification when no categories are defined."""
        state = sample_state()  # Create fresh state
        
        # Create agent with no categories
        with patch("agentic.agent.StateGraph"), \
             patch("agentic.agent.load_mcp_tools", return_value=[]), \
             patch("agentic.agent.get_tools_by_names", return_value=[]):
            agent = Agent()  # Base agent with no categories
            
            result = await agent._classify_node(state)
            
            assert result.workflow_step == "classify"
            assert result.category == "default"


class TestCheckRequirementsNode:
    """Test the requirements checking node."""
    
    @pytest.mark.asyncio
    async def test_requirements_met(self, test_agent, sample_state):
        """Test when all requirements are satisfied."""
        state = sample_state()  # Create fresh state
        state.category = "ReviewRequest"
        
        with patch("agentic.agent.check_requirements_with_llm") as mock_check:
            mock_check.return_value = (True, [])  # Requirements met, no missing fields
            
            result = await test_agent._check_requirements_node(state)
            
            assert result.workflow_step == "check_requirements"
            assert result.missing_requirements == []
            assert len(result.messages) == 1  # Original message only
    
    @pytest.mark.asyncio
    async def test_requirements_missing(self, test_agent, sample_state):
        """Test when requirements are missing."""
        state = sample_state()  # Create fresh state
        state.category = "ReviewRequest"
        
        with patch("agentic.agent.check_requirements_with_llm") as mock_check:
            mock_check.return_value = (False, ["url"])  # Missing URL
            
            result = await test_agent._check_requirements_node(state)
            
            assert result.workflow_step == "check_requirements"
            assert result.missing_requirements == ["url"]
            assert len(result.messages) == 2  # Original + conversational response
            assert "url" in result.messages[-1].content.lower()  # Should ask for URL conversationally


class TestRouteNode:
    """Test the routing decision node."""
    
    @pytest.mark.asyncio
    async def test_route_node_tracking(self, test_agent, sample_state):
        """Test that route node sets workflow step correctly."""
        state = sample_state()  # Create fresh state
        result = await test_agent._route_node(state)
        
        assert result.workflow_step == "route"
        # Route node doesn't change other state - routing handled by conditional edges


class TestExecuteHandlerNode:
    """Test custom handler execution."""
    
    @pytest.mark.asyncio
    async def test_execute_existing_handler(self, test_agent, sample_state):
        """Test execution of registered handler."""
        state = sample_state()  # Create fresh state
        state.category = "ReviewRequest"
        
        result = await test_agent._execute_handler_node(state)
        
        assert result.workflow_step == "execute_handler"
        assert len(result.messages) == 2  # Original + handler response
        assert "Review created" in result.messages[-1].content
    
    @pytest.mark.asyncio
    async def test_execute_missing_handler(self, test_agent, sample_state):
        """Test when handler doesn't exist for category."""
        state = sample_state()  # Create fresh state
        state.category = "NonExistentCategory"
        
        result = await test_agent._execute_handler_node(state)
        
        assert result.workflow_step == "execute_handler"
        assert len(result.messages) == 1  # Only original message, no handler response


class TestGenerateResponseNode:
    """Test default LLM response generation."""
    
    @pytest.mark.asyncio
    async def test_generate_response(self, test_agent, sample_state):
        """Test LLM response generation."""
        state = sample_state()  # Create fresh state
        
        with patch.object(test_agent, "_generate_response") as mock_generate:
            mock_generate.return_value = "I can help you with that!"
            
            result = await test_agent._generate_response_node(state)
            
            assert result.workflow_step == "generate_response"
            assert len(result.messages) == 2  # Original + generated response
            assert result.messages[-1].content == "I can help you with that!"
            assert result.messages[-1].role == "assistant"


class TestScoreConfidenceNode:
    """Test confidence scoring functionality."""
    
    @pytest.mark.asyncio
    async def test_high_confidence(self, test_agent, sample_state):
        """Test high confidence response."""
        state = sample_state()  # Create fresh state
        
        # Add a long response (high confidence)
        state.messages.append(
            Message(role="assistant", content="This is a very detailed and comprehensive response that should score high confidence because of its length and detail.")
        )
        
        result = await test_agent._score_confidence_node(state)
        
        assert result.workflow_step == "score_confidence"
        assert result.confidence is not None
        assert result.confidence > test_agent.confidence_threshold
        assert result.needs_escalation is False
    
    @pytest.mark.asyncio
    async def test_low_confidence(self, test_agent, sample_state):
        """Test low confidence response."""
        state = sample_state()  # Create fresh state
        
        # Add a short response (low confidence)
        state.messages.append(
            Message(role="assistant", content="Short.")
        )
        
        result = await test_agent._score_confidence_node(state)
        
        assert result.workflow_step == "score_confidence"
        assert result.confidence is not None
        assert result.confidence < test_agent.confidence_threshold
        assert result.needs_escalation is True


class TestEscalateNode:
    """Test escalation handling."""
    
    @pytest.mark.asyncio
    async def test_escalation(self, test_agent, sample_state):
        """Test escalation replaces low confidence response."""
        state = sample_state()  # Create fresh state
        
        # Add a low confidence response
        state.messages.append(
            Message(role="assistant", content="Short response.")
        )
        
        result = await test_agent._escalate_node(state)
        
        assert result.workflow_step == "escalate"
        # Escalation should replace the last message with team review message
        assert "reviewed by our team" in result.messages[-1].content.lower()


class TestConditionalRouting:
    """Test conditional routing functions."""
    
    def test_should_check_requirements_with_categories(self, test_agent):
        """Test routing to requirements check when categories exist."""
        state = AgentState(category="ReviewRequest")
        
        result = test_agent._should_check_requirements(state)
        assert result == "check_requirements"
    
    def test_should_check_requirements_default_category(self, test_agent):
        """Test routing to generate response for default category."""
        state = AgentState(category="default")
        
        result = test_agent._should_check_requirements(state)
        assert result == "generate_response"
    
    def test_requirements_met_routing(self, test_agent):
        """Test routing when requirements are satisfied."""
        state = AgentState(missing_requirements=[])
        
        result = test_agent._requirements_met(state)
        assert result == "route"
    
    def test_requirements_not_met_routing(self, test_agent):
        """Test routing when requirements are missing."""
        state = AgentState(missing_requirements=["url"])
        
        result = test_agent._requirements_met(state)
        assert result == "__end__"
    
    def test_has_custom_handler_routing(self, test_agent):
        """Test routing to custom handler when it exists."""
        state = AgentState(category="ReviewRequest")
        
        result = test_agent._has_custom_handler(state)
        assert result == "execute_handler"
    
    def test_no_custom_handler_routing(self, test_agent):
        """Test routing to default response when no handler exists."""
        state = AgentState(category="UnknownCategory")
        
        result = test_agent._has_custom_handler(state)
        assert result == "generate_response"
    
    def test_confidence_check_escalation(self, test_agent):
        """Test routing to escalation on low confidence."""
        state = AgentState(needs_escalation=True)
        
        result = test_agent._confidence_check(state)
        assert result == "escalate"
    
    def test_confidence_check_end(self, test_agent):
        """Test routing to end on high confidence."""
        state = AgentState(needs_escalation=False)
        
        result = test_agent._confidence_check(state)
        assert result == "__end__"