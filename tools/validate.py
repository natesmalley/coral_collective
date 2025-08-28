#!/usr/bin/env python3
"""
Validation CLI for Agent Force quality gates and dependencies.

Commands:
  current --state STATE.json --yaml workflows/project_templates.yaml --template-key KEY
  agent <agent_id> --state STATE.json --yaml workflows/project_templates.yaml
  all --state STATE.json --yaml workflows/project_templates.yaml --template-key KEY

Notes:
  - Requires a saved state from AgentManager.save_state
  - Uses dependencies from workflows/project_templates.yaml (dependencies section)
  - If phases define `outputs`, checks them against context.metadata
"""
import argparse
import json
import os
from typing import Any, Dict, List, Set

try:
    import yaml  # type: ignore
except Exception:
    yaml = None


def load_state(path: str) -> Dict[str, Any]:
    with open(path, 'r') as f:
        return json.load(f)


def load_templates(path: str) -> Dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML not available. Install pyyaml.")
    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}


def completed_agents(state: Dict[str, Any]) -> Set[str]:
    completed: Set[str] = set()
    for entry in state.get("execution_history", []):
        agent = entry.get("agent")
        result = entry.get("result", {})
        # consider completed if no error key present in result
        if agent and not result.get("error"):
            completed.add(agent)
    return completed


def validate_agent(agent_id: str, deps_map: Dict[str, Any], completed: Set[str]) -> Dict[str, Any]:
    req = deps_map.get(agent_id, {}).get("requires", [])
    missing = [r for r in req if r not in completed]
    return {
        "agent": agent_id,
        "dependencies_required": req,
        "dependencies_met": len(missing) == 0,
        "missing": missing,
    }


def collect_phase_outputs(templates: Dict[str, Any], template_key: str, phase_key: str) -> List[str]:
    tpl = (templates.get("templates") or {}).get(template_key) or {}
    phases = tpl.get("phases", {})
    cfg = phases.get(phase_key, {})
    return cfg.get("outputs", [])


def main() -> None:
    p = argparse.ArgumentParser(description="Agent Force Validation")
    sub = p.add_subparsers(dest="cmd")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--state", required=True, help="Path to saved state JSON")
    common.add_argument("--yaml", default="workflows/project_templates.yaml")

    p_current = sub.add_parser("current", parents=[common], help="Validate current phase")
    p_current.add_argument("--template-key", required=True)

    p_agent = sub.add_parser("agent", parents=[common], help="Validate a specific agent")
    p_agent.add_argument("agent_id")

    p_all = sub.add_parser("all", parents=[common], help="Validate all phases")
    p_all.add_argument("--template-key", required=True)

    args = p.parse_args()

    state = load_state(args.state)
    templates = load_templates(args.yaml)
    deps_map = templates.get("dependencies", {})
    done = completed_agents(state)
    warnings: List[str] = []
    # Security baseline check
    if not os.path.exists("SECURITY.md"):
        warnings.append("SECURITY.md missing")
    # Documentation baseline check
    required_docs = [
        "docs/README.md",
        "docs/requirements/",
        "docs/api/",
        "docs/architecture/",
        "docs/deployment/",
    ]
    for path in required_docs:
        if path.endswith("/"):
            if not os.path.isdir(path):
                warnings.append(f"Missing directory: {path}")
        else:
            if not os.path.exists(path):
                warnings.append(f"Missing file: {path}")

    if args.cmd == "agent":
        report = validate_agent(args.agent_id, deps_map, done)
        print(json.dumps(report, indent=2))
        return

    if args.cmd == "current":
        current = state.get("current_phase")
        tpl = (templates.get("templates") or {}).get(args.template_key) or {}
        agents = (tpl.get("phases", {}).get(current, {}) or {}).get("agents", [])
        results = [validate_agent(a, deps_map, done) for a in agents]
        outputs = collect_phase_outputs(templates, args.template_key, current)
        outputs_met = all(o in (state.get("context", {}).get("metadata", {}) or {}) for o in outputs)
        print(json.dumps({
            "phase": current,
            "agents": results,
            "required_outputs": outputs,
            "outputs_met": outputs_met,
            "warnings": warnings,
        }, indent=2))
        return

    if args.cmd == "all":
        tpl = (templates.get("templates") or {}).get(args.template_key) or {}
        phases = list((tpl.get("phases") or {}).keys())
        phase_reports: Dict[str, Any] = {}
        for ph in phases:
            agents = (tpl.get("phases", {}).get(ph, {}) or {}).get("agents", [])
            results = [validate_agent(a, deps_map, done) for a in agents]
            outputs = collect_phase_outputs(templates, args.template_key, ph)
            outputs_met = all(o in (state.get("context", {}).get("metadata", {}) or {}) for o in outputs)
            phase_reports[ph] = {
                "agents": results,
                "required_outputs": outputs,
                "outputs_met": outputs_met,
            }
        print(json.dumps({
            "template": args.template_key,
            "project_phase": state.get("current_phase"),
            "phases": phase_reports,
            "warnings": warnings,
        }, indent=2))
        return

    p.print_help()


if __name__ == "__main__":
    main()
