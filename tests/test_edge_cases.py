"""
Edge case tests for multi-node workflow routing.

Tests unusual situations and boundary conditions to ensure robust behavior.
"""

import pytest
from unittest.mock import Mock, patch
from agentic import Agent, CategoryRequirement, Message, HandlerResponse
from agentic.models import AgentState


class EdgeCaseAgent(Agent):
    """Agent for testing edge cases."""
    
    def get_classification_categories(self):
        return ["Category1", "Category2"]
    
    def get_category_requirements(self):
        return [
            CategoryRequirement(category="Category1", required_fields=["field1"]),
            CategoryRequirement(category="Category2", required_fields=["field1", "field2"])
        ]


@pytest.fixture
def edge_agent():
    """Create edge case test agent."""
    with patch("agentic.agent.StateGraph"), \
         patch("agentic.agent.load_mcp_tools", return_value=[]), \
         patch("agentic.agent.get_tools_by_names", return_value=[]):
        return EdgeCaseAgent()


class TestEdgeCaseRouting:
    """Test edge cases in workflow routing."""
    
    @pytest.mark.asyncio
    async def test_empty_messages_list(self, edge_agent):
        """Test behavior with empty messages list."""
        state = AgentState(messages=[])
        
        # Should handle gracefully without crashing
        with pytest.raises(IndexError):
            await edge_agent._classify_node(state)
    
    @pytest.mark.asyncio 
    async def test_classification_with_unknown_category(self, edge_agent):
        """Test when LLM returns a category not in defined categories."""
        state = AgentState(messages=[Message(role="user", content="Test message")])
        
        with patch("agentic.agent.classify_message_with_llm") as mock_classify:
            mock_classify.return_value = "UnknownCategory"
            
            result = await edge_agent._classify_node(state)
            assert result.category == "UnknownCategory"
            
            # Test routing with unknown category
            routing_result = edge_agent._should_check_requirements(result)
            assert routing_result == "check_requirements"  # Should still check requirements
    
    @pytest.mark.asyncio
    async def test_requirements_check_with_no_requirements_defined(self, edge_agent):
        """Test requirements check when no requirements are defined for category."""
        state = AgentState(
            messages=[Message(role="user", content="Test message")],
            category="CategoryWithNoRequirements"
        )
        
        with patch("agentic.agent.check_requirements_with_llm") as mock_check:
            mock_check.return_value = (True, [])  # No requirements, so met by default
            
            result = await edge_agent._check_requirements_node(state)
            assert result.missing_requirements == []
            assert len(result.messages) == 1  # No "Need:" message added
    
    @pytest.mark.asyncio
    async def test_handler_that_returns_no_messages(self, edge_agent):
        """Test custom handler that returns empty message list."""
        def empty_handler(state):
            return HandlerResponse(messages=[])
        
        edge_agent.register_handler("Category1", empty_handler)
        
        state = AgentState(
            messages=[Message(role="user", content="Test")],
            category="Category1"
        )
        
        result = await edge_agent._execute_handler_node(state)
        assert len(result.messages) == 1  # Only original message
    
    @pytest.mark.asyncio
    async def test_handler_that_returns_multiple_messages(self, edge_agent):
        """Test custom handler that returns multiple messages."""
        def multi_handler(state):
            return HandlerResponse(messages=[
                Message(role="assistant", content="First response"),
                Message(role="assistant", content="Second response"),
                Message(role="system", content="System message")
            ])
        
        edge_agent.register_handler("Category1", multi_handler)
        
        state = AgentState(
            messages=[Message(role="user", content="Test")],
            category="Category1"
        )
        
        result = await edge_agent._execute_handler_node(state)
        assert len(result.messages) == 4  # Original + 3 handler messages
        assert result.messages[1].content == "First response"
        assert result.messages[2].content == "Second response"
        assert result.messages[3].content == "System message"
    
    @pytest.mark.asyncio
    async def test_confidence_scoring_with_no_messages(self, edge_agent):
        """Test confidence scoring when there are no messages."""
        state = AgentState(messages=[])
        
        result = await edge_agent._score_confidence_node(state)
        assert result.confidence is None
        assert result.needs_escalation is False  # Default behavior
    
    @pytest.mark.asyncio
    async def test_confidence_scoring_with_empty_content(self, edge_agent):
        """Test confidence scoring with empty message content."""
        state = AgentState(messages=[
            Message(role="user", content="Test"),
            Message(role="assistant", content="")
        ])
        
        result = await edge_agent._score_confidence_node(state)
        assert result.confidence == 0.0  # Empty content = 0 confidence
        assert result.needs_escalation is True
    
    @pytest.mark.asyncio
    async def test_escalation_with_no_previous_response(self, edge_agent):
        """Test escalation when there's no previous assistant response."""
        state = AgentState(messages=[
            Message(role="user", content="Test")
        ])
        
        result = await edge_agent._escalate_node(state)
        # Should handle gracefully - might replace user message or add new message
        assert len(result.messages) >= 1


