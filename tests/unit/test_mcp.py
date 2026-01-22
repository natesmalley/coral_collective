"""
Unit tests for CoralCollective MCP Integration

Tests cover:
1. MCP client functionality
2. Agent-MCP bridge operations
3. MCP tool integration
4. Error handling and recovery
5. MCP metrics collection
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Mock MCP modules in case they're not installed
sys.modules['mcp'] = MagicMock()
sys.modules['mcp.client'] = MagicMock()
sys.modules['mcp.types'] = MagicMock()

try:
    from mcp.mcp_client import MCPClient
    from coral_collective.tools.agent_mcp_bridge import AgentMCPBridge, MCPToolsPromptGenerator
    from coral_collective.tools.mcp_error_handler import MCPErrorHandler, MCPError
    from coral_collective.tools.mcp_metrics_collector import MCPMetricsCollector
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Create mock classes for testing
    class MCPClient:
        def __init__(self):
            self.connected = False
            
    class AgentMCPBridge:
        def __init__(self, mcp_client):
            self.mcp_client = mcp_client
            
    class MCPToolsPromptGenerator:
        def __init__(self):
            pass
            
    class MCPErrorHandler:
        def __init__(self):
            pass
            
    class MCPError(Exception):
        pass
        
    class MCPMetricsCollector:
        def __init__(self):
            pass


@pytest.mark.mcp
@pytest.mark.unit
@pytest.mark.skip(reason="MCP async tests may hang in CI")
class TestMCPClient:
    """Test MCPClient functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Clean up test files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_mcp_client_initialization(self):
        """Test MCP client initialization"""
        with patch('mcp.mcp_client.asyncio.create_subprocess_exec') as mock_proc:
            mock_process = Mock()
            mock_process.stdin = Mock()
            mock_process.stdout = Mock()
            mock_proc.return_value = mock_process
            
            client = MCPClient()
            
            assert client is not None
            assert hasattr(client, 'connected')
    
    @pytest.mark.asyncio
    async def test_connect_to_server(self):
        """Test connecting to MCP server"""
        client = MCPClient()
        
        with patch.object(client, '_start_server_process') as mock_start, \
             patch.object(client, '_initialize_connection') as mock_init:
            
            mock_start.return_value = True
            mock_init.return_value = True
            
            result = await client.connect('filesystem')
            
            assert result is True
            mock_start.assert_called_once_with('filesystem')
            mock_init.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_list_available_tools(self):
        """Test listing available tools"""
        client = MCPClient()
        client.connected = True
        
        mock_tools = [
            {
                "name": "filesystem_read",
                "description": "Read file content", 
                "parameters": {"path": {"type": "string", "required": True}}
            },
            {
                "name": "filesystem_write",
                "description": "Write file content",
                "parameters": {"path": {"type": "string", "required": True}}
            }
        ]
        
        with patch.object(client, '_send_request') as mock_send:
            mock_send.return_value = {"tools": mock_tools}
            
            tools = await client.list_tools()
            
            assert len(tools) == 2
            assert tools[0]["name"] == "filesystem_read"
            assert tools[1]["name"] == "filesystem_write"
    
    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        """Test successful tool execution"""
        client = MCPClient()
        client.connected = True
        
        mock_response = {
            "result": "File content successfully read",
            "success": True
        }
        
        with patch.object(client, '_send_request') as mock_send:
            mock_send.return_value = mock_response
            
            result = await client.call_tool(
                "filesystem_read",
                {"path": "/test/file.txt"}
            )
            
            assert result["success"] is True
            assert "successfully read" in result["result"]
    
    @pytest.mark.asyncio
    async def test_call_tool_failure(self):
        """Test tool execution failure"""
        client = MCPClient()
        client.connected = True
        
        with patch.object(client, '_send_request') as mock_send:
            mock_send.side_effect = Exception("Tool execution failed")
            
            result = await client.call_tool(
                "filesystem_read",
                {"path": "/nonexistent/file.txt"}
            )
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting from MCP server"""
        client = MCPClient()
        client.connected = True
        client._process = Mock()
        
        await client.disconnect()
        
        assert client.connected is False
        client._process.terminate.assert_called_once()


@pytest.mark.mcp
@pytest.mark.unit
class TestAgentMCPBridge:
    """Test AgentMCPBridge functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.mock_client = Mock()
        self.mock_client.connected = True
        self.mock_client.list_tools = AsyncMock(return_value=[
            {"name": "filesystem_read", "description": "Read files"},
            {"name": "github_create_repo", "description": "Create repository"}
        ])
        self.mock_client.call_tool = AsyncMock(return_value={
            "success": True,
            "result": "Tool executed successfully"
        })
        
        self.bridge = AgentMCPBridge(self.mock_client)
    
    @pytest.mark.asyncio
    async def test_get_available_tools_for_agent(self):
        """Test getting available tools for specific agent"""
        # Mock agent permissions
        with patch.object(self.bridge, '_get_agent_permissions') as mock_perms:
            mock_perms.return_value = ["filesystem", "github"]
            
            tools = await self.bridge.get_available_tools_for_agent("backend_developer")
            
            assert len(tools) == 2
            assert any(tool["name"] == "filesystem_read" for tool in tools)
            assert any(tool["name"] == "github_create_repo" for tool in tools)
    
    @pytest.mark.asyncio
    async def test_execute_tool_for_agent(self):
        """Test executing tool on behalf of agent"""
        with patch.object(self.bridge, '_validate_agent_permission') as mock_validate:
            mock_validate.return_value = True
            
            result = await self.bridge.execute_tool_for_agent(
                agent_id="backend_developer",
                tool_name="filesystem_read",
                parameters={"path": "/src/api.py"}
            )
            
            assert result["success"] is True
            assert "successfully" in result["result"]
            mock_validate.assert_called_once_with("backend_developer", "filesystem_read")
    
    @pytest.mark.asyncio
    async def test_execute_tool_permission_denied(self):
        """Test tool execution with insufficient permissions"""
        with patch.object(self.bridge, '_validate_agent_permission') as mock_validate:
            mock_validate.return_value = False
            
            result = await self.bridge.execute_tool_for_agent(
                agent_id="frontend_developer",
                tool_name="system_admin", 
                parameters={}
            )
            
            assert result["success"] is False
            assert "permission denied" in result["error"].lower()
    
    def test_generate_tools_prompt(self):
        """Test generating tools prompt for agent"""
        tools = [
            {"name": "filesystem_read", "description": "Read file content"},
            {"name": "filesystem_write", "description": "Write file content"}
        ]
        
        with patch.object(self.bridge, 'get_available_tools_for_agent') as mock_tools:
            mock_tools.return_value = tools
            
            prompt = self.bridge.generate_tools_prompt("backend_developer")
            
            assert prompt is not None
            assert "filesystem_read" in prompt
            assert "filesystem_write" in prompt
            assert "Read file content" in prompt
    
    def test_validate_tool_parameters(self):
        """Test tool parameter validation"""
        tool_schema = {
            "name": "filesystem_read",
            "parameters": {
                "path": {"type": "string", "required": True},
                "encoding": {"type": "string", "required": False, "default": "utf-8"}
            }
        }
        
        # Valid parameters
        valid_params = {"path": "/test/file.txt", "encoding": "utf-8"}
        result = self.bridge._validate_tool_parameters(tool_schema, valid_params)
        assert result is True
        
        # Missing required parameter
        invalid_params = {"encoding": "utf-8"}
        result = self.bridge._validate_tool_parameters(tool_schema, invalid_params)
        assert result is False
        
        # Valid with default
        minimal_params = {"path": "/test/file.txt"}
        result = self.bridge._validate_tool_parameters(tool_schema, minimal_params)
        assert result is True


