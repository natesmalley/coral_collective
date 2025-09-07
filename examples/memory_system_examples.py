"""
CoralCollective Memory System Examples

Comprehensive examples demonstrating memory system usage, integration patterns,
and advanced features for CoralCollective agents.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Example project setup (assumes memory system is installed)
async def example_basic_setup():
    """Example: Basic memory system setup for a new project"""
    
    from memory import setup_memory_for_project
    
    # Initialize memory for a project
    memory_integration = await setup_memory_for_project(
        project_path="./example_project",
        auto_migrate=True
    )
    
    print(f"Memory system initialized for project: {memory_integration.project_id}")
    
    # Add a memory
    memory_id = await memory_integration.memory_system.add_memory(
        content="Project initialization completed with memory system",
        agent_id="project_setup",
        project_id=memory_integration.project_id,
        context={"phase": "initialization", "memory_enabled": True},
        tags=["setup", "initialization"]
    )
    
    print(f"Added initial memory: {memory_id}")
    
    return memory_integration

async def example_agent_workflow_with_memory():
    """Example: Complete agent workflow with memory integration"""
    
    from memory import MemoryEnhancedAgentRunner
    
    # Create memory-enhanced runner
    runner = MemoryEnhancedAgentRunner(enable_memory=True)
    
    print("=== Agent Workflow with Memory ===")
    
    # Simulate agent execution workflow
    agents_sequence = [
        ("project_architect", "Design project architecture"),
        ("backend_developer", "Implement REST API"),
        ("frontend_developer", "Create React components"),
        ("qa_testing", "Write and run tests")
    ]
    
    workflow_results = []
    
    for agent_id, task in agents_sequence:
        print(f"\n🤖 Running {agent_id}: {task}")
        
        # Get agent context before execution
        context = await runner.memory_integration.get_agent_context(agent_id)
        print(f"  📋 Context loaded: {len(context['memory_context']['recent_memories'])} recent memories")
        
        # Run agent with memory
        result = await runner.run_agent_with_memory(agent_id, task)
        workflow_results.append(result)
        
        # Simulate agent output
        await runner.memory_integration.record_agent_output(
            agent_id=agent_id,
            output=f"Completed {task} successfully. Created necessary files and configurations.",
            output_type="completion",
            artifacts=[{
                "type": "code",
                "path": f"/src/{agent_id}_output.py",
                "description": f"Generated code from {agent_id}"
            }]
        )
        
        print(f"  ✅ Agent completed with memory ID: {result.get('memory_ids', {}).get('completion')}")
        
    # Show final memory stats
    stats = runner.get_memory_stats()
    print(f"\n📊 Final memory stats: {stats}")
    
    return workflow_results

async def example_memory_search_and_retrieval():
    """Example: Advanced memory search and retrieval patterns"""
    
    from memory import CoralMemoryIntegration
    
    # Initialize memory integration
    memory_integration = CoralMemoryIntegration(Path("./example_project"))
    
    print("=== Memory Search Examples ===")
    
    # Add some example memories
    example_memories = [
        {
            "content": "Created REST API endpoints for user authentication using JWT tokens",
            "agent_id": "backend_developer", 
            "context": {"endpoints": ["login", "register", "logout"], "auth_method": "JWT"},
            "tags": ["api", "authentication", "backend"]
        },
        {
            "content": "Implemented React components with TypeScript and Material-UI styling",
            "agent_id": "frontend_developer",
            "context": {"components": ["UserProfile", "LoginForm"], "framework": "React", "styling": "Material-UI"},
            "tags": ["frontend", "react", "components"]
        },
        {
            "content": "Database schema designed with PostgreSQL, includes users, products, orders tables",
            "agent_id": "database_specialist", 
            "context": {"database": "PostgreSQL", "tables": ["users", "products", "orders"]},
            "tags": ["database", "schema", "postgresql"]
        }
    ]
    
    # Add memories
    memory_ids = []
    for memory_data in example_memories:
        memory_id = await memory_integration.memory_system.add_memory(
            content=memory_data["content"],
            agent_id=memory_data["agent_id"],
            project_id=memory_integration.project_id,
            context=memory_data["context"],
            tags=memory_data["tags"]
        )
        memory_ids.append(memory_id)
        print(f"  Added memory: {memory_data['agent_id']} -> {memory_id[:8]}...")
        
    # Search examples
    search_queries = [
        "authentication API",
        "React components",
        "database schema",
        "PostgreSQL tables",
        "JWT tokens"
    ]
    
    for query in search_queries:
        print(f"\n🔍 Searching for: '{query}'")
        results = await memory_integration.search_project_knowledge(query, limit=3)
        
        for i, result in enumerate(results):
            print(f"  {i+1}. [{result['agent_id']}] {result['content'][:60]}...")
            print(f"     Tags: {', '.join(result['tags'])}")
            
    return memory_ids

async def example_agent_context_enhancement():
    """Example: How memory enhances agent context"""
    
    from memory import CoralMemoryIntegration
    
    memory_integration = CoralMemoryIntegration(Path("./example_project"))
    
    print("=== Agent Context Enhancement ===")
    
    # Simulate previous agent activities
    await memory_integration.record_agent_start(
        "project_architect", 
        "Design microservices architecture",
        {"architecture_type": "microservices", "services": ["user", "product", "order"]}
    )
    
    await memory_integration.record_agent_completion(
        "project_architect",
        success=True,
        outputs={"architecture_doc": "architecture.md", "service_specs": ["user_service.yaml"]},
        handoff_data={
            "next_agent": "backend_developer",
            "summary": "Microservices architecture designed with 3 main services",
            "requirements": ["Implement user service first", "Use PostgreSQL for data", "Add JWT authentication"]
        }
    )
    
    # Now get context for next agent
    print("\n📋 Getting context for backend_developer:")
    context = await memory_integration.get_agent_context("backend_developer")
    
    # Show different types of context
    print(f"Recent memories: {len(context['memory_context']['recent_memories'])}")
    print(f"Relevant memories: {len(context['memory_context']['relevant_memories'])}")
    
    # Show last handoff information
    if context['project_state']['last_handoff']:
        handoff = context['project_state']['last_handoff']
        print(f"\n🤝 Last handoff from: {handoff['from_agent']}")
        print(f"Summary: {handoff['data'].get('summary', 'No summary')}")
        print(f"Requirements: {handoff['data'].get('requirements', [])}")
        
    # Show enhanced prompt example
    base_prompt = "You are a backend developer. Create API endpoints."
    enhanced_prompt = memory_integration.get_memory_enhanced_prompt(
        "backend_developer", 
        base_prompt,
        include_recent=True,
        include_context=True
    )
    
    print(f"\n📝 Enhanced prompt length: {len(enhanced_prompt)} chars (vs {len(base_prompt)} base)")
    print("Enhanced prompt includes recent project context and handoff information")
    
    return context

async def example_memory_consolidation():
    """Example: Memory consolidation and optimization"""
    
    from memory import CoralMemoryIntegration
    
    memory_integration = CoralMemoryIntegration(Path("./example_project"))
    
    print("=== Memory Consolidation Example ===")
    
    # Add many short-term memories to trigger consolidation
    for i in range(30):  # More than default buffer size
        await memory_integration.memory_system.add_memory(
            content=f"Development log entry {i}: Working on feature implementation",
            agent_id="backend_developer",
            project_id=memory_integration.project_id,
            context={"log_entry": i, "feature": f"feature_{i % 5}"},
            tags=["development", "log"]
        )
        
    print(f"Added 30 development log memories")
    
    # Check memory stats before consolidation
    stats_before = memory_integration.memory_system.get_memory_stats()
    print(f"Before consolidation - Short-term: {stats_before['short_term_memories']}")
    
    # Run consolidation
    print("\n🔄 Running memory consolidation...")
    await memory_integration.consolidate_session_memory()
    
    # Check stats after consolidation
    stats_after = memory_integration.memory_system.get_memory_stats()
    print(f"After consolidation - Short-term: {stats_after['short_term_memories']}, Long-term: {stats_after['long_term_memories']}")
    
    return stats_before, stats_after

async def example_project_timeline():
    """Example: Project timeline and historical analysis"""
    
    from memory import CoralMemoryIntegration
    
    memory_integration = CoralMemoryIntegration(Path("./example_project"))
    
    print("=== Project Timeline Example ===")
    
    # Simulate project progression
    timeline_events = [
        ("project_architect", "Project architecture completed", "Project planning phase finished"),
        ("backend_developer", "User authentication API implemented", "Core authentication system ready"),
        ("database_specialist", "Database schema created and migrated", "Database layer established"),
        ("frontend_developer", "React components for user interface created", "UI components implemented"),
        ("qa_testing", "Unit tests written and passing", "Testing framework established"),
        ("devops_deployment", "CI/CD pipeline configured", "Deployment automation ready")
    ]
    
    # Record timeline events
    for i, (agent, task, summary) in enumerate(timeline_events):
        await memory_integration.record_agent_start(agent, task)
        
        # Simulate some work time
        await asyncio.sleep(0.1)  # Small delay for different timestamps
        
        await memory_integration.record_agent_completion(
            agent,
            success=True,
            outputs={"summary": summary, "phase": f"phase_{i+1}"}
        )
        
        print(f"  📅 {agent}: {task}")
        
    # Get project timeline
    print(f"\n📊 Project Timeline (last 10 events):")
    timeline = await memory_integration.get_project_timeline(limit=10)
    
    for event in timeline:
        timestamp = event['timestamp'][:19].replace('T', ' ')
        print(f"  {timestamp} | {event['agent_id']} | {event['event_type']}")
        print(f"    {event['content'][:80]}...")
        
    return timeline

async def example_cross_agent_knowledge_sharing():
    """Example: How agents share knowledge through memory"""
    
    from memory import CoralMemoryIntegration
    
    memory_integration = CoralMemoryIntegration(Path("./example_project"))
    
    print("=== Cross-Agent Knowledge Sharing ===")
    
    # Backend developer creates API documentation
    await memory_integration.memory_system.add_memory(
        content="""API Documentation:
        
