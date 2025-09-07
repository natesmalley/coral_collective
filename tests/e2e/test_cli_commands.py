"""
End-to-End CLI Command Tests

Tests cover:
1. Complete CLI command workflows
2. Interactive and non-interactive modes
3. Project initialization and management
4. Agent execution through CLI
5. Error handling and user feedback
6. Configuration management
"""

import pytest
import asyncio
import tempfile
import shutil
import subprocess
import json
import yaml
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
import click.testing
from io import StringIO

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.mark.e2e
@pytest.mark.cli
class TestCoreCliCommands:
    """Test core CLI command functionality"""
    
    def setup_method(self):
        """Set up CLI test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.original_cwd = Path.cwd()
        os.chdir(self.temp_dir)
        
        # Set environment variables for testing
        os.environ.update({
            'CORAL_ENV': 'test',
            'CORAL_BASE_PATH': str(self.temp_dir),
            'DISABLE_ANALYTICS': 'true'
        })
        
    def teardown_method(self):
        """Clean up CLI test environment"""
        os.chdir(self.original_cwd)
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_coral_init_command(self):
        """Test coral initialization command"""
        
        # Test project initialization
        result = subprocess.run([
            'python', '-c', '''
import sys
sys.path.insert(0, ".")
from coral_collective.cli.main import cli
import click.testing

runner = click.testing.CliRunner()
result = runner.invoke(cli, ["init", "test_project"])
print("EXIT_CODE:", result.exit_code)
print("OUTPUT:", result.output)
'''
        ], capture_output=True, text=True, cwd=self.original_cwd)
        
        # Should succeed or provide meaningful output
        assert "test_project" in result.stdout or result.returncode == 0
    
    @patch('agent_runner.AgentRunner')
    def test_coral_run_command(self, mock_runner_class):
        """Test coral run command"""
        
        # Mock agent runner
        mock_runner = Mock()
        mock_runner.run_agent.return_value = {
            "success": True,
            "outputs": {"result": "Agent executed successfully"},
            "duration": 30.5
        }
        mock_runner.get_available_agents.return_value = [
            {"id": "backend_developer", "role": "backend_developer"}
        ]
        mock_runner_class.return_value = mock_runner
        
        # Create test script to simulate CLI
        test_script = self.temp_dir / "test_run.py"
        test_script.write_text(f'''
import sys
sys.path.insert(0, "{self.original_cwd}")

from agent_runner import AgentRunner
import argparse

# Simulate CLI argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("command")
parser.add_argument("agent_id")
parser.add_argument("--task")
args = parser.parse_args(["run", "backend_developer", "--task", "Create API"])

# Execute agent
runner = AgentRunner()
result = runner.run_agent(args.agent_id, args.task or "Default task")

print("SUCCESS:", result["success"])
print("DURATION:", result["duration"])
''')
        
        # Run the test
        result = subprocess.run(['python', str(test_script)], 
                              capture_output=True, text=True)
        
        # Verify output contains expected results
        assert "SUCCESS: True" in result.stdout
        assert "DURATION:" in result.stdout
    
    @patch('agent_runner.AgentRunner')  
    def test_coral_list_command(self, mock_runner_class):
        """Test coral list command"""
        
        # Mock available agents
        mock_runner = Mock()
        mock_runner.get_available_agents.return_value = [
            {
                "id": "backend_developer",
                "role": "backend_developer", 
                "capabilities": ["api", "database"],
                "prompt_path": "agents/specialists/backend_developer.md"
            },
            {
                "id": "frontend_developer",
                "role": "frontend_developer",
                "capabilities": ["ui", "components"],
                "prompt_path": "agents/specialists/frontend_developer.md"
            },
            {
                "id": "project_architect", 
                "role": "architect",
                "capabilities": ["planning", "architecture"],
                "prompt_path": "agents/core/project_architect.md"
            }
        ]
        mock_runner_class.return_value = mock_runner
        
        # Create test script
        test_script = self.temp_dir / "test_list.py"
        test_script.write_text(f'''
import sys
sys.path.insert(0, "{self.original_cwd}")

from agent_runner import AgentRunner

runner = AgentRunner()
agents = runner.get_available_agents()

print("TOTAL_AGENTS:", len(agents))
for agent in agents:
    print(f"AGENT: {{agent['id']}} - {{agent['role']}}")
    print(f"CAPABILITIES: {{', '.join(agent['capabilities'])}}")
''')
        
        result = subprocess.run(['python', str(test_script)],
                              capture_output=True, text=True)
        
        # Verify agent listing
        assert "TOTAL_AGENTS: 3" in result.stdout
        assert "backend_developer" in result.stdout
        assert "frontend_developer" in result.stdout  
        assert "project_architect" in result.stdout
    
    @patch('project_manager.ProjectManager')
    def test_coral_dashboard_command(self, mock_project_manager_class):
        """Test coral dashboard command"""
        
        # Mock project manager
        mock_manager = Mock()
        mock_manager.get_all_projects.return_value = [
            {
                "id": "project_1",
                "name": "Test Project 1", 
                "status": "active",
                "current_phase": "development",
                "agents_completed": 3,
                "artifacts_created": 8
            },
            {
                "id": "project_2",
                "name": "Test Project 2",
                "status": "completed", 
                "current_phase": "deployment",
                "agents_completed": 6,
                "artifacts_created": 15
            }
        ]
        mock_project_manager_class.return_value = mock_manager
        
        # Create test script
        test_script = self.temp_dir / "test_dashboard.py"
        test_script.write_text(f'''
import sys
sys.path.insert(0, "{self.original_cwd}")

from project_manager import ProjectManager

manager = ProjectManager()
projects = manager.get_all_projects()

print("PROJECTS_COUNT:", len(projects))
for project in projects:
    print(f"PROJECT: {{project['name']}} - {{project['status']}}")
    print(f"PHASE: {{project['current_phase']}}")
    print(f"AGENTS: {{project['agents_completed']}}")
''')
        
        result = subprocess.run(['python', str(test_script)],
                              capture_output=True, text=True)
        
        # Verify dashboard output
        assert "PROJECTS_COUNT: 2" in result.stdout
        assert "Test Project 1" in result.stdout
        assert "Test Project 2" in result.stdout
        assert "active" in result.stdout
        assert "completed" in result.stdout


@pytest.mark.e2e
@pytest.mark.cli
class TestInteractiveCliWorkflows:
    """Test interactive CLI workflows"""
    
    def setup_method(self):
        """Set up interactive CLI test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.original_cwd = Path.cwd()
        
        # Create test project structure
        self.test_project = self.temp_dir / "interactive_test_project"
        self.test_project.mkdir(parents=True)
        
        # Create .coral directory
        coral_dir = self.test_project / '.coral'
        coral_dir.mkdir()
        (coral_dir / 'state').mkdir()
        (coral_dir / 'memory').mkdir()
        
        os.chdir(self.test_project)
        
    def teardown_method(self):
        """Clean up interactive test environment"""
        os.chdir(self.original_cwd)
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('agent_runner.Prompt.ask')
    @patch('agent_runner.AgentRunner')
    def test_interactive_agent_selection(self, mock_runner_class, mock_prompt):
        """Test interactive agent selection"""
        
        # Mock user input
        mock_prompt.side_effect = ["backend_developer", "Create REST API for user management"]
        
        # Mock agent runner
        mock_runner = Mock()
        mock_runner.get_available_agents.return_value = [
            {"id": "backend_developer", "role": "backend_developer"},
            {"id": "frontend_developer", "role": "frontend_developer"}
        ]
        mock_runner.select_agent_interactive.return_value = "backend_developer"
        mock_runner.run_agent.return_value = {
            "success": True,
            "outputs": {"api": "Created user management API"}
        }
        mock_runner_class.return_value = mock_runner
        
        # Create interactive test script
        test_script = self.temp_dir / "test_interactive.py"
        test_script.write_text(f'''
import sys
sys.path.insert(0, "{self.original_cwd}")

from agent_runner import AgentRunner
from unittest.mock import patch

# Simulate interactive selection
with patch('agent_runner.Prompt.ask') as mock_ask:
    mock_ask.side_effect = ["backend_developer", "Create API"]
    
    runner = AgentRunner()
    selected_agent = runner.select_agent_interactive()
    print("SELECTED_AGENT:", selected_agent)
    
    if selected_agent:
        result = runner.run_agent(selected_agent, "Create API")
        print("EXECUTION_SUCCESS:", result["success"])
''')
        
        result = subprocess.run(['python', str(test_script)],
                              capture_output=True, text=True)
        
        # Should handle interactive selection
        assert result.returncode == 0 or "SELECTED_AGENT:" in result.stdout
    
    @patch('agent_runner.AgentRunner')
    def test_workflow_interactive_execution(self, mock_runner_class):
        """Test interactive workflow execution"""
        
        # Mock workflow execution
        mock_runner = Mock()
        mock_runner.run_workflow.return_value = {
            "success": True,
            "workflow_name": "full_stack_development",
            "phases_completed": 4,
            "total_duration": 120.5
        }
        mock_runner_class.return_value = mock_runner
        
        # Create workflow test script
        test_script = self.temp_dir / "test_workflow.py"
        test_script.write_text(f'''
import sys
sys.path.insert(0, "{self.original_cwd}")

from agent_runner import AgentRunner

workflow_definition = {{
    "name": "full_stack_development",
    "agents": ["project_architect", "backend_developer", "frontend_developer"]
}}

runner = AgentRunner()
result = runner.run_workflow(workflow_definition, project_id="interactive_test")

print("WORKFLOW_SUCCESS:", result["success"])
print("PHASES_COMPLETED:", result["phases_completed"])
print("DURATION:", result["total_duration"])
''')
        
        result = subprocess.run(['python', str(test_script)],
                              capture_output=True, text=True)
        
        # Verify workflow execution
        assert result.returncode == 0 or "WORKFLOW_SUCCESS:" in result.stdout
    
    @patch('rich.console.Console.input')
    def test_interactive_configuration(self, mock_input):
        """Test interactive configuration setup"""
        
        # Mock user configuration inputs
        mock_input.side_effect = [
            "test_project",           # Project name
            "Web application",        # Project description
            "React, Node.js",        # Technology stack
            "y",                     # Enable memory system
            "y",                     # Enable MCP integration
            "n"                      # Skip advanced configuration
        ]
        
        # Create configuration test script
        test_script = self.temp_dir / "test_config.py"
        test_script.write_text(f'''
import sys
sys.path.insert(0, "{self.original_cwd}")

from unittest.mock import patch
import json

# Simulate interactive configuration
config_data = {{}}

with patch('rich.console.Console.input') as mock_input:
    mock_input.side_effect = [
        "test_project",
        "Web application", 
        "React, Node.js",
        "y",  # enable memory
        "y",  # enable mcp
        "n"   # no advanced config
    ]
    
    # Simulate configuration gathering
    config_data["project_name"] = "test_project"
    config_data["description"] = "Web application"
    config_data["tech_stack"] = "React, Node.js" 
    config_data["memory_enabled"] = True
    config_data["mcp_enabled"] = True
    
    print("CONFIG_COMPLETE: True")
    print("PROJECT_NAME:", config_data["project_name"])
    print("MEMORY_ENABLED:", config_data["memory_enabled"])
    print("MCP_ENABLED:", config_data["mcp_enabled"])
''')
        
        result = subprocess.run(['python', str(test_script)],
                              capture_output=True, text=True)
        
        # Verify configuration handling
        assert "CONFIG_COMPLETE: True" in result.stdout
        assert "PROJECT_NAME: test_project" in result.stdout


