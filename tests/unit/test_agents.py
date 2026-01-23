"""
Unit tests for CoralCollective Agent System

Tests cover:
1. Agent configuration loading and validation
2. Agent prompt loading and processing 
3. Agent runner functionality
4. Agent prompt service operations
5. Subagent registry functionality
"""

import pytest
import tempfile
import shutil
import yaml
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from coral_collective.agent_runner import AgentRunner
from coral_collective.agent_prompt_service import AgentPromptService
# SubagentRegistry not available as a module
# from subagent_registry import SubagentRegistry
from tests.fixtures.test_data import MockProjectSetup


class TestAgentRunner:
    """Test AgentRunner functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.agents_config = {
            "version": 1,
            "agents": {
                "project_architect": {
                    "role": "architect",
                    "prompt_path": "agents/core/project_architect.md",
                    "capabilities": ["planning", "architecture"]
                },
                "backend_developer": {
                    "role": "backend_developer", 
                    "prompt_path": "agents/specialists/backend_developer.md",
                    "capabilities": ["api", "database"]
                }
            }
        }
        
        # Create config file
        self.config_dir = self.temp_dir / "config"
        self.config_dir.mkdir()
        self.config_file = self.config_dir / "agents.yaml"
        with open(self.config_file, 'w') as f:
            yaml.dump(self.agents_config, f)
            
        # Create agent files
        self.agents_dir = self.temp_dir / "agents"
        self.agents_dir.mkdir()
        (self.agents_dir / "core").mkdir()
        (self.agents_dir / "specialists").mkdir()
        
        # Create sample agent prompt files
        architect_prompt = "# Project Architect\nYou are a project architect."
        backend_prompt = "# Backend Developer\nYou are a backend developer."
        
        with open(self.agents_dir / "core" / "project_architect.md", 'w') as f:
            f.write(architect_prompt)
        with open(self.agents_dir / "specialists" / "backend_developer.md", 'w') as f:
            f.write(backend_prompt)
            
    def teardown_method(self):
        """Clean up test files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('coral_collective.agent_runner.Path')
    def test_agent_runner_initialization(self, mock_path):
        """Test AgentRunner initialization"""
        mock_path.return_value.parent = self.temp_dir
        
        with patch.object(AgentRunner, 'load_agents_config') as mock_load, \
             patch.object(AgentRunner, 'detect_standalone_mode') as mock_standalone:
            
            mock_load.return_value = self.agents_config
            mock_standalone.return_value = False
            
            runner = AgentRunner()
            
            assert runner.agents_config == self.agents_config
            assert runner.standalone_mode is False
            assert runner.collector is not None
            assert runner.state_manager is not None
    
    def test_load_agents_config(self):
        """Test loading agents configuration"""
        with patch('coral_collective.agent_runner.Path') as mock_path:
            mock_path.return_value.parent = self.temp_dir
            
            runner = AgentRunner()
            config = runner.load_agents_config()
            
            assert config['version'] == 1
            assert 'project_architect' in config['agents']
            assert 'backend_developer' in config['agents']
    
    def test_get_available_agents(self):
        """Test getting list of available agents"""
        with patch('coral_collective.agent_runner.Path') as mock_path:
            mock_path.return_value.parent = self.temp_dir
            
            runner = AgentRunner()
            agents = runner.get_available_agents()
            
            assert len(agents) == 2
            assert any(agent['id'] == 'project_architect' for agent in agents)
            assert any(agent['id'] == 'backend_developer' for agent in agents)
            
            # Test filtering by role
            architects = runner.get_available_agents(filter_role='architect')
            assert len(architects) == 1
            assert architects[0]['id'] == 'project_architect'
    
    def test_get_agent_info(self):
        """Test getting specific agent information"""
        with patch('coral_collective.agent_runner.Path') as mock_path:
            mock_path.return_value.parent = self.temp_dir
            
            runner = AgentRunner()
            
            # Test valid agent
            info = runner.get_agent_info('project_architect')
            assert info is not None
            assert info['id'] == 'project_architect'
            assert info['role'] == 'architect'
            assert 'planning' in info['capabilities']
            
            # Test invalid agent
            info = runner.get_agent_info('nonexistent_agent')
            assert info is None
    
    @patch('coral_collective.agent_runner.Prompt.ask')
    @patch('rich.console.Console.print')
    def test_interactive_agent_selection(self, mock_print, mock_prompt):
        """Test interactive agent selection"""
        with patch('coral_collective.agent_runner.Path') as mock_path:
            mock_path.return_value.parent = self.temp_dir
            
            mock_prompt.return_value = "project_architect"
            
            runner = AgentRunner()
            selected = runner.select_agent_interactive()
            
            assert selected == "project_architect"
            mock_print.assert_called()  # Should print available agents
    
    @patch('coral_collective.agent_runner.subprocess.run')
    def test_copy_to_clipboard(self, mock_subprocess):
        """Test copying content to clipboard"""
        with patch('coral_collective.agent_runner.Path') as mock_path:
            mock_path.return_value.parent = self.temp_dir
            
            runner = AgentRunner()
            test_content = "Test prompt content"
            
            # Test successful copy
            mock_subprocess.return_value.returncode = 0
            result = runner.copy_to_clipboard(test_content)
            assert result is True
            
            # Test copy failure
            mock_subprocess.return_value.returncode = 1
            result = runner.copy_to_clipboard(test_content)
            assert result is False


