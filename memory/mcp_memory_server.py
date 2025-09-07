#!/usr/bin/env python3
"""
MCP Memory Server for CoralCollective

Provides memory system tools as MCP server for agent access
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from .memory_integration import CoralMemoryIntegration
from .memory_architecture import MemoryType

logger = logging.getLogger(__name__)


class MCPMemoryServer:
    """MCP server providing memory system tools"""
    
    def __init__(self, memory_integration: CoralMemoryIntegration):
        self.memory = memory_integration
        self.tools = {
            'memory_store': self._store_memory,
            'memory_search': self._search_memory,
            'memory_get_context': self._get_context,
            'memory_get_stats': self._get_stats,
            'memory_summarize_session': self._summarize_session,
            'memory_record_error': self._record_error,
            'memory_record_decision': self._record_decision,
            'memory_record_requirement': self._record_requirement,
            'memory_list_types': self._list_memory_types,
            'memory_get_agent_history': self._get_agent_history
        }
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available memory tools for MCP"""
        return [
            {
                "name": "memory_store",
                "description": "Store information in agent memory system",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Content to store"},
                        "memory_type": {"type": "string", "description": "Type of memory (interaction, code_pattern, requirement, etc.)"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for categorization"},
                        "metadata": {"type": "object", "description": "Additional metadata"}
                    },
                    "required": ["content", "memory_type"]
                }
            },
            {
                "name": "memory_search",
                "description": "Search memory system for relevant information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "memory_types": {"type": "array", "items": {"type": "string"}, "description": "Filter by memory types"},
                        "max_results": {"type": "integer", "default": 10, "description": "Maximum results to return"},
                        "agent_filter": {"type": "string", "description": "Filter by specific agent"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "memory_get_context",
                "description": "Get relevant memory context for current task",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string", "description": "Current task description"},
                        "max_length": {"type": "integer", "default": 2000, "description": "Maximum context length"}
                    },
                    "required": ["task"]
                }
            },
            {
                "name": "memory_get_stats",
                "description": "Get memory system statistics and status",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "memory_summarize_session",
                "description": "Create summary of current session",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "memory_record_error",
                "description": "Record error resolution for learning",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "error_description": {"type": "string", "description": "Description of the error"},
                        "solution": {"type": "string", "description": "Solution that resolved the error"},
                        "error_type": {"type": "string", "description": "Type/category of error"}
                    },
                    "required": ["error_description", "solution"]
                }
            },
            {
                "name": "memory_record_decision",
                "description": "Record important decision with rationale",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "decision": {"type": "string", "description": "The decision made"},
                        "rationale": {"type": "string", "description": "Reasoning behind the decision"},
                        "decision_type": {"type": "string", "description": "Type of decision (technical, architectural, etc.)"}
                    },
                    "required": ["decision", "rationale"]
                }
            },
            {
                "name": "memory_record_requirement",
                "description": "Record project requirement",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "requirement": {"type": "string", "description": "The requirement description"},
                        "requirement_type": {"type": "string", "description": "Type of requirement (functional, non-functional, etc.)"}
                    },
                    "required": ["requirement"]
                }
            },
            {
                "name": "memory_list_types",
                "description": "List available memory types",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "memory_get_agent_history",
                "description": "Get memory history for specific agent",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string", "description": "Agent identifier"},
                        "days": {"type": "integer", "default": 7, "description": "Number of days to look back"}
                    },
                    "required": ["agent_id"]
                }
            }
        ]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute memory tool"""
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            result = await self.tools[tool_name](arguments)
            return {"result": result, "success": True}
        except Exception as e:
            logger.error(f"Memory tool {tool_name} failed: {e}")
            return {"error": str(e), "success": False}
    
    async def _store_memory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Store information in memory"""
        content = args['content']
        memory_type_str = args['memory_type']
        tags = args.get('tags', [])
        metadata = args.get('metadata', {})
        
        # Convert string to enum
        try:
            memory_type = MemoryType(memory_type_str)
        except ValueError:
            return {"error": f"Invalid memory type: {memory_type_str}"}
        
        # Store in memory
        interaction_id = await self.memory.memory_manager.store_interaction(
            agent_id=self.memory.current_agent_id or "unknown",
            content=content,
            memory_type=memory_type,
            project_id=self.memory.current_project_id,
            metadata=metadata,
            tags=tags
        )
        
        return {
            "interaction_id": interaction_id,
            "message": "Memory stored successfully"
        }
    
    async def _search_memory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search memory system"""
        query = args['query']
        memory_types = args.get('memory_types', [])
        max_results = args.get('max_results', 10)
        agent_filter = args.get('agent_filter')
        
        # Search memories
        results = await self.memory.search_memories(
            query=query,
            agent_id=agent_filter,
            memory_types=memory_types,
            max_results=max_results
        )
        
        return {
            "memories": results,
            "count": len(results),
            "query": query
        }
    
    async def _get_context(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get relevant context for task"""
        task = args['task']
        max_length = args.get('max_length', 2000)
        
        context = await self.memory.get_agent_context(
            agent_id=self.memory.current_agent_id or "unknown",
            task=task,
            max_length=max_length
        )
        
        return {
            "context": context,
            "length": len(context),
            "task": task
        }
    
    async def _get_stats(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get memory system statistics"""
        stats = await self.memory.get_memory_stats()
        return stats
    
    async def _summarize_session(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create session summary"""
        summary_id = await self.memory.create_session_summary()
        return {
            "summary_id": summary_id,
            "message": "Session summary created"
        }
    
    async def _record_error(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Record error resolution"""
        await self.memory.on_error_resolution(
            agent_id=self.memory.current_agent_id or "unknown",
            error_description=args['error_description'],
            solution=args['solution'],
            error_type=args.get('error_type', 'unknown')
        )
        
        return {"message": "Error resolution recorded"}
    
    async def _record_decision(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Record important decision"""
        await self.memory.on_decision_made(
            agent_id=self.memory.current_agent_id or "unknown",
            decision=args['decision'],
            rationale=args['rationale'],
            decision_type=args.get('decision_type', 'technical')
        )
        
        return {"message": "Decision recorded"}
    
    async def _record_requirement(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Record project requirement"""
        await self.memory.on_requirement_capture(
            agent_id=self.memory.current_agent_id or "unknown",
            requirement=args['requirement'],
            requirement_type=args.get('requirement_type', 'functional')
        )
        
        return {"message": "Requirement recorded"}
    
    async def _list_memory_types(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List available memory types"""
        types = [
            {
                "name": mt.value,
                "description": mt.value.replace('_', ' ').title()
            }
            for mt in MemoryType
        ]
        
        return {"memory_types": types}
    
    async def _get_agent_history(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get agent history"""
        agent_id = args['agent_id']
        days = args.get('days', 7)
        
        # Create time range
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        
        # Search for agent's memories in time range
        results = await self.memory.search_memories(
            query=f"agent:{agent_id}",
            agent_id=agent_id,
            max_results=50
        )
        
        # Filter by time range
        filtered_results = [
            result for result in results
            if start_time <= datetime.fromisoformat(result['timestamp']) <= end_time
        ]
        
        return {
            "agent_id": agent_id,
            "days": days,
            "memories": filtered_results,
            "count": len(filtered_results)
        }


class MCPMemoryConfig:
    """Configuration for MCP memory server"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.config_path = project_path / "mcp" / "configs" / "memory_config.yaml"
    
    def get_server_config(self) -> Dict[str, Any]:
        """Get MCP server configuration for memory"""
        return {
            "name": "memory",
            "command": "python",
            "args": [
                str(self.project_path / "memory" / "mcp_memory_server.py"),
                "--project-path", str(self.project_path)
            ],
            "env": {},
            "enabled": True,
            "permissions": [
                "memory_store",
                "memory_search", 
                "memory_get_context",
                "memory_get_stats",
                "memory_summarize_session",
                "memory_record_error",
                "memory_record_decision",
                "memory_record_requirement",
                "memory_list_types",
                "memory_get_agent_history"
            ],
            "timeout": 30,
            "retry_attempts": 3,
            "max_concurrent_requests": 5,
            "features": ["memory_storage", "semantic_search", "context_injection"],
            "agents": ["all"]  # All agents can use memory
        }
    
    def get_agent_permissions(self) -> Dict[str, Any]:
        """Get agent permissions for memory server"""
        return {
            "backend_developer": {
                "servers": ["memory"],
                "tools": [
                    "memory_store", "memory_search", "memory_get_context",
                    "memory_record_error", "memory_record_decision"
                ]
            },
            "frontend_developer": {
                "servers": ["memory"],
                "tools": [
                    "memory_store", "memory_search", "memory_get_context",
                    "memory_record_error"
                ]
            },
            "project_architect": {
                "servers": ["memory"],
                "tools": [
                    "memory_store", "memory_search", "memory_get_context",
                    "memory_record_decision", "memory_record_requirement",
                    "memory_get_stats"
                ]
            },
            "qa_testing": {
                "servers": ["memory"],
                "tools": [
                    "memory_store", "memory_search", "memory_record_error"
                ]
            },
            "devops_deployment": {
                "servers": ["memory"],
                "tools": [
                    "memory_store", "memory_search", "memory_get_context",
                    "memory_record_error", "memory_record_decision"
                ]
            }
        }


# Standalone server entry point for MCP
async def main():
    """Main entry point for MCP memory server"""
    import argparse
    import sys
    from pathlib import Path
    
    parser = argparse.ArgumentParser(description="CoralCollective Memory MCP Server")
    parser.add_argument("--project-path", type=Path, required=True,
                       help="Path to CoralCollective project")
    parser.add_argument("--config", type=Path, help="Memory configuration file")
    
    args = parser.parse_args()
    
    try:
        # Initialize memory integration
        config = {}
        if args.config and args.config.exists():
            with open(args.config, 'r') as f:
                config = json.load(f)
        
        memory_integration = CoralMemoryIntegration(args.project_path, config)
        
        # Create MCP server
        mcp_server = MCPMemoryServer(memory_integration)
        
        # Simple JSON-RPC server loop for MCP
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                request = json.loads(line.strip())
                
                if request.get("method") == "tools/list":
                    tools = await mcp_server.list_tools()
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": {"tools": tools}
                    }
                
                elif request.get("method") == "tools/call":
                    params = request.get("params", {})
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    
                    result = await mcp_server.call_tool(tool_name, arguments)
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": result
                    }
                
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {"code": -32601, "message": "Method not found"}
                    }
                
                print(json.dumps(response))
                sys.stdout.flush()
                
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id") if 'request' in locals() else None,
                    "error": {"code": -32603, "message": str(e)}
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
                
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Memory MCP server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())