POST /api/auth/login
- Body: {email, password}
- Returns: {token, user}
- Auth: None required

GET /api/users/profile
- Returns: {id, email, name, created_at}
- Auth: Bearer token required

POST /api/products
- Body: {name, description, price}
- Returns: {id, ...product_data}
- Auth: Admin token required
""",
        agent_id="backend_developer",
        project_id=memory_integration.project_id,
        context={
            "type": "api_documentation",
            "endpoints": ["login", "profile", "products"],
            "auth_required": ["profile", "products"]
        },
        tags=["api", "documentation", "endpoints", "authentication"]
    )
    
    print("  📝 Backend developer documented API endpoints")
    
    # Frontend developer searches for API information
    print("\n🔍 Frontend developer searching for API information:")
    api_info = await memory_integration.search_project_knowledge(
        "API endpoints authentication", 
        agent_id=None,  # Search all agents
        limit=5
    )
    
    for result in api_info:
        if "api" in result['tags']:
            print(f"  Found: {result['agent_id']} - {result['content'][:100]}...")
            print(f"  Context: {result['context']}")
            
    # QA Testing agent searches for authentication requirements
    print("\n🔍 QA Testing agent searching for authentication requirements:")
    auth_info = await memory_integration.search_project_knowledge(
        "authentication Bearer token",
        limit=3
    )
    
    for result in auth_info:
        print(f"  Found: {result['agent_id']} - {result['content'][:80]}...")
        
    return api_info

async def example_memory_export_and_analysis():
    """Example: Export memory for analysis and backup"""
    
    from memory import CoralMemoryIntegration
    
    memory_integration = CoralMemoryIntegration(Path("./example_project"))
    
    print("=== Memory Export and Analysis ===")
    
    # Export project memory
    export_path = await memory_integration.export_project_memory()
    print(f"📤 Memory exported to: {export_path}")
    
    # Load and analyze export
    with open(export_path, 'r') as f:
        export_data = json.load(f)
        
    print(f"\n📊 Export Analysis:")
    print(f"  Total memories: {len(export_data['memories'])}")
    print(f"  Memory stats: {export_data['memory_stats']}")
    
    # Analyze by agent
    agent_counts = {}
    for memory in export_data['memories']:
        agent_id = memory['agent_id']
        agent_counts[agent_id] = agent_counts.get(agent_id, 0) + 1
        
    print(f"\n🤖 Memories by agent:")
    for agent_id, count in sorted(agent_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {agent_id}: {count}")
        
    # Analyze by importance
    importance_counts = {}
    for memory in export_data['memories']:
        importance = memory['importance']
        importance_counts[importance] = importance_counts.get(importance, 0) + 1
        
    print(f"\n⭐ Memories by importance:")
    for importance, count in sorted(importance_counts.items(), reverse=True):
        print(f"  Level {importance}: {count}")
        
    return export_data

async def example_mcp_server_integration():
    """Example: Using memory system through MCP server"""
    
    print("=== MCP Server Integration Example ===")
    
    # This example shows how to use memory through MCP server
    # In practice, this would be called by external MCP clients
    
    try:
        from mcp.servers.memory_server import create_memory_server
        
        # Create memory server
        server = create_memory_server("./example_project")
        await server.initialize()
        
        print("  ✅ MCP Memory server initialized")
        
        # Show available tools
        tools = server.get_available_tools()
        print(f"  🛠️  Available tools: {len(tools)}")
        for tool in tools:
            print(f"    - {tool.name}: {tool.description}")
            
        return server
        
    except ImportError:
        print("  ⚠️  MCP server dependencies not available")
        print("  Install with: pip install mcp")
        return None

async def run_all_examples():
    """Run all examples in sequence"""
    
    print("🧠 CoralCollective Memory System Examples\n")
    print("=" * 50)
    
    examples = [
        ("Basic Setup", example_basic_setup),
        ("Agent Workflow with Memory", example_agent_workflow_with_memory),
        ("Memory Search and Retrieval", example_memory_search_and_retrieval),
        ("Agent Context Enhancement", example_agent_context_enhancement),
        ("Memory Consolidation", example_memory_consolidation),
        ("Project Timeline", example_project_timeline),
        ("Cross-Agent Knowledge Sharing", example_cross_agent_knowledge_sharing),
        ("Memory Export and Analysis", example_memory_export_and_analysis),
        ("MCP Server Integration", example_mcp_server_integration)
    ]
    
    results = {}
    
    for example_name, example_func in examples:
        print(f"\n{'='*20} {example_name} {'='*20}")
        
        try:
            result = await example_func()
            results[example_name] = result
            print(f"✅ {example_name} completed successfully")
            
        except Exception as e:
            print(f"❌ {example_name} failed: {e}")
            results[example_name] = {"error": str(e)}
            
        print("-" * 60)
        
    print(f"\n🎉 Examples completed! {len([r for r in results.values() if 'error' not in r])}/{len(examples)} successful")
    
    return results

if __name__ == "__main__":
    # Run examples
    asyncio.run(run_all_examples())