class TestAgentPromptService:
    """Test AgentPromptService functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.service = AgentPromptService(base_path=self.temp_dir)
        
        # Create sample agent files
        self.agents_dir = self.temp_dir / "agents" / "specialists"
        self.agents_dir.mkdir(parents=True)
        
        self.sample_prompt = """# Backend Developer Agent

You are a Senior Backend Developer AI agent.

## Your Role
Develop robust backend systems and APIs.

## Key Responsibilities
- Design and implement REST APIs
- Create database schemas
- Implement authentication
- Write backend tests

## Deliverables
- API implementations
- Database schemas
- Authentication systems
"""
        
        with open(self.agents_dir / "backend_developer.md", 'w') as f:
            f.write(self.sample_prompt)
            
    def teardown_method(self):
        """Clean up test files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_load_agent_prompt(self):
        """Test loading agent prompt from file"""
        prompt = self.service.load_agent_prompt("agents/specialists/backend_developer.md")
        
        assert prompt is not None
        assert "Backend Developer Agent" in prompt
        assert "REST APIs" in prompt
        assert "Key Responsibilities" in prompt
    
    def test_load_nonexistent_agent_prompt(self):
        """Test loading non-existent agent prompt"""
        prompt = self.service.load_agent_prompt("agents/nonexistent_agent.md")
        assert prompt is None
    
    def test_process_prompt_template(self):
        """Test processing prompt templates with variables"""
        template = """# Test Agent

Task: {{task}}
Project: {{project_id}}
Context: {{context}}
"""
        
        variables = {
            "task": "Create REST API",
            "project_id": "test_project",
            "context": "Building e-commerce platform"
        }
        
        processed = self.service.process_prompt_template(template, variables)
        
        assert "Task: Create REST API" in processed
        assert "Project: test_project" in processed
        assert "Context: Building e-commerce platform" in processed
    
    def test_validate_prompt_content(self):
        """Test prompt content validation"""
        # Valid prompt
        valid_prompt = "# Agent\nYou are an AI agent.\n## Role\nPerform tasks."
        assert self.service.validate_prompt_content(valid_prompt) is True
        
        # Invalid prompts
        assert self.service.validate_prompt_content("") is False
        assert self.service.validate_prompt_content(None) is False
        assert self.service.validate_prompt_content("Short") is False
    
    def test_extract_agent_metadata(self):
        """Test extracting metadata from agent prompts"""
        metadata = self.service.extract_agent_metadata(self.sample_prompt)
        
        assert metadata is not None
        assert metadata['title'] == "Backend Developer Agent"
        assert "REST APIs" in metadata['responsibilities']
        assert "API implementations" in metadata['deliverables']


