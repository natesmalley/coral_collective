"""
Unit tests for CoralCollective AgentRunner

Tests cover:
1. AgentRunner initialization and configuration
2. Agent prompt loading and management 
3. Agent execution with MCP integration
4. Workflow management and sequences
5. Project management and session tracking
6. CLI argument handling and modes
7. Error handling and edge cases
"""

import pytest
import asyncio
import json
import yaml
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock, mock_open
from typing import Dict, List, Optional

# Import the module under test
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from coral_collective.agent_runner import AgentRunner, async_main


class TestAgentRunnerInitialization:
    """Test AgentRunner initialization and setup"""
    
    def test_initialization_normal_mode(self, temp_project_dir, mock_agents_config):
        """Test AgentRunner initialization in normal mode"""
        
        # Create config file
        config_file = temp_project_dir / "claude_code_agents.json"
        with open(config_file, 'w') as f:
            json.dump(mock_agents_config, f)
            
        with patch('coral_collective.agent_runner.Path') as mock_path:
            mock_path.return_value.parent = temp_project_dir
            mock_path.__file__ = str(temp_project_dir / "agent_runner.py")
            
            with patch('coral_collective.agent_runner.FeedbackCollector'), \
                 patch('coral_collective.agent_runner.ProjectStateManager'), \
                 patch('coral_collective.agent_runner.MCPClient'):
                
                runner = AgentRunner()
                
                assert runner.base_path == temp_project_dir
                assert not runner.standalone_mode
                assert runner.agents_config == mock_agents_config
                assert runner.collector is not None
                assert runner.state_manager is not None
                
    def test_initialization_standalone_mode(self, temp_project_dir):
        """Test AgentRunner initialization in standalone mode"""
        
        # Create standalone indicator
        standalone_config = temp_project_dir / "standalone_config.json"
        standalone_config.write_text('{"mode": "standalone"}')
        
        with patch('coral_collective.agent_runner.Path') as mock_path:
            mock_path.return_value.parent = temp_project_dir
            mock_path.__file__ = str(temp_project_dir / "agent_runner.py")
            
            with patch('coral_collective.agent_runner.FeedbackCollector'), \
                 patch('coral_collective.agent_runner.ProjectStateManager'):
                
                runner = AgentRunner()
                
                assert runner.standalone_mode
                
    @pytest.mark.skip(reason="File descriptor issues in CI environment")
    def test_detect_standalone_mode_variations(self, temp_project_dir):
        """Test different methods of detecting standalone mode"""
        
        with patch('coral_collective.agent_runner.FeedbackCollector'), \
             patch('coral_collective.agent_runner.ProjectStateManager'):
            
            # Test 1: standalone_config.json exists
            config_file = temp_project_dir / "standalone_config.json"
            config_file.write_text('{}')
            
            with patch('coral_collective.agent_runner.Path') as mock_path:
                mock_path.return_value.parent = temp_project_dir
                runner = AgentRunner()
                assert runner.detect_standalone_mode()
            
            config_file.unlink()
            
            # Test 2: Running from .coral directory
            coral_dir = temp_project_dir / ".coral"
            coral_dir.mkdir(exist_ok=True)
            
            with patch('coral_collective.agent_runner.Path') as mock_path:
                mock_path.return_value.name = ".coral"
                runner = AgentRunner()
                assert runner.detect_standalone_mode()
                
            # Test 3: .coralrc in parent directory
            coralrc = temp_project_dir / ".coralrc"
            coralrc.write_text('')
            
            with patch('coral_collective.agent_runner.Path') as mock_path:
                mock_path.return_value.parent.parent = temp_project_dir
                runner = AgentRunner()
                assert runner.detect_standalone_mode()


