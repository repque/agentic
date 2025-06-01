"""
Agentic AI Framework

A simplified framework for building agentic AI systems built on LangGraph.
Provides "batteries included, zero boilerplate" development experience.
"""

from .agent import Agent
from .models import AgentState, Message, CategoryRequirement, HandlerResponse
from .tools import load_mcp_tools, load_mcp_tools_async, get_tools_by_names, get_tools_by_names_async, create_mcp_config_template
from .testing import MockLLMAgent
from .cli import cli
from . import system_prompts

__version__ = "0.1.0"
__all__ = [
    "Agent",
    "AgentState",
    "Message",
    "CategoryRequirement",
    "HandlerResponse",
    "load_mcp_tools",
    "load_mcp_tools_async",
    "get_tools_by_names",
    "get_tools_by_names_async", 
    "create_mcp_config_template",
    "MockLLMAgent",
    "cli",
    "system_prompts",
]