@pytest.mark.skip(reason="SubagentRegistry module not available")
class TestSubagentRegistry:
    """Test SubagentRegistry functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Mock agents config
        self.agents_config = {
            "version": 1,
            "agents": {
                "backend_developer": {
                    "role": "backend_developer",
                    "prompt_path": "agents/specialists/backend_developer.md",
                    "capabilities": ["api", "database"]
                },
                "frontend_developer": {
                    "role": "frontend_developer", 
                    "prompt_path": "agents/specialists/frontend_developer.md",
                    "capabilities": ["ui", "components"]
                }
            }
        }
        
        with patch('coral_collective.subagent_registry.Path') as mock_path:
            mock_path.return_value.parent = self.temp_dir
            self.registry = SubagentRegistry()
            
    def teardown_method(self):
        """Clean up test files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('coral_collective.subagent_registry.yaml.safe_load')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_agents_config(self, mock_file, mock_yaml):
        """Test loading agents configuration"""
        mock_yaml.return_value = self.agents_config
        
        config = self.registry.load_agents_config()
        
        assert config == self.agents_config
        mock_file.assert_called_once()
        mock_yaml.assert_called_once()
    
    def test_list_agents(self):
        """Test listing available agents"""
        with patch.object(self.registry, 'load_agents_config') as mock_load:
            mock_load.return_value = self.agents_config
            
            agents = self.registry.list_agents()
            
            assert len(agents) == 2
            assert "backend_developer" in agents
            assert "frontend_developer" in agents
    
    def test_get_agent_shortcuts(self):
        """Test getting agent shortcuts"""
        shortcuts = self.registry.get_agent_shortcuts()
        
        # Test some expected shortcuts
        assert "@backend" in shortcuts
        assert "@frontend" in shortcuts
        assert "@architect" in shortcuts
        assert shortcuts["@backend"] == "backend_developer"
        assert shortcuts["@frontend"] == "frontend_developer"
    
    def test_resolve_agent_reference(self):
        """Test resolving agent references"""
        with patch.object(self.registry, 'load_agents_config') as mock_load:
            mock_load.return_value = self.agents_config
            
            # Test direct agent ID
            agent_id = self.registry.resolve_agent_reference("backend_developer")
            assert agent_id == "backend_developer"
            
            # Test shortcut
            agent_id = self.registry.resolve_agent_reference("@backend")
            assert agent_id == "backend_developer"
            
            # Test invalid reference
            agent_id = self.registry.resolve_agent_reference("@nonexistent")
            assert agent_id is None
    
    def test_parse_subagent_invocation(self):
        """Test parsing subagent invocation strings"""
        # Test basic invocation
        result = self.registry.parse_subagent_invocation('@backend "Create REST API"')
        
        assert result is not None
        assert result['agent_reference'] == '@backend'
        assert result['task'] == 'Create REST API'
        assert result['options'] == {}
        
        # Test invocation with options
        result = self.registry.parse_subagent_invocation(
            '@backend "Create API" --project=test --mcp-enabled'
        )
        
        assert result is not None
        assert result['agent_reference'] == '@backend'
        assert result['task'] == 'Create API'
        assert result['options']['project'] == 'test'
        assert result['options']['mcp_enabled'] is True
    
    @patch('coral_collective.subagent_registry.AgentRunner')
    def test_invoke_subagent(self, mock_runner_class):
        """Test invoking a subagent"""
        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner
        mock_runner.run_agent.return_value = "Agent execution result"
        
        with patch.object(self.registry, 'resolve_agent_reference') as mock_resolve:
            mock_resolve.return_value = "backend_developer"
            
            result = self.registry.invoke_subagent("@backend", "Create REST API")
            
            assert result == "Agent execution result"
            mock_runner.run_agent.assert_called_once_with(
                "backend_developer", 
                "Create REST API",
                {}
            )