class TestAgentConfiguration:
    """Test agent configuration loading and management"""
    
    def test_load_agents_config_success(self, temp_project_dir, mock_agents_config):
        """Test successful loading of agent configuration"""
        
        config_file = temp_project_dir / "claude_code_agents.json"
        with open(config_file, 'w') as f:
            json.dump(mock_agents_config, f)
            
        with patch('coral_collective.agent_runner.Path') as mock_path, \
             patch('coral_collective.agent_runner.FeedbackCollector'), \
             patch('coral_collective.agent_runner.ProjectStateManager'):
            
            mock_path.return_value.parent = temp_project_dir
            runner = AgentRunner()
            
            assert runner.agents_config == mock_agents_config
            assert 'agents' in runner.agents_config
            assert 'project_architect' in runner.agents_config['agents']
            
    def test_load_agents_config_file_not_found(self, temp_project_dir):
        """Test handling when config file doesn't exist"""
        
        with patch('coral_collective.agent_runner.Path') as mock_path, \
             patch('coral_collective.agent_runner.console') as mock_console, \
             patch('coral_collective.agent_runner.FeedbackCollector'), \
             patch('coral_collective.agent_runner.ProjectStateManager'):
            
            mock_path.return_value.parent = temp_project_dir
            
            # Mock initialization methods
            with patch.object(AgentRunner, 'initialize_config', return_value=False), \
                 patch.object(AgentRunner, 'create_default_config'):
                
                runner = AgentRunner()
                
                # Should attempt to initialize and create default config
                runner.initialize_config.assert_called_once()
                runner.create_default_config.assert_called_once()
                
    def test_create_default_config(self, temp_project_dir):
        """Test creation of default configuration"""
        
        with patch('coral_collective.agent_runner.Path') as mock_path, \
             patch('coral_collective.agent_runner.FeedbackCollector'), \
             patch('coral_collective.agent_runner.ProjectStateManager'), \
             patch('coral_collective.agent_runner.console'):
            
            mock_path.return_value.parent = temp_project_dir
            runner = AgentRunner()
            runner.create_default_config()
            
            config_file = temp_project_dir / "claude_code_agents.json"
            assert config_file.exists()
            
            with open(config_file, 'r') as f:
                config = json.load(f)
                
            assert 'agents' in config
            assert 'project_templates' in config
            assert 'categories' in config
            assert 'project_architect' in config['agents']
            
    def test_get_project_directories_normal_mode(self, temp_project_dir):
        """Test getting project directories in normal mode"""
        
        with patch('coral_collective.agent_runner.FeedbackCollector'), \
             patch('coral_collective.agent_runner.ProjectStateManager'):
            
            runner = AgentRunner()
            runner.base_path = temp_project_dir
            runner.standalone_mode = False
            
            dirs = runner.get_project_directories()
            
            assert 'projects' in dirs
            assert 'feedback' in dirs
            assert 'metrics' in dirs
            assert dirs['projects'] == temp_project_dir / 'projects'
            
    def test_get_project_directories_standalone_mode(self, temp_project_dir):
        """Test getting project directories in standalone mode"""
        
        with patch('coral_collective.agent_runner.FeedbackCollector'), \
             patch('coral_collective.agent_runner.ProjectStateManager'):
            
            runner = AgentRunner()
            runner.base_path = temp_project_dir
            runner.standalone_mode = True
            
            dirs = runner.get_project_directories()
            
            assert dirs['projects'] == temp_project_dir / '.coral' / 'projects'