@pytest.mark.mcp
@pytest.mark.unit
class TestMCPToolsPromptGenerator:
    """Test MCPToolsPromptGenerator functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.generator = MCPToolsPromptGenerator()
        
    def test_generate_tools_section(self):
        """Test generating tools section for agent prompt"""
        tools = [
            {
                "name": "filesystem_read",
                "description": "Read file content from filesystem",
                "parameters": {
                    "path": {"type": "string", "description": "File path to read"}
                }
            },
            {
                "name": "github_create_repo",
                "description": "Create new GitHub repository", 
                "parameters": {
                    "name": {"type": "string", "description": "Repository name"},
                    "private": {"type": "boolean", "description": "Private repository flag"}
                }
            }
        ]
        
        section = self.generator.generate_tools_section(tools)
        
        assert section is not None
        assert "Available Tools" in section
        assert "filesystem_read" in section
        assert "github_create_repo" in section
        assert "File path to read" in section
        assert "Repository name" in section
    
    def test_generate_usage_examples(self):
        """Test generating usage examples"""
        tool = {
            "name": "filesystem_write",
            "description": "Write content to file",
            "parameters": {
                "path": {"type": "string", "description": "File path"},
                "content": {"type": "string", "description": "File content"}
            }
        }
        
        examples = self.generator.generate_usage_examples([tool])
        
        assert examples is not None
        assert "filesystem_write" in examples
        assert "example" in examples.lower()
        assert "path" in examples
        assert "content" in examples
    
    def test_generate_permissions_notice(self):
        """Test generating permissions notice"""
        agent_permissions = ["filesystem", "github"]
        
        notice = self.generator.generate_permissions_notice(agent_permissions)
        
        assert notice is not None
        assert "permissions" in notice.lower()
        assert "filesystem" in notice
        assert "github" in notice
        assert "sandboxed" in notice.lower()


@pytest.mark.mcp
@pytest.mark.unit
class TestMCPErrorHandler:
    """Test MCPErrorHandler functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.handler = MCPErrorHandler()
        
    def test_handle_connection_error(self):
        """Test handling connection errors"""
        error = ConnectionError("Failed to connect to MCP server")
        
        result = self.handler.handle_error(error, "connection")
        
        assert result["error_type"] == "connection"
        assert result["recoverable"] is True
        assert result["retry_after"] > 0
        assert "Failed to connect" in result["message"]
    
    def test_handle_tool_execution_error(self):
        """Test handling tool execution errors"""
        error = MCPError("Tool execution failed: permission denied")
        
        result = self.handler.handle_error(error, "tool_execution")
        
        assert result["error_type"] == "tool_execution"
        assert result["recoverable"] is False  # Permission errors typically not recoverable
        assert "permission denied" in result["message"]
    
    def test_handle_timeout_error(self):
        """Test handling timeout errors"""
        error = TimeoutError("MCP server response timeout")
        
        result = self.handler.handle_error(error, "timeout")
        
        assert result["error_type"] == "timeout"
        assert result["recoverable"] is True
        assert result["retry_after"] > 0
        assert "timeout" in result["message"].lower()
    
    def test_get_recovery_suggestions(self):
        """Test getting recovery suggestions"""
        connection_suggestions = self.handler.get_recovery_suggestions("connection")
        assert len(connection_suggestions) > 0
        assert any("restart" in suggestion.lower() for suggestion in connection_suggestions)
        
        permission_suggestions = self.handler.get_recovery_suggestions("permission")
        assert len(permission_suggestions) > 0
        assert any("permission" in suggestion.lower() for suggestion in permission_suggestions)
    
    def test_should_retry_operation(self):
        """Test retry decision logic"""
        # Recoverable errors should be retryable
        assert self.handler.should_retry_operation("connection", attempt=1) is True
        assert self.handler.should_retry_operation("timeout", attempt=2) is True
        
        # Non-recoverable errors should not be retryable
        assert self.handler.should_retry_operation("permission", attempt=1) is False
        assert self.handler.should_retry_operation("invalid_tool", attempt=1) is False
        
        # Max retries exceeded
        assert self.handler.should_retry_operation("connection", attempt=5) is False


