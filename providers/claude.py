#!/usr/bin/env python3
"""
Claude Provider Adapter

Renders a composed prompt in a format friendly for Claude Code usage.
"""

from __future__ import annotations

import json
from .provider_base import BaseProvider


class ClaudeProvider(BaseProvider):
    name = "claude"

    def render(self, payload) -> str:  # noqa: ANN001 - generic payload
        # Produce a compact, readable prompt for Claude Code.
        context = (
            json.dumps(payload.project_context, indent=2)
            if payload.project_context
            else "New project"
        )
        tools = (
            json.dumps(payload.mcp_tools, indent=2)
            if payload.mcp_tools
            else "None"
        )
        return (
            f"You are '{payload.agent_name}' ({payload.agent_id}).\n\n"
            f"## Role Prompt\n{payload.base_prompt}\n\n"
            f"## Project Context\n{context}\n\n"
            f"## MCP Tools\n{tools}\n\n"
            f"## Task\n{payload.task}\n\n"
            f"Please execute with your specialization and provide handoff notes if applicable.\n"
        )

    def render_sections(self, sections) -> str:  # noqa: ANN001
        lines = []
        for s in sections:
            title = s.get('title', s.get('key', 'Section')).title()
            # Claude-style markdown headers
            lines.append(f"## {title}")
            lines.append(str(s.get('text', '')))
            lines.append("")
        return "\n".join(lines).strip() + "\n"