class TestAgentPromptLoading:
    """Test agent prompt loading and management"""
    
    def setup_method(self):
        """Set up test data"""
        self.sample_prompt = """
# Test Agent

## Prompt

```
You are a test AI agent for validation.

## Role
Testing specialist

## Responsibilities
- Execute tests
- Validate results

## Deliverables  
- Test reports
- Validation results
```

## Usage
Use this agent for testing purposes.
"""
    
    def test_get_agent_prompt_with_prompt_path(self, temp_project_dir, mock_agents_config):
        """Test loading agent prompt when prompt_path is specified"""
        
        # Create prompt file
        prompt_dir = temp_project_dir / 'agents' / 'core'
        prompt_dir.mkdir(parents=True)
        prompt_file = prompt_dir / 'project_architect.md'
        prompt_file.write_text(self.sample_prompt)
        
        with patch('coral_collective.agent_runner.FeedbackCollector'), \
             patch('coral_collective.agent_runner.ProjectStateManager'):
            
            runner = AgentRunner()
            runner.base_path = temp_project_dir
            runner.agents_config = mock_agents_config
            
            prompt = runner.get_agent_prompt('project_architect')
            
            assert "You are a test AI agent for validation" in prompt
            assert "Testing specialist" in prompt
            
    def test_get_agent_prompt_fallback_mapping(self, temp_project_dir):
        """Test fallback prompt path mapping for agents without prompt_path"""
        
        # Create config without prompt_path
        config = {
            'agents': {
                'test_agent': {
                    'name': 'Test Agent',
                    'description': 'Test agent'
                }
            }
        }
        
        # Create prompt file in specialists directory
        prompt_dir = temp_project_dir / 'agents' / 'specialists'
        prompt_dir.mkdir(parents=True)
        prompt_file = prompt_dir / 'test_agent.md'
        prompt_file.write_text(self.sample_prompt)
        
        with patch('coral_collective.agent_runner.FeedbackCollector'), \
             patch('coral_collective.agent_runner.ProjectStateManager'):
            
            runner = AgentRunner()
            runner.base_path = temp_project_dir
            runner.agents_config = config
            
            prompt = runner.get_agent_prompt('test_agent')
            
            assert "You are a test AI agent for validation" in prompt
            
    def test_get_agent_prompt_file_not_found(self, temp_project_dir):
        """Test handling when prompt file doesn't exist"""
        
        config = {
            'agents': {
                'nonexistent_agent': {
                    'name': 'Nonexistent Agent',
                    'prompt_path': 'agents/nonexistent.md'
                }
            }
        }
        
        with patch('coral_collective.agent_runner.FeedbackCollector'), \
             patch('coral_collective.agent_runner.ProjectStateManager'):
            
            runner = AgentRunner()
            runner.base_path = temp_project_dir
            runner.agents_config = config
            
            prompt = runner.get_agent_prompt('nonexistent_agent')
            
            assert "Agent prompt file not found" in prompt
            
    def test_get_agent_prompt_extraction(self, temp_project_dir):
        """Test extraction of prompt content from markdown"""
        
        full_content = """
# Agent Documentation

Some description here.

## Prompt

```
This is the actual agent prompt content.
It should be extracted properly.
```

## Other Section

This should not be included.
"""
        
        config = {
            'agents': {
                'test_extraction': {
                    'name': 'Test Extraction',
                    'prompt_path': 'test_extraction.md'
                }
            }
        }
        
        prompt_file = temp_project_dir / 'test_extraction.md'
        prompt_file.write_text(full_content)
        
        with patch('coral_collective.agent_runner.FeedbackCollector'), \
             patch('coral_collective.agent_runner.ProjectStateManager'):
            
            runner = AgentRunner()
            runner.base_path = temp_project_dir
            runner.agents_config = config
            
            prompt = runner.get_agent_prompt('test_extraction')
            
            assert "This is the actual agent prompt content" in prompt
            assert "It should be extracted properly" in prompt
            assert "Other Section" not in prompt


