"""
Simple testing utilities for agents.
"""

from typing import List
from unittest.mock import Mock
from .agent import Agent


class MockLLMAgent(Agent):
    """Agent with mocked LLM responses for testing."""

    def __init__(self, mock_responses: List[str], **kwargs):
        self.mock_responses = mock_responses
        self.response_index = 0
        super().__init__(**kwargs)

    def _create_llm(self, llm_name: str):
        """Create a mock LLM."""
        mock_llm = Mock()

        def mock_invoke(prompt):
            if self.response_index < len(self.mock_responses):
                response = self.mock_responses[self.response_index]
                self.response_index += 1
            else:
                response = "Mock response"

            mock_response = Mock()
            mock_response.content = response
            return mock_response

        mock_llm.invoke = mock_invoke
        return mock_llm