class TestWorkflowStateManagement:
    """Test workflow state management edge cases."""
    
    @pytest.mark.asyncio
    async def test_state_immutability_across_nodes(self, edge_agent):
        """Test that each node properly manages state without side effects."""
        original_state = AgentState(
            messages=[Message(role="user", content="Test message")],
            metadata={"original": True}
        )
        
        # Classification should not modify original messages
        with patch("agentic.agent.classify_message_with_llm", return_value="Category1"):
            classify_result = await edge_agent._classify_node(original_state)
            
        assert len(classify_result.messages) == 1
        assert classify_result.messages[0].content == "Test message"
        assert classify_result.metadata["original"] is True
        assert classify_result.workflow_step == "classify"
        assert classify_result.category == "Category1"
    
    @pytest.mark.asyncio
    async def test_workflow_step_tracking(self, edge_agent):
        """Test that workflow_step is correctly tracked through nodes."""
        state = AgentState(messages=[Message(role="user", content="Test")])
        
        # Test each node sets its step correctly
        classify_result = await edge_agent._classify_node(state)
        assert classify_result.workflow_step == "classify"
        
        route_result = await edge_agent._route_node(classify_result)
        assert route_result.workflow_step == "route"
        
        generate_result = await edge_agent._generate_response_node(route_result)
        assert generate_result.workflow_step == "generate_response"


class TestConditionalRoutingEdgeCases:
    """Test edge cases in conditional routing logic."""
    
    def test_routing_with_none_category(self, edge_agent):
        """Test routing when category is None."""
        state = AgentState(category=None)
        
        result = edge_agent._should_check_requirements(state)
        assert result == "generate_response"  # Should skip requirements check
    
    def test_routing_with_empty_category(self, edge_agent):
        """Test routing when category is empty string."""
        state = AgentState(category="")
        
        result = edge_agent._should_check_requirements(state)
        assert result == "generate_response"  # Should skip requirements check
    
    def test_handler_routing_with_none_category(self, edge_agent):
        """Test handler routing when category is None."""
        state = AgentState(category=None)
        
        result = edge_agent._has_custom_handler(state)
        assert result == "generate_response"  # No handler for None category
    
    def test_requirements_routing_with_empty_missing_requirements(self, edge_agent):
        """Test requirements routing when missing_requirements is empty."""
        state = AgentState(missing_requirements=[])
        
        result = edge_agent._requirements_met(state)
        assert result == "route"  # Empty list means requirements met


class TestErrorHandling:
    """Test error handling in individual nodes."""
    
    @pytest.mark.asyncio
    async def test_classification_llm_error(self, edge_agent):
        """Test behavior when LLM classification fails."""
        state = AgentState(messages=[Message(role="user", content="Test")])
        
        with patch("agentic.agent.classify_message_with_llm", side_effect=Exception("LLM Error")):
            # Should handle error gracefully
            with pytest.raises(Exception):
                await edge_agent._classify_node(state)
    
    @pytest.mark.asyncio
    async def test_requirements_check_llm_error(self, edge_agent):
        """Test behavior when requirements check LLM fails."""
        state = AgentState(
            messages=[Message(role="user", content="Test")],
            category="Category1"
        )
        
        with patch("agentic.agent.check_requirements_with_llm", side_effect=Exception("LLM Error")):
            # Should handle error gracefully
            with pytest.raises(Exception):
                await edge_agent._check_requirements_node(state)
    
    @pytest.mark.asyncio
    async def test_handler_execution_error(self, edge_agent):
        """Test behavior when custom handler raises exception."""
        def failing_handler(state):
            raise Exception("Handler error")
        
        edge_agent.register_handler("Category1", failing_handler)
        
        state = AgentState(
            messages=[Message(role="user", content="Test")],
            category="Category1"
        )
        
        # Should propagate handler errors
        with pytest.raises(Exception, match="Handler error"):
            await edge_agent._execute_handler_node(state)
    
    @pytest.mark.asyncio
    async def test_response_generation_error(self, edge_agent):
        """Test behavior when response generation fails."""
        state = AgentState(messages=[Message(role="user", content="Test")])
        
        with patch.object(edge_agent, "_generate_response", side_effect=Exception("Generation error")):
            with pytest.raises(Exception, match="Generation error"):
                await edge_agent._generate_response_node(state)