#!/usr/bin/env python3
"""
Production-ready MCP Client for CoralCollective
Implements full JSON-RPC 2.0 protocol with async communication, connection pooling, and robust error handling.
"""

import os
import json
import asyncio
import subprocess
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import logging
import traceback
from concurrent.futures import ThreadPoolExecutor

# Third-party imports
try:
    import yaml
except ImportError:
    yaml = None

# Set up comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# Audit logger for security and compliance
audit_logger = logging.getLogger('mcp_audit')
# Create audit log in the same directory as this file
audit_log_path = Path(__file__).parent / 'logs' / 'audit.log'
audit_log_path.parent.mkdir(parents=True, exist_ok=True)
audit_handler = logging.FileHandler(audit_log_path, mode='a')
audit_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
)
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)


@dataclass
class MCPMessage:
    """Represents an MCP JSON-RPC message"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        msg = {"jsonrpc": self.jsonrpc}
        if self.id is not None:
            msg["id"] = self.id
        if self.method is not None:
            msg["method"] = self.method
        if self.params is not None:
            msg["params"] = self.params
        if self.result is not None:
            msg["result"] = self.result
        if self.error is not None:
            msg["error"] = self.error
        return msg
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPMessage':
        """Create MCPMessage from dictionary"""
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            method=data.get("method"),
            params=data.get("params"),
            result=data.get("result"),
            error=data.get("error")
        )


@dataclass
class MCPServer:
    """Represents an MCP server configuration with enhanced metadata"""
    name: str
    command: str
    args: List[str]
    env: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    permissions: List[str] = field(default_factory=list)
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    max_concurrent_requests: int = 10
    health_check_interval: int = 60
    features: List[str] = field(default_factory=list)
    agents: List[str] = field(default_factory=list)


@dataclass
class ConnectionStats:
    """Track connection statistics for monitoring"""
    connect_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    requests_sent: int = 0
    responses_received: int = 0
    errors: int = 0
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_error: Optional[str] = None
    uptime_seconds: float = 0.0


class MCPTransport:
    """Handles stdio transport layer for MCP communication"""
    
    def __init__(self, server_name: str, process: asyncio.subprocess.Process):
        self.server_name = server_name
        self.process = process
        self.message_buffer = ""
        self.lock = asyncio.Lock()
        self.connected = True
        self.stats = ConnectionStats()
        
    async def send_message(self, message: MCPMessage) -> None:
        """Send a message via stdio transport"""
        if not self.connected or self.process.stdin.is_closing():
            raise ConnectionError(f"Transport to {self.server_name} is not connected")
        
        try:
            async with self.lock:
                json_data = json.dumps(message.to_dict())
                logger.debug(f"Sending to {self.server_name}: {json_data}")
                
                self.process.stdin.write(json_data.encode('utf-8') + b'\n')
                await self.process.stdin.drain()
                
                self.stats.requests_sent += 1
                self.stats.last_activity = datetime.now(timezone.utc)
                
        except Exception as e:
            self.stats.errors += 1
            self.stats.last_error = str(e)
            logger.error(f"Failed to send message to {self.server_name}: {e}")
            raise
    
    async def read_message(self, timeout: float = 30.0) -> MCPMessage:
        """Read a message from stdio transport with timeout"""
        if not self.connected:
            raise ConnectionError(f"Transport to {self.server_name} is not connected")
        
        try:
            # Use asyncio.wait_for for timeout handling
            line = await asyncio.wait_for(
                self.process.stdout.readline(),
                timeout=timeout
            )
            
            if not line:
                raise ConnectionError(f"Connection to {self.server_name} closed unexpectedly")
            
            json_data = line.decode('utf-8').strip()
            logger.debug(f"Received from {self.server_name}: {json_data}")
            
            try:
                data = json.loads(json_data)
                message = MCPMessage.from_dict(data)
                
                self.stats.responses_received += 1
                self.stats.last_activity = datetime.now(timezone.utc)
                
                return message
                
            except json.JSONDecodeError as e:
                self.stats.errors += 1
                self.stats.last_error = f"JSON decode error: {e}"
                raise ValueError(f"Invalid JSON received from {self.server_name}: {json_data}")
                
        except asyncio.TimeoutError:
            self.stats.errors += 1
            self.stats.last_error = f"Read timeout after {timeout}s"
            raise TimeoutError(f"Timeout reading from {self.server_name} after {timeout}s")
        except Exception as e:
            self.stats.errors += 1
            self.stats.last_error = str(e)
            logger.error(f"Failed to read from {self.server_name}: {e}")
            raise
    
    async def close(self):
        """Close the transport connection"""
        self.connected = False
        try:
            if not self.process.stdin.is_closing():
                self.process.stdin.close()
                await self.process.stdin.wait_closed()
            
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()
                
            logger.info(f"Transport to {self.server_name} closed")
            
        except Exception as e:
            logger.error(f"Error closing transport to {self.server_name}: {e}")


class MCPConnection:
    """Manages a connection to a single MCP server with advanced features"""
    
    def __init__(self, server: MCPServer):
        self.server = server
        self.transport: Optional[MCPTransport] = None
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.request_semaphore = asyncio.Semaphore(server.max_concurrent_requests)
        self.connection_lock = asyncio.Lock()
        self.connected = False
        self.tools_cache: Optional[List[Dict[str, Any]]] = None
        self.cache_timestamp: Optional[datetime] = None
        self.cache_ttl = 300  # 5 minutes
        self.circuit_breaker_failures = 0
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_open_until: Optional[datetime] = None
        self.health_check_task: Optional[asyncio.Task] = None
        
    async def connect(self) -> bool:
        """Establish connection to MCP server with retry logic"""
        async with self.connection_lock:
            if self.connected:
                return True
            
            # Check circuit breaker
            if self._is_circuit_breaker_open():
                logger.warning(f"Circuit breaker open for {self.server.name}")
                return False
            
            for attempt in range(self.server.retry_attempts):
                try:
                    logger.info(f"Connecting to {self.server.name} (attempt {attempt + 1})")
                    
                    # Build environment
                    env = os.environ.copy()
                    env.update(self.server.env)
                    
                    # Expand environment variables in env values
                    for key, value in env.items():
                        if isinstance(value, str):
                            env[key] = os.path.expandvars(value)
                    
                    # Start MCP server process
                    process = await asyncio.create_subprocess_exec(
                        self.server.command,
                        *self.server.args,
                        stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        env=env,
                        cwd=os.getcwd()
                    )
                    
                    # Create transport
                    self.transport = MCPTransport(self.server.name, process)
                    
                    # Perform MCP initialization handshake
                    await self._initialize_connection()
                    
                    self.connected = True
                    self.circuit_breaker_failures = 0
                    self.circuit_breaker_open_until = None
                    
                    # Start background tasks
                    self._start_background_tasks()
                    
                    logger.info(f"Successfully connected to {self.server.name}")
                    audit_logger.info(f"MCP server connected: {self.server.name}")
                    
                    return True
                    
                except Exception as e:
                    logger.error(f"Connection attempt {attempt + 1} failed for {self.server.name}: {e}")
                    
                    if self.transport:
                        await self.transport.close()
                        self.transport = None
                    
                    if attempt < self.server.retry_attempts - 1:
                        await asyncio.sleep(self.server.retry_delay * (2 ** attempt))  # Exponential backoff
                    
            # All attempts failed - open circuit breaker
            self.circuit_breaker_failures += 1
            if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
                self.circuit_breaker_open_until = datetime.now(timezone.utc).replace(
                    second=datetime.now(timezone.utc).second + 60
                )
                logger.warning(f"Circuit breaker opened for {self.server.name}")
            
            return False
    
    async def _initialize_connection(self):
        """Perform MCP protocol initialization"""
        # Send initialize request
        init_request = MCPMessage(
            id=str(uuid.uuid4()),
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "logging": {}
                },
                "clientInfo": {
                    "name": "CoralCollective",
                    "version": "1.0.0"
                }
            }
        )
        
        response = await self._send_request(init_request, initialize=True)
        
        if response.error:
            raise Exception(f"Initialization failed: {response.error}")
        
        logger.debug(f"Server {self.server.name} initialized with capabilities: {response.result}")
        
        # Send initialized notification
        initialized_notification = MCPMessage(
            method="notifications/initialized"
        )
        
        await self.transport.send_message(initialized_notification)
    
    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open"""
        if not self.circuit_breaker_open_until:
            return False
        
        if datetime.now(timezone.utc) > self.circuit_breaker_open_until:
            self.circuit_breaker_open_until = None
            self.circuit_breaker_failures = 0
            return False
        
        return True
    
    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        if self.health_check_task is None or self.health_check_task.done():
            self.health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def _health_check_loop(self):
        """Background health check task"""
        while self.connected:
            try:
                await asyncio.sleep(self.server.health_check_interval)
                
                if not self.connected:
                    break
                
                # Simple ping to check server health
                ping_request = MCPMessage(
                    id=str(uuid.uuid4()),
                    method="ping",
                    params={}
                )
                
                try:
                    await asyncio.wait_for(
                        self._send_request(ping_request),
                        timeout=10.0
                    )
                    logger.debug(f"Health check passed for {self.server.name}")
                    
                except (asyncio.TimeoutError, Exception) as e:
                    logger.warning(f"Health check failed for {self.server.name}: {e}")
                    # Don't disconnect on health check failure, just log it
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error for {self.server.name}: {e}")
    
    async def _send_request(self, request: MCPMessage, initialize: bool = False) -> MCPMessage:
        """Send request and wait for response"""
        if not initialize and not self.connected:
            raise ConnectionError(f"Not connected to {self.server.name}")
        
        if not request.id:
            request.id = str(uuid.uuid4())
        
        # Create future for response
        response_future = asyncio.Future()
        self.pending_requests[request.id] = response_future
        
        try:
            # Send request
            await self.transport.send_message(request)
            
            # Wait for response with timeout
            response = await asyncio.wait_for(
                response_future,
                timeout=self.server.timeout
            )
            
            return response
            
        except Exception as e:
            # Clean up pending request
            self.pending_requests.pop(request.id, None)
            raise
        finally:
            # Always clean up the future
            self.pending_requests.pop(request.id, None)
    
    async def list_tools(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """List available tools from the server"""
        # Check cache first
        if use_cache and self._is_cache_valid():
            logger.debug(f"Using cached tools for {self.server.name}")
            return self.tools_cache or []
        
        async with self.request_semaphore:
            request = MCPMessage(
                id=str(uuid.uuid4()),
                method="tools/list",
                params={}
            )
            
            response = await self._send_request(request)
            
            if response.error:
                logger.error(f"Error listing tools from {self.server.name}: {response.error}")
                audit_logger.warning(f"Tools list error for {self.server.name}: {response.error}")
                return []
            
            tools = response.result.get("tools", []) if response.result else []
            
            # Update cache
            self.tools_cache = tools
            self.cache_timestamp = datetime.now(timezone.utc)
            
            audit_logger.info(f"Listed {len(tools)} tools from {self.server.name}")
            return tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool on the server"""
        async with self.request_semaphore:
            request = MCPMessage(
                id=str(uuid.uuid4()),
                method="tools/call",
                params={
                    "name": tool_name,
                    "arguments": arguments
                }
            )
            
            audit_logger.info(
                f"Tool call: {self.server.name}/{tool_name} with args: {json.dumps(arguments, default=str)}"
            )
            
            response = await self._send_request(request)
            
            if response.error:
                error_msg = f"Tool execution error: {response.error}"
                logger.error(error_msg)
                audit_logger.error(f"Tool call failed: {self.server.name}/{tool_name} - {response.error}")
                raise Exception(error_msg)
            
            result = response.result
            audit_logger.info(f"Tool call succeeded: {self.server.name}/{tool_name}")
            
            return result
    
    def _is_cache_valid(self) -> bool:
        """Check if tools cache is still valid"""
        if not self.cache_timestamp or not self.tools_cache:
            return False
        
        age = (datetime.now(timezone.utc) - self.cache_timestamp).total_seconds()
        return age < self.cache_ttl
    
    async def start_message_handler(self):
        """Start background message handler for responses and notifications"""
        while self.connected and self.transport:
            try:
                message = await self.transport.read_message()
                
                if message.id and message.id in self.pending_requests:
                    # This is a response to a pending request
                    future = self.pending_requests.get(message.id)
                    if future and not future.done():
                        future.set_result(message)
                elif message.method:
                    # This is a notification - log it
                    logger.debug(f"Notification from {self.server.name}: {message.method}")
                else:
                    logger.warning(f"Unhandled message from {self.server.name}: {message.to_dict()}")
                    
            except ConnectionError:
                logger.info(f"Connection to {self.server.name} closed")
                break
            except Exception as e:
                logger.error(f"Message handler error for {self.server.name}: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying
    
    async def disconnect(self):
        """Disconnect from the server"""
        async with self.connection_lock:
            if not self.connected:
                return
            
            self.connected = False
            
            # Cancel health check task
            if self.health_check_task:
                self.health_check_task.cancel()
                try:
                    await self.health_check_task
                except asyncio.CancelledError:
                    pass
            
            # Cancel all pending requests
            for future in self.pending_requests.values():
                if not future.done():
                    future.cancel()
            self.pending_requests.clear()
            
            # Close transport
            if self.transport:
                await self.transport.close()
                self.transport = None
            
            logger.info(f"Disconnected from {self.server.name}")
            audit_logger.info(f"MCP server disconnected: {self.server.name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        if not self.transport:
            return {"connected": False}
        
        stats = {
            "connected": self.connected,
            "server_name": self.server.name,
            "uptime_seconds": (datetime.now(timezone.utc) - self.transport.stats.connect_time).total_seconds(),
            "requests_sent": self.transport.stats.requests_sent,
            "responses_received": self.transport.stats.responses_received,
            "errors": self.transport.stats.errors,
            "last_activity": self.transport.stats.last_activity.isoformat(),
            "last_error": self.transport.stats.last_error,
            "pending_requests": len(self.pending_requests),
            "circuit_breaker_failures": self.circuit_breaker_failures,
            "circuit_breaker_open": self._is_circuit_breaker_open()
        }
        
        return stats


class MCPClient:
    """Production-ready MCP Client with full JSON-RPC 2.0 support"""
    
    def __init__(self, config_path: str = "mcp/configs/mcp_config.yaml"):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.servers: Dict[str, MCPServer] = {}
        self.connections: Dict[str, MCPConnection] = {}
        self.connection_pool_lock = asyncio.Lock()
        self.initialized = False
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.metrics = defaultdict(int)
        self.load_configuration()
        
        # Ensure log directory exists
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
    
    def load_configuration(self):
        """Load MCP configuration from YAML or JSON file"""
        try:
            if not self.config_path.exists():
                logger.error(f"Configuration file not found: {self.config_path}")
                return
            
            with open(self.config_path, 'r') as f:
                if self.config_path.suffix in ['.yaml', '.yml']:
                    if yaml is None:
                        raise ImportError("PyYAML is required for YAML configuration files")
                    self.config = yaml.safe_load(f)
                else:
                    self.config = json.load(f)
            
            # Load server configurations
            for server_name, server_config in self.config.get('mcp_servers', {}).items():
                if server_config.get('enabled', True):
                    self.servers[server_name] = MCPServer(
                        name=server_name,
                        command=server_config['command'],
                        args=server_config.get('args', []),
                        env=server_config.get('env', {}),
                        enabled=True,
                        permissions=server_config.get('permissions', []),
                        timeout=server_config.get('timeout', 30),
                        retry_attempts=server_config.get('retry_attempts', 3),
                        retry_delay=server_config.get('retry_delay', 1.0),
                        max_concurrent_requests=server_config.get('max_concurrent_requests', 10),
                        health_check_interval=server_config.get('health_check_interval', 60),
                        features=server_config.get('features', []),
                        agents=server_config.get('agents', [])
                    )
            
            logger.info(f"Loaded configuration for {len(self.servers)} MCP servers")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            traceback.print_exc()
    
    async def initialize(self) -> None:
        """Initialize the MCP client and establish connections"""
        if self.initialized:
            return
        
        logger.info("Initializing MCP client...")
        
        # Create connections for all enabled servers
        for server_name, server in self.servers.items():
            self.connections[server_name] = MCPConnection(server)
        
        self.initialized = True
        logger.info("MCP client initialized")
    
    async def connect_server(self, server_name: str) -> bool:
        """Connect to a specific MCP server"""
        if not self.initialized:
            await self.initialize()
        
        if server_name not in self.connections:
            logger.error(f"Server {server_name} not found in configuration")
            return False
        
        connection = self.connections[server_name]
        
        async with self.connection_pool_lock:
            if connection.connected:
                return True
            
            success = await connection.connect()
            
            if success:
                # Start message handler
                asyncio.create_task(connection.start_message_handler())
                self.metrics[f"{server_name}_connections"] += 1
            
            return success
    
    async def disconnect_server(self, server_name: str) -> None:
        """Disconnect from a specific MCP server"""
        if server_name in self.connections:
            await self.connections[server_name].disconnect()
    
    async def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """List available tools from a specific server"""
        if not await self.connect_server(server_name):
            return []
        
        connection = self.connections[server_name]
        
        try:
            tools = await connection.list_tools()
            self.metrics[f"{server_name}_list_tools"] += 1
            return tools
            
        except Exception as e:
            logger.error(f"Failed to list tools from {server_name}: {e}")
            self.metrics[f"{server_name}_errors"] += 1
            return []
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool on a specific server"""
        if not await self.connect_server(server_name):
            raise ConnectionError(f"Could not connect to server {server_name}")
        
        connection = self.connections[server_name]
        
        try:
            result = await connection.call_tool(tool_name, arguments)
            self.metrics[f"{server_name}_tool_calls"] += 1
            return result
            
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name} on {server_name}: {e}")
            self.metrics[f"{server_name}_errors"] += 1
            raise
    
    async def send_request(self, server_name: str, method: str, params: Dict[str, Any]) -> Any:
        """Send a custom JSON-RPC request to a server"""
        if not await self.connect_server(server_name):
            raise ConnectionError(f"Could not connect to server {server_name}")
        
        connection = self.connections[server_name]
        
        request = MCPMessage(
            id=str(uuid.uuid4()),
            method=method,
            params=params
        )
        
        try:
            response = await connection._send_request(request)
            self.metrics[f"{server_name}_custom_requests"] += 1
            
            if response.error:
                raise Exception(f"Server error: {response.error}")
            
            return response.result
            
        except Exception as e:
            logger.error(f"Failed to send request to {server_name}: {e}")
            self.metrics[f"{server_name}_errors"] += 1
            raise
    
    async def handle_response(self, response: Dict[str, Any]) -> Any:
        """Handle and validate JSON-RPC response"""
        message = MCPMessage.from_dict(response)
        
        if message.error:
            raise Exception(f"MCP Error: {message.error}")
        
        return message.result
    
    def check_agent_permissions(self, agent_id: str, server_name: str) -> bool:
        """Check if an agent has permission to use a specific server"""
        agent_perms = self.config.get('agent_permissions', {}).get(agent_id, {})
        allowed_servers = agent_perms.get('servers', [])
        
        return 'all' in allowed_servers or server_name in allowed_servers
    
    def get_tools_for_agent(self, agent_id: str) -> Dict[str, List[str]]:
        """Get available tools for a specific agent based on permissions"""
        if not self.config.get('agent_permissions'):
            return {}
        
        agent_perms = self.config.get('agent_permissions', {}).get(agent_id, {})
        allowed_servers = agent_perms.get('servers', [])
        
        agent_tools = {}
        for server_name in allowed_servers:
            if server_name in self.servers:
                agent_tools[server_name] = self.servers[server_name].permissions
        
        return agent_tools
    
    def get_available_servers(self) -> List[str]:
        """Get list of all available server names"""
        return list(self.servers.keys())
    
    def get_server_info(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a server"""
        if server_name not in self.servers:
            return None
        
        server = self.servers[server_name]
        connection_stats = {}
        
        if server_name in self.connections:
            connection_stats = self.connections[server_name].get_stats()
        
        return {
            "name": server.name,
            "enabled": server.enabled,
            "permissions": server.permissions,
            "features": server.features,
            "agents": server.agents,
            "timeout": server.timeout,
            "max_concurrent_requests": server.max_concurrent_requests,
            "connection_stats": connection_stats
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics for monitoring"""
        return dict(self.metrics)
    
    async def shutdown(self) -> None:
        """Shutdown all connections and cleanup resources"""
        logger.info("Shutting down MCP client...")
        
        # Disconnect all servers
        disconnect_tasks = []
        for server_name in list(self.connections.keys()):
            disconnect_tasks.append(self.disconnect_server(server_name))
        
        if disconnect_tasks:
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        self.initialized = False
        logger.info("MCP client shutdown complete")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.shutdown()


class AgentMCPInterface:
    """High-level MCP interface for CoralCollective agents with enhanced security"""
    
    def __init__(self, agent_type: str, client: Optional[MCPClient] = None):
        self.agent_type = agent_type
        self.client = client or MCPClient()
        self.session_id = str(uuid.uuid4())
        audit_logger.info(f"Agent interface created: {agent_type} (session: {self.session_id})")
    
    def _check_permission(self, server_name: str) -> bool:
        """Check if agent has permission to use server"""
        allowed = self.client.check_agent_permissions(self.agent_type, server_name)
        if not allowed:
            audit_logger.warning(f"Permission denied: {self.agent_type} tried to access {server_name}")
        return allowed
    
    async def github_create_issue(self, title: str, body: str, labels: List[str] = None) -> Optional[Dict]:
        """Create a GitHub issue"""
        if not self._check_permission('github'):
            return None
        
        params = {
            'title': title,
            'body': body,
            'labels': labels or []
        }
        
        try:
            return await self.client.call_tool('github', 'create_issue', params)
        except Exception as e:
            logger.error(f"GitHub issue creation failed: {e}")
            return None
    
    async def github_create_pr(self, title: str, body: str, head: str, base: str = 'main') -> Optional[Dict]:
        """Create a GitHub pull request"""
        if not self._check_permission('github'):
            return None
        
        params = {
            'title': title,
            'body': body,
            'head': head,
            'base': base
        }
        
        try:
            return await self.client.call_tool('github', 'create_pull_request', params)
        except Exception as e:
            logger.error(f"GitHub PR creation failed: {e}")
            return None
    
    async def filesystem_read(self, path: str) -> Optional[str]:
        """Read a file from the filesystem"""
        if not self._check_permission('filesystem'):
            return None
        
        params = {'path': path}
        
        try:
            result = await self.client.call_tool('filesystem', 'read_file', params)
            return result.get('content') if result else None
        except Exception as e:
            logger.error(f"Filesystem read failed: {e}")
            return None
    
    async def filesystem_write(self, path: str, content: str) -> bool:
        """Write a file to the filesystem"""
        if not self._check_permission('filesystem'):
            return False
        
        params = {
            'path': path,
            'content': content
        }
        
        try:
            result = await self.client.call_tool('filesystem', 'write_file', params)
            return result.get('success', False) if result else False
        except Exception as e:
            logger.error(f"Filesystem write failed: {e}")
            return False
    
    async def filesystem_list(self, path: str) -> List[str]:
        """List files in a directory"""
        if not self._check_permission('filesystem'):
            return []
        
        params = {'path': path}
        
        try:
            result = await self.client.call_tool('filesystem', 'list_directory', params)
            return result.get('files', []) if result else []
        except Exception as e:
            logger.error(f"Filesystem list failed: {e}")
            return []
    
    async def database_query(self, query: str, params: List[Any] = None) -> List[Dict]:
        """Execute a database query"""
        if not self._check_permission('postgres'):
            return []
        
        query_params = {
            'query': query,
            'params': params or []
        }
        
        try:
            result = await self.client.call_tool('postgres', 'execute_query', query_params)
            return result.get('rows', []) if result else []
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return []
    
    async def search_web(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search the web using Brave Search"""
        if not self._check_permission('brave-search'):
            return []
        
        params = {
            'query': query,
            'count': max_results
        }
        
        try:
            result = await self.client.call_tool('brave-search', 'web_search', params)
            return result.get('web', {}).get('results', []) if result else []
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return []
    
    async def docker_run(self, image: str, command: str = None, env: Dict[str, str] = None) -> Optional[str]:
        """Run a Docker container"""
        if not self._check_permission('docker'):
            return None
        
        params = {
            'image': image,
            'command': command,
            'environment': env or {}
        }
        
        try:
            result = await self.client.call_tool('docker', 'run_container', params)
            return result.get('output') if result else None
        except Exception as e:
            logger.error(f"Docker run failed: {e}")
            return None
    
    async def e2b_execute(self, code: str, language: str = 'python') -> Optional[Dict]:
        """Execute code in E2B sandbox"""
        if not self._check_permission('e2b'):
            return None
        
        params = {
            'language': language,
            'code': code
        }
        
        try:
            result = await self.client.call_tool('e2b', 'execute_code', params)
            return result
        except Exception as e:
            logger.error(f"E2B execution failed: {e}")
            return None
    
    async def get_available_tools(self) -> Dict[str, List[Dict]]:
        """Get all available tools for this agent"""
        tools_by_server = {}
        
        agent_perms = self.client.get_tools_for_agent(self.agent_type)
        
        for server_name in agent_perms:
            try:
                tools = await self.client.list_tools(server_name)
                tools_by_server[server_name] = tools
            except Exception as e:
                logger.error(f"Failed to list tools from {server_name}: {e}")
                tools_by_server[server_name] = []
        
        return tools_by_server
    
    async def close(self):
        """Close the agent interface"""
        audit_logger.info(f"Agent interface closed: {self.agent_type} (session: {self.session_id})")


# Example usage and testing
async def main():
    """Example usage of the production MCP client"""
    
    print("=== CoralCollective MCP Client Demo ===")
    
    # Create MCP client with configuration
    async with MCPClient() as client:
        
        # Get available servers
        servers = client.get_available_servers()
        print(f"Available servers: {servers}")
        
        # Test filesystem operations
        if 'filesystem' in servers:
            print("\n--- Testing Filesystem Operations ---")
            
            # Create agent interface
            backend_agent = AgentMCPInterface('backend_developer', client)
            
            try:
                # Read a file
                content = await backend_agent.filesystem_read('README.md')
                if content:
                    print(f"Successfully read README.md ({len(content)} chars)")
                
                # List directory
                files = await backend_agent.filesystem_list('.')
                print(f"Found {len(files)} files in current directory")
                
                # Write a test file
                success = await backend_agent.filesystem_write(
                    'mcp_test.txt',
                    f'MCP test file created at {datetime.now().isoformat()}'
                )
                print(f"Test file write: {'success' if success else 'failed'}")
                
            except Exception as e:
                print(f"Filesystem test error: {e}")
        
        # Test web search
        if 'brave-search' in servers:
            print("\n--- Testing Web Search ---")
            
            frontend_agent = AgentMCPInterface('frontend_developer', client)
            
            try:
                results = await frontend_agent.search_web('React hooks tutorial', max_results=3)
                print(f"Found {len(results)} search results")
                for i, result in enumerate(results[:2]):
                    print(f"  {i+1}. {result.get('title', 'No title')}")
                    
            except Exception as e:
                print(f"Web search test error: {e}")
        
        # Display metrics
        print("\n--- Client Metrics ---")
        metrics = client.get_metrics()
        for key, value in metrics.items():
            print(f"  {key}: {value}")
        
        # Display server info
        print("\n--- Server Information ---")
        for server_name in servers:
            info = client.get_server_info(server_name)
            if info:
                print(f"  {server_name}:")
                print(f"    Connected: {info['connection_stats'].get('connected', False)}")
                print(f"    Features: {', '.join(info.get('features', []))}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()