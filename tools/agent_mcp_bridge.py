#!/usr/bin/env python3
"""
Agent-MCP Bridge for CoralCollective
Provides secure, high-level MCP tool access for agents with permission validation,
usage tracking, and error handling.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from pathlib import Path
import traceback

# Import error handler
try:
    from .mcp_error_handler import MCPErrorHandler
except ImportError:
    from mcp_error_handler import MCPErrorHandler

# Set up logging
logger = logging.getLogger(__name__)

@dataclass
class ToolUsageRecord:
    """Track individual tool usage for metrics"""
    agent_id: str
    tool_name: str
    server_name: str
    timestamp: datetime
    success: bool
    execution_time_ms: float
    error_message: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

@dataclass
class AgentSession:
    """Track an agent's MCP session"""
    agent_id: str
    session_id: str
    start_time: datetime
    tool_usage: List[ToolUsageRecord] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    permissions: Dict[str, bool] = field(default_factory=dict)

class AgentMCPBridge:
    """
    High-level bridge between CoralCollective agents and MCP tools
    
    Features:
    - Permission validation per agent type
    - Usage tracking and metrics
    - Error handling with fallbacks
    - Tool discovery and documentation
    - Session management
    """
    
    def __init__(self, agent_type: str, mcp_client=None, session_id: Optional[str] = None, base_path: Path = None):
        self.agent_type = agent_type
        self.mcp_client = mcp_client
        self.session_id = session_id or f"{agent_type}_{int(time.time())}"
        self.base_path = base_path or Path.cwd()
        
        # Initialize session
        self.session = AgentSession(
            agent_id=agent_type,
            session_id=self.session_id,
            start_time=datetime.now(timezone.utc)
        )
        
        # Initialize error handler
        self.error_handler = MCPErrorHandler(self.base_path)
        
        # Tool cache
        self.available_tools: Dict[str, List[Dict]] = {}
        self.tools_cache_time: Optional[datetime] = None
        self.cache_ttl = 300  # 5 minutes
        
        # Usage tracking
        self.usage_metrics = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'servers_used': set(),
            'tools_used': set()
        }
        
        logger.info(f"AgentMCPBridge initialized for {agent_type} (session: {self.session_id})")
    
    def _check_permission(self, server_name: str) -> bool:
        """Check if agent has permission to use a specific server"""
        if not self.mcp_client:
            logger.warning(f"No MCP client available for {self.agent_type}")
            return False
        
        allowed = self.mcp_client.check_agent_permissions(self.agent_type, server_name)
        self.session.permissions[server_name] = allowed
        
        if not allowed:
            logger.warning(f"Permission denied: {self.agent_type} attempted to access {server_name}")
            self.session.errors.append(f"Permission denied for server: {server_name}")
        
        return allowed
    
    def _record_usage(self, tool_name: str, server_name: str, success: bool, 
                     execution_time: float, error: Optional[str] = None,
                     parameters: Optional[Dict[str, Any]] = None):
        """Record tool usage for metrics"""
        record = ToolUsageRecord(
            agent_id=self.agent_type,
            tool_name=tool_name,
            server_name=server_name,
            timestamp=datetime.now(timezone.utc),
            success=success,
            execution_time_ms=execution_time * 1000,
            error_message=error,
            parameters=parameters
        )
        
        self.session.tool_usage.append(record)
        
        # Update metrics
        self.usage_metrics['total_calls'] += 1
        if success:
            self.usage_metrics['successful_calls'] += 1
        else:
            self.usage_metrics['failed_calls'] += 1
        
        self.usage_metrics['servers_used'].add(server_name)
        self.usage_metrics['tools_used'].add(f"{server_name}.{tool_name}")
    
    async def get_available_tools(self, refresh_cache: bool = False) -> Dict[str, List[Dict]]:
        """Get all available tools for this agent with caching"""
        # Check cache validity
        if (not refresh_cache and self.available_tools and self.tools_cache_time and 
            (datetime.now(timezone.utc) - self.tools_cache_time).total_seconds() < self.cache_ttl):
            return self.available_tools
        
        if not self.mcp_client:
            logger.error(f"No MCP client available for {self.agent_type}")
            return {}
        
        tools_by_server = {}
        agent_permissions = self.mcp_client.get_tools_for_agent(self.agent_type)
        
        for server_name in agent_permissions:
            if not self._check_permission(server_name):
                continue
            
            try:
                tools = await self.mcp_client.list_tools(server_name)
                tools_by_server[server_name] = tools
                logger.debug(f"Listed {len(tools)} tools from {server_name} for {self.agent_type}")
            except Exception as e:
                logger.error(f"Failed to list tools from {server_name}: {e}")
                tools_by_server[server_name] = []
                self.session.errors.append(f"Failed to list tools from {server_name}: {str(e)}")
        
        # Update cache
        self.available_tools = tools_by_server
        self.tools_cache_time = datetime.now(timezone.utc)
        
        return tools_by_server
    
    def get_tool_documentation(self, server_name: str, tool_name: str) -> Optional[Dict]:
        """Get documentation for a specific tool"""
        if server_name not in self.available_tools:
            return None
        
        for tool in self.available_tools[server_name]:
            if tool.get('name') == tool_name:
                return {
                    'name': tool.get('name'),
                    'description': tool.get('description'),
                    'parameters': tool.get('inputSchema', {}).get('properties', {}),
                    'required': tool.get('inputSchema', {}).get('required', []),
                    'examples': tool.get('examples', [])
                }
        
        return None
    
    def validate_permissions(self, server_name: str, tool_name: str) -> bool:
        """Validate if agent can use a specific tool"""
        if not self._check_permission(server_name):
            return False
        
        # Additional tool-specific permission checks can be added here
        # For now, if server access is allowed, all tools on that server are allowed
        return True
    
    async def use_tool(self, server_name: str, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool with comprehensive error handling and logging
        
        Returns:
            Dict with 'success', 'result', 'error', 'metadata', and 'recovery_info' keys
        """
        start_time = time.time()
        context = {
            'server_name': server_name,
            'tool_name': tool_name,
            'agent_id': self.agent_type,
            'parameters': parameters
        }
        
        try:
            # Validate permissions
            if not self.validate_permissions(server_name, tool_name):
                error_msg = f"Permission denied for {server_name}.{tool_name}"
                self._record_usage(tool_name, server_name, False, time.time() - start_time, error_msg, parameters)
                
                # Handle permission error
                permission_error = Exception(error_msg)
                recovery_result = await self.error_handler.handle_error(permission_error, context)
                
                return {
                    'success': False,
                    'result': None,
                    'error': error_msg,
                    'metadata': {
                        'execution_time_ms': (time.time() - start_time) * 1000,
                        'agent': self.agent_type,
                        'session': self.session_id
                    },
                    'recovery_info': recovery_result
                }
            
            # Validate MCP client
            if not self.mcp_client:
                error_msg = "No MCP client available"
                self._record_usage(tool_name, server_name, False, time.time() - start_time, error_msg, parameters)
                
                client_error = Exception(error_msg)
                recovery_result = await self.error_handler.handle_error(client_error, context)
                
                return {
                    'success': False,
                    'result': None,
                    'error': error_msg,
                    'metadata': {'execution_time_ms': (time.time() - start_time) * 1000},
                    'recovery_info': recovery_result
                }
            
            # Execute tool with retry logic
            result = None
            last_error = None
            max_retries = 2
            
            for attempt in range(max_retries + 1):
                try:
                    logger.info(f"Executing {server_name}.{tool_name} for {self.agent_type} (attempt {attempt + 1})")
                    result = await self.mcp_client.call_tool(server_name, tool_name, parameters)
                    
                    execution_time = time.time() - start_time
                    self._record_usage(tool_name, server_name, True, execution_time, parameters=parameters)
                    
                    return {
                        'success': True,
                        'result': result,
                        'error': None,
                        'metadata': {
                            'execution_time_ms': execution_time * 1000,
                            'agent': self.agent_type,
                            'session': self.session_id,
                            'server': server_name,
                            'attempts': attempt + 1
                        }
                    }
                    
                except Exception as tool_error:
                    last_error = tool_error
                    
                    # Handle error with recovery
                    recovery_result = await self.error_handler.handle_error(tool_error, context)
                    
                    if recovery_result.get('success') and attempt < max_retries:
                        # Recovery successful, try again
                        logger.info(f"Recovery successful, retrying {server_name}.{tool_name}")
                        continue
                    elif attempt < max_retries:
                        # Recovery failed, but we can try once more
                        delay = (attempt + 1) * 2
                        logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        # Final attempt failed
                        break
            
            # All attempts failed
            execution_time = time.time() - start_time
            error_msg = str(last_error) if last_error else "Unknown error"
            
            logger.error(f"Tool execution failed after {max_retries + 1} attempts: {server_name}.{tool_name} - {error_msg}")
            logger.debug(f"Tool execution traceback: {traceback.format_exc()}")
            
            self._record_usage(tool_name, server_name, False, execution_time, error_msg, parameters)
            self.session.errors.append(f"Tool {tool_name} failed: {error_msg}")
            
            # Final error recovery attempt
            final_recovery = await self.error_handler.handle_error(last_error, context) if last_error else {}
            
            return {
                'success': False,
                'result': None,
                'error': error_msg,
                'metadata': {
                    'execution_time_ms': execution_time * 1000,
                    'agent': self.agent_type,
                    'session': self.session_id,
                    'server': server_name,
                    'attempts': max_retries + 1
                },
                'recovery_info': final_recovery
            }
            
        except Exception as e:
            # Unexpected error in error handling
            execution_time = time.time() - start_time
            error_msg = f"Unexpected error in tool execution: {str(e)}"
            
            logger.error(f"Unexpected error: {error_msg}")
            logger.debug(f"Unexpected error traceback: {traceback.format_exc()}")
            
            self._record_usage(tool_name, server_name, False, execution_time, error_msg, parameters)
            self.session.errors.append(error_msg)
            
            return {
                'success': False,
                'result': None,
                'error': error_msg,
                'metadata': {
                    'execution_time_ms': execution_time * 1000,
                    'agent': self.agent_type,
                    'session': self.session_id,
                    'server': server_name
                },
                'recovery_info': {'success': False, 'reason': 'Unexpected error in error handling'}
            }
    
    # High-level tool methods for common operations
    async def github_create_issue(self, title: str, body: str, labels: List[str] = None) -> Dict:
        """Create a GitHub issue"""
        return await self.use_tool('github', 'create_issue', {
            'title': title,
            'body': body,
            'labels': labels or []
        })
    
    async def github_create_pr(self, title: str, body: str, head: str, base: str = 'main') -> Dict:
        """Create a GitHub pull request"""
        return await self.use_tool('github', 'create_pull_request', {
            'title': title,
            'body': body,
            'head': head,
            'base': base
        })
    
    async def filesystem_read(self, path: str) -> Dict:
        """Read a file from the filesystem"""
        return await self.use_tool('filesystem', 'read_file', {'path': path})
    
    async def filesystem_write(self, path: str, content: str) -> Dict:
        """Write a file to the filesystem"""
        return await self.use_tool('filesystem', 'write_file', {
            'path': path,
            'content': content
        })
    
    async def filesystem_list(self, path: str) -> Dict:
        """List files in a directory"""
        return await self.use_tool('filesystem', 'list_directory', {'path': path})
    
    async def database_query(self, query: str, params: List[Any] = None) -> Dict:
        """Execute a database query"""
        return await self.use_tool('postgres', 'execute_query', {
            'query': query,
            'params': params or []
        })
    
    async def search_web(self, query: str, max_results: int = 10) -> Dict:
        """Search the web using Brave Search"""
        return await self.use_tool('brave-search', 'web_search', {
            'query': query,
            'count': max_results
        })
    
    async def docker_run(self, image: str, command: str = None, env: Dict[str, str] = None) -> Dict:
        """Run a Docker container"""
        return await self.use_tool('docker', 'run_container', {
            'image': image,
            'command': command,
            'environment': env or {}
        })
    
    async def e2b_execute(self, code: str, language: str = 'python') -> Dict:
        """Execute code in E2B sandbox"""
        return await self.use_tool('e2b', 'execute_code', {
            'language': language,
            'code': code
        })
    
    def get_session_metrics(self) -> Dict[str, Any]:
        """Get comprehensive session metrics"""
        session_duration = (datetime.now(timezone.utc) - self.session.start_time).total_seconds()
        
        return {
            'session_id': self.session_id,
            'agent_type': self.agent_type,
            'session_duration_seconds': session_duration,
            'usage_metrics': {
                'total_calls': self.usage_metrics['total_calls'],
                'successful_calls': self.usage_metrics['successful_calls'],
                'failed_calls': self.usage_metrics['failed_calls'],
                'success_rate': (
                    self.usage_metrics['successful_calls'] / self.usage_metrics['total_calls'] 
                    if self.usage_metrics['total_calls'] > 0 else 0
                ),
                'servers_used': list(self.usage_metrics['servers_used']),
                'tools_used': list(self.usage_metrics['tools_used'])
            },
            'permissions': self.session.permissions,
            'error_count': len(self.session.errors),
            'recent_errors': self.session.errors[-5:] if self.session.errors else [],
            'tool_usage_by_server': self._get_usage_by_server(),
            'average_execution_time_ms': self._get_average_execution_time()
        }
    
    def _get_usage_by_server(self) -> Dict[str, int]:
        """Get tool usage breakdown by server"""
        usage_by_server = {}
        for record in self.session.tool_usage:
            usage_by_server[record.server_name] = usage_by_server.get(record.server_name, 0) + 1
        return usage_by_server
    
    def _get_average_execution_time(self) -> float:
        """Get average tool execution time"""
        if not self.session.tool_usage:
            return 0.0
        
        total_time = sum(record.execution_time_ms for record in self.session.tool_usage)
        return total_time / len(self.session.tool_usage)
    
    def generate_tool_usage_report(self) -> str:
        """Generate a human-readable tool usage report"""
        metrics = self.get_session_metrics()
        
        report = f"""
=== MCP Tool Usage Report ===
Agent: {self.agent_type}
Session: {self.session_id}
Duration: {metrics['session_duration_seconds']:.1f} seconds

Usage Summary:
- Total tool calls: {metrics['usage_metrics']['total_calls']}
- Successful calls: {metrics['usage_metrics']['successful_calls']}
- Failed calls: {metrics['usage_metrics']['failed_calls']}
- Success rate: {metrics['usage_metrics']['success_rate']:.1%}
- Average execution time: {metrics['average_execution_time_ms']:.1f}ms

Servers Used: {', '.join(metrics['usage_metrics']['servers_used']) if metrics['usage_metrics']['servers_used'] else 'None'}
Tools Used: {len(metrics['usage_metrics']['tools_used'])}

Permissions:"""
        
        for server, allowed in metrics['permissions'].items():
            report += f"\n- {server}: {'✓' if allowed else '✗'}"
        
        if metrics['recent_errors']:
            report += f"\n\nRecent Errors ({metrics['error_count']} total):"
            for error in metrics['recent_errors']:
                report += f"\n- {error}"
        
        return report
    
    async def close(self):
        """Close the bridge and generate final metrics"""
        logger.info(f"Closing AgentMCPBridge for {self.agent_type}")
        
        # Generate final report
        if self.usage_metrics['total_calls'] > 0:
            report = self.generate_tool_usage_report()
            logger.info(f"Final MCP usage report for {self.agent_type}:\n{report}")
        
        # Save metrics to file for analysis
        await self._save_session_metrics()
    
    async def _save_session_metrics(self):
        """Save session metrics to file for analysis"""
        try:
            metrics_dir = Path(__file__).parent.parent / "metrics" / "mcp_usage"
            metrics_dir.mkdir(parents=True, exist_ok=True)
            
            metrics_file = metrics_dir / f"{self.agent_type}_{self.session_id}.json"
            
            # Prepare data for serialization
            session_data = {
                'session_id': self.session_id,
                'agent_type': self.agent_type,
                'start_time': self.session.start_time.isoformat(),
                'end_time': datetime.now(timezone.utc).isoformat(),
                'metrics': self.get_session_metrics(),
                'tool_usage': [
                    {
                        'tool_name': record.tool_name,
                        'server_name': record.server_name,
                        'timestamp': record.timestamp.isoformat(),
                        'success': record.success,
                        'execution_time_ms': record.execution_time_ms,
                        'error_message': record.error_message
                    }
                    for record in self.session.tool_usage
                ],
                'errors': self.session.errors
            }
            
            with open(metrics_file, 'w') as f:
                json.dump(session_data, f, indent=2, default=str)
            
            logger.debug(f"Session metrics saved to {metrics_file}")
            
        except Exception as e:
            logger.error(f"Failed to save session metrics: {e}")


class MCPToolsPromptGenerator:
    """Generate prompt sections documenting available MCP tools for agents"""
    
    def __init__(self, bridge: AgentMCPBridge):
        self.bridge = bridge
    
    async def generate_tools_section(self) -> str:
        """Generate a formatted section about available MCP tools"""
        if not self.bridge.mcp_client:
            return ""
        
        tools_by_server = await self.bridge.get_available_tools()
        
        if not tools_by_server:
            return ""
        
        section = """
## MCP TOOLS AVAILABLE

You have access to the following MCP (Model Context Protocol) tools for direct operations:

"""
        
        for server_name, tools in tools_by_server.items():
            if not tools:
                continue
                
            section += f"### {server_name.upper()} Server\n\n"
            
            for tool in tools:
                name = tool.get('name', 'Unknown')
                description = tool.get('description', 'No description available')
                
                section += f"**{name}**: {description}\n"
                
                # Add parameter info if available
                input_schema = tool.get('inputSchema', {})
                properties = input_schema.get('properties', {})
                required = input_schema.get('required', [])
                
                if properties:
                    section += "Parameters:\n"
                    for param_name, param_info in properties.items():
                        param_type = param_info.get('type', 'unknown')
                        param_desc = param_info.get('description', '')
                        required_marker = " (required)" if param_name in required else ""
                        section += f"  - `{param_name}` ({param_type}){required_marker}: {param_desc}\n"
                
                section += "\n"
        
        section += """
**Usage Instructions:**
- Use these tools to directly manipulate files, databases, repositories, and services
- All tool usage is logged and monitored
- Tools respect agent-specific permissions
- Always handle tool failures gracefully

**Examples:**
```python
# Using the bridge in your agent
result = await bridge.filesystem_read('/path/to/file.py')
if result['success']:
    content = result['result']['content']
else:
    print(f"Failed to read file: {result['error']}")

result = await bridge.github_create_issue(
    title="Bug report",
    body="Description of the issue",
    labels=["bug", "high-priority"]
)
```

"""
        
        return section
    
    async def generate_quick_reference(self) -> str:
        """Generate a quick reference of available tools"""
        tools_by_server = await self.bridge.get_available_tools()
        
        if not tools_by_server:
            return "No MCP tools available for this agent."
        
        reference = "**Available MCP Tools:** "
        
        tool_list = []
        for server_name, tools in tools_by_server.items():
            for tool in tools:
                tool_list.append(f"{server_name}.{tool.get('name', 'unknown')}")
        
        reference += ", ".join(tool_list)
        
        return reference