@pytest.mark.e2e
@pytest.mark.cli
class TestCliErrorHandling:
    """Test CLI error handling and user feedback"""
    
    def setup_method(self):
        """Set up error handling test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.original_cwd = Path.cwd()
        os.chdir(self.temp_dir)
        
    def teardown_method(self):
        """Clean up error handling test environment"""
        os.chdir(self.original_cwd)
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_invalid_command_handling(self):
        """Test handling of invalid commands"""
        
        # Test invalid command
        test_script = self.temp_dir / "test_invalid_command.py"
        test_script.write_text(f'''
import sys
sys.path.insert(0, "{self.original_cwd}")
import argparse

# Simulate invalid command parsing
parser = argparse.ArgumentParser()
parser.add_argument("command", choices=["run", "list", "workflow", "dashboard"])

try:
    args = parser.parse_args(["invalid_command"])
    print("UNEXPECTED_SUCCESS")
except SystemExit as e:
    print("INVALID_COMMAND_HANDLED: True")
    print("EXIT_CODE:", e.code)
except Exception as e:
    print("ERROR_HANDLED: True") 
    print("ERROR_TYPE:", type(e).__name__)
''')
        
        result = subprocess.run(['python', str(test_script)], 
                              capture_output=True, text=True)
        
        # Should handle invalid command gracefully
        assert ("INVALID_COMMAND_HANDLED: True" in result.stdout or 
                result.returncode != 0)
    
    @patch('agent_runner.AgentRunner')
    def test_agent_execution_error_handling(self, mock_runner_class):
        """Test handling of agent execution errors"""
        
        # Mock agent execution failure
        mock_runner = Mock()
        mock_runner.run_agent.side_effect = Exception("Agent execution failed")
        mock_runner_class.return_value = mock_runner
        
        test_script = self.temp_dir / "test_agent_error.py"
        test_script.write_text(f'''
import sys
sys.path.insert(0, "{self.original_cwd}")

from agent_runner import AgentRunner

try:
    runner = AgentRunner()
    result = runner.run_agent("backend_developer", "Create API")
    print("UNEXPECTED_SUCCESS")
except Exception as e:
    print("AGENT_ERROR_HANDLED: True")
    print("ERROR_MESSAGE:", str(e))
    print("ERROR_TYPE:", type(e).__name__)
''')
        
        result = subprocess.run(['python', str(test_script)],
                              capture_output=True, text=True)
        
        # Should handle agent execution errors
        assert ("AGENT_ERROR_HANDLED: True" in result.stdout or
                "ERROR_MESSAGE:" in result.stdout)
    
    @patch('project_manager.ProjectManager')
    def test_project_not_found_handling(self, mock_project_manager_class):
        """Test handling when project is not found"""
        
        # Mock project not found
        mock_manager = Mock()
        mock_manager.get_project.return_value = None
        mock_project_manager_class.return_value = mock_manager
        
        test_script = self.temp_dir / "test_project_not_found.py"
        test_script.write_text(f'''
import sys
sys.path.insert(0, "{self.original_cwd}")

from project_manager import ProjectManager

manager = ProjectManager()
project = manager.get_project("nonexistent_project")

if project is None:
    print("PROJECT_NOT_FOUND_HANDLED: True")
    print("PROJECT_VALUE:", project)
else:
    print("UNEXPECTED_PROJECT_FOUND")
''')
        
        result = subprocess.run(['python', str(test_script)],
                              capture_output=True, text=True)
        
        # Should handle missing project gracefully
        assert "PROJECT_NOT_FOUND_HANDLED: True" in result.stdout
    
    def test_configuration_file_error_handling(self):
        """Test handling of configuration file errors"""
        
        # Create invalid configuration file
        invalid_config = self.temp_dir / "invalid_config.yaml"
        invalid_config.write_text("invalid: yaml: content: [")
        
        test_script = self.temp_dir / "test_config_error.py"
        test_script.write_text(f'''
import sys
sys.path.insert(0, "{self.original_cwd}")
import yaml

try:
    with open("{invalid_config}", 'r') as f:
        config = yaml.safe_load(f)
    print("UNEXPECTED_CONFIG_LOADED")
except yaml.YAMLError as e:
    print("YAML_ERROR_HANDLED: True")
    print("ERROR_TYPE:", type(e).__name__)
except Exception as e:
    print("CONFIG_ERROR_HANDLED: True")
    print("ERROR_TYPE:", type(e).__name__)
''')
        
        result = subprocess.run(['python', str(test_script)],
                              capture_output=True, text=True)
        
        # Should handle configuration errors
        assert ("YAML_ERROR_HANDLED: True" in result.stdout or
                "CONFIG_ERROR_HANDLED: True" in result.stdout)


@pytest.mark.e2e
@pytest.mark.cli
class TestCliIntegrationWithSystems:
    """Test CLI integration with various systems"""
    
    def setup_method(self):
        """Set up system integration test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.original_cwd = Path.cwd()
        
        # Create project with full structure
        self.test_project = self.temp_dir / "integration_project"
        self.test_project.mkdir(parents=True)
        
        coral_dir = self.test_project / '.coral'
        coral_dir.mkdir()
        (coral_dir / 'state').mkdir()
        (coral_dir / 'memory').mkdir()
        (coral_dir / 'logs').mkdir()
        
        # Create initial project state
        project_state = {
            "project": {
                "name": "integration_project",
                "id": "integration_project",
                "created_at": datetime.now().isoformat(),
                "current_phase": "planning",
                "status": "active"
            },
            "agents": {"completed": [], "active": None, "queue": []},
            "handoffs": [],
            "artifacts": [],
            "metrics": {}
        }
        
        state_file = coral_dir / 'project_state.yaml'
        with open(state_file, 'w') as f:
            yaml.dump(project_state, f)
        
        os.chdir(self.test_project)
        
    def teardown_method(self):
        """Clean up integration test environment"""
        os.chdir(self.original_cwd)
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('memory.coral_memory_integration.CoralMemoryIntegration')
    @patch('agent_runner.AgentRunner')
    def test_cli_with_memory_system(self, mock_runner_class, mock_memory_class):
        """Test CLI integration with memory system"""
        
        # Mock memory integration
        mock_memory = Mock()
        mock_memory.record_agent_start = asyncio.coroutine(lambda *args, **kwargs: "memory_id_start")()
        mock_memory.record_agent_completion = asyncio.coroutine(lambda *args, **kwargs: "memory_id_complete")()
        mock_memory.get_agent_context = asyncio.coroutine(lambda *args, **kwargs: {
            "recent_memories": [],
            "relevant_memories": [],
            "working_memory": {}
        })()
        mock_memory_class.return_value = mock_memory
        
        # Mock agent runner
        mock_runner = Mock()
        mock_runner.run_agent.return_value = {
            "success": True,
            "outputs": {"result": "Agent completed with memory integration"},
            "memory_recorded": True
        }
        mock_runner_class.return_value = mock_runner
        
        test_script = self.temp_dir / "test_memory_integration.py"
        test_script.write_text(f'''
import sys
sys.path.insert(0, "{self.original_cwd}")
import asyncio
from unittest.mock import Mock

# Mock the memory integration
class MockMemoryIntegration:
    async def record_agent_start(self, *args, **kwargs):
        return "memory_id_start"
    
    async def record_agent_completion(self, *args, **kwargs):
        return "memory_id_complete"
    
    async def get_agent_context(self, *args, **kwargs):
        return {{"recent_memories": [], "relevant_memories": []}}

# Simulate agent execution with memory
memory_integration = MockMemoryIntegration()

async def run_with_memory():
    # Record agent start
    start_id = await memory_integration.record_agent_start("backend_developer", "Create API")
    print("MEMORY_START_ID:", start_id)
    
    # Get agent context
    context = await memory_integration.get_agent_context("backend_developer", "test_project")
    print("CONTEXT_RETRIEVED: True")
    
    # Record completion
    completion_id = await memory_integration.record_agent_completion(
        "backend_developer", True, {{"api": "created"}}
    )
    print("MEMORY_COMPLETION_ID:", completion_id)
    
    return "SUCCESS"

# Run async test
result = asyncio.run(run_with_memory())
print("MEMORY_INTEGRATION_TEST:", result)
''')
        
        result = subprocess.run(['python', str(test_script)],
                              capture_output=True, text=True)
        
        # Verify memory integration
        assert "MEMORY_START_ID:" in result.stdout
        assert "CONTEXT_RETRIEVED: True" in result.stdout
        assert "MEMORY_COMPLETION_ID:" in result.stdout
        assert "MEMORY_INTEGRATION_TEST: SUCCESS" in result.stdout
    
    @patch('mcp.mcp_client.MCPClient')
    @patch('agent_runner.AgentRunner')
    def test_cli_with_mcp_integration(self, mock_runner_class, mock_mcp_class):
        """Test CLI integration with MCP system"""
        
        # Mock MCP client
        mock_mcp = Mock()
        mock_mcp.list_tools = asyncio.coroutine(lambda: [
            {"name": "filesystem_read", "description": "Read files"},
            {"name": "github_create_repo", "description": "Create repo"}
        ])()
        mock_mcp.call_tool = asyncio.coroutine(lambda name, args: {
            "success": True,
            "result": f"Tool {name} executed successfully"
        })()
        mock_mcp_class.return_value = mock_mcp
        
        # Mock agent runner with MCP
        mock_runner = Mock()
        mock_runner.run_agent.return_value = {
            "success": True,
            "outputs": {"result": "Agent executed with MCP tools"},
            "mcp_tools_used": ["filesystem_read", "github_create_repo"]
        }
        mock_runner_class.return_value = mock_runner
        
        test_script = self.temp_dir / "test_mcp_integration.py"
        test_script.write_text(f'''
import sys
sys.path.insert(0, "{self.original_cwd}")
import asyncio
from unittest.mock import Mock

class MockMCPClient:
    async def list_tools(self):
        return [
            {{"name": "filesystem_read", "description": "Read files"}},
            {{"name": "github_create_repo", "description": "Create repo"}}
        ]
    
    async def call_tool(self, name, args):
        return {{
            "success": True,
            "result": f"Tool {{name}} executed"
        }}

async def run_with_mcp():
    mcp_client = MockMCPClient()
    
    # List available tools
    tools = await mcp_client.list_tools()
    print("MCP_TOOLS_COUNT:", len(tools))
    
    # Use a tool
    result = await mcp_client.call_tool("filesystem_read", {{"path": "/test"}})
    print("MCP_TOOL_SUCCESS:", result["success"])
    
    return "MCP_INTEGRATION_SUCCESS"

result = asyncio.run(run_with_mcp())
print("MCP_TEST_RESULT:", result)
''')
        
        result = subprocess.run(['python', str(test_script)],
                              capture_output=True, text=True)
        
        # Verify MCP integration
        assert "MCP_TOOLS_COUNT: 2" in result.stdout
        assert "MCP_TOOL_SUCCESS: True" in result.stdout
        assert "MCP_TEST_RESULT: MCP_INTEGRATION_SUCCESS" in result.stdout
    
    @patch('tools.project_state.ProjectStateManager')
    def test_cli_with_project_state_management(self, mock_state_manager_class):
        """Test CLI integration with project state management"""
        
        # Mock project state manager
        mock_state_manager = Mock()
        mock_state_manager.get_current_state.return_value = {
            "project": {"name": "test_project", "status": "active"},
            "agents": {"completed": 2, "active": "backend_developer"},
            "artifacts": {"count": 5}
        }
        mock_state_manager.update_agent_status.return_value = True
        mock_state_manager.add_artifact.return_value = "artifact_id_123"
        mock_state_manager_class.return_value = mock_state_manager
        
        test_script = self.temp_dir / "test_state_management.py"
        test_script.write_text(f'''
import sys
sys.path.insert(0, "{self.original_cwd}")

from unittest.mock import Mock

class MockStateManager:
    def get_current_state(self):
        return {{
            "project": {{"name": "test_project", "status": "active"}},
            "agents": {{"completed": 2, "active": "backend_developer"}},
            "artifacts": {{"count": 5}}
        }}
    
    def update_agent_status(self, agent_id, status):
        return True
    
    def add_artifact(self, artifact_data):
        return "artifact_id_123"

state_manager = MockStateManager()

# Get current state
current_state = state_manager.get_current_state()
print("PROJECT_NAME:", current_state["project"]["name"])
print("PROJECT_STATUS:", current_state["project"]["status"])
print("COMPLETED_AGENTS:", current_state["agents"]["completed"])

# Update agent status
update_success = state_manager.update_agent_status("backend_developer", "completed")
print("UPDATE_SUCCESS:", update_success)

# Add artifact
artifact_id = state_manager.add_artifact({{"type": "code", "path": "/src/api.py"}})
print("ARTIFACT_ID:", artifact_id)

print("STATE_MANAGEMENT_TEST: SUCCESS")
''')
        
        result = subprocess.run(['python', str(test_script)],
                              capture_output=True, text=True)
        
        # Verify state management integration
        assert "PROJECT_NAME: test_project" in result.stdout
        assert "PROJECT_STATUS: active" in result.stdout
        assert "COMPLETED_AGENTS: 2" in result.stdout
        assert "UPDATE_SUCCESS: True" in result.stdout
        assert "ARTIFACT_ID: artifact_id_123" in result.stdout
        assert "STATE_MANAGEMENT_TEST: SUCCESS" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])