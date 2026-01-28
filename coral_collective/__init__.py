"""
CoralCollective - AI Agent Orchestration Framework

A modular framework for orchestrating specialized AI agents in software development workflows.
"""

__version__ = "1.0.0"
__author__ = "CoralCollective Contributors"

from typing import Any, Dict, List, Optional

# Core imports
try:
    from .agent_prompt_service import (
        AgentPromptService,
        PromptPayload,
        compose,
        compose_async,
    )
    from .agent_runner import AgentRunner
    from .project_manager import ProjectManager
except ImportError:
    # For development, allow imports from root
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from coral_collective.agent_prompt_service import (
        AgentPromptService,
        PromptPayload,
        compose,
        compose_async,
    )
    from coral_collective.agent_runner import AgentRunner
    from coral_collective.project_manager import ProjectManager

# Tools imports
# Configuration
from .config import load_agents_config, load_model_config
from .tools.feedback_collector import FeedbackCollector
from .tools.project_state import ProjectStateManager

__all__ = [
    "AgentRunner",
    "ProjectManager",
    "AgentPromptService",
    "PromptPayload",
    "compose",
    "compose_async",
    "ProjectStateManager",
    "FeedbackCollector",
    "load_agents_config",
    "load_model_config",
    "__version__",
]


def get_version() -> str:
    """Get the current version of CoralCollective."""
    return __version__


def list_agents() -> List[str]:
    """List all available agents."""
    try:
        config = load_agents_config()
        return list(config.get("agents", {}).keys())
    except Exception:
        return []
