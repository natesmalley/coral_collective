#!/usr/bin/env python3
"""
Test script for the MCP Client implementation
Tests core functionality without requiring actual MCP servers
"""

import asyncio
import json
import os
import tempfile
import unittest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from mcp_client import (
    MCPClient, MCPConnection, MCPTransport, MCPMessage, 
    MCPServer, AgentMCPInterface, ConnectionStats
)


class TestMCPMessage(unittest.TestCase):
    """Test MCP message serialization and deserialization"""
    
    def test_message_creation(self):
        """Test creating MCP messages"""
        msg = MCPMessage(
            id="test-123",
            method="tools/list",
            params={"test": "value"}
        )
        
        self.assertEqual(msg.jsonrpc, "2.0")
        self.assertEqual(msg.id, "test-123")
        self.assertEqual(msg.method, "tools/list")
        self.assertEqual(msg.params, {"test": "value"})
    
    def test_message_serialization(self):
        """Test message to_dict conversion"""
        msg = MCPMessage(
            id="test-123",
            method="tools/call",
            params={"name": "test_tool", "arguments": {}}
        )
        
        expected = {
            "jsonrpc": "2.0",
            "id": "test-123",
            "method": "tools/call",
            "params": {"name": "test_tool", "arguments": {}}
        }
        
        self.assertEqual(msg.to_dict(), expected)
    
    def test_message_deserialization(self):
        """Test message from_dict creation"""
        data = {
            "jsonrpc": "2.0",
            "id": "response-123",
            "result": {"tools": []}
        }
        
        msg = MCPMessage.from_dict(data)
        
        self.assertEqual(msg.jsonrpc, "2.0")
        self.assertEqual(msg.id, "response-123")
        self.assertEqual(msg.result, {"tools": []})
        self.assertIsNone(msg.method)
        self.assertIsNone(msg.params)


class TestMCPClient(unittest.TestCase):
    """Test MCP Client functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary config file
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"
        
        # Test configuration
        test_config = {
            "mcp_servers": {
                "test_server": {
                    "enabled": True,
                    "command": "echo",
                    "args": ["test"],
                    "env": {"TEST_VAR": "test_value"},
                    "permissions": ["read", "write"],
                    "features": ["testing"],
                    "agents": ["backend_developer"]
                },
                "disabled_server": {
                    "enabled": False,
                    "command": "disabled",
                    "args": []
                }
            },
            "agent_permissions": {
                "backend_developer": {
                    "servers": ["test_server"],
                    "max_tokens_per_operation": 25000
                },
                "frontend_developer": {
                    "servers": ["test_server"],
                    "max_tokens_per_operation": 20000
                }
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_client_initialization(self):
        """Test client loads configuration correctly"""
        client = MCPClient(str(self.config_path))
        
        self.assertEqual(len(client.servers), 1)  # Only enabled server
        self.assertIn("test_server", client.servers)
        self.assertNotIn("disabled_server", client.servers)
        
        server = client.servers["test_server"]
        self.assertEqual(server.name, "test_server")
        self.assertEqual(server.command, "echo")
        self.assertEqual(server.args, ["test"])
        self.assertEqual(server.env, {"TEST_VAR": "test_value"})
        self.assertEqual(server.permissions, ["read", "write"])
        self.assertTrue(server.enabled)
    
    def test_agent_permissions(self):
        """Test agent permission checking"""
        client = MCPClient(str(self.config_path))
        
        # Test valid permissions
        self.assertTrue(client.check_agent_permissions("backend_developer", "test_server"))
        self.assertTrue(client.check_agent_permissions("frontend_developer", "test_server"))
        
        # Test invalid permissions
        self.assertFalse(client.check_agent_permissions("qa_testing", "test_server"))
        self.assertFalse(client.check_agent_permissions("backend_developer", "nonexistent_server"))
    
    def test_get_tools_for_agent(self):
        """Test getting tools for specific agents"""
        client = MCPClient(str(self.config_path))
        
        backend_tools = client.get_tools_for_agent("backend_developer")
        self.assertIn("test_server", backend_tools)
        self.assertEqual(backend_tools["test_server"], ["read", "write"])
        
        invalid_tools = client.get_tools_for_agent("nonexistent_agent")
        self.assertEqual(invalid_tools, {})
    
    def test_server_info(self):
        """Test getting server information"""
        client = MCPClient(str(self.config_path))
        
        info = client.get_server_info("test_server")
        self.assertIsNotNone(info)
        self.assertEqual(info["name"], "test_server")
        self.assertEqual(info["permissions"], ["read", "write"])
        self.assertEqual(info["features"], ["testing"])
        
        # Test nonexistent server
        info = client.get_server_info("nonexistent")
        self.assertIsNone(info)


class MockAsyncProcess:
    """Mock asyncio subprocess for testing"""
    
    def __init__(self):
        self.stdin = AsyncMock()
        self.stdout = AsyncMock()
        self.stderr = AsyncMock()
        self.returncode = 0
        
        # Configure stdin
        self.stdin.write = AsyncMock()
        self.stdin.drain = AsyncMock()
        self.stdin.close = Mock()
        self.stdin.wait_closed = AsyncMock()
        self.stdin.is_closing = Mock(return_value=False)
        
        # Configure stdout for reading JSON responses
        self.stdout.readline = AsyncMock()
    
    async def wait(self):
        """Mock process wait"""
        return self.returncode
    
    def terminate(self):
        """Mock process terminate"""
        pass
    
    def kill(self):
        """Mock process kill"""
        pass


class TestMCPIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for MCP client"""
    
    async def test_agent_interface_creation(self):
        """Test creating agent interface"""
        # Mock the config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_config = {
                "mcp_servers": {
                    "filesystem": {
                        "enabled": True,
                        "command": "npx",
                        "args": ["@modelcontextprotocol/server-filesystem"],
                        "permissions": ["read", "write"]
                    }
                },
                "agent_permissions": {
                    "backend_developer": {
                        "servers": ["filesystem"]
                    }
                }
            }
            json.dump(test_config, f)
            config_path = f.name
        
        try:
            client = MCPClient(config_path)
            interface = AgentMCPInterface("backend_developer", client)
            
            self.assertEqual(interface.agent_type, "backend_developer")
            self.assertIsNotNone(interface.client)
            self.assertIsNotNone(interface.session_id)
            
            # Test permission checking
            self.assertTrue(interface._check_permission("filesystem"))
            self.assertFalse(interface._check_permission("nonexistent"))
            
        finally:
            os.unlink(config_path)
    
    @patch('asyncio.create_subprocess_exec')
    async def test_connection_lifecycle(self, mock_subprocess):
        """Test connection establishment and cleanup"""
        # Setup mock process
        mock_process = MockAsyncProcess()
        mock_subprocess.return_value = mock_process
        
        # Mock successful initialization response
        init_response = {
            "jsonrpc": "2.0",
            "id": "test-init",
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}}
            }
        }
        
        mock_process.stdout.readline.side_effect = [
            json.dumps(init_response).encode() + b'\n',
            b''  # EOF
        ]
        
        # Create test server config
        server = MCPServer(
            name="test_server",
            command="echo",
            args=["test"],
            timeout=5,
            retry_attempts=1
        )
        
        connection = MCPConnection(server)
        
        # Test connection
        success = await connection.connect()
        self.assertTrue(success)
        self.assertTrue(connection.connected)
        
        # Verify subprocess was called correctly
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        self.assertEqual(call_args[0][0], "echo")  # command
        self.assertEqual(call_args[0][1], "test")   # first arg
        
        # Test disconnection
        await connection.disconnect()
        self.assertFalse(connection.connected)
    
    @patch('asyncio.create_subprocess_exec')
    async def test_tool_call_flow(self, mock_subprocess):
        """Test complete tool call flow"""
        # Setup mock process
        mock_process = MockAsyncProcess()
        mock_subprocess.return_value = mock_process
        
        # Mock responses for init and tool call
        init_response = {
            "jsonrpc": "2.0",
            "id": "init",
            "result": {"protocolVersion": "2024-11-05", "capabilities": {}}
        }
        
        tool_response = {
            "jsonrpc": "2.0",
            "id": "tool-call",
            "result": {"success": True, "output": "test result"}
        }
        
        mock_process.stdout.readline.side_effect = [
            json.dumps(init_response).encode() + b'\n',
            json.dumps(tool_response).encode() + b'\n'
        ]
        
        # Create connection
        server = MCPServer(name="test", command="echo", args=["test"])
        connection = MCPConnection(server)
        
        # Connect
        await connection.connect()
        
        # Mock the request handling to avoid the message handler loop
        original_send_request = connection._send_request
        
        async def mock_send_request(request, initialize=False):
            if initialize:
                return original_send_request.__func__(connection, request, initialize)
            else:
                # Return the tool response directly
                return MCPMessage.from_dict(tool_response)
        
        connection._send_request = mock_send_request
        
        # Call tool
        result = await connection.call_tool("test_tool", {"param": "value"})
        self.assertEqual(result, {"success": True, "output": "test result"})
        
        await connection.disconnect()


