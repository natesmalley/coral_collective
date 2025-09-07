"""
Memory-Enhanced Agent Runner for CoralCollective

Extends the existing AgentRunner with advanced memory capabilities.
Provides seamless integration between agent workflow and memory system.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from ..agent_runner import AgentRunner
from .coral_memory_integration import CoralMemoryIntegration, initialize_project_memory, create_memory_config
from .migration_strategy import MemoryMigrationStrategy

logger = logging.getLogger(__name__)

class MemoryEnhancedAgentRunner(AgentRunner):
    """
    Extended AgentRunner with advanced memory capabilities
    """
    
    def __init__(self, enable_memory: bool = True, auto_migrate: bool = True):
        super().__init__()
        
        self.memory_enabled = enable_memory
        self.memory_integration: Optional[CoralMemoryIntegration] = None
        self.memory_initialized = False
        
        # Initialize memory system if enabled
        if self.memory_enabled:
            asyncio.run(self._initialize_memory_system(auto_migrate))
            
    async def _initialize_memory_system(self, auto_migrate: bool = True):
        """Initialize memory system for the project"""
        
        try:
            # Check if memory system exists
            memory_config_path = self.base_path / '.coral' / 'memory_config.json'
            
            if not memory_config_path.exists():
                # Create memory configuration
                create_memory_config(self.base_path)
                
                # Run migration if auto_migrate and existing project state exists
                if auto_migrate and (self.base_path / '.coral' / 'project_state.yaml').exists():
                    migration = MemoryMigrationStrategy(self.base_path)
                    migration_report = await migration.migrate_project()
                    
                    if migration_report['errors']:
                        logger.warning(f"Memory migration completed with {len(migration_report['errors'])} errors")
                    else:
                        logger.info("Memory migration completed successfully")
                        
            # Initialize memory integration
            self.memory_integration = await initialize_project_memory(
                self.base_path, str(memory_config_path)
            )
            
            self.memory_initialized = True
            logger.info("Memory system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize memory system: {e}")
            self.memory_enabled = False
            
    async def run_agent_with_memory(self, agent_id: str, task: str = None, 
                                  context: Dict = None) -> Dict[str, Any]:
        """Run agent with full memory integration"""
        
        if not self.memory_enabled or not self.memory_integration:
            # Fallback to regular agent running
            return await self._run_agent_fallback(agent_id, task, context)
            
        try:
            # Get agent context from memory
            agent_context = await self.memory_integration.get_agent_context(agent_id)
            
            # Record agent start
            memory_id = await self.memory_integration.record_agent_start(
                agent_id, task or "Unnamed task", context
            )
            
            # Enhanced prompt with memory context
            base_prompt = self.get_agent_prompt(agent_id)
            enhanced_prompt = self.memory_integration.get_memory_enhanced_prompt(
                agent_id, base_prompt, include_recent=True, include_context=True
            )
            
            # Run agent with enhanced prompt
            result = await self._execute_agent_with_prompt(agent_id, enhanced_prompt, context)
            
            # Record agent completion
            completion_memory_id = await self.memory_integration.record_agent_completion(
                agent_id=agent_id,
                success=result.get('success', True),
                outputs=result.get('outputs', {}),
                artifacts=result.get('artifacts', []),
                handoff_data=result.get('handoff_data')
            )
            
            # Add memory IDs to result
            result['memory_ids'] = {
                'start': memory_id,
                'completion': completion_memory_id
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error running agent with memory: {e}")
            
            # Record the error in memory
            if self.memory_integration:
                await self.memory_integration.record_agent_output(
                    agent_id, f"Error: {str(e)}", "error"
                )
                
            # Fallback to regular execution
            return await self._run_agent_fallback(agent_id, task, context)
            
    async def _run_agent_fallback(self, agent_id: str, task: str, context: Dict) -> Dict[str, Any]:
        """Fallback to regular agent execution without memory"""
        
        # Use the parent class's agent running logic
        return {
            'success': False,
            'error': 'Memory system not available, fallback execution needed',
            'agent_id': agent_id,
            'task': task
        }
        
    async def _execute_agent_with_prompt(self, agent_id: str, prompt: str, 
                                       context: Dict) -> Dict[str, Any]:
        """Execute agent with given prompt"""
        
        # This is a placeholder for actual agent execution
        # In practice, this would integrate with Claude Code or other execution methods
        
        return {
            'success': True,
            'agent_id': agent_id,
            'prompt_length': len(prompt),
            'outputs': {'message': 'Agent executed successfully'},
            'timestamp': datetime.now().isoformat()
        }
        
    def get_agent_prompt(self, agent_id: str) -> str:
        """Get base agent prompt"""
        
        if agent_id not in self.agents_config['agents']:
            raise ValueError(f"Agent {agent_id} not found")
            
        agent = self.agents_config['agents'][agent_id]
        
        # Build prompt from agent configuration
        prompt_parts = [
            f"# {agent['name']}",
            "",
            f"## Role",
            agent['description'],
            "",
            f"## When to Use",
            agent['when_to_use'],
            "",
            f"## Capabilities",
            "\n".join(f"- {cap}" for cap in agent.get('capabilities', [])),
            "",
            f"## Expected Outputs",
            "\n".join(f"- {output}" for output in agent.get('outputs', [])),
        ]
        
        return "\n".join(prompt_parts)
        
    async def search_project_memory(self, query: str, agent_id: str = None, 
                                  limit: int = 10) -> List[Dict[str, Any]]:
        """Search project memory"""
        
        if not self.memory_enabled or not self.memory_integration:
            return []
            
        return await self.memory_integration.search_project_knowledge(
            query, agent_id, limit
        )
        
    async def get_project_timeline(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get project timeline from memory"""
        
        if not self.memory_enabled or not self.memory_integration:
            return []
            
        return await self.memory_integration.get_project_timeline(limit)
        
    async def export_project_memory(self, output_path: str = None) -> str:
        """Export project memory"""
        
        if not self.memory_enabled or not self.memory_integration:
            return ""
            
        export_path = await self.memory_integration.export_project_memory(
            Path(output_path) if output_path else None
        )
        
        return str(export_path)
        
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        
        if not self.memory_enabled or not self.memory_integration:
            return {}
            
        return self.memory_integration.memory_system.get_memory_stats()
        
    # Enhanced workflow methods
    
    async def run_workflow_with_memory(self, workflow_name: str, 
                                     context: Dict = None) -> Dict[str, Any]:
        """Run a complete workflow with memory tracking"""
        
        if workflow_name not in self.agents_config.get('workflows', {}):
            raise ValueError(f"Workflow {workflow_name} not found")
            
        workflow = self.agents_config['workflows'][workflow_name]
        workflow_results = {
            'workflow_name': workflow_name,
            'start_time': datetime.now().isoformat(),
            'agents_executed': [],
            'total_success': True,
            'memory_enabled': self.memory_enabled
        }
        
        # Record workflow start
        if self.memory_integration:
            await self.memory_integration.memory_system.add_memory(
                content=f"Starting workflow: {workflow_name}",
                agent_id="workflow_orchestrator",
                project_id=self.memory_integration.project_id,
                context={
                    'type': 'workflow_start',
                    'workflow_name': workflow_name,
                    'context': context or {}
                },
                tags=['workflow', 'orchestration']
            )
            
        # Execute workflow steps
        for step in workflow.get('steps', []):
            agent_id = step.get('agent_id')
            task = step.get('task', f"Execute {agent_id}")
            step_context = {**(context or {}), **step.get('context', {})}
            
            try:
                result = await self.run_agent_with_memory(agent_id, task, step_context)
                
                workflow_results['agents_executed'].append({
                    'agent_id': agent_id,
                    'success': result.get('success', True),
                    'memory_ids': result.get('memory_ids', {}),
                    'timestamp': datetime.now().isoformat()
                })
                
                if not result.get('success', True):
                    workflow_results['total_success'] = False
                    
            except Exception as e:
                logger.error(f"Error executing workflow step {agent_id}: {e}")
                workflow_results['agents_executed'].append({
                    'agent_id': agent_id,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                workflow_results['total_success'] = False
                
        # Record workflow completion
        if self.memory_integration:
            await self.memory_integration.memory_system.add_memory(
                content=f"Completed workflow: {workflow_name} ({'Success' if workflow_results['total_success'] else 'With errors'})",
                agent_id="workflow_orchestrator",
                project_id=self.memory_integration.project_id,
                context={
                    'type': 'workflow_completion',
                    'workflow_name': workflow_name,
                    'success': workflow_results['total_success'],
                    'agents_count': len(workflow_results['agents_executed'])
                },
                tags=['workflow', 'orchestration', 'completion']
            )
            
        workflow_results['end_time'] = datetime.now().isoformat()
        return workflow_results
        
    # CLI enhancements for memory features
    
    def show_memory_status(self):
        """Show memory system status"""
        
        if not self.memory_enabled:
            console.print("[red]Memory system is disabled[/red]")
            return
            
        if not self.memory_initialized:
            console.print("[yellow]Memory system is enabled but not initialized[/yellow]")
            return
            
        stats = self.get_memory_stats()
        
        console.print(Panel(f"""
[bold green]Memory System Status[/bold green]

• Short-term memories: {stats.get('short_term_memories', 0)}
• Long-term memories: {stats.get('long_term_memories', 0)}
• Working memory keys: {stats.get('working_memory_keys', 0)}
• Session context keys: {stats.get('session_context_keys', 0)}

[bold]Project:[/bold] {self.memory_integration.project_id if self.memory_integration else 'N/A'}
[bold]Session:[/bold] {self.memory_integration.memory_state.get('active_session', 'N/A') if self.memory_integration else 'N/A'}
        """, title="🧠 Memory System", border_style="green"))
        
    async def interactive_memory_search(self):
        """Interactive memory search interface"""
        
        if not self.memory_enabled or not self.memory_integration:
            console.print("[red]Memory system not available[/red]")
            return
            
        console.print("[bold cyan]🔍 Memory Search[/bold cyan]")
        
        while True:
            query = Prompt.ask("Enter search query (or 'quit' to exit)")
            
            if query.lower() == 'quit':
                break
                
            agent_filter = Prompt.ask("Filter by agent (or press Enter for all)", default="")
            limit = IntPrompt.ask("Number of results", default=10)
            
            results = await self.search_project_memory(
                query, 
                agent_filter if agent_filter else None, 
                limit
            )
            
            if results:
                table = Table(title=f"Search Results for: '{query}'")
                table.add_column("Agent", style="cyan")
                table.add_column("Timestamp", style="green")
                table.add_column("Content", style="white")
                table.add_column("Importance", style="yellow")
                
                for result in results:
                    table.add_row(
                        result['agent_id'],
                        result['timestamp'][:19],
                        result['content'][:100] + "..." if len(result['content']) > 100 else result['content'],
                        result['importance']
                    )
                    
                console.print(table)
            else:
                console.print("[yellow]No results found[/yellow]")
                
            if not Confirm.ask("Search again?"):
                break

# Factory function for creating memory-enhanced runner
def create_memory_enhanced_runner(enable_memory: bool = True, 
                                auto_migrate: bool = True) -> MemoryEnhancedAgentRunner:
    """Create memory-enhanced agent runner"""
    
    return MemoryEnhancedAgentRunner(enable_memory, auto_migrate)

# CLI integration
if __name__ == "__main__":
    import argparse
    from rich.console import Console
    
    console = Console()
    
    parser = argparse.ArgumentParser(description="Memory-Enhanced CoralCollective Runner")
    parser.add_argument("command", choices=['run', 'workflow', 'search', 'status', 'export'], 
                       help="Command to execute")
    parser.add_argument("--agent-id", help="Agent ID for run command")
    parser.add_argument("--workflow", help="Workflow name for workflow command")
    parser.add_argument("--task", help="Task description")
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--no-memory", action="store_true", help="Disable memory system")
    parser.add_argument("--no-migrate", action="store_true", help="Don't auto-migrate existing state")
    
    args = parser.parse_args()
    
    async def main():
        runner = create_memory_enhanced_runner(
            enable_memory=not args.no_memory,
            auto_migrate=not args.no_migrate
        )
        
        if args.command == 'run':
            if not args.agent_id:
                console.print("[red]Agent ID required for run command[/red]")
                return
                
            result = await runner.run_agent_with_memory(
                args.agent_id, 
                args.task or "Unnamed task"
            )
            console.print(json.dumps(result, indent=2))
            
        elif args.command == 'workflow':
            if not args.workflow:
                console.print("[red]Workflow name required[/red]")
                return
                
            result = await runner.run_workflow_with_memory(args.workflow)
            console.print(json.dumps(result, indent=2))
            
        elif args.command == 'search':
            if not args.query:
                await runner.interactive_memory_search()
            else:
                results = await runner.search_project_memory(args.query)
                console.print(json.dumps(results, indent=2))
                
        elif args.command == 'status':
            runner.show_memory_status()
            
        elif args.command == 'export':
            export_path = await runner.export_project_memory(args.output)
            console.print(f"Memory exported to: {export_path}")
            
    asyncio.run(main())