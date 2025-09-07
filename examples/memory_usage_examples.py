#!/usr/bin/env python3
"""
CoralCollective Memory System Usage Examples

This file demonstrates practical usage patterns for the advanced memory system
in real-world CoralCollective projects.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Memory system imports
from memory.memory_system import MemorySystem, MemoryType, ImportanceLevel
from memory.coral_memory_integration import CoralMemoryIntegration, initialize_project_memory
from memory.memory_enhanced_runner import MemoryEnhancedAgentRunner
from memory.migration_strategy import MemoryMigrationStrategy

class MemoryUsageExamples:
    """Collection of memory system usage examples"""
    
    def __init__(self, project_path: Path = None):
        self.project_path = project_path or Path.cwd()
        self.memory_integration = None
        self.memory_system = None
        
    async def initialize_memory_system(self):
        """Initialize the memory system for examples"""
        
        print("🧠 Initializing Memory System...")
        
        # Initialize memory integration
        self.memory_integration = await initialize_project_memory(
            project_path=self.project_path,
            config_path=str(self.project_path / ".coral" / "memory_config.json")
        )
        
        self.memory_system = self.memory_integration.memory_system
        
        print("✅ Memory system initialized successfully")
        return True

    async def example_1_basic_memory_operations(self):
        """Example 1: Basic memory operations - adding, searching, retrieving"""
        
        print("\n" + "="*60)
        print("EXAMPLE 1: Basic Memory Operations")
        print("="*60)
        
        # Add various types of memories
        memories_to_add = [
            {
                "content": "Project architecture designed with microservices pattern",
                "agent_id": "architect",
                "context": {"type": "architecture_decision", "pattern": "microservices"},
                "tags": ["architecture", "microservices", "design"],
                "memory_type": MemoryType.SEMANTIC
            },
            {
                "content": "Database schema created with users, products, and orders tables",
                "agent_id": "database_specialist",
                "context": {"type": "implementation", "component": "database"},
                "tags": ["database", "schema", "implementation"],
                "memory_type": MemoryType.SEMANTIC
            },
            {
                "content": "User authentication API endpoint implemented successfully",
                "agent_id": "backend_developer",
                "context": {"type": "completion", "feature": "auth"},
                "tags": ["api", "authentication", "backend", "completion"],
                "memory_type": MemoryType.EPISODIC
            },
            {
                "content": "Frontend components need API integration for user login",
                "agent_id": "frontend_developer",
                "context": {"type": "requirement", "priority": "high"},
                "tags": ["frontend", "api", "integration", "todo"],
                "memory_type": MemoryType.SHORT_TERM
            }
        ]
        
        print("Adding memories to the system...")
        added_memory_ids = []
        
        for memory_data in memories_to_add:
            memory_id = await self.memory_system.add_memory(
                content=memory_data["content"],
                agent_id=memory_data["agent_id"],
                project_id=self.memory_integration.project_id,
                context=memory_data["context"],
                tags=memory_data["tags"],
                memory_type=memory_data["memory_type"]
            )
            added_memory_ids.append(memory_id)
            print(f"  ✓ Added memory: {memory_id[:8]}... by {memory_data['agent_id']}")
            
        print(f"\n📊 Memory Statistics:")
        stats = self.memory_system.get_memory_stats()
        for key, value in stats.items():
            print(f"  • {key}: {value}")
            
        # Search memories by query
        print(f"\n🔍 Searching for 'API authentication'...")
        search_results = await self.memory_system.search_memories(
            query="API authentication",
            limit=10
        )
        
        print(f"Found {len(search_results)} relevant memories:")
        for result in search_results:
            print(f"  • [{result.agent_id}] {result.content[:80]}...")
            print(f"    Tags: {', '.join(result.tags)}")
            print(f"    Importance: {result.importance.name}")
            
        return added_memory_ids

    async def example_2_agent_context_and_handoffs(self):
        """Example 2: Agent context retrieval and handoff tracking"""
        
        print("\n" + "="*60)
        print("EXAMPLE 2: Agent Context and Handoffs")
        print("="*60)
        
        # Simulate agent workflow with memory tracking
        agents = ["architect", "backend_developer", "frontend_developer", "qa_testing"]
        
        for i, agent_id in enumerate(agents):
            print(f"\n👤 Agent: {agent_id}")
            
            # Record agent start
            task = f"Execute phase {i+1} of development workflow"
            start_memory_id = await self.memory_integration.record_agent_start(
                agent_id=agent_id,
                task=task,
                context={"phase": i+1, "workflow": "full_stack_development"}
            )
            print(f"  🟢 Started: {task}")
            
            # Get agent context
            agent_context = await self.memory_integration.get_agent_context(
                agent_id=agent_id,
                include_history=True
            )
            
            print(f"  📋 Agent Context Summary:")
            print(f"    • Recent memories: {len(agent_context['memory_context']['recent_memories'])}")
            print(f"    • Working memory keys: {len(agent_context['memory_context']['working_memory'])}")
            print(f"    • Relevant memories: {len(agent_context['memory_context']['relevant_memories'])}")
            
            # Simulate some agent work by adding output memory
            outputs = {
                "architect": "System architecture documented with component diagrams",
                "backend_developer": "REST API endpoints implemented with authentication",
                "frontend_developer": "React components created with API integration",
                "qa_testing": "Automated test suite implemented with 90% coverage"
            }
            
            await self.memory_integration.record_agent_output(
                agent_id=agent_id,
                output=outputs[agent_id],
                output_type="completion",
                artifacts=[{"type": "documentation", "path": f"{agent_id}_output.md"}]
            )
            
            # Record agent completion with handoff to next agent
            if i < len(agents) - 1:
                next_agent = agents[i + 1]
                handoff_data = {
                    "summary": f"{agent_id} completed their phase, ready for {next_agent}",
                    "next_agent": next_agent,
                    "artifacts": [f"{agent_id}_output.md"],
                    "context": {"completed_phase": i+1}
                }
                
                completion_memory_id = await self.memory_integration.record_agent_completion(
                    agent_id=agent_id,
                    success=True,
                    outputs={"phase": i+1, "status": "completed"},
                    artifacts=[{"type": "output", "path": f"{agent_id}_output.md"}],
                    handoff_data=handoff_data
                )
                
                print(f"  ✅ Completed with handoff to {next_agent}")
            else:
                # Final agent completion
                await self.memory_integration.record_agent_completion(
                    agent_id=agent_id,
                    success=True,
                    outputs={"phase": i+1, "status": "final_completion"}
                )
                print(f"  ✅ Final completion")
                
        # Show project timeline
        print(f"\n📅 Project Timeline (last 10 events):")
        timeline = await self.memory_integration.get_project_timeline(limit=10)
        
        for event in timeline:
            timestamp = event['timestamp'][:19].replace('T', ' ')
            print(f"  [{timestamp}] {event['agent_id']}: {event['content'][:60]}...")

    async def example_3_memory_search_and_knowledge_base(self):
        """Example 3: Advanced memory search and knowledge base querying"""
        
        print("\n" + "="*60)
        print("EXAMPLE 3: Memory Search and Knowledge Base")
        print("="*60)
        
        # Add some technical knowledge to memory
        knowledge_items = [
            {
                "content": "JWT authentication implementation uses bcrypt for password hashing and includes refresh token rotation for security",
                "agent_id": "security_specialist",
                "context": {"type": "technical_knowledge", "domain": "security"},
                "tags": ["jwt", "authentication", "security", "bcrypt", "tokens"]
            },
            {
                "content": "PostgreSQL database configured with connection pooling, read replicas for scaling, and automated backups every 6 hours",
                "agent_id": "database_specialist", 
                "context": {"type": "technical_knowledge", "domain": "database"},
                "tags": ["postgresql", "database", "scaling", "backups", "performance"]
            },
            {
                "content": "React components follow atomic design principles with shared component library and consistent theming using styled-components",
                "agent_id": "frontend_developer",
                "context": {"type": "technical_knowledge", "domain": "frontend"},
                "tags": ["react", "components", "atomic-design", "theming", "styled-components"]
            },
            {
                "content": "API rate limiting implemented with Redis using sliding window algorithm, configured for 100 requests per minute per user",
                "agent_id": "backend_developer",
                "context": {"type": "technical_knowledge", "domain": "api"},
                "tags": ["api", "rate-limiting", "redis", "sliding-window", "performance"]
            }
        ]
        
        print("Adding technical knowledge to memory...")
        for knowledge in knowledge_items:
            await self.memory_system.add_memory(
                content=knowledge["content"],
                agent_id=knowledge["agent_id"],
                project_id=self.memory_integration.project_id,
                context=knowledge["context"],
                tags=knowledge["tags"],
                memory_type=MemoryType.SEMANTIC
            )
            
        # Perform various searches
        search_queries = [
            "authentication security",
            "database performance scaling", 
            "React component design patterns",
            "API rate limiting Redis",
            "PostgreSQL backup strategy"
        ]
        
        for query in search_queries:
            print(f"\n🔍 Searching: '{query}'")
            
            # Search project knowledge
            results = await self.memory_integration.search_project_knowledge(
                query=query,
                limit=3
            )
            
            if results:
                print(f"  Found {len(results)} relevant items:")
                for result in results:
                    print(f"    • [{result['agent_id']}] {result['content'][:70]}...")
                    print(f"      Importance: {result['importance']}, Tags: {', '.join(result['tags'][:3])}")
            else:
                print("  No relevant results found")
                
        # Demonstrate agent-specific knowledge search
        print(f"\n🎯 Agent-specific search for 'security_specialist':")
        security_knowledge = await self.memory_integration.search_project_knowledge(
            query="",  # Empty query to get all
            agent_id="security_specialist",
            limit=10
        )
        
        print(f"  Found {len(security_knowledge)} items from security_specialist:")
        for item in security_knowledge:
            print(f"    • {item['content'][:80]}...")

    async def example_4_memory_enhanced_agent_runner(self):
        """Example 4: Using the memory-enhanced agent runner"""
        
        print("\n" + "="*60)
        print("EXAMPLE 4: Memory-Enhanced Agent Runner")
        print("="*60)
        
        # Create memory-enhanced runner
        print("Creating memory-enhanced agent runner...")
        runner = MemoryEnhancedAgentRunner(enable_memory=True, auto_migrate=False)
        
        # Check if memory is available
        if not runner.memory_enabled:
            print("⚠️  Memory system not available, using fallback mode")
            return
            
        # Show memory status
        print("\n📊 Memory System Status:")
        stats = runner.get_memory_stats()
        for key, value in stats.items():
            print(f"  • {key}: {value}")
            
        # Simulate running agents with memory
        test_agents = [
            {
                "agent_id": "api_designer", 
                "task": "Design RESTful API endpoints for user management",
                "context": {"priority": "high", "deadline": "2024-01-15"}
            },
            {
                "agent_id": "security_specialist",
                "task": "Review API security and implement authentication",
                "context": {"focus": "authentication", "compliance": "OWASP"}
            }
        ]
        
        for agent_config in test_agents:
            print(f"\n🤖 Running agent: {agent_config['agent_id']}")
            
            try:
                # This would normally execute the actual agent
                # For this example, we'll simulate the result
                result = await runner.run_agent_with_memory(
                    agent_id=agent_config["agent_id"],
                    task=agent_config["task"],
                    context=agent_config["context"]
                )
                
                print(f"  ✅ Agent execution completed")
                print(f"     Success: {result.get('success', 'N/A')}")
                if "memory_ids" in result:
                    print(f"     Memory IDs: {result['memory_ids']}")
                    
            except Exception as e:
                print(f"  ❌ Agent execution failed: {e}")
                
        # Search recent memory activities
        print(f"\n🔍 Recent project activities:")
        recent_memories = await runner.search_project_memory(
            query="",  # Get all recent
            limit=5
        )
        
        for memory in recent_memories:
            timestamp = memory['timestamp'][:19].replace('T', ' ')
            print(f"  [{timestamp}] {memory['agent_id']}: {memory['content'][:60]}...")

    async def example_5_memory_export_and_analysis(self):
        """Example 5: Memory export and project analysis"""
        
        print("\n" + "="*60)
        print("EXAMPLE 5: Memory Export and Analysis")
        print("="*60)
        
        # Export project memory
        print("📤 Exporting project memory...")
        export_path = await self.memory_integration.export_project_memory()
        print(f"  Memory exported to: {export_path}")
        
        # Load and analyze exported memory
        with open(export_path, 'r') as f:
            exported_data = json.load(f)
            
        print(f"\n📊 Export Analysis:")
        print(f"  • Project ID: {exported_data['project_id']}")
        print(f"  • Export timestamp: {exported_data['export_timestamp']}")
        print(f"  • Total memories: {len(exported_data['memories'])}")
        
        # Analyze memory by agent
        agent_counts = {}
        memory_types = {}
        importance_levels = {}
        
        for memory in exported_data['memories']:
            # Count by agent
            agent_id = memory['agent_id']
            agent_counts[agent_id] = agent_counts.get(agent_id, 0) + 1
            
            # Count by memory type
            mem_type = memory['memory_type']
            memory_types[mem_type] = memory_types.get(mem_type, 0) + 1
            
            # Count by importance
            importance = memory['importance']
            importance_levels[importance] = importance_levels.get(importance, 0) + 1
            
        print(f"\n🤖 Memories by Agent:")
        for agent, count in sorted(agent_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {agent}: {count} memories")
            
        print(f"\n🧠 Memory Types:")
        for mem_type, count in memory_types.items():
            print(f"  • {mem_type}: {count}")
            
        print(f"\n⭐ Importance Levels:")
        for importance, count in importance_levels.items():
            print(f"  • Level {importance}: {count}")
            
        # Show most recent activities
        recent_memories = sorted(
            exported_data['memories'], 
            key=lambda x: x['timestamp'], 
            reverse=True
        )[:5]
        
        print(f"\n🕐 Most Recent Activities:")
        for memory in recent_memories:
            timestamp = memory['timestamp'][:19].replace('T', ' ')
            print(f"  [{timestamp}] {memory['agent_id']}: {memory['content'][:60]}...")

    async def example_6_memory_consolidation_and_cleanup(self):
        """Example 6: Memory consolidation and cleanup operations"""
        
        print("\n" + "="*60)
        print("EXAMPLE 6: Memory Consolidation and Cleanup")
        print("="*60)
        
        # Show current memory statistics
        print("📊 Current Memory Statistics:")
        stats_before = self.memory_system.get_memory_stats()
        for key, value in stats_before.items():
            print(f"  • {key}: {value}")
            
        # Perform memory consolidation
        print(f"\n🔄 Performing memory consolidation...")
        await self.memory_system.consolidate_memories()
        print("  ✅ Consolidation completed")
        
        # Show updated statistics
        print(f"\n📊 Updated Memory Statistics:")
        stats_after = self.memory_system.get_memory_stats()
        for key, value in stats_after.items():
            change = value - stats_before.get(key, 0)
            change_str = f" (+{change})" if change > 0 else f" ({change})" if change < 0 else ""
            print(f"  • {key}: {value}{change_str}")
            
        # Cleanup old memories (simulation)
        print(f"\n🧹 Memory cleanup simulation...")
        # In a real scenario, this would remove old, low-importance memories
        print("  ℹ️  Cleanup would remove memories older than 90 days with low importance")
        print("  ℹ️  Current implementation preserves all memories for safety")
        
        # Show session consolidation
        print(f"\n📝 Session memory consolidation...")
        await self.memory_integration.consolidate_session_memory()
        print("  ✅ Session consolidation completed")

    async def run_all_examples(self):
        """Run all memory system examples"""
        
        print("🧠 CoralCollective Memory System Usage Examples")
        print("=" * 80)
        print("This demonstration shows practical usage patterns for the advanced memory system")
        print("=" * 80)
        
        # Initialize memory system
        await self.initialize_memory_system()
        
        # Run examples in sequence
        examples = [
            self.example_1_basic_memory_operations,
            self.example_2_agent_context_and_handoffs,
            self.example_3_memory_search_and_knowledge_base,
            self.example_4_memory_enhanced_agent_runner,
            self.example_5_memory_export_and_analysis,
            self.example_6_memory_consolidation_and_cleanup
        ]
        
        for i, example in enumerate(examples, 1):
            try:
                await example()
                print(f"\n✅ Example {i} completed successfully")
            except Exception as e:
                print(f"\n❌ Example {i} failed: {e}")
                import traceback
                traceback.print_exc()
                
        print("\n" + "="*80)
        print("🎉 All examples completed!")
        print("💡 The memory system is now populated with example data")
        print("🔍 Try running searches or exploring the timeline")
        print("="*80)

# Utility functions for standalone usage

async def quick_memory_test():
    """Quick test of memory system functionality"""
    
    print("🧠 Quick Memory System Test")
    print("-" * 40)
    
    # Initialize memory
    project_path = Path(".")
    examples = MemoryUsageExamples(project_path)
    
    try:
        await examples.initialize_memory_system()
        
        # Add a test memory
        memory_id = await examples.memory_system.add_memory(
            content="Quick test memory - system is working correctly",
            agent_id="test_agent",
            project_id="test_project",
            tags=["test", "quick"]
        )
        
        print(f"✅ Added test memory: {memory_id}")
        
        # Search for it
        results = await examples.memory_system.search_memories(
            query="test memory",
            limit=5
        )
        
        print(f"✅ Found {len(results)} memories")
        
        # Get stats
        stats = examples.memory_system.get_memory_stats()
        print(f"✅ Memory stats: {stats}")
        
        print("\n🎉 Memory system is working correctly!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def create_sample_config():
    """Create a sample memory configuration file"""
    
    config = {
        "short_term": {
            "buffer_size": 20,
            "max_tokens": 8000
        },
        "long_term": {
            "type": "chroma",
            "collection_name": "example_project_memory",
            "persist_directory": "./.coral/memory/chroma_db"
        },
        "orchestrator": {
            "short_term_limit": 20,
            "consolidation_threshold": 0.7,
            "importance_decay_hours": 24
        },
        "summarizer": {
            "max_summary_length": 500,
            "preserve_critical_info": True
        }
    }
    
    config_path = Path(".coral/memory_config.json")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
        
    print(f"📄 Sample configuration created at: {config_path}")
    return config_path

# CLI interface
async def main():
    """Main function for running examples"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="CoralCollective Memory System Examples")
    parser.add_argument("--example", type=int, choices=range(1, 7), 
                       help="Run specific example (1-6)")
    parser.add_argument("--all", action="store_true", 
                       help="Run all examples")
    parser.add_argument("--quick-test", action="store_true",
                       help="Run quick memory system test")
    parser.add_argument("--create-config", action="store_true",
                       help="Create sample memory configuration")
    parser.add_argument("--project-path", type=str, default=".",
                       help="Project directory path")
    
    args = parser.parse_args()
    
    project_path = Path(args.project_path)
    
    if args.create_config:
        create_sample_config()
        return
        
    if args.quick_test:
        await quick_memory_test()
        return
        
    # Create examples instance
    examples = MemoryUsageExamples(project_path)
    
    if args.all:
        await examples.run_all_examples()
    elif args.example:
        await examples.initialize_memory_system()
        example_methods = [
            examples.example_1_basic_memory_operations,
            examples.example_2_agent_context_and_handoffs,
            examples.example_3_memory_search_and_knowledge_base,
            examples.example_4_memory_enhanced_agent_runner,
            examples.example_5_memory_export_and_analysis,
            examples.example_6_memory_consolidation_and_cleanup
        ]
        await example_methods[args.example - 1]()
    else:
        print("Please specify --all, --example N, --quick-test, or --create-config")
        print("Use --help for more information")

if __name__ == "__main__":
    asyncio.run(main())