"""
Unit tests for CoralCollective MCP Client

Tests cover:
1. MCPMessage creation and serialization
2. MCPServer configuration and validation
3. MCPTransport communication layer
4. MCPConnection management and lifecycle
5. MCPClient orchestration and connection pooling
6. AgentMCPInterface high-level operations
7. Error handling and circuit breaker functionality
8. Security and permission validation
9. Configuration loading and validation
10. Async protocol handling and JSON-RPC compliance
"""

import pytest
import json
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, mock_open
from typing import Dict, List, Any

# Import the modules under test
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

# Add mcp directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / 'mcp'))

from mcp_client import (
    MCPMessage,
    MCPServer,
    ConnectionStats,
    MCPTransport,
    MCPConnection,
    MCPClient,
    AgentMCPInterface
)


class TestMCPMessage:
    """Test MCPMessage data structure and serialization"""
    
    def test_mcp_message_creation_request(self):
        """Test creating a request MCPMessage"""
        
        message = MCPMessage(
            id="test-123",
            method="test_method",
            params={"arg1": "value1", "arg2": 42}
        )
        
        assert message.jsonrpc == "2.0"
        assert message.id == "test-123"
        assert message.method == "test_method"
        assert message.params == {"arg1": "value1", "arg2": 42}
        assert message.result is None
        assert message.error is None
        
    def test_mcp_message_creation_response(self):
        """Test creating a response MCPMessage"""
        
        message = MCPMessage(
            id="test-123",
            result={"status": "success", "data": [1, 2, 3]}
        )
        
        assert message.jsonrpc == "2.0"
        assert message.id == "test-123"
        assert message.method is None
        assert message.params is None
        assert message.result == {"status": "success", "data": [1, 2, 3]}
        assert message.error is None
        
    def test_mcp_message_creation_error(self):
        """Test creating an error MCPMessage"""
        
        message = MCPMessage(
            id="test-123",
            error={"code": -32600, "message": "Invalid Request"}
        )
        
        assert message.id == "test-123"
        assert message.error == {"code": -32600, "message": "Invalid Request"}
        assert message.result is None
        
    def test_mcp_message_to_dict(self):
        """Test MCPMessage serialization to dictionary"""
        
        message = MCPMessage(
            id="test-123",
            method="tools/list",
            params={}
        )
        
        result = message.to_dict()
        
        expected = {
            "jsonrpc": "2.0",
            "id": "test-123",
            "method": "tools/list",
            "params": {}
        }
        
        assert result == expected
        
    def test_mcp_message_to_dict_minimal(self):
        """Test MCPMessage serialization with minimal fields"""
        
        message = MCPMessage(method="ping")
        result = message.to_dict()
        
        # Should only include jsonrpc and method
        assert "jsonrpc" in result
        assert "method" in result
        assert "id" not in result
        assert "params" not in result
        assert "result" not in result
        assert "error" not in result
        
    def test_mcp_message_from_dict(self):
        """Test MCPMessage deserialization from dictionary"""
        
        data = {
            "jsonrpc": "2.0",
            "id": "test-456",
            "method": "tools/call",
            "params": {"name": "test_tool", "args": {"input": "test"}}
        }
        
        message = MCPMessage.from_dict(data)
        
        assert message.jsonrpc == "2.0"
        assert message.id == "test-456"
        assert message.method == "tools/call"
        assert message.params == {"name": "test_tool", "args": {"input": "test"}}
        
    def test_mcp_message_from_dict_defaults(self):
        """Test MCPMessage deserialization with missing fields"""
        
        data = {"method": "test"}
        message = MCPMessage.from_dict(data)
        
        assert message.jsonrpc == "2.0"  # Default value
        assert message.method == "test"
        assert message.id is None
        assert message.params is None