@pytest.mark.mcp
@pytest.mark.unit
class TestMCPMetricsCollector:
    """Test MCPMetricsCollector functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.collector = MCPMetricsCollector(base_path=self.temp_dir)
        
    def teardown_method(self):
        """Clean up test files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_record_tool_execution(self):
        """Test recording tool execution metrics"""
        self.collector.record_tool_execution(
            agent_id="backend_developer",
            tool_name="filesystem_read",
            success=True,
            execution_time=0.150,
            parameters={"path": "/src/api.py"}
        )
        
        metrics = self.collector.get_metrics()
        
        assert metrics["total_executions"] == 1
        assert metrics["successful_executions"] == 1
        assert metrics["failed_executions"] == 0
        assert "filesystem_read" in metrics["tool_usage"]
        assert metrics["tool_usage"]["filesystem_read"]["count"] == 1
    
    def test_record_connection_event(self):
        """Test recording connection events"""
        self.collector.record_connection_event(
            server_name="filesystem",
            event_type="connect",
            success=True,
            duration=0.500
        )
        
        self.collector.record_connection_event(
            server_name="github", 
            event_type="disconnect",
            success=True,
            duration=0.100
        )
        
        metrics = self.collector.get_metrics()
        
        assert metrics["connection_events"] == 2
        assert "filesystem" in metrics["server_connections"]
        assert "github" in metrics["server_connections"]
    
    def test_get_performance_stats(self):
        """Test getting performance statistics"""
        # Record multiple executions
        execution_times = [0.100, 0.150, 0.200, 0.125, 0.175]
        
        for i, time in enumerate(execution_times):
            self.collector.record_tool_execution(
                agent_id="test_agent",
                tool_name="test_tool",
                success=True,
                execution_time=time
            )
        
        stats = self.collector.get_performance_stats()
        
        assert stats["average_execution_time"] == sum(execution_times) / len(execution_times)
        assert stats["min_execution_time"] == min(execution_times)
        assert stats["max_execution_time"] == max(execution_times)
        assert stats["total_executions"] == len(execution_times)
    
    def test_get_agent_usage_report(self):
        """Test getting agent usage report"""
        # Record usage for multiple agents
        agents_data = [
            ("backend_developer", "filesystem_read", True),
            ("backend_developer", "filesystem_write", True),
            ("frontend_developer", "filesystem_read", True),
            ("frontend_developer", "github_create_repo", False)
        ]
        
        for agent_id, tool_name, success in agents_data:
            self.collector.record_tool_execution(
                agent_id=agent_id,
                tool_name=tool_name,
                success=success,
                execution_time=0.100
            )
        
        report = self.collector.get_agent_usage_report()
        
        assert "backend_developer" in report
        assert "frontend_developer" in report
        assert report["backend_developer"]["total_executions"] == 2
        assert report["backend_developer"]["successful_executions"] == 2
        assert report["frontend_developer"]["total_executions"] == 2
        assert report["frontend_developer"]["successful_executions"] == 1
    
    def test_export_metrics_data(self):
        """Test exporting metrics data"""
        # Record some sample data
        self.collector.record_tool_execution(
            agent_id="test_agent",
            tool_name="test_tool",
            success=True,
            execution_time=0.100
        )
        
        # Export data
        export_data = self.collector.export_metrics_data()
        
        assert "metrics" in export_data
        assert "executions" in export_data
        assert "connections" in export_data
        assert "export_timestamp" in export_data
        assert export_data["metrics"]["total_executions"] == 1


