"""
Performance comparison tests for multi-node vs single-node workflow.

Tests to ensure the multi-node architecture doesn't introduce significant overhead.
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, patch
from agentic import Agent, CategoryRequirement, Message, HandlerResponse
from agentic.models import AgentState


class PerformanceTestAgent(Agent):
    """Agent for performance testing."""
    
    def get_classification_categories(self):
        return ["TestCategory"]
    
    def get_category_requirements(self):
        return [CategoryRequirement(category="TestCategory", required_fields=["field1"])]
    
    def handle_test_category(self, state: AgentState) -> HandlerResponse:
        return HandlerResponse(
            messages=[Message(role="assistant", content="Handler response")]
        )


@pytest.fixture
def perf_agent():
    """Create performance test agent."""
    with patch("agentic.agent.StateGraph"), \
         patch("agentic.agent.load_mcp_tools", return_value=[]), \
         patch("agentic.agent.get_tools_by_names", return_value=[]):
        agent = PerformanceTestAgent()
        agent.register_handler("TestCategory", agent.handle_test_category)
        return agent


class TestNodePerformance:
    """Test performance characteristics of individual nodes."""
    
    @pytest.mark.asyncio
    async def test_classify_node_performance(self, perf_agent):
        """Test classification node performance."""
        state = AgentState(messages=[Message(role="user", content="Test message")])
        
        with patch("agentic.agent.classify_message_with_llm", return_value="TestCategory"):
            start_time = time.perf_counter()
            
            # Run classification multiple times
            for _ in range(100):
                await perf_agent._classify_node(state)
            
            end_time = time.perf_counter()
            avg_time = (end_time - start_time) / 100
            
            # Should be fast (less than 1ms per call, excluding actual LLM call)
            assert avg_time < 0.001, f"Classification too slow: {avg_time:.4f}s"
    
    @pytest.mark.asyncio
    async def test_requirements_node_performance(self, perf_agent):
        """Test requirements checking node performance."""
        state = AgentState(
            messages=[Message(role="user", content="Test message")],
            category="TestCategory"
        )
        
        with patch("agentic.agent.check_requirements_with_llm", return_value=(True, [])):
            start_time = time.perf_counter()
            
            # Run requirements check multiple times
            for _ in range(100):
                await perf_agent._check_requirements_node(state)
            
            end_time = time.perf_counter()
            avg_time = (end_time - start_time) / 100
            
            # Should be fast (less than 1ms per call, excluding actual LLM call)
            assert avg_time < 0.001, f"Requirements check too slow: {avg_time:.4f}s"
    
    @pytest.mark.asyncio
    async def test_handler_execution_performance(self, perf_agent):
        """Test handler execution performance."""
        state = AgentState(
            messages=[Message(role="user", content="Test message")],
            category="TestCategory"
        )
        
        start_time = time.perf_counter()
        
        # Run handler execution multiple times
        for _ in range(100):
            await perf_agent._execute_handler_node(state)
        
        end_time = time.perf_counter()
        avg_time = (end_time - start_time) / 100
        
        # Should be very fast (less than 1ms per call)
        assert avg_time < 0.001, f"Handler execution too slow: {avg_time:.4f}s"
    
    @pytest.mark.asyncio
    async def test_confidence_scoring_performance(self, perf_agent):
        """Test confidence scoring performance."""
        state = AgentState(messages=[
            Message(role="user", content="Test"),
            Message(role="assistant", content="Test response")
        ])
        
        start_time = time.perf_counter()
        
        # Run confidence scoring multiple times
        for _ in range(1000):
            await perf_agent._score_confidence_node(state)
        
        end_time = time.perf_counter()
        avg_time = (end_time - start_time) / 1000
        
        # Should be very fast (less than 0.01ms per call)
        assert avg_time < 0.00001, f"Confidence scoring too slow: {avg_time:.4f}s"


class TestRoutingPerformance:
    """Test performance of conditional routing functions."""
    
    def test_routing_function_performance(self, perf_agent):
        """Test conditional routing function performance."""
        state = AgentState(
            category="TestCategory",
            missing_requirements=[],
            needs_escalation=False
        )
        
        start_time = time.perf_counter()
        
        # Run routing functions many times
        for _ in range(10000):
            perf_agent._should_check_requirements(state)
            perf_agent._requirements_met(state)
            perf_agent._has_custom_handler(state)
            perf_agent._confidence_check(state)
        
        end_time = time.perf_counter()
        avg_time = (end_time - start_time) / 40000  # 4 functions * 10000 iterations
        
        # Routing should be extremely fast (microseconds)
        assert avg_time < 0.000001, f"Routing functions too slow: {avg_time:.6f}s"


class TestWorkflowOverhead:
    """Test the overhead introduced by multi-node architecture."""
    
    @pytest.mark.asyncio
    async def test_node_sequence_overhead(self, perf_agent):
        """Test overhead of running nodes in sequence."""
        # Simulate a complete workflow path
        state = AgentState(messages=[Message(role="user", content="Test message")])
        
        with patch("agentic.agent.classify_message_with_llm", return_value="TestCategory"), \
             patch("agentic.agent.check_requirements_with_llm", return_value=(True, [])):
            
            start_time = time.perf_counter()
            
            # Run a complete node sequence
            for _ in range(10):
                # Simulate the main workflow path
                state = await perf_agent._classify_node(state)
                state = await perf_agent._check_requirements_node(state)
                state = await perf_agent._route_node(state)
                state = await perf_agent._execute_handler_node(state)
                
                # Reset state for next iteration
                state = AgentState(messages=[Message(role="user", content="Test message")])
            
            end_time = time.perf_counter()
            avg_time = (end_time - start_time) / 10
            
            # Complete sequence should be reasonably fast (less than 10ms, excluding LLM calls)
            assert avg_time < 0.01, f"Node sequence too slow: {avg_time:.4f}s"
    
    @pytest.mark.asyncio
    async def test_state_copying_overhead(self, perf_agent):
        """Test overhead of state object copying between nodes."""
        large_messages = [
            Message(role="user", content="User message"),
            Message(role="assistant", content="A" * 1000),  # Large response
            Message(role="user", content="Follow up"),
            Message(role="assistant", content="B" * 1000),  # Another large response
        ]
        
        state = AgentState(messages=large_messages, metadata={"large_data": "X" * 1000})
        
        start_time = time.perf_counter()
        
        # Run operations that might copy state
        for _ in range(100):
            result = await perf_agent._route_node(state)
            # Verify state is modified (not just copied)
            assert result.workflow_step == "route"
        
        end_time = time.perf_counter()
        avg_time = (end_time - start_time) / 100
        
        # State operations should be fast even with large state
        assert avg_time < 0.001, f"State operations too slow: {avg_time:.4f}s"


class TestMemoryUsage:
    """Test memory characteristics of multi-node workflow."""
    
    @pytest.mark.asyncio
    async def test_no_memory_leaks_in_nodes(self, perf_agent):
        """Test that nodes don't accumulate memory over time."""
        import gc
        import sys
        
        # Get initial memory reference count
        initial_objects = len(gc.get_objects())
        
        # Run many operations
        for i in range(100):
            state = AgentState(messages=[
                Message(role="user", content=f"Message {i}")
            ])
            
            await perf_agent._classify_node(state)
            await perf_agent._route_node(state)
            
            # Periodically force garbage collection
            if i % 20 == 0:
                gc.collect()
        
        # Force final garbage collection
        gc.collect()
        
        # Check that we haven't accumulated too many objects
        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects
        
        # Allow some growth but not excessive
        assert object_growth < 1000, f"Potential memory leak: {object_growth} new objects"
    
    @pytest.mark.asyncio
    async def test_state_size_remains_bounded(self, perf_agent):
        """Test that state object doesn't grow unbounded."""
        import sys
        
        state = AgentState(messages=[Message(role="user", content="Test")])
        initial_size = sys.getsizeof(state)
        
        # Run operations that might grow state
        for _ in range(100):
            state = await perf_agent._route_node(state)
            state.metadata[f"key_{_}"] = f"value_{_}"  # Simulate metadata growth
        
        final_size = sys.getsizeof(state)
        
        # State should not grow excessively (allowing for some metadata)
        size_growth = final_size - initial_size
        assert size_growth < 10000, f"State size grew too much: {size_growth} bytes"