class TestMCPServer:
    """Test MCPServer configuration"""
    
    def test_mcp_server_creation_minimal(self):
        """Test MCPServer creation with minimal configuration"""
        
        server = MCPServer(
            name="test_server",
            command="node",
            args=["server.js"]
        )
        
        assert server.name == "test_server"
        assert server.command == "node"
        assert server.args == ["server.js"]
        assert server.env == {}
        assert server.enabled is True
        assert server.permissions == []
        assert server.timeout == 30
        assert server.retry_attempts == 3
        assert server.retry_delay == 1.0
        assert server.max_concurrent_requests == 10
        
    def test_mcp_server_creation_full(self):
        """Test MCPServer creation with full configuration"""
        
        server = MCPServer(
            name="full_server",
            command="python",
            args=["-m", "server"],
            env={"API_KEY": "secret", "DEBUG": "true"},
            enabled=True,
            permissions=["read", "write"],
            timeout=60,
            retry_attempts=5,
            retry_delay=2.0,
            max_concurrent_requests=20,
            health_check_interval=120,
            features=["filesystem", "database"],
            agents=["backend_developer", "frontend_developer"]
        )
        
        assert server.env == {"API_KEY": "secret", "DEBUG": "true"}
        assert server.permissions == ["read", "write"]
        assert server.timeout == 60
        assert server.retry_attempts == 5
        assert server.retry_delay == 2.0
        assert server.max_concurrent_requests == 20
        assert server.health_check_interval == 120
        assert server.features == ["filesystem", "database"]
        assert server.agents == ["backend_developer", "frontend_developer"]


class TestConnectionStats:
    """Test ConnectionStats tracking"""
    
    def test_connection_stats_creation(self):
        """Test ConnectionStats creation with defaults"""
        
        stats = ConnectionStats()
        
        assert isinstance(stats.connect_time, datetime)
        assert stats.requests_sent == 0
        assert stats.responses_received == 0
        assert stats.errors == 0
        assert isinstance(stats.last_activity, datetime)
        assert stats.last_error is None
        assert stats.uptime_seconds == 0.0
        
    def test_connection_stats_tracking(self):
        """Test ConnectionStats tracking updates"""
        
        stats = ConnectionStats()
        
        # Simulate activity
        stats.requests_sent += 1
        stats.responses_received += 1
        stats.errors += 1
        stats.last_error = "Connection timeout"
        stats.last_activity = datetime.now(timezone.utc)
        
        assert stats.requests_sent == 1
        assert stats.responses_received == 1
        assert stats.errors == 1
        assert stats.last_error == "Connection timeout"


