#!/usr/bin/env python3
"""
Agent Prompt Service

Builds a provider-agnostic prompt payload from agent definitions, task, and context.
Adapters can render and deliver the payload for different providers (Claude, Codex, etc.).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from agent_runner import AgentRunner
except Exception:  # pragma: no cover - fallback for partial environments
    AgentRunner = None  # type: ignore


@dataclass
class PromptPayload:
    agent_id: str
    agent_name: str
    base_prompt: str
    task: str
    project_context: Optional[Dict[str, Any]]
    mcp_tools: Optional[Dict[str, Any]]

    def to_default_text(self) -> str:
        """Default, model-agnostic prompt rendering."""
        context = (
            json.dumps(self.project_context, indent=2)
            if self.project_context
            else "New project"
        )
        tools = (
            json.dumps(self.mcp_tools, indent=2)
            if self.mcp_tools
            else "None"
        )
        return (
            f"You are acting as '{self.agent_name}' ({self.agent_id}).\n\n"
            f"=== ROLE PROMPT ===\n{self.base_prompt}\n\n"
            f"=== PROJECT CONTEXT ===\n{context}\n\n"
            f"=== MCP TOOLS (if any) ===\n{tools}\n\n"
            f"=== TASK ===\n{self.task}\n\n"
            f"Provide clear outputs and, if applicable, handoff notes.\n"
        )


def compose(
    agent_id: str,
    task: str,
    runner: Optional[AgentRunner] = None,
    project_context: Optional[Dict[str, Any]] = None,
    include_mcp_tools: bool = True,
) -> PromptPayload:
    """Compose a provider-agnostic prompt payload for a given agent and task."""
    # Lazy init to avoid side effects in import
    if runner is None and AgentRunner is not None:
        runner = AgentRunner()

    if runner is None:
        raise RuntimeError("AgentRunner unavailable; cannot compose prompt")

    # Use the existing AgentRunner logic to get the base agent prompt
    base_prompt = runner.get_agent_prompt(agent_id)

    # Agent metadata from config
    agent_cfg = runner.agents_config.get("agents", {}).get(agent_id, {})
    agent_name = agent_cfg.get("name", agent_id)

    # MCP tools (optional)
    mcp_tools: Optional[Dict[str, Any]] = None
    if include_mcp_tools and getattr(runner, "mcp_client", None):
        try:
            tools = runner.mcp_client.get_tools_for_agent(agent_id)  # type: ignore[attr-defined]
            if tools:
                mcp_tools = tools
        except Exception:
            # Tools unavailable; keep None
            pass

    return PromptPayload(
        agent_id=agent_id,
        agent_name=agent_name,
        base_prompt=base_prompt,
        task=task,
        project_context=project_context,
        mcp_tools=mcp_tools,
    )

