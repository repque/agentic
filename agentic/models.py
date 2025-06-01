"""
Core type definitions for the Agentic framework.

All models use Pydantic for type safety and validation.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class Message(BaseModel):
    """A message in the conversation."""

    role: Literal["user", "assistant", "system"]
    content: str


class AgentState(BaseModel):
    """State object passed through LangGraph workflow."""

    messages: List[Message] = Field(default_factory=list)
    category: Optional[str] = None
    missing_requirements: List[str] = Field(default_factory=list)
    confidence: Optional[float] = None
    needs_escalation: bool = False
    workflow_step: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CategoryRequirement(BaseModel):
    """Defines required information for a category."""

    category: str
    required_fields: List[str]


class HandlerResponse(BaseModel):
    """Response from custom handlers."""

    messages: List[Message]
    metadata: Dict[str, Any] = Field(default_factory=dict)