@pytest.mark.asyncio
class TestMCPTransport:
    """Test MCPTransport communication layer"""
    
    async def test_transport_creation(self):
        """Test MCPTransport creation"""
        
        mock_process = AsyncMock()
        transport = MCPTransport("test_server", mock_process)
        
        assert transport.server_name == "test_server"
        assert transport.process == mock_process
        assert transport.connected is True
        assert transport.message_buffer == ""
        assert isinstance(transport.stats, ConnectionStats)
        
    async def test_send_message_success(self):
        """Test successful message sending"""
        
        mock_process = AsyncMock()
        mock_stdin = AsyncMock()
        mock_process.stdin = mock_stdin
        mock_stdin.is_closing.return_value = False
        
        transport = MCPTransport("test_server", mock_process)
        
        message = MCPMessage(method="ping")
        await transport.send_message(message)
        
        # Verify message was written and drained
        mock_stdin.write.assert_called_once()
        mock_stdin.drain.assert_called_once()
        
        # Check that stats were updated
        assert transport.stats.requests_sent == 1
        
    async def test_send_message_not_connected(self):
        """Test sending message when not connected"""
        
        mock_process = AsyncMock()
        transport = MCPTransport("test_server", mock_process)
        transport.connected = False
        
        message = MCPMessage(method="ping")
        
        with pytest.raises(ConnectionError, match="Transport to test_server is not connected"):
            await transport.send_message(message)
            
    async def test_send_message_stdin_closed(self):
        """Test sending message when stdin is closed"""
        
        mock_process = AsyncMock()
        mock_stdin = AsyncMock()
        mock_process.stdin = mock_stdin
        mock_stdin.is_closing.return_value = True
        
        transport = MCPTransport("test_server", mock_process)
        
        message = MCPMessage(method="ping")
        
        with pytest.raises(ConnectionError):
            await transport.send_message(message)
            
    async def test_read_message_success(self):
        """Test successful message reading"""
        
        mock_process = AsyncMock()
        mock_stdout = AsyncMock()
        mock_process.stdout = mock_stdout
        
        # Mock reading a valid JSON response
        json_response = json.dumps({
            "jsonrpc": "2.0",
            "id": "test-123",
            "result": {"status": "ok"}
        })
        mock_stdout.readline.return_value = json_response.encode('utf-8') + b'\n'
        
        transport = MCPTransport("test_server", mock_process)
        
        message = await transport.read_message(timeout=5.0)
        
        assert message.jsonrpc == "2.0"
        assert message.id == "test-123"
        assert message.result == {"status": "ok"}
        assert transport.stats.responses_received == 1
        
    async def test_read_message_timeout(self):
        """Test reading message with timeout"""
        
        mock_process = AsyncMock()
        mock_stdout = AsyncMock()
        mock_process.stdout = mock_stdout
        
        # Mock timeout on readline
        mock_stdout.readline.side_effect = asyncio.TimeoutError()
        
        transport = MCPTransport("test_server", mock_process)
        
        with pytest.raises(TimeoutError, match="Timeout reading from test_server"):
            await transport.read_message(timeout=1.0)
            
        assert transport.stats.errors == 1
        assert "timeout" in transport.stats.last_error.lower()
        
    async def test_read_message_connection_closed(self):
        """Test reading when connection is closed"""
        
        mock_process = AsyncMock()
        mock_stdout = AsyncMock()
        mock_process.stdout = mock_stdout
        mock_stdout.readline.return_value = b''  # Empty indicates closed
        
        transport = MCPTransport("test_server", mock_process)
        
        with pytest.raises(ConnectionError, match="Connection to test_server closed unexpectedly"):
            await transport.read_message()
            
    async def test_read_message_invalid_json(self):
        """Test reading invalid JSON"""
        
        mock_process = AsyncMock()
        mock_stdout = AsyncMock()
        mock_process.stdout = mock_stdout
        mock_stdout.readline.return_value = b'invalid json\n'
        
        transport = MCPTransport("test_server", mock_process)
        
        with pytest.raises(ValueError, match="Invalid JSON received"):
            await transport.read_message()
            
        assert transport.stats.errors == 1
        
    async def test_close_transport(self):
        """Test transport close operation"""
        
        mock_process = AsyncMock()
        mock_stdin = AsyncMock()
        mock_process.stdin = mock_stdin
        mock_stdin.is_closing.return_value = False
        
        transport = MCPTransport("test_server", mock_process)
        
        await transport.close()
        
        assert transport.connected is False
        mock_stdin.close.assert_called_once()
        mock_stdin.wait_closed.assert_called_once()
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called()