class TestConcurrencyPerformance:
    """Test performance under concurrent load."""
    
    @pytest.mark.asyncio
    async def test_concurrent_node_execution(self, perf_agent):
        """Test that nodes can handle concurrent execution."""
        
        async def run_classification():
            state = AgentState(messages=[Message(role="user", content="Test")])
            with patch("agentic.agent.classify_message_with_llm", return_value="TestCategory"):
                return await perf_agent._classify_node(state)
        
        start_time = time.perf_counter()
        
        # Run many concurrent classifications
        tasks = [run_classification() for _ in range(50)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # All should complete successfully
        assert len(results) == 50
        assert all(r.workflow_step == "classify" for r in results)
        
        # Should benefit from concurrency (less than 50x sequential time)
        assert total_time < 0.1, f"Concurrent execution too slow: {total_time:.4f}s"


@pytest.mark.slow
class TestLongRunningPerformance:
    """Long-running performance tests (marked as slow)."""
    
    @pytest.mark.asyncio
    async def test_sustained_performance(self, perf_agent):
        """Test performance over sustained usage."""
        times = []
        
        for i in range(1000):
            state = AgentState(messages=[Message(role="user", content=f"Message {i}")])
            
            start = time.perf_counter()
            await perf_agent._route_node(state)
            end = time.perf_counter()
            
            times.append(end - start)
            
            # Check every 100 iterations that performance isn't degrading
            if i > 0 and i % 100 == 0:
                recent_avg = sum(times[-100:]) / 100
                early_avg = sum(times[:100]) / 100
                
                # Performance shouldn't degrade by more than 50%
                assert recent_avg < early_avg * 1.5, f"Performance degraded at iteration {i}"
        
        # Overall average should be reasonable
        overall_avg = sum(times) / len(times)
        assert overall_avg < 0.001, f"Overall performance too slow: {overall_avg:.4f}s"