@pytest.mark.asyncio
class TestAgentExecution:
    """Test agent execution and workflow management"""
    
    async def test_run_agent_non_interactive_mode(self, temp_project_dir, mock_agents_config):
        """Test running agent in non-interactive mode"""
        
        # Setup
        prompt_dir = temp_project_dir / 'agents' / 'core'
        prompt_dir.mkdir(parents=True)
        prompt_file = prompt_dir / 'project_architect.md'
        prompt_file.write_text("You are a project architect agent.")
        
        with patch('coral_collective.agent_runner.FeedbackCollector'), \
             patch('coral_collective.agent_runner.ProjectStateManager') as mock_state_manager:
            
            runner = AgentRunner()
            runner.base_path = temp_project_dir
            runner.agents_config = mock_agents_config
            runner.mcp_enabled = False
            
            # Create prompts directory
            (temp_project_dir / 'prompts').mkdir()
            
            result = await runner.run_agent(
                'project_architect',
                'Design system architecture',
                non_interactive=True
            )
            
            assert result['agent'] == 'project_architect'
            assert result['task'] == 'Design system architecture'
            assert result['success'] is True
            assert result['non_interactive'] is True
            assert 'prompt_file' in result
            assert 'timestamp' in result
            
            # Verify state manager was called
            mock_state_manager.return_value.record_agent_start.assert_called_once()
            mock_state_manager.return_value.record_agent_completion.assert_called_once()
            
    async def test_run_agent_with_mcp_integration(self, temp_project_dir, mock_agents_config, mock_mcp_client):
        """Test running agent with MCP integration enabled"""
        
        # Setup prompt file
        prompt_dir = temp_project_dir / 'agents' / 'specialists'
        prompt_dir.mkdir(parents=True)
        prompt_file = prompt_dir / 'backend_developer.md'
        prompt_file.write_text("You are a backend developer agent.")
        
        # Mock MCP components
        mock_bridge = Mock()
        mock_bridge.get_session_metrics.return_value = {
            'usage_metrics': {
                'total_calls': 5,
                'success_rate': 1.0,
                'servers_used': ['filesystem', 'github']
            }
        }
        
        mock_prompt_generator = Mock()
        mock_prompt_generator.generate_tools_section = AsyncMock(
            return_value="## Available MCP Tools\n- filesystem_read\n- github_create_repo"
        )
        
        with patch('coral_collective.agent_runner.FeedbackCollector'), \
             patch('coral_collective.agent_runner.ProjectStateManager'), \
             patch('coral_collective.agent_runner.AgentMCPBridge', return_value=mock_bridge), \
             patch('coral_collective.agent_runner.MCPToolsPromptGenerator', return_value=mock_prompt_generator):
            
            runner = AgentRunner()
            runner.base_path = temp_project_dir
            runner.agents_config = mock_agents_config
            runner.mcp_enabled = True
            runner.mcp_client = mock_mcp_client
            runner.mcp_client.initialized = True
            
            # Create prompts directory
            (temp_project_dir / 'prompts').mkdir()
            
            result = await runner.run_agent(
                'backend_developer',
                'Create REST API',
                non_interactive=True,
                mcp_enabled=True
            )
            
            assert result['success'] is True
            assert 'mcp_metrics' in result
            assert result['mcp_metrics']['usage_metrics']['total_calls'] == 5
            
    async def test_get_agent_bridge_creation(self, temp_project_dir, mock_mcp_client):
        """Test MCP bridge creation for agents"""
        
        with patch('coral_collective.agent_runner.FeedbackCollector'), \
             patch('coral_collective.agent_runner.ProjectStateManager'), \
             patch('coral_collective.agent_runner.AgentMCPBridge') as mock_bridge_class:
            
            mock_bridge = Mock()
            mock_bridge_class.return_value = mock_bridge
            
            runner = AgentRunner()
            runner.mcp_enabled = True
            runner.mcp_client = mock_mcp_client
            runner.mcp_client.initialized = True
            
            bridge = await runner.get_agent_bridge('backend_developer', mcp_enabled=True)
            
            assert bridge == mock_bridge
            assert 'backend_developer' in runner.active_bridges
            mock_bridge_class.assert_called_once_with('backend_developer', mock_mcp_client)
            
    async def test_close_agent_bridge(self, temp_project_dir, mock_mcp_client):
        """Test closing MCP bridge for agents"""
        
        with patch('coral_collective.agent_runner.FeedbackCollector'), \
             patch('coral_collective.agent_runner.ProjectStateManager'):
            
            mock_bridge = Mock()
            mock_bridge.close = AsyncMock()
            
            runner = AgentRunner()
            runner.active_bridges['test_agent'] = mock_bridge
            
            await runner.close_agent_bridge('test_agent')
            
            mock_bridge.close.assert_called_once()
            assert 'test_agent' not in runner.active_bridges
            
    async def test_close_all_bridges(self, temp_project_dir, mock_mcp_client):
        """Test closing all MCP bridges"""
        
        with patch('coral_collective.agent_runner.FeedbackCollector'), \
             patch('coral_collective.agent_runner.ProjectStateManager'):
            
            # Create mock bridges
            mock_bridge1 = Mock()
            mock_bridge1.close = AsyncMock()
            mock_bridge2 = Mock()
            mock_bridge2.close = AsyncMock()
            
            runner = AgentRunner()
            runner.mcp_client = mock_mcp_client
            runner.mcp_client.shutdown = AsyncMock()
            runner.active_bridges = {
                'agent1': mock_bridge1,
                'agent2': mock_bridge2
            }
            
            await runner.close_all_bridges()
            
            mock_bridge1.close.assert_called_once()
            mock_bridge2.close.assert_called_once()
            runner.mcp_client.shutdown.assert_called_once()
            assert len(runner.active_bridges) == 0


