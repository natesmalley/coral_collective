#!/usr/bin/env python3
"""
Codex Subagents Interface

Lightweight CLI to use CoralCollective agents with Codex (or any LLM).
Generates a composed prompt from existing agent definitions and an ad‑hoc task.

Usage examples:
  # List agents
  python codex_subagents.py list

  # Get a composed prompt for an agent + task (prints to stdout)
  python codex_subagents.py prompt --agent backend_developer --task "Scaffold users API"

  # Parse '@agent "task"' shorthand
  python codex_subagents.py parse "@frontend_developer Build dashboard with auth"
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional

# Local imports
sys.path.insert(0, str(Path(__file__).parent))
from agent_runner import AgentRunner  # noqa: E402


def build_composed_prompt(agent_id: str, task: str, project_context: Optional[Dict] = None) -> str:
    """Create a model-agnostic prompt from an agent definition + task."""
    runner = AgentRunner()

    base_prompt = runner.get_agent_prompt(agent_id)
    if base_prompt.startswith("Agent prompt file not found"):
        return base_prompt

    # Compose a concise execution frame suitable for Codex or any LLM
    header = f"You are acting as the '{agent_id}' specialist."
    context = (
        json.dumps(project_context, indent=2) if project_context else "No additional project context."
    )

    composed = (
        f"{header}\n\n"
        f"=== ROLE PROMPT ===\n{base_prompt}\n\n"
        f"=== PROJECT CONTEXT ===\n{context}\n\n"
        f"=== TASK ===\n{task}\n\n"
        f"Produce clear outputs and, if applicable, handoff notes."
    )

    return composed


def list_agents() -> Dict[str, Dict]:
    runner = AgentRunner()
    return runner.agents_config.get("agents", {})


def parse_shorthand(expr: str) -> Optional[Dict[str, str]]:
    """Parse '@agent task text' shorthand into {agent, task}."""
    expr = expr.strip()
    if not expr.startswith("@"):
        return None
    # Split on first space after '@agent'
    try:
        head, tail = expr[1:].split(" ", 1)
        agent = head.strip()
        task = tail.strip().strip('"')
        return {"agent": agent, "task": task}
    except ValueError:
        return None


def main():
    parser = argparse.ArgumentParser(description="Codex Subagents Interface")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List available agents")

    p_prompt = sub.add_parser("prompt", help="Generate composed prompt for an agent + task")
    p_prompt.add_argument("--agent", required=True, help="Agent ID (e.g., backend_developer)")
    p_prompt.add_argument("--task", required=True, help="Task description")
    p_prompt.add_argument("--context", help="Path to JSON file with project context")

    p_parse = sub.add_parser("parse", help="Parse '@agent task' and emit composed prompt")
    p_parse.add_argument("expr", help="Expression like: @backend_developer Build API")
    p_parse.add_argument("--context", help="Path to JSON file with project context")

    args = parser.parse_args()

    if args.cmd == "list":
        agents = list_agents()
        for agent_id, info in agents.items():
            name = info.get("name", agent_id)
            category = info.get("category", "")
            desc = info.get("description", "")
            print(f"- {agent_id} [{category}] - {name}: {desc}")
        return

    context_obj = None
    ctx_path = getattr(args, "context", None)
    if ctx_path:
        p = Path(ctx_path)
        if p.exists():
            context_obj = json.loads(p.read_text())

    if args.cmd == "prompt":
        prompt = build_composed_prompt(args.agent, args.task, context_obj)
        print(prompt)
        return

    if args.cmd == "parse":
        parsed = parse_shorthand(args.expr)
        if not parsed:
            print("Error: expression must start with '@agent ' and include a task", file=sys.stderr)
            sys.exit(1)
        prompt = build_composed_prompt(parsed["agent"], parsed["task"], context_obj)
        print(prompt)
        return


if __name__ == "__main__":
    main()

