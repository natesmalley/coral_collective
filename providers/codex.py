#!/usr/bin/env python3
"""
Codex Provider Adapter

Renders a clearly sectioned prompt for Codex or similar LLMs.
"""

from __future__ import annotations

import json
from .provider_base import BaseProvider


class CodexProvider(BaseProvider):
    name = "codex"

    def render(self, payload) -> str:  # noqa: ANN001 - generic payload
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
            f"ROLE: {payload.agent_name} ({payload.agent_id})\n\n"
            f"PROMPT:\n{payload.base_prompt}\n\n"
            f"PROJECT CONTEXT:\n{context}\n\n"
            f"MCP TOOLS:\n{tools}\n\n"
            f"TASK:\n{payload.task}\n\n"
            f"OUTPUT: Provide concrete deliverables and handoff guidance.\n"
        )

    def render_sections(self, sections) -> str:  # noqa: ANN001
        parts = []
        for s in sections:
            title = s.get('title', s.get('key', 'SECTION')).upper()
            parts.append(f"{title}:")
            parts.append(str(s.get('text', '')))
            parts.append("")
        return "\n".join(parts).strip() + "\n"