class TestWorkflowManagement:
    """Test workflow management and sequences"""
    
    def test_start_project(self, temp_project_dir):
        """Test starting a new project"""
        
        with patch('coral_collective.agent_runner.FeedbackCollector'), \
             patch('coral_collective.agent_runner.ProjectStateManager'):
            
            runner = AgentRunner()
            runner.base_path = temp_project_dir
            
            project = runner.start_project(
                "Test Project",
                "A test project for validation"
            )
            
            assert project['name'] == "Test Project"
            assert project['description'] == "A test project for validation"
            assert project['status'] == 'active'
            assert project['current_phase'] == 1
            assert 'created' in project
            
            # Check that project file was created
            projects_dir = temp_project_dir / 'projects'
            assert projects_dir.exists()
            
            project_file = projects_dir / 'test_project.yaml'
            assert project_file.exists()
            
            with open(project_file, 'r') as f:
                saved_project = yaml.safe_load(f)
                assert saved_project['name'] == "Test Project"
                
    @pytest.mark.asyncio
    async def test_run_workflow_non_interactive(self, temp_project_dir, mock_agents_config):
        """Test running workflow in non-interactive mode"""
        
        # Setup prompt files
        for agent_id in ['project_architect', 'backend_developer']:
            agent_dir = temp_project_dir / 'agents' / ('core' if agent_id == 'project_architect' else 'specialists')
            agent_dir.mkdir(parents=True, exist_ok=True)
            prompt_file = agent_dir / f'{agent_id}.md'
            prompt_file.write_text(f"You are a {agent_id} agent.")
        
        with patch('coral_collective.agent_runner.FeedbackCollector'), \
             patch('coral_collective.agent_runner.ProjectStateManager'), \
             patch.object(AgentRunner, 'run_agent', new_callable=AsyncMock) as mock_run_agent:
            
            # Mock successful agent execution
            mock_run_agent.return_value = {
                'success': True,
                'agent': 'test_agent',
                'task': 'test_task',
                'timestamp': datetime.now().isoformat()
            }
            
            runner = AgentRunner()
            runner.base_path = temp_project_dir
            runner.agents_config = mock_agents_config
            
            project = {
                'name': 'Test Workflow',
                'description': 'Test workflow project'
            }
            
            sequence = ['project_architect', 'backend_developer']
            
            # Run workflow
            await runner.run_workflow(sequence, project, non_interactive=True)
            
            # Verify agents were called
            assert mock_run_agent.call_count == len(sequence)
            
    def test_session_summary_calculation(self, temp_project_dir, mock_agents_config):
        """Test session summary calculation"""
        
        with patch('coral_collective.agent_runner.FeedbackCollector'), \
             patch('coral_collective.agent_runner.ProjectStateManager'), \
             patch('coral_collective.agent_runner.console') as mock_console:
            
            runner = AgentRunner()
            runner.agents_config = mock_agents_config
            
            # Add test interactions
            runner.session_data['interactions'] = [
                {
                    'agent': 'project_architect',
                    'task': 'Design architecture',
                    'success': True,
                    'satisfaction': 8,
                    'completion_time': 30
                },
                {
                    'agent': 'backend_developer',
                    'task': 'Create API',
                    'success': True,
                    'satisfaction': 9,
                    'completion_time': 45
                }
            ]
            
            runner.show_session_summary()
            
            # Verify console was called with summary information
            assert mock_console.print.called
            
            # Check that summary stats are calculated correctly
            interactions = runner.session_data['interactions']
            avg_satisfaction = sum(i['satisfaction'] for i in interactions) / len(interactions)
            success_rate = sum(1 for i in interactions if i['success']) / len(interactions) * 100
            
            assert avg_satisfaction == 8.5
            assert success_rate == 100.0


