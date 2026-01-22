"""
CoralCollective - AI Agent Orchestration Framework

A modular framework for orchestrating specialized AI agents in software development workflows.
"""

__version__ = "1.0.0"
__author__ = "CoralCollective Contributors"

from typing import Optional, Dict, Any, List

# Core imports
try:
    from .agent_runner import AgentRunner
    from .project_manager import ProjectManager
    from .agent_prompt_service import AgentPromptService
except ImportError:
    # For development, allow imports from root
    import sys
    import os

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from agent_runner import AgentRunner
    from project_manager import ProjectManager
    from agent_prompt_service import AgentPromptService

# Tools imports
from .tools.project_state import ProjectStateManager
from .tools.feedback_collector import FeedbackCollector

# Configuration
from .config import load_agents_config, load_model_config

__all__ = [
    "AgentRunner",
    "ProjectManager",
    "AgentPromptService",
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
