import json
import os
from agents.core.base_agent import AgentContext
from agents.managers.agent_manager import AgentManager


def test_state_save_and_load(tmp_path):
    ctx = AgentContext(project_path=".", project_name="PersistApp")
    mgr = AgentManager(ctx)
    mgr.project_context.metadata["sample_output"] = True
    state_file = tmp_path / "state.json"
    mgr.save_state(str(state_file))

    mgr2 = AgentManager(AgentContext(project_path=".", project_name="Other"))
    assert mgr2.load_state(str(state_file)) is True
    assert mgr2.project_context.project_name == "PersistApp"
    assert mgr2.project_context.metadata.get("sample_output") is True