@pytest.mark.asyncio
class TestMCPConnection:
    """Test MCPConnection management"""
    
    def setup_method(self):
        """Set up test data"""
        self.mock_server = MCPServer(
            name="test_server",
            command="node",
            args=["server.js"],
            timeout=5,
            retry_attempts=2,
            retry_delay=0.1
        )
        
    async def test_connection_creation(self):
        """Test MCPConnection creation"""
        
        connection = MCPConnection(self.mock_server)
        
        assert connection.server == self.mock_server
        assert connection.transport is None
        assert connection.pending_requests == {}
        assert connection.connected is False
        assert connection.tools_cache is None
        assert connection.circuit_breaker_failures == 0
        
    async def test_connect_success(self):
        """Test successful connection"""
        
        connection = MCPConnection(self.mock_server)
        
        with patch('mcp_client.asyncio.create_subprocess_exec') as mock_create_subprocess:
            mock_process = AsyncMock()
            mock_stdin = AsyncMock()
            mock_stdout = AsyncMock()
            
            mock_process.stdin = mock_stdin
            mock_process.stdout = mock_stdout
            mock_stdin.is_closing.return_value = False
            
            # Mock initialization response
            init_response = json.dumps({
                "jsonrpc": "2.0",
                "id": "init-id",
                "result": {"capabilities": {"tools": {}}}
            })
            mock_stdout.readline.return_value = init_response.encode('utf-8') + b'\n'
            
            mock_create_subprocess.return_value = mock_process
            
            # Mock initialization methods
            with patch.object(connection, '_initialize_connection', new_callable=AsyncMock), \
                 patch.object(connection, '_start_background_tasks'):
                
                success = await connection.connect()
                
                assert success is True
                assert connection.connected is True
                assert connection.transport is not None
                assert connection.circuit_breaker_failures == 0
                
    async def test_connect_failure_all_attempts(self):
        """Test connection failure after all retry attempts"""
        
        connection = MCPConnection(self.mock_server)
        
        with patch('mcp_client.asyncio.create_subprocess_exec', side_effect=Exception("Connection failed")):
            success = await connection.connect()
            
            assert success is False
            assert connection.connected is False
            assert connection.circuit_breaker_failures == 1
            
    async def test_connect_circuit_breaker_open(self):
        """Test connection when circuit breaker is open"""
        
        connection = MCPConnection(self.mock_server)
        
        # Set circuit breaker to open state
        connection.circuit_breaker_failures = 10
        connection.circuit_breaker_open_until = datetime.now(timezone.utc) + timedelta(minutes=1)
        
        success = await connection.connect()
        
        assert success is False
        
    async def test_send_request_and_response(self):
        """Test sending request and receiving response"""
        
        connection = MCPConnection(self.mock_server)
        connection.connected = True
        
        # Mock transport
        mock_transport = AsyncMock()
        connection.transport = mock_transport
        
        request = MCPMessage(method="test", params={})
        
        # Create a future that resolves immediately with response
        response = MCPMessage(id=request.id, result={"status": "ok"})
        response_future = asyncio.Future()
        response_future.set_result(response)
        
        with patch.object(asyncio, 'wait_for', return_value=response):
            result = await connection._send_request(request)
            
            assert result == response
            mock_transport.send_message.assert_called_once_with(request)
            
    async def test_send_request_timeout(self):
        """Test request timeout"""
        
        connection = MCPConnection(self.mock_server)
        connection.connected = True
        connection.transport = AsyncMock()
        
        request = MCPMessage(method="test")
        
        with patch.object(asyncio, 'wait_for', side_effect=asyncio.TimeoutError()):
            with pytest.raises(asyncio.TimeoutError):
                await connection._send_request(request)
                
    async def test_list_tools_with_cache(self):
        """Test listing tools with cache"""
        
        connection = MCPConnection(self.mock_server)
        connection.connected = True
        
        # Set up cache
        cached_tools = [{"name": "test_tool", "description": "Test tool"}]
        connection.tools_cache = cached_tools
        connection.cache_timestamp = datetime.now(timezone.utc)
        
        tools = await connection.list_tools(use_cache=True)
        
        assert tools == cached_tools
        
    async def test_list_tools_no_cache(self):
        """Test listing tools without cache"""
        
        connection = MCPConnection(self.mock_server)
        connection.connected = True
        
        mock_transport = AsyncMock()
        connection.transport = mock_transport
        
        # Mock successful response
        tools_data = [{"name": "filesystem_read"}, {"name": "filesystem_write"}]
        response = MCPMessage(result={"tools": tools_data})
        
        with patch.object(connection, '_send_request', return_value=response), \
             patch('mcp_client.uuid.uuid4', return_value=Mock()):
            
            tools = await connection.list_tools(use_cache=False)
            
            assert tools == tools_data
            assert connection.tools_cache == tools_data
            assert connection.cache_timestamp is not None
            
    async def test_call_tool_success(self):
        """Test successful tool call"""
        
        connection = MCPConnection(self.mock_server)
        connection.connected = True
        
        response = MCPMessage(result={"output": "Tool executed successfully"})
        
        with patch.object(connection, '_send_request', return_value=response), \
             patch('mcp_client.uuid.uuid4', return_value=Mock()):
            
            result = await connection.call_tool("test_tool", {"input": "test"})
            
            assert result == {"output": "Tool executed successfully"}
            
    async def test_call_tool_error(self):
        """Test tool call with error response"""
        
        connection = MCPConnection(self.mock_server)
        connection.connected = True
        
        response = MCPMessage(error={"code": -32602, "message": "Invalid params"})
        
        with patch.object(connection, '_send_request', return_value=response):
            with pytest.raises(Exception, match="Tool execution error"):
                await connection.call_tool("test_tool", {"input": "invalid"})
                
    async def test_disconnect(self):
        """Test connection disconnect"""
        
        connection = MCPConnection(self.mock_server)
        connection.connected = True
        
        # Set up mocks
        mock_transport = AsyncMock()
        connection.transport = mock_transport
        
        mock_health_task = AsyncMock()
        connection.health_check_task = mock_health_task
        
        # Add pending request
        future = asyncio.Future()
        connection.pending_requests['test-id'] = future
        
        await connection.disconnect()
        
        assert connection.connected is False
        assert len(connection.pending_requests) == 0
        mock_transport.close.assert_called_once()
        connection.transport is None


