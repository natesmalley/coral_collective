import json
from agents.core.base_agent import AgentContext
from agents.managers.agent_manager import AgentManager


def test_dynamic_workflow_loading():
    ctx = AgentContext(project_path=".", project_name="TestApp")
    mgr = AgentManager(ctx)
    ok = mgr.load_workflow_from_yaml("workflows/project_templates.yaml", "web_app_standard")
    assert ok, "Failed to load workflow"
    assert mgr.current_phase == "planning"
    agents = mgr.get_current_phase_agents()
    assert "project_architect" in agents
    assert "technical_writer_phase1" in agents


def test_phase_advance_with_empty_outputs():
    ctx = AgentContext(project_path=".", project_name="TestApp")
    mgr = AgentManager(ctx)
    mgr.load_workflow_from_yaml("workflows/project_templates.yaml", "web_app_standard")
    # With no outputs in template phases, advance should succeed
    assert mgr.advance_phase() is True
    assert mgr.current_phase != "planning"