def run_performance_test():
    """Run performance test for MCP client"""
    import time
    import statistics
    
    async def performance_test():
        print("\n=== MCP Client Performance Test ===")
        
        # Create temporary config
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {
                "mcp_servers": {
                    "test": {
                        "enabled": True,
                        "command": "echo",
                        "args": ["test"],
                        "max_concurrent_requests": 10
                    }
                },
                "agent_permissions": {
                    "test_agent": {"servers": ["test"]}
                }
            }
            json.dump(config, f)
            config_path = f.name
        
        try:
            client = MCPClient(config_path)
            
            # Test configuration loading speed
            start = time.time()
            for _ in range(100):
                client.load_configuration()
            config_time = (time.time() - start) / 100
            
            print(f"Config loading time: {config_time*1000:.2f}ms per operation")
            
            # Test permission checking speed
            start = time.time()
            for _ in range(1000):
                client.check_agent_permissions("test_agent", "test")
            perm_time = (time.time() - start) / 1000
            
            print(f"Permission check time: {perm_time*1000:.3f}ms per operation")
            
            # Test message serialization speed
            msg = MCPMessage(
                id="test",
                method="tools/call",
                params={"name": "test", "arguments": {"data": "x" * 1000}}
            )
            
            times = []
            for _ in range(1000):
                start = time.time()
                msg.to_dict()
                times.append(time.time() - start)
            
            avg_time = statistics.mean(times)
            print(f"Message serialization: {avg_time*1000:.3f}ms avg, {max(times)*1000:.3f}ms max")
            
        finally:
            os.unlink(config_path)
    
    asyncio.run(performance_test())


if __name__ == "__main__":
    print("Running MCP Client Tests...")
    
    # Run unit tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
        
        # Run performance test if all tests pass
        try:
            run_performance_test()
        except Exception as e:
            print(f"Performance test failed: {e}")
    else:
        print("\n❌ Some tests failed!")
        exit(1)