@pytest.mark.asyncio
class TestMCPClient:
    """Test MCPClient orchestration"""
    
    def setup_method(self):
        """Set up test configuration"""
        self.test_config = {
            "mcp_servers": {
                "filesystem": {
                    "command": "node",
                    "args": ["filesystem-server.js"],
                    "enabled": True,
                    "permissions": ["read", "write"],
                    "features": ["file_operations"]
                },
                "github": {
                    "command": "python",
                    "args": ["-m", "github_server"],
                    "enabled": True,
                    "permissions": ["repo_access"],
                    "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}
                },
                "disabled_server": {
                    "command": "echo",
                    "args": ["disabled"],
                    "enabled": False
                }
            },
            "agent_permissions": {
                "backend_developer": {
                    "servers": ["filesystem", "github"]
                },
                "frontend_developer": {
                    "servers": ["filesystem"]
                }
            }
        }
        
    def test_client_creation(self):
        """Test MCPClient creation"""
        
        with patch.object(MCPClient, 'load_configuration'):
            client = MCPClient("test_config.yaml")
            
            assert client.config_path == Path("test_config.yaml")
            assert client.servers == {}
            assert client.connections == {}
            assert client.initialized is False
            
    def test_load_configuration_yaml(self):
        """Test loading YAML configuration"""
        
        mock_yaml_content = json.dumps(self.test_config)  # JSON is valid YAML
        
        with patch('builtins.open', mock_open(read_data=mock_yaml_content)), \
             patch('mcp_client.yaml') as mock_yaml, \
             patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.suffix', '.yaml'):
            
            mock_yaml.safe_load.return_value = self.test_config
            
            client = MCPClient("test_config.yaml")
            
            assert len(client.servers) == 2  # Only enabled servers
            assert "filesystem" in client.servers
            assert "github" in client.servers
            assert "disabled_server" not in client.servers
            
    def test_load_configuration_json(self):
        """Test loading JSON configuration"""
        
        with patch('builtins.open', mock_open(read_data=json.dumps(self.test_config))), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.suffix', '.json'):
            
            client = MCPClient("test_config.json")
            
            assert len(client.servers) == 2
            assert client.servers["filesystem"].name == "filesystem"
            assert client.servers["github"].env == {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}
            
    def test_load_configuration_file_not_found(self):
        """Test handling missing configuration file"""
        
        with patch('pathlib.Path.exists', return_value=False):
            client = MCPClient("nonexistent.yaml")
            
            assert client.servers == {}
            
    async def test_initialize(self):
        """Test client initialization"""
        
        with patch.object(MCPClient, 'load_configuration'):
            client = MCPClient()
            client.servers = {"test_server": MCPServer("test_server", "echo", [])}
            
            await client.initialize()
            
            assert client.initialized is True
            assert "test_server" in client.connections
            
    async def test_connect_server_success(self):
        """Test successful server connection"""
        
        client = MCPClient()
        client.initialized = True
        
        mock_connection = AsyncMock()
        mock_connection.connected = False
        mock_connection.connect.return_value = True
        
        client.connections = {"test_server": mock_connection}
        
        with patch('mcp_client.asyncio.create_task'):
            success = await client.connect_server("test_server")
            
            assert success is True
            mock_connection.connect.assert_called_once()
            
    async def test_connect_server_not_found(self):
        """Test connecting to non-existent server"""
        
        client = MCPClient()
        client.initialized = True
        client.connections = {}
        
        success = await client.connect_server("nonexistent_server")
        
        assert success is False
        
    async def test_list_tools(self):
        """Test listing tools from server"""
        
        client = MCPClient()
        
        mock_connection = AsyncMock()
        mock_connection.list_tools.return_value = [{"name": "test_tool"}]
        
        client.connections = {"test_server": mock_connection}
        
        with patch.object(client, 'connect_server', return_value=True):
            tools = await client.list_tools("test_server")
            
            assert tools == [{"name": "test_tool"}]
            mock_connection.list_tools.assert_called_once()
            
    async def test_call_tool(self):
        """Test calling tool on server"""
        
        client = MCPClient()
        
        mock_connection = AsyncMock()
        mock_connection.call_tool.return_value = {"result": "success"}
        
        client.connections = {"test_server": mock_connection}
        
        with patch.object(client, 'connect_server', return_value=True):
            result = await client.call_tool("test_server", "test_tool", {"arg": "value"})
            
            assert result == {"result": "success"}
            mock_connection.call_tool.assert_called_once_with("test_tool", {"arg": "value"})
            
    async def test_call_tool_connection_failed(self):
        """Test calling tool when connection fails"""
        
        client = MCPClient()
        
        with patch.object(client, 'connect_server', return_value=False):
            with pytest.raises(ConnectionError, match="Could not connect"):
                await client.call_tool("test_server", "test_tool", {})
                
    def test_check_agent_permissions_allowed(self):
        """Test agent permission checking - allowed"""
        
        client = MCPClient()
        client.config = self.test_config
        
        allowed = client.check_agent_permissions("backend_developer", "filesystem")
        assert allowed is True
        
    def test_check_agent_permissions_denied(self):
        """Test agent permission checking - denied"""
        
        client = MCPClient()
        client.config = self.test_config
        
        allowed = client.check_agent_permissions("frontend_developer", "github")
        assert allowed is False
        
    def test_get_tools_for_agent(self):
        """Test getting available tools for agent"""
        
        client = MCPClient()
        client.config = self.test_config
        client.servers = {
            "filesystem": MCPServer("filesystem", "node", [], permissions=["read", "write"]),
            "github": MCPServer("github", "python", [], permissions=["repo_access"])
        }
        
        tools = client.get_tools_for_agent("backend_developer")
        
        assert "filesystem" in tools
        assert "github" in tools
        assert tools["filesystem"] == ["read", "write"]
        assert tools["github"] == ["repo_access"]
        
    def test_get_available_servers(self):
        """Test getting available servers list"""
        
        client = MCPClient()
        client.servers = {
            "server1": MCPServer("server1", "cmd1", []),
            "server2": MCPServer("server2", "cmd2", [])
        }
        
        servers = client.get_available_servers()
        
        assert set(servers) == {"server1", "server2"}
        
    def test_get_server_info(self):
        """Test getting server information"""
        
        client = MCPClient()
        server = MCPServer(
            "test_server", 
            "node", 
            [],
            permissions=["read"],
            features=["filesystem"],
            agents=["backend_dev"]
        )
        client.servers = {"test_server": server}
        
        mock_connection = Mock()
        mock_connection.get_stats.return_value = {"connected": True, "requests": 5}
        client.connections = {"test_server": mock_connection}
        
        info = client.get_server_info("test_server")
        
        assert info["name"] == "test_server"
        assert info["permissions"] == ["read"]
        assert info["features"] == ["filesystem"]
        assert info["agents"] == ["backend_dev"]
        assert info["connection_stats"]["connected"] is True
        
    def test_get_server_info_not_found(self):
        """Test getting info for non-existent server"""
        
        client = MCPClient()
        client.servers = {}
        
        info = client.get_server_info("nonexistent")
        assert info is None
        
    async def test_shutdown(self):
        """Test client shutdown"""
        
        client = MCPClient()
        client.initialized = True
        
        mock_connection = AsyncMock()
        client.connections = {"test_server": mock_connection}
        
        with patch.object(client, 'disconnect_server', new_callable=AsyncMock) as mock_disconnect:
            await client.shutdown()
            
            mock_disconnect.assert_called_once_with("test_server")
            assert client.initialized is False


