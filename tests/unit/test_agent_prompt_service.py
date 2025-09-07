"""
Unit tests for CoralCollective Agent Prompt Service

Tests cover:
1. PromptPayload creation and serialization
2. Prompt composition (sync and async)
3. Token estimation and budgeting
4. Section building and organization
5. Text chunking and truncation
6. MCP tools integration
7. Error handling and edge cases
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Optional

# Import the module under test
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from agent_prompt_service import (
    PromptPayload,
    compose,
    compose_async,
    TokenEstimator,
    build_sections,
    fit_sections_to_budget,
    chunk_text,
    _truncate_text_by_ratio
)


class TestPromptPayload:
    """Test PromptPayload data structure and methods"""
    
    def test_prompt_payload_creation(self):
        """Test basic PromptPayload creation"""
        
        payload = PromptPayload(
            agent_id="backend_developer",
            agent_name="Backend Developer",
            base_prompt="You are a backend developer.",
            task="Create REST API",
            project_context={"type": "web_app"},
            mcp_tools={"filesystem": ["read", "write"]}
        )
        
        assert payload.agent_id == "backend_developer"
        assert payload.agent_name == "Backend Developer"
        assert payload.base_prompt == "You are a backend developer."
        assert payload.task == "Create REST API"
        assert payload.project_context == {"type": "web_app"}
        assert payload.mcp_tools == {"filesystem": ["read", "write"]}
        
    def test_to_default_text_with_full_data(self):
        """Test default text rendering with all data"""
        
        payload = PromptPayload(
            agent_id="test_agent",
            agent_name="Test Agent",
            base_prompt="You are a test agent for validation purposes.",
            task="Execute test scenarios",
            project_context={"name": "test_project", "type": "testing"},
            mcp_tools={"test_tools": ["validate", "report"]}
        )
        
        text = payload.to_default_text()
        
        assert "You are acting as 'Test Agent' (test_agent)" in text
        assert "=== ROLE PROMPT ===" in text
        assert "You are a test agent for validation purposes." in text
        assert "=== PROJECT CONTEXT ===" in text
        assert '"name": "test_project"' in text
        assert "=== MCP TOOLS (if any) ===" in text
        assert '"test_tools"' in text
        assert "=== TASK ===" in text
        assert "Execute test scenarios" in text
        assert "Provide clear outputs and, if applicable, handoff notes." in text
        
    def test_to_default_text_minimal_data(self):
        """Test default text rendering with minimal data"""
        
        payload = PromptPayload(
            agent_id="minimal_agent",
            agent_name="Minimal Agent", 
            base_prompt="Minimal prompt",
            task="Minimal task",
            project_context=None,
            mcp_tools=None
        )
        
        text = payload.to_default_text()
        
        assert "You are acting as 'Minimal Agent' (minimal_agent)" in text
        assert "Minimal prompt" in text
        assert "New project" in text  # Default context
        assert "None" in text  # Default MCP tools
        assert "Minimal task" in text


class TestTokenEstimator:
    """Test token estimation functionality"""
    
    def test_token_estimator_creation_without_tiktoken(self):
        """Test TokenEstimator creation when tiktoken is not available"""
        
        with patch('agent_prompt_service.tiktoken', side_effect=ImportError):
            estimator = TokenEstimator()
            
            assert estimator.model == "generic"
            assert estimator._tk is None
            
    def test_token_estimator_creation_with_model(self):
        """Test TokenEstimator creation with specific model"""
        
        with patch('agent_prompt_service.tiktoken') as mock_tiktoken:
            mock_encoding = Mock()
            mock_tiktoken.encoding_for_model.return_value = mock_encoding
            
            estimator = TokenEstimator("gpt-4")
            
            assert estimator.model == "gpt-4"
            assert estimator._tk == mock_encoding
            mock_tiktoken.encoding_for_model.assert_called_with("gpt-4")
            
    def test_token_estimator_fallback_encoding(self):
        """Test TokenEstimator fallback to default encoding"""
        
        with patch('agent_prompt_service.tiktoken') as mock_tiktoken:
            mock_tiktoken.encoding_for_model.side_effect = Exception("Model not found")
            mock_encoding = Mock()
            mock_tiktoken.get_encoding.return_value = mock_encoding
            
            estimator = TokenEstimator("unknown_model")
            
            assert estimator._tk == mock_encoding
            mock_tiktoken.get_encoding.assert_called_with("cl100k_base")
            
    def test_estimate_with_tiktoken(self):
        """Test token estimation with tiktoken available"""
        
        with patch('agent_prompt_service.tiktoken') as mock_tiktoken:
            mock_encoding = Mock()
            mock_encoding.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
            mock_tiktoken.get_encoding.return_value = mock_encoding
            
            estimator = TokenEstimator()
            tokens = estimator.estimate("Hello world")
            
            assert tokens == 5
            mock_encoding.encode.assert_called_with("Hello world")
            
    def test_estimate_fallback_heuristic(self):
        """Test token estimation using fallback heuristic"""
        
        with patch('agent_prompt_service.tiktoken', side_effect=ImportError):
            estimator = TokenEstimator()
            
            # Test various text lengths
            assert estimator.estimate("") == 0
            assert estimator.estimate("Hi") == 1  # 2 chars / 4 = 0.5, rounded up to 1
            assert estimator.estimate("Hello") == 2  # 5 chars / 4 = 1.25, rounded up to 2
            assert estimator.estimate("Hello world!") == 3  # 12 chars / 4 = 3
            
    def test_estimate_edge_cases(self):
        """Test token estimation edge cases"""
        
        with patch('agent_prompt_service.tiktoken', side_effect=ImportError):
            estimator = TokenEstimator()
            
            # Empty string
            assert estimator.estimate("") == 0
            
            # Single character
            assert estimator.estimate("a") == 1
            
            # Very long text
            long_text = "a" * 1000
            expected_tokens = 250  # 1000 / 4 = 250
            assert estimator.estimate(long_text) == expected_tokens


class TestPromptComposition:
    """Test prompt composition functionality"""
    
    def test_compose_basic(self):
        """Test basic prompt composition"""
        
        mock_runner = Mock()
        mock_runner.get_agent_prompt.return_value = "You are a test agent."
        mock_runner.agents_config = {
            "agents": {
                "test_agent": {
                    "name": "Test Agent"
                }
            }
        }
        mock_runner.mcp_client = None
        
        payload = compose("test_agent", "Test task", runner=mock_runner)
        
        assert payload.agent_id == "test_agent"
        assert payload.agent_name == "Test Agent"
        assert payload.base_prompt == "You are a test agent."
        assert payload.task == "Test task"
        assert payload.project_context is None
        assert payload.mcp_tools is None
        
        mock_runner.get_agent_prompt.assert_called_with("test_agent")
        
    def test_compose_with_project_context(self):
        """Test prompt composition with project context"""
        
        mock_runner = Mock()
        mock_runner.get_agent_prompt.return_value = "You are a test agent."
        mock_runner.agents_config = {"agents": {"test_agent": {"name": "Test Agent"}}}
        mock_runner.mcp_client = None
        
        context = {"project": "test", "phase": 1}
        payload = compose("test_agent", "Test task", runner=mock_runner, project_context=context)
        
        assert payload.project_context == context
        
    def test_compose_with_mcp_tools(self):
        """Test prompt composition with MCP tools"""
        
        mock_runner = Mock()
        mock_runner.get_agent_prompt.return_value = "You are a test agent."
        mock_runner.agents_config = {"agents": {"test_agent": {"name": "Test Agent"}}}
        
        mock_mcp_client = Mock()
        mock_mcp_client.get_tools_for_agent.return_value = {"filesystem": ["read", "write"]}
        mock_runner.mcp_client = mock_mcp_client
        
        payload = compose("test_agent", "Test task", runner=mock_runner, include_mcp_tools=True)
        
        assert payload.mcp_tools == {"filesystem": ["read", "write"]}
        mock_mcp_client.get_tools_for_agent.assert_called_with("test_agent")
        
    def test_compose_mcp_tools_disabled(self):
        """Test prompt composition with MCP tools disabled"""
        
        mock_runner = Mock()
        mock_runner.get_agent_prompt.return_value = "You are a test agent."
        mock_runner.agents_config = {"agents": {"test_agent": {"name": "Test Agent"}}}
        mock_runner.mcp_client = Mock()
        
        payload = compose("test_agent", "Test task", runner=mock_runner, include_mcp_tools=False)
        
        assert payload.mcp_tools is None
        
    def test_compose_mcp_tools_exception(self):
        """Test prompt composition when MCP tools raise exception"""
        
        mock_runner = Mock()
        mock_runner.get_agent_prompt.return_value = "You are a test agent."
        mock_runner.agents_config = {"agents": {"test_agent": {"name": "Test Agent"}}}
        
        mock_mcp_client = Mock()
        mock_mcp_client.get_tools_for_agent.side_effect = Exception("MCP error")
        mock_runner.mcp_client = mock_mcp_client
        
        payload = compose("test_agent", "Test task", runner=mock_runner, include_mcp_tools=True)
        
        assert payload.mcp_tools is None  # Should handle exception gracefully
        
    def test_compose_no_runner_available(self):
        """Test compose when AgentRunner is not available"""
        
        with patch('agent_prompt_service.AgentRunner', None):
            with pytest.raises(RuntimeError, match="AgentRunner unavailable"):
                compose("test_agent", "Test task", runner=None)
                
    def test_compose_agent_name_fallback(self):
        """Test agent name fallback to agent_id when name not in config"""
        
        mock_runner = Mock()
        mock_runner.get_agent_prompt.return_value = "You are a test agent."
        mock_runner.agents_config = {"agents": {"test_agent": {}}}  # No name field
        mock_runner.mcp_client = None
        
        payload = compose("test_agent", "Test task", runner=mock_runner)
        
        assert payload.agent_name == "test_agent"  # Falls back to agent_id


@pytest.mark.asyncio
class TestAsyncPromptComposition:
    """Test async prompt composition functionality"""
    
    async def test_compose_async_basic(self):
        """Test basic async prompt composition"""
        
        mock_runner = Mock()
        mock_runner.get_agent_prompt.return_value = "You are a test agent."
        mock_runner.agents_config = {"agents": {"test_agent": {"name": "Test Agent"}}}
        
        payload = await compose_async("test_agent", "Test task", runner=mock_runner, include_mcp_tools=False)
        
        assert payload.agent_id == "test_agent"
        assert payload.agent_name == "Test Agent"
        assert payload.base_prompt == "You are a test agent."
        assert payload.task == "Test task"
        
    async def test_compose_async_with_mcp_bridge(self):
        """Test async composition with MCP bridge"""
        
        mock_runner = Mock()
        mock_runner.get_agent_prompt.return_value = "You are a test agent."
        mock_runner.agents_config = {"agents": {"test_agent": {"name": "Test Agent"}}}
        
        mock_bridge = AsyncMock()
        
        with patch('agent_prompt_service.MCPToolsPromptGenerator') as mock_generator_class:
            mock_generator = AsyncMock()
            mock_generator.generate_tools_section.return_value = "## Available MCP Tools\n- filesystem_read\n- github_create"
            mock_generator_class.return_value = mock_generator
            
            payload = await compose_async(
                "test_agent", 
                "Test task", 
                runner=mock_runner, 
                include_mcp_tools=True,
                mcp_bridge=mock_bridge
            )
            
            assert payload.mcp_tools is not None
            assert payload.mcp_tools["documentation"] == "## Available MCP Tools\n- filesystem_read\n- github_create"
            mock_generator.generate_tools_section.assert_called_once()
            
    async def test_compose_async_mcp_bridge_failure(self):
        """Test async composition when MCP bridge fails"""
        
        mock_runner = Mock()
        mock_runner.get_agent_prompt.return_value = "You are a test agent."
        mock_runner.agents_config = {"agents": {"test_agent": {"name": "Test Agent"}}}
        
        mock_bridge = AsyncMock()
        mock_bridge.get_available_tools.return_value = {"filesystem_read": {}, "github_create": {}}
        
        with patch('agent_prompt_service.MCPToolsPromptGenerator', side_effect=Exception("Import error")):
            payload = await compose_async(
                "test_agent",
                "Test task", 
                runner=mock_runner,
                include_mcp_tools=True,
                mcp_bridge=mock_bridge
            )
            
            # Should fall back to simple tools list
            assert payload.mcp_tools is not None
            assert "filesystem_read, github_create" in payload.mcp_tools["documentation"]
            
    async def test_compose_async_no_mcp_bridge(self):
        """Test async composition without MCP bridge"""
        
        mock_runner = Mock()
        mock_runner.get_agent_prompt.return_value = "You are a test agent."
        mock_runner.agents_config = {"agents": {"test_agent": {"name": "Test Agent"}}}
        
        payload = await compose_async("test_agent", "Test task", runner=mock_runner, mcp_bridge=None)
        
        assert payload.mcp_tools is None


class TestSectionBuilding:
    """Test section building functionality"""
    
    def test_build_sections_basic(self):
        """Test basic section building"""
        
        payload = PromptPayload(
            agent_id="test_agent",
            agent_name="Test Agent",
            base_prompt="You are a test agent.",
            task="Test task",
            project_context=None,
            mcp_tools=None
        )
        
        sections = build_sections(payload, expand=False)
        
        # Should have role_prompt and task sections only
        assert len(sections) == 2
        
        role_section = sections[0]
        assert role_section['key'] == 'role_prompt'
        assert role_section['title'] == 'ROLE PROMPT'
        assert role_section['text'] == 'You are a test agent.'
        assert role_section['required'] is True
        
        task_section = sections[1]
        assert task_section['key'] == 'task'
        assert task_section['title'] == 'TASK'
        assert task_section['text'] == 'Test task'
        assert task_section['required'] is True
        
    def test_build_sections_with_expand(self):
        """Test section building with expand=True"""
        
        payload = PromptPayload(
            agent_id="test_agent",
            agent_name="Test Agent",
            base_prompt="You are a test agent.",
            task="Test task",
            project_context={"name": "test_project"},
            mcp_tools={"tools": ["filesystem"]})
            
        sections = build_sections(payload, expand=True)
        
        assert len(sections) == 4  # role_prompt, project_context, mcp_tools, task
        
        # Check project context section
        context_section = next(s for s in sections if s['key'] == 'project_context')
        assert context_section['title'] == 'PROJECT CONTEXT'
        assert '"name": "test_project"' in context_section['text']
        assert context_section['required'] is False
        
        # Check MCP tools section
        mcp_section = next(s for s in sections if s['key'] == 'mcp_tools')
        assert mcp_section['title'] == 'MCP TOOLS'
        assert '"tools"' in mcp_section['text']
        assert mcp_section['required'] is False
        
    def test_build_sections_new_mcp_format(self):
        """Test section building with new MCP documentation format"""
        
        payload = PromptPayload(
            agent_id="test_agent",
            agent_name="Test Agent",
            base_prompt="You are a test agent.",
            task="Test task",
            project_context=None,
            mcp_tools={"documentation": "## Available Tools\n- filesystem_read: Read files\n- filesystem_write: Write files"}
        )
        
        sections = build_sections(payload, expand=True)
        
        mcp_section = next(s for s in sections if s['key'] == 'mcp_tools')
        assert mcp_section['title'] == 'MCP TOOLS AVAILABLE'
        assert '## Available Tools' in mcp_section['text']
        assert 'filesystem_read' in mcp_section['text']
        
    def test_build_sections_no_project_context_with_expand(self):
        """Test section building with expand=True but no project context"""
        
        payload = PromptPayload(
            agent_id="test_agent",
            agent_name="Test Agent",
            base_prompt="You are a test agent.",
            task="Test task",
            project_context=None,
            mcp_tools=None
        )
        
        sections = build_sections(payload, expand=True)
        
        # Should include default project context
        context_section = next(s for s in sections if s['key'] == 'project_context')
        assert context_section['text'] == 'New project'


class TestTextProcessing:
    """Test text processing utilities"""
    
    def test_truncate_text_by_ratio(self):
        """Test text truncation by ratio"""
        
        text = "This is a test sentence. This is another sentence. Final sentence."
        
        # Test 100% (no truncation)
        result = _truncate_text_by_ratio(text, 1.0)
        assert result == text
        
        # Test 50% truncation
        result = _truncate_text_by_ratio(text, 0.5)
        assert len(result) < len(text)
        assert result.startswith("This is a test")
        
        # Test 0% (complete truncation)
        result = _truncate_text_by_ratio(text, 0.0)
        assert result == ""
        
        # Test over 100% (should return original)
        result = _truncate_text_by_ratio(text, 1.5)
        assert result == text
        
    def test_chunk_text_basic(self):
        """Test basic text chunking"""
        
        estimator = TokenEstimator()
        
        # Create text with clear paragraph boundaries
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph.\n\nFourth paragraph."
        
        chunks = chunk_text(text, estimator, chunk_tokens=10)
        
        assert len(chunks) > 1
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert ''.join(chunks).replace('\n', '').replace(' ', '') in text.replace('\n', '').replace(' ', '')
        
    def test_chunk_text_single_chunk(self):
        """Test text chunking when text fits in single chunk"""
        
        estimator = TokenEstimator()
        
        text = "Short text"
        chunks = chunk_text(text, estimator, chunk_tokens=1000)
        
        assert len(chunks) == 1
        assert chunks[0] == text
        
    def test_chunk_text_empty(self):
        """Test chunking empty text"""
        
        estimator = TokenEstimator()
        chunks = chunk_text("", estimator)
        
        assert len(chunks) == 1
        assert chunks[0] == ""


class TestBudgetFitting:
    """Test budget fitting and section optimization"""
    
    def test_fit_sections_under_budget(self):
        """Test fitting sections when already under budget"""
        
        estimator = TokenEstimator()
        
        sections = [
            {'key': 'role_prompt', 'text': 'Short prompt', 'required': True},
            {'key': 'task', 'text': 'Short task', 'required': True}
        ]
        
        result = fit_sections_to_budget(sections, estimator, budget_tokens=1000)
        
        assert len(result) == 2
        assert result[0]['text'] == 'Short prompt'
        assert result[1]['text'] == 'Short task'
        
    def test_fit_sections_drop_mcp_tools(self):
        """Test dropping MCP tools to fit budget"""
        
        estimator = TokenEstimator()
        
        sections = [
            {'key': 'role_prompt', 'text': 'Short prompt', 'required': True},
            {'key': 'project_context', 'text': 'Short context', 'required': False},
            {'key': 'mcp_tools', 'text': 'Long MCP tools documentation' * 100, 'required': False},
            {'key': 'task', 'text': 'Short task', 'required': True}
        ]
        
        result = fit_sections_to_budget(sections, estimator, budget_tokens=50, overhead_tokens=10)
        
        # MCP tools should be dropped
        assert len(result) == 3
        assert not any(s['key'] == 'mcp_tools' for s in result)
        
    def test_fit_sections_truncate_context(self):
        """Test truncating project context to fit budget"""
        
        estimator = TokenEstimator()
        
        long_context = "Very long project context description. " * 50
        sections = [
            {'key': 'role_prompt', 'text': 'Short prompt', 'required': True},
            {'key': 'project_context', 'text': long_context, 'required': False},
            {'key': 'task', 'text': 'Short task', 'required': True}
        ]
        
        result = fit_sections_to_budget(sections, estimator, budget_tokens=100, overhead_tokens=10)
        
        # Context should be truncated
        context_section = next(s for s in result if s['key'] == 'project_context')
        assert len(context_section['text']) < len(long_context)
        assert context_section['text'].endswith('…')
        
    def test_fit_sections_drop_context(self):
        """Test dropping project context when still too large after truncation"""
        
        estimator = TokenEstimator()
        
        very_long_context = "Extremely long project context description. " * 200
        sections = [
            {'key': 'role_prompt', 'text': 'Short prompt', 'required': True},
            {'key': 'project_context', 'text': very_long_context, 'required': False},
            {'key': 'task', 'text': 'Short task', 'required': True}
        ]
        
        result = fit_sections_to_budget(sections, estimator, budget_tokens=20, overhead_tokens=5)
        
        # Context should be dropped entirely
        assert not any(s['key'] == 'project_context' for s in result)
        assert len(result) == 2
        
    def test_fit_sections_truncate_role_prompt(self):
        """Test truncating role prompt as last resort"""
        
        estimator = TokenEstimator()
        
        long_prompt = "Very long role prompt description. " * 100
        sections = [
            {'key': 'role_prompt', 'text': long_prompt, 'required': True},
            {'key': 'task', 'text': 'Task', 'required': True}
        ]
        
        result = fit_sections_to_budget(sections, estimator, budget_tokens=50, overhead_tokens=10)
        
        # Role prompt should be truncated but not removed
        role_section = next(s for s in result if s['key'] == 'role_prompt')
        assert len(role_section['text']) < len(long_prompt)
        assert len(role_section['text']) > 0  # Should not be empty


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_compose_with_none_runner_and_no_agentrunner(self):
        """Test compose when runner is None and AgentRunner is not available"""
        
        with patch('agent_prompt_service.AgentRunner', None):
            with pytest.raises(RuntimeError):
                compose("test_agent", "test_task", runner=None)
                
    def test_token_estimator_with_tiktoken_encode_error(self):
        """Test TokenEstimator when tiktoken encoding fails"""
        
        with patch('agent_prompt_service.tiktoken') as mock_tiktoken:
            mock_encoding = Mock()
            mock_encoding.encode.side_effect = Exception("Encoding error")
            mock_tiktoken.get_encoding.return_value = mock_encoding
            
            estimator = TokenEstimator()
            
            # Should fall back to heuristic
            tokens = estimator.estimate("Hello world")
            assert tokens == 3  # 11 chars / 4 ≈ 3
            
    def test_build_sections_empty_mcp_documentation(self):
        """Test build_sections with empty MCP documentation"""
        
        payload = PromptPayload(
            agent_id="test_agent",
            agent_name="Test Agent",
            base_prompt="Test prompt",
            task="Test task",
            project_context=None,
            mcp_tools={"documentation": ""}  # Empty documentation
        )
        
        sections = build_sections(payload, expand=True)
        
        # Should not include MCP tools section when documentation is empty
        assert not any(s['key'] == 'mcp_tools' for s in sections)
        
    def test_fit_sections_extreme_budget_constraint(self):
        """Test fitting sections with extremely small budget"""
        
        estimator = TokenEstimator()
        
        sections = [
            {'key': 'role_prompt', 'text': 'Role prompt', 'required': True},
            {'key': 'task', 'text': 'Task', 'required': True}
        ]
        
        result = fit_sections_to_budget(sections, estimator, budget_tokens=1, overhead_tokens=1)
        
        # Should still have sections, but heavily truncated
        assert len(result) == 2
        assert all(len(s['text']) > 0 for s in result)  # Should not be completely empty


# Integration test for complete prompt flow
@pytest.mark.integration
class TestPromptServiceIntegration:
    """Integration tests for complete prompt service workflow"""
    
    def test_complete_prompt_pipeline(self):
        """Test complete prompt pipeline from composition to rendering"""
        
        # Create mock runner
        mock_runner = Mock()
        mock_runner.get_agent_prompt.return_value = "You are a comprehensive backend developer agent specialized in creating robust server-side applications."
        mock_runner.agents_config = {
            "agents": {
                "backend_developer": {
                    "name": "Backend Developer",
                    "capabilities": ["api", "database", "authentication"]
                }
            }
        }
        mock_runner.mcp_client = Mock()
        mock_runner.mcp_client.get_tools_for_agent.return_value = {
            "filesystem": ["read", "write", "list"],
            "database": ["query", "migrate", "backup"]
        }
        
        # 1. Compose payload
        payload = compose(
            "backend_developer",
            "Create a REST API with user authentication and PostgreSQL database integration",
            runner=mock_runner,
            project_context={
                "name": "E-commerce Platform",
                "type": "web_application",
                "database": "postgresql",
                "requirements": ["user_auth", "product_catalog", "order_management"]
            },
            include_mcp_tools=True
        )
        
        # 2. Build sections
        sections = build_sections(payload, expand=True)
        
        # 3. Check section structure
        assert len(sections) == 4  # role_prompt, project_context, mcp_tools, task
        
        section_keys = [s['key'] for s in sections]
        assert 'role_prompt' in section_keys
        assert 'project_context' in section_keys
        assert 'mcp_tools' in section_keys
        assert 'task' in section_keys
        
        # 4. Apply token budgeting
        estimator = TokenEstimator()
        fitted_sections = fit_sections_to_budget(sections, estimator, budget_tokens=1000)
        
        # Should preserve required sections
        fitted_keys = [s['key'] for s in fitted_sections]
        assert 'role_prompt' in fitted_keys
        assert 'task' in fitted_keys
        
        # 5. Generate final text
        final_text = payload.to_default_text()
        
        assert "Backend Developer" in final_text
        assert "REST API" in final_text
        assert "E-commerce Platform" in final_text
        assert "filesystem" in final_text or "database" in final_text  # MCP tools
        
    @pytest.mark.asyncio
    async def test_async_prompt_pipeline_with_mcp_bridge(self):
        """Test async prompt pipeline with MCP bridge integration"""
        
        # Create mock runner and bridge
        mock_runner = Mock()
        mock_runner.get_agent_prompt.return_value = "You are a frontend developer agent."
        mock_runner.agents_config = {
            "agents": {
                "frontend_developer": {"name": "Frontend Developer"}
            }
        }
        
        mock_bridge = AsyncMock()
        
        with patch('agent_prompt_service.MCPToolsPromptGenerator') as mock_generator_class:
            mock_generator = AsyncMock()
            mock_generator.generate_tools_section.return_value = """
## Available MCP Tools

### Filesystem Operations
- **filesystem_read**: Read file contents
- **filesystem_write**: Write content to files  
- **filesystem_list**: List directory contents

### GitHub Integration
- **github_create_repo**: Create new repository
- **github_create_pr**: Create pull request

Usage examples and detailed documentation included.
"""
            mock_generator_class.return_value = mock_generator
            
            # Compose async payload
            payload = await compose_async(
                "frontend_developer",
                "Create a React application with routing and state management",
                runner=mock_runner,
                project_context={"framework": "react", "features": ["routing", "state_management"]},
                include_mcp_tools=True,
                mcp_bridge=mock_bridge
            )
            
            # Build and verify sections
            sections = build_sections(payload, expand=True)
            
            # Should include enhanced MCP tools documentation
            mcp_section = next((s for s in sections if s['key'] == 'mcp_tools'), None)
            assert mcp_section is not None
            assert "Available MCP Tools" in mcp_section['text']
            assert "filesystem_read" in mcp_section['text']
            assert "github_create_repo" in mcp_section['text']
            assert "Usage examples" in mcp_section['text']