@pytest.mark.mcp
@pytest.mark.integration
class TestMCPIntegration:
    """Integration tests for MCP system components"""
    
    def setup_method(self):
        """Set up integration test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create mock MCP client
        self.mock_client = Mock()
        self.mock_client.connected = True
        self.mock_client.list_tools = AsyncMock()
        self.mock_client.call_tool = AsyncMock()
        
        # Initialize components
        self.bridge = AgentMCPBridge(self.mock_client)
        self.generator = MCPToolsPromptGenerator()
        self.error_handler = MCPErrorHandler()
        self.metrics_collector = MCPMetricsCollector(base_path=self.temp_dir)
        
    def teardown_method(self):
        """Clean up test files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_full_tool_execution_workflow(self):
        """Test complete tool execution workflow"""
        # Setup mock responses
        self.mock_client.list_tools.return_value = [
            {
                "name": "filesystem_read",
                "description": "Read file content", 
                "parameters": {"path": {"type": "string", "required": True}}
            }
        ]
        
        self.mock_client.call_tool.return_value = {
            "success": True,
            "result": "File content successfully read"
        }
        
        # Execute workflow
        with patch.object(self.bridge, '_validate_agent_permission', return_value=True):
            # Get available tools
            tools = await self.bridge.get_available_tools_for_agent("backend_developer")
            assert len(tools) == 1
            
            # Generate prompt with tools
            prompt = self.bridge.generate_tools_prompt("backend_developer")
            assert "filesystem_read" in prompt
            
            # Execute tool
            result = await self.bridge.execute_tool_for_agent(
                agent_id="backend_developer",
                tool_name="filesystem_read",
                parameters={"path": "/src/api.py"}
            )
            
            assert result["success"] is True
            
            # Record metrics
            self.metrics_collector.record_tool_execution(
                agent_id="backend_developer",
                tool_name="filesystem_read",
                success=True,
                execution_time=0.100
            )
            
            # Verify metrics
            metrics = self.metrics_collector.get_metrics()
            assert metrics["total_executions"] == 1
            assert metrics["successful_executions"] == 1
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self):
        """Test error handling in MCP workflow"""
        # Setup mock error
        self.mock_client.call_tool.side_effect = Exception("Connection lost")
        
        with patch.object(self.bridge, '_validate_agent_permission', return_value=True):
            # Execute tool (should fail)
            result = await self.bridge.execute_tool_for_agent(
                agent_id="backend_developer",
                tool_name="filesystem_read",
                parameters={"path": "/test.py"}
            )
            
            assert result["success"] is False
            assert "error" in result
            
            # Handle error
            error_result = self.error_handler.handle_error(
                Exception("Connection lost"),
                "connection"
            )
            
            assert error_result["error_type"] == "connection"
            assert error_result["recoverable"] is True
            
            # Record failed execution
            self.metrics_collector.record_tool_execution(
                agent_id="backend_developer",
                tool_name="filesystem_read", 
                success=False,
                execution_time=0.050
            )
            
            # Verify metrics include failure
            metrics = self.metrics_collector.get_metrics()
            assert metrics["total_executions"] == 1
            assert metrics["failed_executions"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])