@pytest.mark.asyncio
class TestAgentMCPInterface:
    """Test AgentMCPInterface high-level operations"""
    
    def setup_method(self):
        """Set up test interface"""
        self.mock_client = AsyncMock()
        self.interface = AgentMCPInterface("backend_developer", self.mock_client)
        
    def test_interface_creation(self):
        """Test AgentMCPInterface creation"""
        
        interface = AgentMCPInterface("frontend_developer")
        
        assert interface.agent_type == "frontend_developer"
        assert interface.client is not None
        assert interface.session_id is not None
        
    def test_check_permission_allowed(self):
        """Test permission checking - allowed"""
        
        self.mock_client.check_agent_permissions.return_value = True
        
        allowed = self.interface._check_permission("filesystem")
        
        assert allowed is True
        self.mock_client.check_agent_permissions.assert_called_once_with("backend_developer", "filesystem")
        
    def test_check_permission_denied(self):
        """Test permission checking - denied"""
        
        self.mock_client.check_agent_permissions.return_value = False
        
        allowed = self.interface._check_permission("restricted_server")
        
        assert allowed is False
        
    async def test_filesystem_read_success(self):
        """Test successful filesystem read"""
        
        self.mock_client.check_agent_permissions.return_value = True
        self.mock_client.call_tool.return_value = {"content": "file content"}
        
        content = await self.interface.filesystem_read("/path/to/file.txt")
        
        assert content == "file content"
        self.mock_client.call_tool.assert_called_once_with(
            "filesystem", "read_file", {"path": "/path/to/file.txt"}
        )
        
    async def test_filesystem_read_permission_denied(self):
        """Test filesystem read with permission denied"""
        
        self.mock_client.check_agent_permissions.return_value = False
        
        content = await self.interface.filesystem_read("/path/to/file.txt")
        
        assert content is None
        self.mock_client.call_tool.assert_not_called()
        
    async def test_filesystem_write_success(self):
        """Test successful filesystem write"""
        
        self.mock_client.check_agent_permissions.return_value = True
        self.mock_client.call_tool.return_value = {"success": True}
        
        success = await self.interface.filesystem_write("/path/to/file.txt", "new content")
        
        assert success is True
        self.mock_client.call_tool.assert_called_once_with(
            "filesystem", "write_file", {"path": "/path/to/file.txt", "content": "new content"}
        )
        
    async def test_filesystem_list_success(self):
        """Test successful filesystem listing"""
        
        self.mock_client.check_agent_permissions.return_value = True
        self.mock_client.call_tool.return_value = {"files": ["file1.txt", "file2.py"]}
        
        files = await self.interface.filesystem_list("/path/to/directory")
        
        assert files == ["file1.txt", "file2.py"]
        
    async def test_github_create_issue_success(self):
        """Test successful GitHub issue creation"""
        
        self.mock_client.check_agent_permissions.return_value = True
        self.mock_client.call_tool.return_value = {"number": 123, "url": "https://github.com/repo/issues/123"}
        
        result = await self.interface.github_create_issue(
            "Bug report", "Description of bug", ["bug", "urgent"]
        )
        
        assert result["number"] == 123
        self.mock_client.call_tool.assert_called_once_with(
            "github", "create_issue", {
                "title": "Bug report",
                "body": "Description of bug",
                "labels": ["bug", "urgent"]
            }
        )
        
    async def test_database_query_success(self):
        """Test successful database query"""
        
        self.mock_client.check_agent_permissions.return_value = True
        self.mock_client.call_tool.return_value = {
            "rows": [{"id": 1, "name": "test"}, {"id": 2, "name": "test2"}]
        }
        
        rows = await self.interface.database_query(
            "SELECT * FROM users WHERE active = ?", [True]
        )
        
        assert len(rows) == 2
        assert rows[0]["name"] == "test"
        
    async def test_search_web_success(self):
        """Test successful web search"""
        
        self.mock_client.check_agent_permissions.return_value = True
        self.mock_client.call_tool.return_value = {
            "web": {
                "results": [
                    {"title": "React Tutorial", "url": "https://react.dev"},
                    {"title": "React Hooks", "url": "https://react.dev/hooks"}
                ]
            }
        }
        
        results = await self.interface.search_web("React tutorial", max_results=5)
        
        assert len(results) == 2
        assert results[0]["title"] == "React Tutorial"
        
    async def test_docker_run_success(self):
        """Test successful Docker container run"""
        
        self.mock_client.check_agent_permissions.return_value = True
        self.mock_client.call_tool.return_value = {"output": "Container executed successfully"}
        
        output = await self.interface.docker_run(
            "python:3.9", "python -c 'print(\"Hello World\")'", {"ENV_VAR": "value"}
        )
        
        assert output == "Container executed successfully"
        
    async def test_get_available_tools(self):
        """Test getting available tools for agent"""
        
        self.mock_client.get_tools_for_agent.return_value = {"filesystem": [], "github": []}
        self.mock_client.list_tools.side_effect = [
            [{"name": "read_file"}, {"name": "write_file"}],  # filesystem tools
            [{"name": "create_issue"}, {"name": "create_pr"}]  # github tools
        ]
        
        tools = await self.interface.get_available_tools()
        
        assert "filesystem" in tools
        assert "github" in tools
        assert len(tools["filesystem"]) == 2
        assert len(tools["github"]) == 2
        
    async def test_error_handling(self):
        """Test error handling in interface methods"""
        
        self.mock_client.check_agent_permissions.return_value = True
        self.mock_client.call_tool.side_effect = Exception("Server error")
        
        # Test that exceptions are handled gracefully
        content = await self.interface.filesystem_read("/path/to/file.txt")
        assert content is None
        
        success = await self.interface.filesystem_write("/path/to/file.txt", "content")
        assert success is False
        
        files = await self.interface.filesystem_list("/path")
        assert files == []


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_connection_stats_timezone_handling(self):
        """Test ConnectionStats handles timezones properly"""
        
        stats = ConnectionStats()
        
        # Should use UTC timezone
        assert stats.connect_time.tzinfo == timezone.utc
        assert stats.last_activity.tzinfo == timezone.utc
        
    def test_mcp_message_serialization_edge_cases(self):
        """Test MCPMessage handles edge cases in serialization"""
        
        # Test with None values
        message = MCPMessage()
        result = message.to_dict()
        
        # Should only include jsonrpc field
        assert list(result.keys()) == ["jsonrpc"]
        assert result["jsonrpc"] == "2.0"
        
    @pytest.mark.asyncio
    async def test_transport_error_recovery(self):
        """Test transport error recovery and stats tracking"""
        
        mock_process = AsyncMock()
        mock_stdin = AsyncMock()
        mock_process.stdin = mock_stdin
        
        transport = MCPTransport("test_server", mock_process)
        
        # Simulate send error
        mock_stdin.write.side_effect = Exception("Write failed")
        
        message = MCPMessage(method="test")
        
        with pytest.raises(Exception):
            await transport.send_message(message)
            
        # Error should be tracked
        assert transport.stats.errors == 1
        assert transport.stats.last_error == "Write failed"


