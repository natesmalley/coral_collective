from typing import Dict, List, Optional, Type, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import os
from pathlib import Path
from dataclasses import asdict

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

from ..core.base_agent import BaseAgent, AgentRole, AgentStatus, AgentContext, AgentHandoff


@dataclass
class WorkflowPhase:
    name: str
    agents: List[str]
    description: str
    prerequisites: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)


class AgentManager:
    def __init__(self, project_context: AgentContext):
        self.agents: Dict[str, BaseAgent] = {}
        self.project_context = project_context
        self.workflow_phases = self._initialize_workflow_phases()
        self.current_phase = "planning"
        self.execution_history: List[Dict[str, Any]] = []
        self.handoff_history: List[AgentHandoff] = []
        self.agent_metrics: Dict[str, Dict[str, Any]] = {}

    def _initialize_workflow_phases(self) -> Dict[str, WorkflowPhase]:
        return {
            "planning": WorkflowPhase(
                name="Planning & Documentation Foundation",
                agents=["architect", "technical_writer_phase1"],
                description="Create technical plan and documentation foundation",
                outputs=["project_structure", "technical_spec", "documentation_templates"]
            ),
            "development": WorkflowPhase(
                name="Development to Specification",
                agents=["backend", "ai_ml", "frontend", "security"],
                description="Build following documented specifications",
                prerequisites=["project_structure", "technical_spec"],
                outputs=["backend_api", "ai_features", "frontend_ui", "security_implementation"]
            ),
            "quality": WorkflowPhase(
                name="Quality & Deployment",
                agents=["qa", "devops"],
                description="Test and deploy the application",
                prerequisites=["backend_api", "frontend_ui"],
                outputs=["test_results", "deployment_config", "live_application"]
            ),
            "documentation": WorkflowPhase(
                name="Documentation Completion",
                agents=["technical_writer_phase2"],
                description="Finalize user documentation and guides",
                prerequisites=["live_application"],
                outputs=["user_documentation", "api_docs", "deployment_guides"]
            )
        }

    def register_agent(self, agent: BaseAgent) -> None:
        agent.context = self.project_context
        self.agents[agent.name] = agent
        print(f"✅ Registered agent: {agent.name} ({agent.role.value})")

    def unregister_agent(self, agent_name: str) -> None:
        if agent_name in self.agents:
            del self.agents[agent_name]
            print(f"❌ Unregistered agent: {agent_name}")

    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        return self.agents.get(agent_name)

    def get_agents_by_role(self, role: AgentRole) -> List[BaseAgent]:
        return [agent for agent in self.agents.values() if agent.role == role]

    def get_available_agents(self) -> List[str]:
        return [
            f"{agent.name} ({agent.role.value}): {agent.status.value}"
            for agent in self.agents.values()
        ]

    def execute_task(self, agent_name: str, task: Dict[str, Any]) -> Dict[str, Any]:
        agent = self.get_agent(agent_name)
        if not agent:
            return {"error": f"Agent {agent_name} not found"}

        if not agent.validate_prerequisites():
            return {"error": f"Prerequisites not met for {agent_name}"}

        agent.update_status(AgentStatus.WORKING)
        
        try:
            result = agent.execute(task)
            agent.update_status(AgentStatus.COMPLETED)
            self._record_execution(agent_name, task, result)
            return result
        except Exception as e:
            agent.update_status(AgentStatus.ERROR)
            error_result = {"error": str(e), "agent": agent_name}
            self._record_execution(agent_name, task, error_result)
            return error_result

    def handoff(self, from_agent: str, to_agent: str, context: Dict[str, Any] = None) -> bool:
        source = self.get_agent(from_agent)
        target = self.get_agent(to_agent)

        if not source or not target:
            print(f"❌ Handoff failed: Agent not found")
            return False

        handoff = source.generate_handoff(to_agent)
        self.handoff_history.append(handoff)
        
        target.context = source.context
        if context:
            target.context.metadata.update(context)

        self._display_handoff(handoff)
        return True

    def _display_handoff(self, handoff: AgentHandoff) -> None:
        print(f"\n{'='*50}")
        print(f"🤝 AGENT HANDOFF")
        print(f"{'='*50}")
        print(f"From: {handoff.from_agent}")
        print(f"To: {handoff.to_agent}")
        print(f"\nCompleted:")
        for item in handoff.completed_items:
            print(f"  ✅ {item}")
        print(f"\nNext Prompt:")
        print(f"  {handoff.next_prompt}")
        print(f"\nRecommendations:")
        for rec in handoff.recommendations:
            print(f"  • {rec}")
        print(f"{'='*50}\n")

    def _record_execution(self, agent_name: str, task: Dict[str, Any], result: Dict[str, Any]) -> None:
        record = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "task": task,
            "result": result
        }
        self.execution_history.append(record)
        # Update basic learning metrics
        m = self.agent_metrics.setdefault(agent_name, {"success": 0, "error": 0, "total": 0})
        m["total"] += 1
        if result.get("error"):
            m["error"] += 1
        else:
            m["success"] += 1

    def get_current_phase_agents(self) -> List[str]:
        if self.current_phase in self.workflow_phases:
            return self.workflow_phases[self.current_phase].agents
        return []

    def advance_phase(self) -> bool:
        phases = list(self.workflow_phases.keys())
        current_idx = phases.index(self.current_phase)
        
        if current_idx < len(phases) - 1:
            next_phase = phases[current_idx + 1]
            current = self.workflow_phases[self.current_phase]
            next_phase_obj = self.workflow_phases[next_phase]
            
            if all(output in self.project_context.metadata for output in current.outputs):
                self.current_phase = next_phase
                print(f"📈 Advanced to phase: {next_phase}")
                return True
            else:
                print(f"⚠️ Cannot advance: Missing outputs from {self.current_phase}")
                return False
        else:
            print("✅ All phases completed!")
            return False

    def get_workflow_status(self) -> Dict[str, Any]:
        return {
            "current_phase": self.current_phase,
            "phases": {
                name: {
                    "description": phase.description,
                    "agents": phase.agents,
                    "completed": all(
                        output in self.project_context.metadata 
                        for output in phase.outputs
                    )
                }
                for name, phase in self.workflow_phases.items()
            },
            "active_agents": [
                agent.name for agent in self.agents.values() 
                if agent.status == AgentStatus.WORKING
            ],
            "completed_tasks": self.project_context.completed_tasks[-10:]
        }

    def save_state(self, filepath: str) -> None:
        state = {
            "current_phase": self.current_phase,
            "context": {
                "project_path": self.project_context.project_path,
                "project_name": self.project_context.project_name,
                "tech_stack": self.project_context.tech_stack,
                "requirements": self.project_context.requirements,
                "completed_tasks": self.project_context.completed_tasks,
                "metadata": self.project_context.metadata
            },
            "execution_history": self.execution_history[-50:],
            "agent_metrics": self.agent_metrics,
            "timestamp": datetime.now().isoformat()
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        print(f"💾 State saved to: {filepath}")

    def load_state(self, filepath: str) -> bool:
        if not os.path.exists(filepath):
            print(f"❌ State file not found: {filepath}")
            return False

        with open(filepath, 'r') as f:
            state = json.load(f)

        self.current_phase = state["current_phase"]
        ctx = state["context"]
        self.project_context = AgentContext(
            project_path=ctx["project_path"],
            project_name=ctx["project_name"],
            tech_stack=ctx["tech_stack"],
            requirements=ctx["requirements"],
            completed_tasks=ctx["completed_tasks"],
            metadata=ctx["metadata"]
        )
        self.execution_history = state.get("execution_history", [])
        self.agent_metrics = state.get("agent_metrics", {})
        
        print(f"📂 State loaded from: {filepath}")
        return True

    # -------- Learning & Feedback --------
    def record_feedback(self, agent_name: str, task_name: str, outcome: str, notes: str = "", tags: List[str] = None, filepath: str = "docs/learning/agent_feedback.jsonl") -> bool:
        """Persist agent feedback for continuous improvement.

        Writes JSONL entries with fields: timestamp, agent, task, outcome, notes, tags
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "task": task_name,
            "outcome": outcome,
            "notes": notes,
            "tags": tags or [],
        }
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "a") as f:
                f.write(json.dumps(entry) + "\n")
            return True
        except Exception as e:
            print(f"⚠️ Failed to write feedback: {e}")
            return False

    # -------- Dynamic Workflow Loading --------
    def load_workflow_from_yaml(self, yaml_path: str, template_key: str) -> bool:
        """Load workflow phases from YAML templates, replacing current phases.

        YAML layout expected similar to workflows/project_templates.yaml
        with a top-level key `templates` and nested templates keyed by name.
        Each template has `phases` mapping names -> {agents: [...], parallel: bool, required: bool}
        """
        if yaml is None:
            print("❌ PyYAML not available. Install pyyaml to load workflows.")
            return False

        if not os.path.exists(yaml_path):
            print(f"❌ Workflow YAML not found: {yaml_path}")
            return False

        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f) or {}

        templates = data.get("templates", {})
        if template_key not in templates:
            print(f"❌ Template '{template_key}' not found in {yaml_path}")
            return False

        tpl = templates[template_key]
        phases = tpl.get("phases", {})
        new_phases: Dict[str, WorkflowPhase] = {}
        for phase_key, phase_cfg in phases.items():
            agents = phase_cfg.get("agents", [])
            desc = tpl.get("description", phase_key)
            # YAML may not encode prerequisites/outputs; keep empty for now
            new_phases[phase_key] = WorkflowPhase(
                name=phase_key,
                agents=agents,
                description=desc,
                prerequisites=phase_cfg.get("prerequisites", []),
                outputs=phase_cfg.get("outputs", []),
            )

        self.workflow_phases = new_phases
        # Reset current phase to first in order
        if new_phases:
            self.current_phase = list(new_phases.keys())[0]
        print(f"📜 Loaded workflow template: {template_key} ({len(new_phases)} phases)")
        return True

    def list_templates(self, yaml_path: str) -> List[str]:
        if yaml is None or not os.path.exists(yaml_path):
            return []
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f) or {}
        return list((data.get("templates") or {}).keys())
