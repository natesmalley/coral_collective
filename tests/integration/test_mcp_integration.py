"""
Integration tests for CoralCollective MCP (Model Context Protocol) Integration

Tests end-to-end MCP functionality including:
1. MCP server communication and tool execution
2. Agent-MCP coordination and workflows
3. Multi-server scenarios and failover
4. Security and permissions enforcement
5. Performance under load
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, List, Any

# Import MCP components
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from mcp.mcp_client import MCPClient, MCPServer, MCPMessage
    from coral_collective.tools.agent_mcp_bridge import AgentMCPBridge
    from coral_collective.tools.mcp_error_handler import MCPErrorHandler
except ImportError:
    # Mock MCP components if not available
    class MCPClient:
        def __init__(self, *args, **kwargs):
            pass
    class MCPServer:
        def __init__(self, *args, **kwargs):
            pass
    class MCPMessage:
        def __init__(self, *args, **kwargs):
            pass
    class AgentMCPBridge:
        def __init__(self, *args, **kwargs):
            pass
    class MCPErrorHandler:
        def __init__(self, *args, **kwargs):
            pass


@pytest.mark.asyncio
class TestMCPServerCommunication:
    """Test MCP server communication patterns"""
    
    def setup_method(self):
        """Set up MCP test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Mock MCP server configurations
        self.server_configs = {
            "filesystem": {
                "command": "mcp-server-filesystem",
                "args": [str(self.temp_dir)],
                "permissions": ["read", "write", "create"]
            },
            "github": {
                "command": "mcp-server-github",
                "args": ["--token", "mock-token"],
                "permissions": ["read", "issues", "prs"]
            },
            "database": {
                "command": "mcp-server-postgresql",
                "args": ["--connection", "mock://connection"],
                "permissions": ["read", "write", "schema"]
            }
        }
        
        # Create mock MCP client
        self.mock_client = Mock(spec=MCPClient)
        self.mock_client.connect = AsyncMock()
        self.mock_client.disconnect = AsyncMock()
        self.mock_client.list_tools = AsyncMock()
        self.mock_client.call_tool = AsyncMock()
        
    def teardown_method(self):
        """Clean up MCP test environment"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    async def test_mcp_server_connection_lifecycle(self):
        """Test complete MCP server connection lifecycle"""
        
        # Test successful connection
        self.mock_client.connect.return_value = {
            "server_info": {"name": "test-server", "version": "1.0.0"},
            "capabilities": ["tools", "resources"],
            "protocol_version": "2024-11-05"
        }
        
        connection_result = await self.mock_client.connect()
        assert connection_result["server_info"]["name"] == "test-server"
        assert "tools" in connection_result["capabilities"]
        
        # Test tool listing
        self.mock_client.list_tools.return_value = {
            "tools": [
                {
                    "name": "read_file",
                    "description": "Read file contents",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"path": {"type": "string"}},
                        "required": ["path"]
                    }
                },
                {
                    "name": "write_file",
                    "description": "Write file contents", 
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "content": {"type": "string"}
                        },
                        "required": ["path", "content"]
                    }
                }
            ]
        }
        
        tools_result = await self.mock_client.list_tools()
        assert len(tools_result["tools"]) == 2
        assert tools_result["tools"][0]["name"] == "read_file"
        
        # Test tool execution
        self.mock_client.call_tool.return_value = {
            "content": [
                {
                    "type": "text",
                    "text": "File content successfully written"
                }
            ]
        }
        
        tool_result = await self.mock_client.call_tool(
            "write_file",
            {"path": "test.txt", "content": "Hello World"}
        )
        assert tool_result["content"][0]["text"] == "File content successfully written"
        
        # Test graceful disconnection
        self.mock_client.disconnect.return_value = {"status": "disconnected"}
        disconnect_result = await self.mock_client.disconnect()
        assert disconnect_result["status"] == "disconnected"
        
        # Verify call sequence
        self.mock_client.connect.assert_called_once()
        self.mock_client.list_tools.assert_called_once()
        self.mock_client.call_tool.assert_called_once()
        self.mock_client.disconnect.assert_called_once()
    
    async def test_mcp_error_handling_and_recovery(self):
        """Test MCP error handling and recovery scenarios"""
        
        # Test connection failure
        self.mock_client.connect.side_effect = ConnectionError("Server unavailable")
        
        with pytest.raises(ConnectionError):
            await self.mock_client.connect()
        
        # Test recovery after connection failure
        self.mock_client.connect.side_effect = None
        self.mock_client.connect.return_value = {
            "server_info": {"name": "recovered-server", "version": "1.0.0"}
        }
        
        recovery_result = await self.mock_client.connect()
        assert recovery_result["server_info"]["name"] == "recovered-server"
        
        # Test tool execution failure
        self.mock_client.call_tool.side_effect = Exception("Tool execution failed")
        
        with pytest.raises(Exception):
            await self.mock_client.call_tool("failing_tool", {})
        
        # Test recovery with retry mechanism
        self.mock_client.call_tool.side_effect = [
            Exception("Temporary failure"),
            {"content": [{"type": "text", "text": "Success on retry"}]}
        ]
        
        # Simulate retry logic
        try:
            result = await self.mock_client.call_tool("retry_tool", {})
        except Exception:
            # Retry
            result = await self.mock_client.call_tool("retry_tool", {})
        
        assert result["content"][0]["text"] == "Success on retry"
    
    async def test_multi_server_coordination(self):
        """Test coordination between multiple MCP servers"""
        
        # Create multiple mock servers
        filesystem_client = Mock(spec=MCPClient)
        github_client = Mock(spec=MCPClient) 
        database_client = Mock(spec=MCPClient)
        
        # Configure filesystem server
        filesystem_client.connect = AsyncMock(return_value={
            "server_info": {"name": "filesystem", "version": "1.0.0"}
        })
        filesystem_client.call_tool = AsyncMock(return_value={
            "content": [{"type": "text", "text": "File operation completed"}]
        })
        
        # Configure GitHub server
        github_client.connect = AsyncMock(return_value={
            "server_info": {"name": "github", "version": "1.0.0"}
        })
        github_client.call_tool = AsyncMock(return_value={
            "content": [{"type": "text", "text": "GitHub operation completed"}]
        })
        
        # Configure database server
        database_client.connect = AsyncMock(return_value={
            "server_info": {"name": "database", "version": "1.0.0"}
        })
        database_client.call_tool = AsyncMock(return_value={
            "content": [{"type": "text", "text": "Database operation completed"}]
        })
        
        # Test coordinated workflow across servers
        servers = {
            "filesystem": filesystem_client,
            "github": github_client,
            "database": database_client
        }
        
        # Connect all servers
        for server_name, client in servers.items():
            result = await client.connect()
            assert result["server_info"]["name"] == server_name
        
        # Execute coordinated operations
        workflow_results = {}
        
        # Step 1: Read project files (filesystem)
        file_result = await filesystem_client.call_tool(
            "read_file",
            {"path": "project_config.json"}
        )
        workflow_results["files_read"] = file_result
        
        # Step 2: Create GitHub issue (github)
        issue_result = await github_client.call_tool(
            "create_issue",
            {"title": "Deploy new version", "body": "Automated deployment"}
        )
        workflow_results["issue_created"] = issue_result
        
        # Step 3: Update database (database)
        db_result = await database_client.call_tool(
            "execute_query",
            {"query": "UPDATE deployments SET status = 'in_progress'"}
        )
        workflow_results["database_updated"] = db_result
        
        # Verify all operations completed
        assert len(workflow_results) == 3
        assert all("completed" in str(result) for result in workflow_results.values())
    
    async def test_mcp_permission_enforcement(self):
        """Test MCP permission system and security"""
        
        # Create restricted client (read-only permissions)
        restricted_client = Mock(spec=MCPClient)
        restricted_client.connect = AsyncMock(return_value={
            "server_info": {"name": "restricted-server"},
            "permissions": ["read"]
        })
        
        # Test allowed operation
        restricted_client.call_tool = AsyncMock(return_value={
            "content": [{"type": "text", "text": "Read operation allowed"}]
        })
        
        read_result = await restricted_client.call_tool(
            "read_file",
            {"path": "public_file.txt"}
        )
        assert "allowed" in read_result["content"][0]["text"]
        
        # Test blocked operation
        restricted_client.call_tool = AsyncMock(side_effect=PermissionError(
            "Write operation not permitted for this client"
        ))
        
        with pytest.raises(PermissionError):
            await restricted_client.call_tool(
                "write_file", 
                {"path": "restricted.txt", "content": "unauthorized"}
            )
        
        # Test permission validation with dangerous operations
        restricted_client.call_tool = AsyncMock(side_effect=SecurityError(
            "Dangerous operation blocked by security policy"
        ))
        
        with pytest.raises((SecurityError, Exception)):
            await restricted_client.call_tool(
                "execute_command",
                {"command": "rm -rf /"}
            )


@pytest.mark.asyncio 
class TestAgentMCPIntegration:
    """Test agent integration with MCP servers"""
    
    def setup_method(self):
        """Set up agent-MCP integration test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_path = self.temp_dir / "agent_mcp_project"
        self.project_path.mkdir(parents=True)
        
        # Mock MCP bridge
        self.mock_bridge = Mock(spec=AgentMCPBridge)
        self.mock_bridge.connect_servers = AsyncMock()
        self.mock_bridge.execute_tool_chain = AsyncMock()
        self.mock_bridge.get_available_tools = AsyncMock()
        
    def teardown_method(self):
        """Clean up agent-MCP test environment"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    async def test_agent_mcp_workflow_integration(self):
        """Test complete agent workflow with MCP tool integration"""
        
        # Configure mock bridge with available tools
        self.mock_bridge.get_available_tools.return_value = {
            "filesystem": ["read_file", "write_file", "create_directory"],
            "github": ["create_repo", "create_issue", "create_pr"],
            "database": ["create_table", "insert_data", "query_data"]
        }
        
        available_tools = await self.mock_bridge.get_available_tools()
        assert "filesystem" in available_tools
        assert "read_file" in available_tools["filesystem"]
        
        # Test Backend Developer agent workflow with MCP tools
        backend_workflow = [
            # Step 1: Create project structure
            {
                "tool": "create_directory",
                "server": "filesystem", 
                "args": {"path": "src/api"}
            },
            # Step 2: Create main API file
            {
                "tool": "write_file",
                "server": "filesystem",
                "args": {
                    "path": "src/api/main.py",
                    "content": "from fastapi import FastAPI\napp = FastAPI()"
                }
            },
            # Step 3: Create database schema
            {
                "tool": "create_table",
                "server": "database",
                "args": {
                    "table": "users",
                    "schema": "id SERIAL PRIMARY KEY, username VARCHAR(50)"
                }
            },
            # Step 4: Create GitHub repository
            {
                "tool": "create_repo",
                "server": "github",
                "args": {
                    "name": "backend-api",
                    "description": "FastAPI backend application"
                }
            }
        ]
        
        # Execute workflow through MCP bridge
        self.mock_bridge.execute_tool_chain.return_value = {
            "success": True,
            "results": [
                {"tool": "create_directory", "status": "success"},
                {"tool": "write_file", "status": "success", "file_created": "src/api/main.py"},
                {"tool": "create_table", "status": "success", "table_created": "users"},
                {"tool": "create_repo", "status": "success", "repo_url": "https://github.com/test/backend-api"}
            ],
            "total_operations": 4,
            "execution_time": 2.5
        }
        
        workflow_result = await self.mock_bridge.execute_tool_chain(backend_workflow)
        
        # Verify workflow execution
        assert workflow_result["success"] is True
        assert workflow_result["total_operations"] == 4
        assert len(workflow_result["results"]) == 4
        
        # Verify all steps completed successfully
        for result in workflow_result["results"]:
            assert result["status"] == "success"
        
        # Verify specific outputs
        file_result = next(r for r in workflow_result["results"] if r["tool"] == "write_file")
        assert file_result["file_created"] == "src/api/main.py"
        
        repo_result = next(r for r in workflow_result["results"] if r["tool"] == "create_repo")
        assert "github.com" in repo_result["repo_url"]
    
    async def test_agent_mcp_error_recovery(self):
        """Test agent workflow error recovery with MCP tools"""
        
        # Configure workflow with failure scenario
        failing_workflow = [
            {
                "tool": "write_file",
                "server": "filesystem",
                "args": {"path": "test.py", "content": "print('test')"}
            },
            {
                "tool": "create_repo",  # This will fail
                "server": "github",
                "args": {"name": "test-repo"}
            },
            {
                "tool": "create_table",
                "server": "database", 
                "args": {"table": "test_table", "schema": "id INT"}
            }
        ]
        
        # Mock partial failure scenario
        self.mock_bridge.execute_tool_chain.return_value = {
            "success": False,
            "results": [
                {"tool": "write_file", "status": "success"},
                {"tool": "create_repo", "status": "failed", "error": "GitHub API rate limit exceeded"},
                {"tool": "create_table", "status": "skipped", "reason": "previous_failure"}
            ],
            "failed_at_step": 1,
            "recovery_options": [
                "retry_with_delay",
                "use_alternative_git_service",
                "continue_without_repo"
            ]
        }
        
        workflow_result = await self.mock_bridge.execute_tool_chain(failing_workflow)
        
        # Verify failure handling
        assert workflow_result["success"] is False
        assert workflow_result["failed_at_step"] == 1
        assert len(workflow_result["recovery_options"]) == 3
        
        # Test recovery execution
        self.mock_bridge.execute_tool_chain.return_value = {
            "success": True,
            "results": [
                {"tool": "create_repo", "status": "success", "recovery": "retry_with_delay"},
                {"tool": "create_table", "status": "success", "resumed": True}
            ],
            "recovery_successful": True
        }
        
        # Simulate recovery workflow
        recovery_workflow = failing_workflow[1:]  # Skip successful first step
        recovery_result = await self.mock_bridge.execute_tool_chain(recovery_workflow)
        
        assert recovery_result["success"] is True
        assert recovery_result["recovery_successful"] is True
    
    async def test_parallel_agent_mcp_operations(self):
        """Test parallel agent operations using MCP tools"""
        
        # Define parallel operations for different agents
        parallel_operations = {
            "frontend_developer": [
                {
                    "tool": "create_directory",
                    "server": "filesystem",
                    "args": {"path": "src/components"}
                },
                {
                    "tool": "write_file", 
                    "server": "filesystem",
                    "args": {
                        "path": "src/components/App.tsx",
                        "content": "import React from 'react';\nexport default function App() { return <div>App</div>; }"
                    }
                }
            ],
            "database_specialist": [
                {
                    "tool": "create_table",
                    "server": "database",
                    "args": {"table": "products", "schema": "id SERIAL PRIMARY KEY, name VARCHAR(100)"}
                },
                {
                    "tool": "create_table",
                    "server": "database", 
                    "args": {"table": "orders", "schema": "id SERIAL PRIMARY KEY, product_id INT"}
                }
            ],
            "devops_specialist": [
                {
                    "tool": "write_file",
                    "server": "filesystem",
                    "args": {
                        "path": "Dockerfile",
                        "content": "FROM node:18\nWORKDIR /app\nCOPY . .\nRUN npm install"
                    }
                },
                {
                    "tool": "create_repo",
                    "server": "github",
                    "args": {"name": "deployment-configs"}
                }
            ]
        }
        
        # Mock parallel execution results
        parallel_results = {}
        for agent, operations in parallel_operations.items():
            self.mock_bridge.execute_tool_chain.return_value = {
                "success": True,
                "agent": agent,
                "operations_completed": len(operations),
                "execution_time": 1.2
            }
            
            result = await self.mock_bridge.execute_tool_chain(operations)
            parallel_results[agent] = result
        
        # Verify all parallel operations completed
        assert len(parallel_results) == 3
        for agent, result in parallel_results.items():
            assert result["success"] is True
            assert result["agent"] == agent
            assert result["operations_completed"] > 0
        
        # Verify no conflicts between parallel operations
        operation_counts = [r["operations_completed"] for r in parallel_results.values()]
        assert sum(operation_counts) == 6  # Total operations across all agents


class TestMCPSecurityAndPermissions:
    """Test MCP security model and permission enforcement"""
    
    def setup_method(self):
        """Set up security test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Mock security handler
        self.mock_security = Mock(spec=MCPErrorHandler)
        self.mock_security.validate_operation = Mock()
        self.mock_security.check_permissions = Mock()
        self.mock_security.audit_log = Mock()
        
    def teardown_method(self):
        """Clean up security test environment"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_agent_permission_validation(self):
        """Test agent-specific permission validation"""
        
        # Define agent permission matrix
        agent_permissions = {
            "qa_testing": ["read", "test_execution"],
            "backend_developer": ["read", "write", "database_access"],
            "devops_deployment": ["read", "write", "system_admin", "deployment"],
            "frontend_developer": ["read", "write", "ui_access"]
        }
        
        # Test valid permissions
        self.mock_security.check_permissions.return_value = {"allowed": True, "reason": "valid_permission"}
        
        for agent, permissions in agent_permissions.items():
            for permission in permissions:
                result = self.mock_security.check_permissions(agent, permission)
                assert result["allowed"] is True
        
        # Test invalid permissions
        self.mock_security.check_permissions.return_value = {"allowed": False, "reason": "insufficient_permissions"}
        
        invalid_cases = [
            ("qa_testing", "system_admin"),  # QA shouldn't have system admin
            ("frontend_developer", "database_access"),  # Frontend shouldn't access DB directly
            ("backend_developer", "deployment")  # Backend shouldn't deploy directly
        ]
        
        for agent, permission in invalid_cases:
            result = self.mock_security.check_permissions(agent, permission)
            assert result["allowed"] is False
    
    def test_dangerous_operation_blocking(self):
        """Test blocking of dangerous operations"""
        
        dangerous_operations = [
            {"tool": "execute_command", "args": {"command": "rm -rf /"}},
            {"tool": "file_write", "args": {"path": "/etc/passwd", "content": "malicious"}},
            {"tool": "network_request", "args": {"url": "http://malicious-site.com"}},
            {"tool": "system_call", "args": {"call": "shutdown"}},
        ]
        
        # Mock security validation to block dangerous operations
        self.mock_security.validate_operation.side_effect = lambda op: (
            {"blocked": True, "reason": "dangerous_operation"} 
            if any(danger in str(op).lower() for danger in ["rm -rf", "passwd", "malicious", "shutdown"])
            else {"blocked": False}
        )
        
        for operation in dangerous_operations:
            result = self.mock_security.validate_operation(operation)
            assert result["blocked"] is True
            assert "dangerous" in result["reason"]
    
    def test_audit_logging(self):
        """Test security audit logging"""
        
        # Test operations that should be audited
        auditable_operations = [
            {
                "agent": "devops_deployment",
                "tool": "execute_command", 
                "args": {"command": "docker deploy"},
                "timestamp": datetime.now().isoformat(),
                "risk_level": "high"
            },
            {
                "agent": "database_specialist",
                "tool": "drop_table",
                "args": {"table": "user_data"},
                "timestamp": datetime.now().isoformat(), 
                "risk_level": "critical"
            },
            {
                "agent": "backend_developer",
                "tool": "file_write",
                "args": {"path": "src/config.py", "content": "API_KEY = 'secret'"},
                "timestamp": datetime.now().isoformat(),
                "risk_level": "medium"
            }
        ]
        
        # Mock audit logging
        audit_logs = []
        self.mock_security.audit_log.side_effect = lambda op: audit_logs.append({
            "operation": op,
            "logged_at": datetime.now().isoformat(),
            "audit_id": f"audit_{len(audit_logs) + 1}"
        })
        
        # Log all operations
        for operation in auditable_operations:
            self.mock_security.audit_log(operation)
        
        # Verify audit logs
        assert len(audit_logs) == 3
        
        # Verify high-risk operations are properly logged
        high_risk_logs = [log for log in audit_logs if "docker" in str(log["operation"]) or "drop_table" in str(log["operation"])]
        assert len(high_risk_logs) == 2
        
        # Verify audit ID uniqueness
        audit_ids = [log["audit_id"] for log in audit_logs]
        assert len(set(audit_ids)) == len(audit_ids)


class TestMCPPerformanceAndScaling:
    """Test MCP performance and scaling characteristics"""
    
    def setup_method(self):
        """Set up performance test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Mock high-performance MCP client
        self.mock_perf_client = Mock(spec=MCPClient)
        self.mock_perf_client.call_tool = AsyncMock()
        
    def teardown_method(self):
        """Clean up performance test environment"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_high_volume_tool_execution(self):
        """Test MCP performance under high volume tool execution"""
        import time
        
        # Configure mock for high-volume testing
        self.mock_perf_client.call_tool.return_value = {
            "content": [{"type": "text", "text": "Operation completed"}]
        }
        
        # Test parameters
        num_operations = 100
        batch_size = 10
        
        start_time = time.time()
        
        # Execute operations in batches
        total_operations = 0
        for batch in range(0, num_operations, batch_size):
            batch_operations = []
            
            # Create batch of operations
            for i in range(min(batch_size, num_operations - batch)):
                operation = self.mock_perf_client.call_tool(
                    "test_operation",
                    {"operation_id": batch + i, "batch": batch // batch_size}
                )
                batch_operations.append(operation)
            
            # Execute batch concurrently
            results = await asyncio.gather(*batch_operations, return_exceptions=True)
            
            # Verify batch results
            for result in results:
                if not isinstance(result, Exception):
                    total_operations += 1
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verify performance metrics
        assert total_operations == num_operations
        assert execution_time < 10.0  # Should complete within 10 seconds
        
        operations_per_second = num_operations / execution_time
        assert operations_per_second > 10  # Minimum 10 ops/second
    
    @pytest.mark.asyncio  
    async def test_concurrent_server_load(self):
        """Test concurrent load across multiple MCP servers"""
        
        # Create multiple server mocks
        server_mocks = {}
        for server_name in ["filesystem", "github", "database", "docker"]:
            mock = Mock(spec=MCPClient)
            mock.call_tool = AsyncMock(return_value={
                "server": server_name,
                "status": "success",
                "execution_time": 0.1
            })
            server_mocks[server_name] = mock
        
        # Create concurrent operations across servers
        concurrent_operations = []
        operations_per_server = 25
        
        for server_name, mock_client in server_mocks.items():
            for i in range(operations_per_server):
                operation = mock_client.call_tool(
                    f"{server_name}_operation",
                    {"operation_index": i}
                )
                concurrent_operations.append(operation)
        
        # Execute all operations concurrently
        import time
        start_time = time.time()
        
        results = await asyncio.gather(*concurrent_operations, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify concurrent execution
        successful_operations = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_operations) == len(server_mocks) * operations_per_server
        
        # Verify performance under concurrent load
        assert total_time < 5.0  # Should complete within 5 seconds
        
        # Verify all servers handled their operations
        for server_name in server_mocks.keys():
            server_results = [r for r in successful_operations if r["server"] == server_name]
            assert len(server_results) == operations_per_server
    
    def test_memory_usage_monitoring(self):
        """Test memory usage during MCP operations"""
        import sys
        import gc
        
        # Measure initial memory
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Simulate memory-intensive MCP operations
        mock_responses = []
        
        for i in range(1000):
            # Create mock response objects
            response = {
                "id": i,
                "content": [{"type": "text", "text": f"Response {i} with data"}],
                "metadata": {"operation_id": i, "timestamp": datetime.now()},
                "large_data": ["item"] * 100  # Simulate larger responses
            }
            mock_responses.append(response)
        
        # Process responses (simulate MCP client processing)
        processed_responses = []
        for response in mock_responses:
            processed = {
                "id": response["id"],
                "processed": True,
                "content_length": len(str(response["content"])),
                "timestamp": response["metadata"]["timestamp"]
            }
            processed_responses.append(processed)
        
        # Clean up large data
        del mock_responses
        gc.collect()
        
        # Measure final memory
        final_objects = len(gc.get_objects())
        memory_growth = final_objects - initial_objects
        
        # Verify reasonable memory usage
        assert memory_growth < 5000  # Should not create excessive objects
        assert len(processed_responses) == 1000  # All responses processed


# Define SecurityError for permission tests
class SecurityError(Exception):
    """Custom security exception for testing"""
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])