# Integration test for complete MCP workflow
@pytest.mark.integration
@pytest.mark.asyncio
class TestMCPIntegration:
    """Integration tests for complete MCP workflow"""
    
    async def test_complete_mcp_workflow(self):
        """Test complete MCP workflow from client creation to tool execution"""
        
        config_data = {
            "mcp_servers": {
                "test_server": {
                    "command": "echo",
                    "args": ["test"],
                    "enabled": True,
                    "permissions": ["read", "write"]
                }
            },
            "agent_permissions": {
                "test_agent": {
                    "servers": ["test_server"]
                }
            }
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.suffix', '.json'):
            
            # 1. Create and initialize client
            client = MCPClient("test_config.json")
            
            assert len(client.servers) == 1
            assert "test_server" in client.servers
            
            # 2. Check permissions
            assert client.check_agent_permissions("test_agent", "test_server") is True
            assert client.check_agent_permissions("test_agent", "other_server") is False
            
            # 3. Get tools for agent
            tools = client.get_tools_for_agent("test_agent")
            assert "test_server" in tools
            assert tools["test_server"] == ["read", "write"]
            
            # 4. Test agent interface
            interface = AgentMCPInterface("test_agent", client)
            assert interface.agent_type == "test_agent"
            assert interface.client == client
            
            # 5. Check server info
            info = client.get_server_info("test_server")
            assert info is not None
            assert info["name"] == "test_server"
            assert info["permissions"] == ["read", "write"]