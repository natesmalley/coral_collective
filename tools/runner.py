#!/usr/bin/env python3
"""
Minimal CLI runner for Agent Force

Features:
- Initialize project context
- Load workflow from YAML templates
- Register prompt-based placeholder agents from config/agents.yaml
- Show status and phases; advance phases
- Save/load manager state

Note: This runner uses a lightweight PromptAgent to satisfy BaseAgent.
It does not implement real execution; it exposes prompts for human/LLM use.
"""
import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

from agents.core.base_agent import BaseAgent, AgentRole, AgentContext, AgentHandoff, AgentStatus
from agents.managers.agent_manager import AgentManager


class PromptAgent(BaseAgent):
    def __init__(self, name: str, role: AgentRole, description: str, prompt_path: str, capabilities: List[str], context: AgentContext):
        super().__init__(name=name, role=role, description=description, capabilities=capabilities, context=context)
        self.prompt_path = prompt_path

    def _load_prompt_template(self) -> str:
        if not os.path.exists(self.prompt_path):
            return f"Prompt not found: {self.prompt_path}"
        try:
            with open(self.prompt_path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error loading prompt: {e}"

    def validate_prerequisites(self) -> bool:
        # Placeholder: always true
        return True

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        # Return the prompt and echo the task; no side effects
        prompt = self._load_prompt_template()
        self.add_completed_task(task.get('name', 'task'))
        return {"agent": self.name, "role": self.role.value, "task": task, "prompt": prompt}

    def generate_handoff(self, next_agent: str) -> AgentHandoff:
        return AgentHandoff(
            from_agent=self.name,
            to_agent=next_agent,
            completed_items=self.tasks_completed[-5:],
            context=self.context.metadata,
            next_prompt=f"Refer to config/agents.yaml for next agent '{next_agent}' and use its prompt.",
            recommendations=["Follow documentation-first handoff protocol."]
        )


def load_agents_registry(path: str) -> Dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML not available. Install pyyaml to use the registry.")
    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}


def register_all_agents(manager: AgentManager, registry_path: str) -> None:
    data = load_agents_registry(registry_path)
    agents = data.get('agents', {})
    for agent_id, cfg in agents.items():
        role_str = cfg.get('role')
        try:
            # Map role string to AgentRole if possible; fallback to TECHNICAL_WRITER
            role = AgentRole(role_str) if role_str in AgentRole._value2member_map_ else AgentRole.TECHNICAL_WRITER
        except Exception:
            role = AgentRole.TECHNICAL_WRITER
        description = cfg.get('description') or f"Agent {agent_id} ({role.value})"
        prompt_path = cfg.get('prompt_path')
        capabilities = cfg.get('capabilities', [])
        agent = PromptAgent(
            name=agent_id,
            role=role,
            description=description,
            prompt_path=prompt_path,
            capabilities=capabilities,
            context=manager.project_context,
        )
        manager.register_agent(agent)


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent Force Runner")
    sub = parser.add_subparsers(dest="cmd")

    p_init = sub.add_parser("init", help="Initialize a project context")
    p_init.add_argument("--project-name", required=True)
    p_init.add_argument("--project-path", default=str(Path.cwd()))

    p_load = sub.add_parser("load-workflow", help="Load workflow from YAML template")
    p_load.add_argument("template_key")
    p_load.add_argument("--yaml", default="workflows/project_templates.yaml")

    sub.add_parser("list-templates", help="List available workflow templates")

    p_reg = sub.add_parser("register-all", help="Register all agents from registry")
    p_reg.add_argument("--registry", default="config/agents.yaml")

    sub.add_parser("status", help="Show workflow status")
    sub.add_parser("phase", help="Show current phase agents")
    sub.add_parser("advance", help="Advance to next phase if outputs met")

    p_save = sub.add_parser("save-state", help="Save manager state")
    p_save.add_argument("filepath")

    p_load_state = sub.add_parser("load-state", help="Load manager state")
    p_load_state.add_argument("filepath")

    p_prompt = sub.add_parser("prompt", help="Print an agent's prompt")
    p_prompt.add_argument("agent_id")

    p_run = sub.add_parser("run", help="Run a simple task with an agent")
    p_run.add_argument("agent_id")
    p_run.add_argument("--name", default="task", help="Task name")
    p_run.add_argument("--data", default="{}", help="JSON string with task data")
    p_run.add_argument("--autosave", default=None, help="Optional state file to save after run")

    args = parser.parse_args()

    # Maintain a simple context across commands within a run
    context = AgentContext(project_path=str(Path.cwd()), project_name="unnamed")
    manager = AgentManager(project_context=context)

    if args.cmd == "init":
        manager.project_context = AgentContext(project_path=args.project_path, project_name=args.project_name)
        print(json.dumps({"ok": True, "project": args.project_name, "path": args.project_path}))
        return

    if args.cmd == "list-templates":
        tpls = manager.list_templates("workflows/project_templates.yaml")
        print("\n".join(tpls))
        return

    if args.cmd == "load-workflow":
        ok = manager.load_workflow_from_yaml(args.yaml, args.template_key)
        print(json.dumps({"ok": ok, "template": args.template_key}))
        return

    if args.cmd == "register-all":
        register_all_agents(manager, args.registry)
        return

    if args.cmd == "status":
        print(json.dumps(manager.get_workflow_status(), indent=2))
        return

    if args.cmd == "phase":
        print(json.dumps({"current_phase": manager.current_phase, "agents": manager.get_current_phase_agents()}, indent=2))
        return

    if args.cmd == "advance":
        ok = manager.advance_phase()
        print(json.dumps({"advanced": ok, "current_phase": manager.current_phase}))
        return

    if args.cmd == "save-state":
        manager.save_state(args.filepath)
        return

    if args.cmd == "load-state":
        manager.load_state(args.filepath)
        return

    if args.cmd == "prompt":
        # Ensure agents are registered to find the id
        register_all_agents(manager, "config/agents.yaml")
        agent = manager.get_agent(args.agent_id)
        if not agent:
            print(json.dumps({"error": f"Agent not found: {args.agent_id}"}))
            return
        print(agent.get_prompt())
        return

    if args.cmd == "run":
        # Register all so the agent exists
        register_all_agents(manager, "config/agents.yaml")
        try:
            data = json.loads(args.data)
        except Exception:
            data = {}
        result = manager.execute_task(args.agent_id, {"name": args.name, **data})
        print(json.dumps(result, indent=2))
        if args.autosave:
            manager.save_state(args.autosave)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