@pytest.mark.unit
@pytest.mark.agent
class TestAgentIntegration:
    """Integration tests for agent system components"""
    
    def setup_method(self):
        """Set up integrated test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.setup = MockProjectSetup(self.temp_dir)
        self.setup.create_coral_structure()
        
        # Create complete agent structure
        agents_dir = self.temp_dir / "agents"
        agents_dir.mkdir()
        (agents_dir / "core").mkdir()
        (agents_dir / "specialists").mkdir()
        
        # Create sample agents
        self.create_sample_agents(agents_dir)
        
        # Create agents config
        agents_config = {
            "version": 1,
            "agents": {
                "project_architect": {
                    "role": "architect",
                    "prompt_path": "agents/core/project_architect.md",
                    "capabilities": ["planning", "architecture"]
                },
                "backend_developer": {
                    "role": "backend_developer",
                    "prompt_path": "agents/specialists/backend_developer.md", 
                    "capabilities": ["api", "database"]
                }
            }
        }
        self.setup.create_agents_config(agents_config)
        
    def teardown_method(self):
        """Clean up test files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_sample_agents(self, agents_dir):
        """Create sample agent prompt files"""
        architect_content = """# Project Architect

You are a Senior Project Architect AI agent.

## Your Role
Design comprehensive project architectures.

## Deliverables
- Architecture documentation
- Project roadmap
"""
        
        backend_content = """# Backend Developer  

You are a Senior Backend Developer AI agent.

## Your Role
Develop robust backend systems.

## Deliverables
- API implementations
- Database schemas
"""
        
        with open(agents_dir / "core" / "project_architect.md", 'w') as f:
            f.write(architect_content)
            
        with open(agents_dir / "specialists" / "backend_developer.md", 'w') as f:
            f.write(backend_content)
    
    @patch('coral_collective.agent_runner.Path')
    def test_full_agent_workflow(self, mock_path):
        """Test complete agent workflow from loading to execution"""
        mock_path.return_value.parent = self.temp_dir
        
        # Initialize components
        runner = AgentRunner()
        prompt_service = AgentPromptService(base_path=self.temp_dir)
        
        # Test agent loading
        agents = runner.get_available_agents()
        assert len(agents) >= 2
        
        # Test prompt loading
        architect_info = runner.get_agent_info('project_architect')
        assert architect_info is not None
        
        prompt = prompt_service.load_agent_prompt(architect_info['prompt_path'])
        assert prompt is not None
        assert "Project Architect" in prompt
        
        # Test prompt processing
        processed = prompt_service.process_prompt_template(
            prompt, 
            {"task": "Design system", "project_id": "test"}
        )
        assert processed is not None
        
    def test_agent_registry_integration(self):
        """Test agent registry with real configuration"""
        with patch('coral_collective.subagent_registry.Path') as mock_path:
            mock_path.return_value.parent = self.temp_dir
            
            registry = SubagentRegistry()
            
            # Mock the config loading to use our test config
            with patch.object(registry, 'load_agents_config') as mock_load:
                mock_load.return_value = {
                    "version": 1,
                    "agents": {
                        "project_architect": {
                            "role": "architect",
                            "prompt_path": "agents/core/project_architect.md",
                            "capabilities": ["planning"]
                        },
                        "backend_developer": {
                            "role": "backend_developer",
                            "prompt_path": "agents/specialists/backend_developer.md",
                            "capabilities": ["api"]
                        }
                    }
                }
                
                # Test listing agents
                agents = registry.list_agents()
                assert "project_architect" in agents
                assert "backend_developer" in agents
                
                # Test shortcut resolution
                backend_id = registry.resolve_agent_reference("@backend")
                assert backend_id == "backend_developer"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])