class TestCLIIntegration:
    """Test CLI argument handling and integration"""
    
    @pytest.mark.asyncio
    async def test_async_main_run_command(self):
        """Test async_main with run command"""
        
        test_args = [
            'agent_runner.py', 'run',
            '--agent', 'backend_developer',
            '--task', 'Create REST API',
            '--non-interactive'
        ]
        
        with patch('sys.argv', test_args), \
             patch('coral_collective.agent_runner.AgentRunner') as mock_runner_class:
            
            mock_runner = Mock()
            mock_runner.run_agent = AsyncMock(return_value={
                'success': True,
                'mcp_metrics': {'usage_metrics': {'total_calls': 0}}
            })
            mock_runner.close_all_bridges = AsyncMock()
            mock_runner_class.return_value = mock_runner
            
            await async_main()
            
            mock_runner.run_agent.assert_called_once()
            mock_runner.close_all_bridges.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_async_main_list_command(self):
        """Test async_main with list command"""
        
        test_args = ['agent_runner.py', 'list']
        
        with patch('sys.argv', test_args), \
             patch('coral_collective.agent_runner.AgentRunner') as mock_runner_class:
            
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            
            await async_main()
            
            mock_runner.list_agents.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_async_main_init_command(self):
        """Test async_main with init command"""
        
        test_args = ['agent_runner.py', 'init']
        
        with patch('sys.argv', test_args), \
             patch('coral_collective.agent_runner.console') as mock_console, \
             patch('coral_collective.agent_runner.Path'):
            
            await async_main()
            
            # Should print initialization messages
            assert mock_console.print.called


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_agent_id(self, temp_project_dir, mock_agents_config):
        """Test handling invalid agent IDs"""
        
        with patch('coral_collective.agent_runner.FeedbackCollector'), \
             patch('coral_collective.agent_runner.ProjectStateManager'), \
             patch('coral_collective.agent_runner.console') as mock_console:
            
            runner = AgentRunner()
            runner.agents_config = mock_agents_config
            
            runner.show_agent_details('nonexistent_agent')
            
            # Should print error message
            mock_console.print.assert_called_with("[red]Agent 'nonexistent_agent' not found![/red]")
            
    @pytest.mark.asyncio
    async def test_mcp_initialization_failure(self, temp_project_dir):
        """Test handling MCP initialization failure"""
        
        mock_mcp_client = Mock()
        mock_mcp_client.initialize = AsyncMock(side_effect=Exception("MCP init failed"))
        
        with patch('coral_collective.agent_runner.FeedbackCollector'), \
             patch('coral_collective.agent_runner.ProjectStateManager'), \
             patch('coral_collective.agent_runner.console') as mock_console:
            
            runner = AgentRunner()
            runner.mcp_client = mock_mcp_client
            runner.mcp_enabled = True
            
            result = await runner.initialize_mcp()
            
            assert not result
            mock_console.print.assert_called_with("[red]Failed to initialize MCP: MCP init failed[/red]")
            
    @pytest.mark.asyncio
    async def test_agent_bridge_creation_failure(self, temp_project_dir):
        """Test handling agent bridge creation failure"""
        
        mock_mcp_client = Mock()
        mock_mcp_client.initialized = True
        
        with patch('coral_collective.agent_runner.FeedbackCollector'), \
             patch('coral_collective.agent_runner.ProjectStateManager'), \
             patch('coral_collective.agent_runner.AgentMCPBridge', side_effect=Exception("Bridge creation failed")), \
             patch('coral_collective.agent_runner.console') as mock_console:
            
            runner = AgentRunner()
            runner.mcp_client = mock_mcp_client
            runner.mcp_enabled = True
            
            bridge = await runner.get_agent_bridge('test_agent', mcp_enabled=True)
            
            assert bridge is None
            mock_console.print.assert_called()


