"""
MCP Memory Server for CoralCollective

Provides Memory Context Protocol interface for the advanced memory system.
Allows external tools and agents to interact with project memory.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import logging

from mcp.server import Server
from mcp.types import Tool, TextContent, CallToolRequest, CallToolResult
import mcp.types as types

# Import memory system components
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from memory.memory_system import MemorySystem, MemoryType, ImportanceLevel
from memory.coral_memory_integration import CoralMemoryIntegration

logger = logging.getLogger(__name__)

class MemoryMCPServer:
    """MCP Server for CoralCollective Memory System"""
    
    def __init__(self, project_path: str = None):
        self.server = Server("coral-memory")
        self.project_path = Path(project_path) if project_path else Path.cwd()
        
        # Initialize memory integration
        self.memory_integration: Optional[CoralMemoryIntegration] = None
        
        # Register tools
        self._register_tools()
        
    async def initialize(self):
        """Initialize memory integration"""
        self.memory_integration = CoralMemoryIntegration(
            project_path=self.project_path,
            config_path=str(self.project_path / '.coral' / 'memory_config.json')
        )
        logger.info("Memory MCP Server initialized")
        
    def _register_tools(self):
        """Register MCP tools for memory operations"""
        
        @self.server.call_tool()
        async def add_memory(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Add new memory to the system"""
            
            if not self.memory_integration:
                await self.initialize()
                
            try:
                content = arguments.get("content", "")
                agent_id = arguments.get("agent_id", "unknown")
                context = arguments.get("context", {})
                tags = arguments.get("tags", [])
                memory_type = arguments.get("memory_type", "short_term")
                
                # Convert string memory_type to enum
                if isinstance(memory_type, str):
                    memory_type = MemoryType(memory_type)
                    
                memory_id = await self.memory_integration.memory_system.add_memory(
                    content=content,
                    agent_id=agent_id,
                    project_id=self.memory_integration.project_id,
                    context=context,
                    tags=tags,
                    memory_type=memory_type
                )
                
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "memory_id": memory_id,
                        "message": f"Memory added successfully for agent {agent_id}"
                    }, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"Error adding memory: {e}")
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": str(e)
                    }, indent=2)
                )]
                
        @self.server.call_tool()
        async def search_memories(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Search memories using semantic search"""
            
            if not self.memory_integration:
                await self.initialize()
                
            try:
                query = arguments.get("query", "")
                agent_id = arguments.get("agent_id")
                limit = arguments.get("limit", 10)
                include_short_term = arguments.get("include_short_term", True)
                
                memories = await self.memory_integration.memory_system.search_memories(
                    query=query,
                    agent_id=agent_id,
                    project_id=self.memory_integration.project_id,
                    limit=limit,
                    include_short_term=include_short_term
                )
                
                # Convert memories to serializable format
                results = []
                for memory in memories:
                    results.append({
                        "id": memory.id,
                        "content": memory.content,
                        "agent_id": memory.agent_id,
                        "timestamp": memory.timestamp.isoformat(),
                        "importance": memory.importance.name,
                        "memory_type": memory.memory_type.value,
                        "tags": memory.tags,
                        "context": memory.context
                    })
                    
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "memories": results,
                        "count": len(results)
                    }, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"Error searching memories: {e}")
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": str(e)
                    }, indent=2)
                )]
                
        @self.server.call_tool()
        async def get_agent_context(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Get comprehensive context for an agent"""
            
            if not self.memory_integration:
                await self.initialize()
                
            try:
                agent_id = arguments.get("agent_id")
                include_history = arguments.get("include_history", True)
                context_limit = arguments.get("context_limit", 10)
                
                if not agent_id:
                    raise ValueError("agent_id is required")
                    
                context = await self.memory_integration.get_agent_context(
                    agent_id=agent_id,
                    include_history=include_history,
                    context_limit=context_limit
                )
                
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "agent_id": agent_id,
                        "context": context
                    }, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"Error getting agent context: {e}")
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": str(e)
                    }, indent=2)
                )]
                
        @self.server.call_tool()
        async def record_agent_start(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Record agent start with memory tracking"""
            
            if not self.memory_integration:
                await self.initialize()
                
            try:
                agent_id = arguments.get("agent_id")
                task = arguments.get("task", "")
                context = arguments.get("context", {})
                
                if not agent_id:
                    raise ValueError("agent_id is required")
                    
                memory_id = await self.memory_integration.record_agent_start(
                    agent_id=agent_id,
                    task=task,
                    context=context
                )
                
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "agent_id": agent_id,
                        "memory_id": memory_id,
                        "message": f"Agent start recorded for {agent_id}"
                    }, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"Error recording agent start: {e}")
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": str(e)
                    }, indent=2)
                )]
                
        @self.server.call_tool()
        async def record_agent_completion(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Record agent completion with memory tracking"""
            
            if not self.memory_integration:
                await self.initialize()
                
            try:
                agent_id = arguments.get("agent_id")
                success = arguments.get("success", True)
                outputs = arguments.get("outputs", {})
                artifacts = arguments.get("artifacts", [])
                handoff_data = arguments.get("handoff_data")
                
                if not agent_id:
                    raise ValueError("agent_id is required")
                    
                memory_id = await self.memory_integration.record_agent_completion(
                    agent_id=agent_id,
                    success=success,
                    outputs=outputs,
                    artifacts=artifacts,
                    handoff_data=handoff_data
                )
                
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "agent_id": agent_id,
                        "memory_id": memory_id,
                        "message": f"Agent completion recorded for {agent_id}"
                    }, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"Error recording agent completion: {e}")
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": str(e)
                    }, indent=2)
                )]
                
        @self.server.call_tool()
        async def get_project_timeline(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Get chronological timeline of project activities"""
            
            if not self.memory_integration:
                await self.initialize()
                
            try:
                limit = arguments.get("limit", 20)
                
                timeline = await self.memory_integration.get_project_timeline(limit=limit)
                
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "timeline": timeline,
                        "count": len(timeline)
                    }, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"Error getting project timeline: {e}")
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": str(e)
                    }, indent=2)
                )]
                
        @self.server.call_tool()
        async def search_project_knowledge(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Search project knowledge base"""
            
            if not self.memory_integration:
                await self.initialize()
                
            try:
                query = arguments.get("query", "")
                agent_id = arguments.get("agent_id")
                limit = arguments.get("limit", 10)
                
                results = await self.memory_integration.search_project_knowledge(
                    query=query,
                    agent_id=agent_id,
                    limit=limit
                )
                
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "query": query,
                        "results": results,
                        "count": len(results)
                    }, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"Error searching project knowledge: {e}")
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": str(e)
                    }, indent=2)
                )]
                
        @self.server.call_tool()
        async def get_memory_stats(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Get memory system statistics"""
            
            if not self.memory_integration:
                await self.initialize()
                
            try:
                stats = self.memory_integration.memory_system.get_memory_stats()
                
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "stats": stats,
                        "project_id": self.memory_integration.project_id
                    }, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"Error getting memory stats: {e}")
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": str(e)
                    }, indent=2)
                )]
                
        @self.server.call_tool()
        async def consolidate_memory(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Perform memory consolidation"""
            
            if not self.memory_integration:
                await self.initialize()
                
            try:
                await self.memory_integration.consolidate_session_memory()
                
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "message": "Memory consolidation completed"
                    }, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"Error consolidating memory: {e}")
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": str(e)
                    }, indent=2)
                )]
                
        @self.server.call_tool()
        async def export_project_memory(arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Export project memory to file"""
            
            if not self.memory_integration:
                await self.initialize()
                
            try:
                output_path = arguments.get("output_path")
                if output_path:
                    output_path = Path(output_path)
                    
                export_path = await self.memory_integration.export_project_memory(output_path)
                
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "export_path": str(export_path),
                        "message": f"Project memory exported to {export_path}"
                    }, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"Error exporting memory: {e}")
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": str(e)
                    }, indent=2)
                )]

    def get_available_tools(self) -> List[Tool]:
        """Get list of available MCP tools"""
        
        return [
            Tool(
                name="add_memory",
                description="Add new memory to the system",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Memory content"
                        },
                        "agent_id": {
                            "type": "string",
                            "description": "ID of the agent creating the memory"
                        },
                        "context": {
                            "type": "object",
                            "description": "Optional context data"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags for categorizing memory"
                        },
                        "memory_type": {
                            "type": "string",
                            "enum": ["short_term", "long_term", "episodic", "procedural", "semantic"],
                            "description": "Type of memory"
                        }
                    },
                    "required": ["content", "agent_id"]
                }
            ),
            Tool(
                name="search_memories",
                description="Search memories using semantic search",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "agent_id": {
                            "type": "string",
                            "description": "Optional agent ID filter"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results"
                        },
                        "include_short_term": {
                            "type": "boolean",
                            "description": "Include short-term memories"
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="get_agent_context",
                description="Get comprehensive context for an agent",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "description": "Agent ID"
                        },
                        "include_history": {
                            "type": "boolean",
                            "description": "Include agent history"
                        },
                        "context_limit": {
                            "type": "integer",
                            "description": "Limit for context items"
                        }
                    },
                    "required": ["agent_id"]
                }
            ),
            Tool(
                name="record_agent_start",
                description="Record agent start with memory tracking",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "description": "Agent ID"
                        },
                        "task": {
                            "type": "string",
                            "description": "Task description"
                        },
                        "context": {
                            "type": "object",
                            "description": "Optional context data"
                        }
                    },
                    "required": ["agent_id", "task"]
                }
            ),
            Tool(
                name="record_agent_completion",
                description="Record agent completion with memory tracking",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "description": "Agent ID"
                        },
                        "success": {
                            "type": "boolean",
                            "description": "Success status"
                        },
                        "outputs": {
                            "type": "object",
                            "description": "Agent outputs"
                        },
                        "artifacts": {
                            "type": "array",
                            "description": "Created artifacts"
                        },
                        "handoff_data": {
                            "type": "object",
                            "description": "Handoff data for next agent"
                        }
                    },
                    "required": ["agent_id"]
                }
            ),
            Tool(
                name="get_project_timeline",
                description="Get chronological timeline of project activities",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of timeline events"
                        }
                    }
                }
            ),
            Tool(
                name="search_project_knowledge",
                description="Search project knowledge base",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "agent_id": {
                            "type": "string",
                            "description": "Optional agent ID filter"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results"
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="get_memory_stats",
                description="Get memory system statistics",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="consolidate_memory",
                description="Perform memory consolidation",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="export_project_memory",
                description="Export project memory to file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "output_path": {
                            "type": "string",
                            "description": "Optional output file path"
                        }
                    }
                }
            )
        ]

# Server factory function
def create_memory_server(project_path: str = None) -> MemoryMCPServer:
    """Create and configure memory MCP server"""
    return MemoryMCPServer(project_path)

# CLI for running the server
if __name__ == "__main__":
    import argparse
    import asyncio
    
    parser = argparse.ArgumentParser(description="CoralCollective Memory MCP Server")
    parser.add_argument("--project-path", type=str, help="Project path")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    
    args = parser.parse_args()
    
    async def main():
        server = create_memory_server(args.project_path)
        await server.initialize()
        
        # Start MCP server
        import mcp.server.stdio
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.server.run(read_stream, write_stream, server.initialize)
            
    asyncio.run(main())