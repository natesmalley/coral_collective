"""
CoralCollective Configuration Module

Handles loading and management of agent and model configurations.
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional


def load_agents_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load agents configuration from YAML file.

    Args:
        config_path: Path to agents.yaml file. Defaults to config/agents.yaml

    Returns:
        Dictionary containing agent configurations
    """
    if config_path:
        path = Path(config_path)
    else:
        # Try multiple locations
        possible_paths = [
            Path.cwd() / "config" / "agents.yaml",
            Path(__file__).parent.parent.parent / "config" / "agents.yaml",
        ]

        for p in possible_paths:
            if p.exists():
                path = p
                break
        else:
            raise FileNotFoundError("Could not find agents.yaml configuration file")

    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_model_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load model assignments configuration from YAML file.

    Args:
        config_path: Path to model config file. Defaults to config/model_assignments_2026.yaml

    Returns:
        Dictionary containing model configurations
    """
    if config_path:
        path = Path(config_path)
    else:
        # Try multiple locations
        possible_paths = [
            Path.cwd() / "config" / "model_assignments_2026.yaml",
            Path(__file__).parent.parent.parent
            / "config"
            / "model_assignments_2026.yaml",
        ]

        for p in possible_paths:
            if p.exists():
                path = p
                break
        else:
            # Fall back to older config if 2026 not found
            fallback = Path.cwd() / "config" / "model_assignments.yaml"
            if fallback.exists():
                path = fallback
            else:
                raise FileNotFoundError(
                    "Could not find model assignments configuration file"
                )

    with open(path, "r") as f:
        return yaml.safe_load(f)


def get_agent_config(agent_id: str) -> Optional[Dict[str, Any]]:
    """
    Get configuration for a specific agent.

    Args:
        agent_id: The agent identifier

    Returns:
        Agent configuration dictionary or None if not found
    """
    try:
        config = load_agents_config()
        return config.get("agents", {}).get(agent_id)
    except Exception:
        return None


def list_available_agents() -> list:
    """
    List all available agent IDs.

    Returns:
        List of agent identifiers
    """
    try:
        config = load_agents_config()
        return list(config.get("agents", {}).keys())
    except Exception:
        return []


__all__ = [
    "load_agents_config",
    "load_model_config",
    "get_agent_config",
    "list_available_agents",
]