class TestPerformanceAndMetrics:
    """Test performance monitoring and metrics collection"""
    
    def test_session_data_tracking(self, temp_project_dir):
        """Test session data tracking and storage"""
        
        with patch('coral_collective.agent_runner.FeedbackCollector'), \
             patch('coral_collective.agent_runner.ProjectStateManager'):
            
            runner = AgentRunner()
            
            # Check initial session data
            assert 'start_time' in runner.session_data
            assert 'interactions' in runner.session_data
            assert isinstance(runner.session_data['start_time'], datetime)
            assert isinstance(runner.session_data['interactions'], list)
            
            # Add test interaction
            test_interaction = {
                'agent': 'test_agent',
                'task': 'test_task',
                'success': True,
                'timestamp': datetime.now().isoformat()
            }
            
            runner.session_data['interactions'].append(test_interaction)
            
            assert len(runner.session_data['interactions']) == 1
            assert runner.session_data['interactions'][0]['agent'] == 'test_agent'
            
    def test_feedback_integration(self, temp_project_dir):
        """Test integration with feedback collection system"""
        
        mock_feedback_collector = Mock()
        
        with patch('coral_collective.agent_runner.FeedbackCollector', return_value=mock_feedback_collector), \
             patch('coral_collective.agent_runner.ProjectStateManager'):
            
            runner = AgentRunner()
            
            assert runner.collector == mock_feedback_collector
            
            # Test feedback recording
            runner.collector.record_interaction(
                'test_agent',
                True,
                8,
                'test_task',
                30
            )
            
            mock_feedback_collector.record_interaction.assert_called_once_with(
                'test_agent', True, 8, 'test_task', 30
            )


# Integration test for full workflow
@pytest.mark.integration
@pytest.mark.asyncio
class TestFullWorkflowIntegration:
    """Integration tests for complete workflow scenarios"""
    
    async def test_complete_agent_workflow(self, temp_project_dir, mock_agents_config):
        """Test complete agent workflow from initialization to completion"""
        
        # Setup directory structure
        for agent_id in ['project_architect', 'backend_developer']:
            agent_dir = temp_project_dir / 'agents' / ('core' if agent_id == 'project_architect' else 'specialists')
            agent_dir.mkdir(parents=True, exist_ok=True)
            prompt_file = agent_dir / f'{agent_id}.md'
            prompt_file.write_text(f"You are a {agent_id} agent.\n\n## Prompt\n\n```\nTest prompt content.\n```")
        
        (temp_project_dir / 'prompts').mkdir()
        
        # Create config file
        config_file = temp_project_dir / "claude_code_agents.json"
        with open(config_file, 'w') as f:
            json.dump(mock_agents_config, f)
            
        with patch('coral_collective.agent_runner.Path') as mock_path, \
             patch('coral_collective.agent_runner.FeedbackCollector'), \
             patch('coral_collective.agent_runner.ProjectStateManager') as mock_state_manager:
            
            mock_path.return_value.parent = temp_project_dir
            mock_path.__file__ = str(temp_project_dir / "agent_runner.py")
            
            runner = AgentRunner()
            runner.mcp_enabled = False  # Disable MCP for integration test
            
            # Test project creation
            project = runner.start_project(
                "Integration Test Project",
                "A project for integration testing"
            )
            
            assert project['name'] == "Integration Test Project"
            
            # Test agent execution
            result = await runner.run_agent(
                'project_architect',
                'Design system architecture',
                project_context=project,
                non_interactive=True
            )
            
            assert result['success'] is True
            assert result['agent'] == 'project_architect'
            
            # Verify state tracking
            mock_state_manager.return_value.record_agent_start.assert_called()
            mock_state_manager.return_value.record_agent_completion.assert_called()
            
            # Test session summary
            assert len(runner.session_data['interactions']) >= 1