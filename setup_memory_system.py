#!/usr/bin/env python3
"""
CoralCollective Memory System Setup Script

Automatically sets up and configures the advanced memory system for CoralCollective projects.
Handles installation, migration, and validation.
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from rich.console import Console
from rich.progress import Progress, TaskID
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
import argparse

# Set up logging and console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

class MemorySystemSetup:
    """Handles memory system setup and installation"""
    
    def __init__(self, project_path: Path, interactive: bool = True):
        self.project_path = project_path
        self.interactive = interactive
        self.coral_path = project_path / '.coral'
        
        # Check if CoralCollective is available
        self.coral_available = self._check_coral_availability()
        
    def _check_coral_availability(self) -> bool:
        """Check if CoralCollective is properly set up"""
        
        # Check for agent runner
        agent_runner = self.project_path / 'agent_runner.py'
        if not agent_runner.exists():
            return False
            
        # Check for agents config
        agents_config = self.project_path / 'claude_code_agents.json'
        config_yaml = self.project_path / 'config' / 'agents.yaml'
        
        return agents_config.exists() or config_yaml.exists()
        
    async def setup_memory_system(self, force: bool = False) -> Dict[str, Any]:
        """Complete memory system setup"""
        
        setup_report = {
            'timestamp': datetime.now().isoformat(),
            'project_path': str(self.project_path),
            'steps_completed': [],
            'errors': [],
            'success': True
        }
        
        with Progress() as progress:
            # Define setup steps
            steps = [
                ("Checking prerequisites", self._check_prerequisites),
                ("Installing dependencies", self._install_dependencies),
                ("Creating directory structure", self._create_directories),
                ("Generating configuration", self._create_configuration),
                ("Running migration", self._run_migration),
                ("Validating installation", self._validate_installation),
                ("Setting up MCP server", self._setup_mcp_server)
            ]
            
            main_task = progress.add_task("Setting up memory system...", total=len(steps))
            
            for step_name, step_func in steps:
                step_task = progress.add_task(f"  {step_name}", total=1)
                
                try:
                    result = await step_func()
                    setup_report['steps_completed'].append({
                        'step': step_name,
                        'success': True,
                        'result': result
                    })
                    progress.update(step_task, completed=1)
                    console.print(f"  ✓ {step_name}")
                    
                except Exception as e:
                    error_msg = f"Error in {step_name}: {str(e)}"
                    setup_report['errors'].append(error_msg)
                    setup_report['success'] = False
                    
                    progress.update(step_task, completed=1)
                    console.print(f"  ✗ {step_name}: {str(e)}", style="red")
                    
                    if not force:
                        break
                        
                progress.advance(main_task)
                
        return setup_report
        
    async def _check_prerequisites(self) -> Dict[str, Any]:
        """Check system prerequisites"""
        
        prereqs = {
            'python_version': sys.version_info >= (3, 8),
            'coral_available': self.coral_available,
            'pip_available': subprocess.run(['pip', '--version'], 
                                          capture_output=True).returncode == 0,
            'git_available': subprocess.run(['git', '--version'], 
                                          capture_output=True).returncode == 0
        }
        
        if not all(prereqs.values()):
            missing = [k for k, v in prereqs.items() if not v]
            raise RuntimeError(f"Missing prerequisites: {', '.join(missing)}")
            
        return prereqs
        
    async def _install_dependencies(self) -> Dict[str, Any]:
        """Install required dependencies"""
        
        requirements_file = self.project_path / 'memory' / 'requirements.txt'
        
        if not requirements_file.exists():
            # Create requirements file
            requirements_content = """
