#!/usr/bin/env python3
"""
Agent Prompt Service

Builds a provider-agnostic prompt payload from agent definitions, task, and context.
Adapters can render and deliver the payload for different providers (Claude, Codex, etc.).
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any

try:
    from .agent_runner import AgentRunner
except Exception:  # pragma: no cover - fallback for partial environments
    AgentRunner = None  # type: ignore


@dataclass
class PromptPayload:
    agent_id: str
    agent_name: str
    base_prompt: str
    task: str
    project_context: dict[str, Any] | None
    mcp_tools: dict[str, Any] | None

    def to_default_text(self) -> str:
        """Default, model-agnostic prompt rendering."""
        context = (
            json.dumps(self.project_context, indent=2)
            if self.project_context
            else "New project"
        )
        tools = json.dumps(self.mcp_tools, indent=2) if self.mcp_tools else "None"
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
    runner: AgentRunner | None = None,
    project_context: dict[str, Any] | None = None,
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
    mcp_tools: dict[str, Any] | None = None
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


# --- Token utilities and budgeting ---


class TokenEstimator:
    """Rough token estimator with optional tiktoken support."""

    def __init__(self, model: str | None = None):
        self.model = model or "generic"
        self._tk = None
        try:  # optional dependency
            import tiktoken  # type: ignore

            # Select encoding if model known; fallback to cl100k_base
            try:
                enc = tiktoken.encoding_for_model(self.model)
            except Exception:
                enc = tiktoken.get_encoding("cl100k_base")
            self._tk = enc
        except Exception:
            self._tk = None

    def estimate(self, text: str) -> int:
        if not text:
            return 0
        if self._tk is not None:
            try:
                return len(self._tk.encode(text))
            except Exception:
                pass
        # Fallback heuristic: ~4 chars/token
        return max(1, math.ceil(len(text) / 4))


def build_sections(payload: PromptPayload, expand: bool = True) -> list[dict[str, Any]]:
    """Build ordered sections with required/optional flags before provider rendering."""
    sections: list[dict[str, Any]] = []
    sections.append(
        {
            "key": "role_prompt",
            "title": "ROLE PROMPT",
            "text": payload.base_prompt,
            "required": True,
        }
    )

    # Project context is optional; include if provided or expand requested
    context_text = None
    if payload.project_context is not None:
        context_text = json.dumps(payload.project_context, indent=2)
    elif expand:
        context_text = "New project"
    if context_text is not None:
        sections.append(
            {
                "key": "project_context",
                "title": "PROJECT CONTEXT",
                "text": context_text,
                "required": False,
            }
        )

    # MCP tools optional - handle both old dict format and new documentation format
    if expand and payload.mcp_tools:
        if isinstance(payload.mcp_tools, dict) and "documentation" in payload.mcp_tools:
            # New bridge-generated documentation format
            mcp_text = payload.mcp_tools["documentation"]
            if mcp_text:
                sections.append(
                    {
                        "key": "mcp_tools",
                        "title": "MCP TOOLS AVAILABLE",
                        "text": mcp_text,
                        "required": False,
                    }
                )
        else:
            # Legacy format - raw JSON
            sections.append(
                {
                    "key": "mcp_tools",
                    "title": "MCP TOOLS",
                    "text": json.dumps(payload.mcp_tools, indent=2),
                    "required": False,
                }
            )

    sections.append(
        {
            "key": "task",
            "title": "TASK",
            "text": payload.task,
            "required": True,
        }
    )

    return sections


def _truncate_text_by_ratio(text: str, ratio: float) -> str:
    if ratio >= 1.0:
        return text
    if ratio <= 0:
        return ""
    n = max(1, int(len(text) * ratio))
    # Try to end on a sentence boundary
    truncated = text[:n]
    m = re.search(r"[\.!?]\s+\Z", truncated)
    return truncated if m else truncated.rstrip() + "…"


def fit_sections_to_budget(
    sections: list[dict[str, Any]],
    estimator: TokenEstimator,
    budget_tokens: int,
    overhead_tokens: int = 128,
) -> list[dict[str, Any]]:
    """Reduce optional sections and truncate long ones to fit budget.

    Strategy:
    1) Drop MCP tools if needed
    2) Truncate project context progressively; drop if still too large
    3) Truncate role prompt until it fits
    Required sections (role_prompt, task) are preserved; task is not truncated.
    """
    # Work on a copy
    secs = [dict(s) for s in sections]

    def total_tokens(items: list[dict[str, Any]]) -> int:
        return sum(estimator.estimate(s["text"]) for s in items) + overhead_tokens

    # Quick success path
    if total_tokens(secs) <= budget_tokens:
        return secs

    # 1) Drop MCP tools if present
    for i, s in list(enumerate(secs)):
        if s["key"] == "mcp_tools":
            test = secs[:i] + secs[i + 1 :]
            if total_tokens(test) <= budget_tokens:
                return test
            secs = test
            break

    # 2) Truncate project context
    for i, s in list(enumerate(secs)):
        if s["key"] == "project_context":
            # Iteratively reduce to 75%, 50%, 25%
            for ratio in (0.75, 0.5, 0.25):
                s["text"] = _truncate_text_by_ratio(s["text"], ratio)
                if total_tokens(secs) <= budget_tokens:
                    return secs
            # Drop entirely if still too big
            test = secs[:i] + secs[i + 1 :]
            if total_tokens(test) <= budget_tokens:
                return test
            secs = test
            break

    # 3) Truncate role prompt (required) progressively until we fit
    for _i, s in enumerate(secs):
        if s["key"] == "role_prompt":
            # Coarse passes
            for ratio in (0.75, 0.5, 0.35, 0.25):
                s["text"] = _truncate_text_by_ratio(s["text"], ratio)
                if total_tokens(secs) <= budget_tokens:
                    return secs
            # Fine-grained trimming loop
            ratio = 0.25
            while total_tokens(secs) > budget_tokens and len(s["text"]) > 0:
                ratio *= 0.85
                s["text"] = _truncate_text_by_ratio(s["text"], ratio)
            return secs

    return secs


def chunk_text(
    text: str, estimator: TokenEstimator, chunk_tokens: int = 2000
) -> list[str]:
    """Split text into chunks near chunk_tokens boundaries, preferring paragraph breaks."""
    paragraphs = re.split(r"(\n\n+)", text)  # keep separators
    chunks: list[str] = []
    buf = []
    buf_tokens = 0
    for part in paragraphs:
        ptoks = estimator.estimate(part)
        if buf_tokens + ptoks > chunk_tokens and buf:
            chunks.append("".join(buf).strip())
            buf = [part]
            buf_tokens = ptoks
        else:
            buf.append(part)
            buf_tokens += ptoks
    if buf:
        chunks.append("".join(buf).strip())
    return chunks


class AgentPromptService:
    """Compatibility wrapper for the refactored prompt service functions."""

    def __init__(self, base_path=None):
        """Initialize the service (base_path kept for compatibility)."""
        self.base_path = base_path

    def compose(
        self,
        agent_id: str,
        task: str,
        runner=None,
        project_context=None,
        include_mcp_tools=True,
    ):
        """Wrapper for the compose function."""
        return compose(agent_id, task, runner, project_context, include_mcp_tools)

    async def compose_async(
        self,
        agent_id: str,
        task: str,
        runner=None,
        project_context=None,
        include_mcp_tools=True,
        mcp_bridge=None,
    ):
        """Wrapper for the compose_async function."""
        return await compose_async(
            agent_id, task, runner, project_context, include_mcp_tools, mcp_bridge
        )


async def compose_async(
    agent_id: str,
    task: str,
    runner: AgentRunner | None = None,
    project_context: dict[str, Any] | None = None,
    include_mcp_tools: bool = True,
    mcp_bridge=None,
) -> PromptPayload:
    """
    Async version of compose that uses the new MCP bridge system.
    Provides enhanced MCP tool documentation with examples and permissions.
    """
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

    # Enhanced MCP tools with bridge system
    mcp_tools_text: str | None = None
    if include_mcp_tools and mcp_bridge:
        try:
            # Import bridge components
            from .tools.agent_mcp_bridge import MCPToolsPromptGenerator

            # Generate comprehensive MCP tools documentation
            prompt_generator = MCPToolsPromptGenerator(mcp_bridge)
            mcp_tools_text = await prompt_generator.generate_tools_section()

            if not mcp_tools_text.strip():
                mcp_tools_text = None

        except Exception as e:
            print(f"Warning: Failed to generate MCP tools documentation: {e}")
            # Fallback to simple tools list
            try:
                available_tools = await mcp_bridge.get_available_tools()
                if available_tools:
                    mcp_tools_text = (
                        f"Available MCP Tools: {', '.join(available_tools.keys())}"
                    )
            except Exception:
                pass

    # Convert text to dict format for compatibility (will be converted back in build_sections)
    mcp_tools_dict = {"documentation": mcp_tools_text} if mcp_tools_text else None

    return PromptPayload(
        agent_id=agent_id,
        agent_name=agent_name,
        base_prompt=base_prompt,
        task=task,
        project_context=project_context,
        mcp_tools=mcp_tools_dict,
    )