chromadb>=0.4.15
numpy>=1.24.0
sentence-transformers>=2.2.0
asyncio
aiofiles>=23.0.0
pandas>=2.0.0
pydantic>=2.0.0
python-dateutil>=2.8.0
pyyaml>=6.0
rich>=13.0.0
""".strip()
            
            requirements_file.parent.mkdir(parents=True, exist_ok=True)
            requirements_file.write_text(requirements_content)
            
        # Install dependencies
        if self.interactive:
            install = Confirm.ask(f"Install dependencies from {requirements_file}?")
            if not install:
                return {'skipped': True}
                
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
            ], capture_output=True, text=True, check=True)
            
            return {
                'success': True,
                'installed_packages': result.stdout.count('Successfully installed')
            }
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to install dependencies: {e.stderr}")
            
    async def _create_directories(self) -> Dict[str, Any]:
        """Create necessary directory structure"""
        
        directories = [
            self.coral_path,
            self.coral_path / 'memory',
            self.coral_path / 'memory' / 'chroma_db',
            self.coral_path / 'migration_backup',
            self.project_path / 'docs'
        ]
        
        created = []
        for directory in directories:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
                created.append(str(directory))
                
        return {'created_directories': created}
        
    async def _create_configuration(self) -> Dict[str, Any]:
        """Create memory system configuration"""
        
        from memory.coral_memory_integration import create_memory_config
        
        config_path = create_memory_config(self.project_path)
        
        return {
            'config_path': str(config_path),
            'config_exists': config_path.exists()
        }
        
    async def _run_migration(self) -> Dict[str, Any]:
        """Run migration from existing project state"""
        
        # Check if migration is needed
        state_file = self.coral_path / 'project_state.yaml'
        if not state_file.exists():
            return {'migration_needed': False}
            
        if self.interactive:
            migrate = Confirm.ask("Migrate existing project state to memory system?")
            if not migrate:
                return {'migration_skipped': True}
                
        # Run migration
        from memory.migration_strategy import run_migration
        
        migration_report = await run_migration(str(self.project_path))
        
        return {
            'migration_completed': True,
            'migrated_items': migration_report.get('migrated_items', {}),
            'errors': migration_report.get('errors', [])
        }
        
    async def _validate_installation(self) -> Dict[str, Any]:
        """Validate memory system installation"""
        
        try:
            # Import memory system
            from memory import MemorySystem, CoralMemoryIntegration
            
            # Test initialization
            config_path = self.coral_path / 'memory_config.json'
            memory_system = MemorySystem(str(config_path))
            
            # Test basic operations
            test_memory_id = await memory_system.add_memory(
                content="Installation validation test",
                agent_id="setup_validator",
                project_id=self.project_path.name,
                context={'type': 'validation'},
                tags=['validation', 'setup']
            )
            
            # Test search
            results = await memory_system.search_memories(
                query="validation test",
                limit=1
            )
            
            return {
                'validation_passed': True,
                'test_memory_id': test_memory_id,
                'search_results': len(results),
                'memory_stats': memory_system.get_memory_stats()
            }
            
        except Exception as e:
            raise RuntimeError(f"Validation failed: {str(e)}")
            
    async def _setup_mcp_server(self) -> Dict[str, Any]:
        """Set up MCP memory server"""
        
        try:
            # Check if MCP is available
            mcp_path = self.project_path / 'mcp'
            if not mcp_path.exists():
                return {'mcp_not_available': True}
                
            # Create memory server configuration
            server_config = {
                "name": "coral-memory",
                "description": "CoralCollective Memory System MCP Server",
                "version": "1.0.0",
                "project_path": str(self.project_path),
                "tools": [
                    "add_memory",
                    "search_memories", 
                    "get_agent_context",
                    "record_agent_start",
                    "record_agent_completion",
                    "get_project_timeline",
                    "search_project_knowledge",
                    "get_memory_stats",
                    "consolidate_memory",
                    "export_project_memory"
                ]
            }
            
            config_file = mcp_path / 'configs' / 'memory_server_config.json'
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump(server_config, f, indent=2)
                
            return {
                'mcp_configured': True,
                'config_file': str(config_file)
            }
            
        except Exception as e:
            return {
                'mcp_setup_error': str(e)
            }

def create_startup_script(project_path: Path):
    """Create convenience startup script"""
    
    script_content = f'''#!/usr/bin/env python3
"""
CoralCollective Memory-Enhanced Runner
Auto-generated startup script for memory-enabled CoralCollective
"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from memory import MemoryEnhancedAgentRunner

async def main():
    # Create memory-enhanced runner
    runner = MemoryEnhancedAgentRunner(
        enable_memory=True,
        auto_migrate=False  # Migration already completed
    )
    
    # Show memory status
    runner.show_memory_status()
    
    # Start interactive mode (placeholder)
    print("\\nMemory-enhanced CoralCollective ready!")
    print("Use: python memory_runner.py [command] for memory operations")

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    script_path = project_path / 'memory_runner.py'
    script_path.write_text(script_content)
    script_path.chmod(0o755)
    
    return script_path

async def main():
    """Main setup function"""
    
    parser = argparse.ArgumentParser(description="CoralCollective Memory System Setup")
    parser.add_argument("project_path", nargs='?', default=".", 
                       help="Path to CoralCollective project")
    parser.add_argument("--force", action="store_true", 
                       help="Continue setup even if errors occur")
    parser.add_argument("--non-interactive", action="store_true", 
                       help="Run in non-interactive mode")
    parser.add_argument("--validate-only", action="store_true",
                       help="Only run validation")
    
    args = parser.parse_args()
    
    project_path = Path(args.project_path).resolve()
    
    console.print(Panel.fit(
        f"🧠 [bold]CoralCollective Memory System Setup[/bold]\n\n"
        f"Project: {project_path.name}\n"
        f"Path: {project_path}",
        border_style="blue"
    ))
    
    # Initialize setup
    setup = MemorySystemSetup(project_path, not args.non_interactive)
    
    if args.validate_only:
        # Only run validation
        try:
            result = await setup._validate_installation()
            console.print("✓ Validation passed", style="green")
            console.print(json.dumps(result, indent=2))
        except Exception as e:
            console.print(f"✗ Validation failed: {e}", style="red")
            sys.exit(1)
    else:
        # Run full setup
        report = await setup.setup_memory_system(args.force)
        
        # Show results
        if report['success']:
            console.print("\n✓ Memory system setup completed successfully!", style="green")
            
            # Create startup script
            script_path = create_startup_script(project_path)
            console.print(f"✓ Created startup script: {script_path}")
            
            # Show next steps
            console.print(Panel.fit(
                f"[bold green]Setup Complete![/bold green]\n\n"
                f"Next steps:\n"
                f"1. Run: python memory_runner.py\n"
                f"2. Or use: python -m memory.memory_enhanced_runner status\n"
                f"3. See docs: docs/memory_system_architecture.md\n\n"
                f"Memory system is now ready for CoralCollective agents!",
                border_style="green"
            ))
            
        else:
            console.print("\n✗ Setup completed with errors", style="red")
            for error in report['errors']:
                console.print(f"  • {error}", style="red")
                
        # Save setup report
        report_path = project_path / '.coral' / 'memory_setup_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        console.print(f"\nSetup report saved to: {report_path}")

if __name__ == "__main__":
    # Import datetime here to avoid issues during import
    from datetime import datetime
    asyncio.run(main())