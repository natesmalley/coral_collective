#!/usr/bin/env python3
"""
CoralCollective Runner - Main operational interface for running agents with automatic tracking
"""

import os
import sys
import yaml
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.panel import Panel
from rich.markdown import Markdown
from tools.feedback_collector import FeedbackCollector
from tools.project_state import ProjectStateManager

console = Console()

# Try to import MCP client and bridge if available
MCP_AVAILABLE = False
mcp_client = None
try:
    sys.path.append(str(Path(__file__).parent / 'mcp'))
    from mcp_client import MCPClient
    from tools.agent_mcp_bridge import AgentMCPBridge, MCPToolsPromptGenerator
    MCP_AVAILABLE = True
except ImportError:
    pass

class AgentRunner:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.standalone_mode = self.detect_standalone_mode()
        self.agents_config = self.load_agents_config()
        self.collector = FeedbackCollector()
        self.state_manager = ProjectStateManager(self.base_path)
        self.mcp_client = None
        
        # Initialize MCP if available
        self.mcp_enabled = False
        if MCP_AVAILABLE:
            try:
                self.mcp_client = MCPClient()
                self.mcp_enabled = True
                console.print("[green]✓ MCP integration loaded[/green]")
            except Exception as e:
                console.print(f"[yellow]MCP available but not configured: {e}[/yellow]")
                self.mcp_client = None
        
        # Track active MCP bridges
        self.active_bridges: Dict[str, AgentMCPBridge] = {}
        self.current_project = None
        self.session_data = {
            'start_time': datetime.now(),
            'interactions': []
        }
    
    def detect_standalone_mode(self) -> bool:
        """Detect if running in standalone mode (inside existing project)"""
        # Check for standalone config
        standalone_config = self.base_path / "standalone_config.json"
        if standalone_config.exists():
            return True
        
        # Check if we're in a .coral directory
        if self.base_path.name == ".coral":
            return True
        
        # Check for .coralrc in parent directory
        coralrc = self.base_path.parent / ".coralrc"
        if coralrc.exists():
            return True
        
        return False
    
    def get_project_directories(self) -> Dict[str, Path]:
        """Get directory paths based on mode"""
        if self.standalone_mode:
            # In standalone mode, use .coral subdirectories
            base = self.base_path if self.base_path.name == ".coral" else self.base_path / ".coral"
            return {
                'projects': base / 'projects',
                'feedback': base / 'feedback',
                'metrics': base / 'metrics'
            }
        else:
            # Normal mode, use regular directories
            return {
                'projects': self.base_path / 'projects',
                'feedback': self.base_path / 'feedback',
                'metrics': self.base_path / 'metrics'
            }
    
    def load_agents_config(self) -> Dict:
        """Load agent configurations with fallback initialization"""
        config_path = self.base_path / "claude_code_agents.json"
        
        # If JSON doesn't exist, try to initialize it
        if not config_path.exists():
            console.print("[yellow]Configuration file not found. Initializing CoralCollective...[/yellow]")
            if self.initialize_config():
                console.print("[green]✓ Configuration initialized successfully![/green]")
            else:
                console.print("[red]Failed to initialize configuration. Creating default config...[/red]")
                self.create_default_config()
        
        # Now try to load the config
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            console.print(f"[red]Error: Configuration file not found at {config_path}[/red]")
            console.print("[yellow]Run 'python agent_runner.py init' to initialize[/yellow]")
            sys.exit(1)
        except json.JSONDecodeError as e:
            console.print(f"[red]Error: Invalid JSON in configuration file: {e}[/red]")
            sys.exit(1)
    
    def list_agents(self, category: Optional[str] = None):
        """Display available agents in a nice table"""
        table = Table(title="🪸 Available CoralCollective Specialists")
        table.add_column("Agent ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="magenta")
        table.add_column("Category", style="green")
        table.add_column("Description", style="yellow")
        
        agents = self.agents_config['agents']
        for agent_id, agent_data in agents.items():
            if category and agent_data.get('category') != category:
                continue
            
            table.add_row(
                agent_id,
                agent_data['name'],
                agent_data.get('category', 'general'),
                agent_data['description'][:60] + "..."
            )
        
        console.print(table)
    
    def show_agent_details(self, agent_id: str):
        """Show detailed information about an agent"""
        if agent_id not in self.agents_config['agents']:
            console.print(f"[red]Agent '{agent_id}' not found![/red]")
            return
        
        agent = self.agents_config['agents'][agent_id]
        
        # Create detailed view
        details = f"""
# {agent['name']}

**Category:** {agent.get('category', 'general')}
**Phase:** {agent.get('phase', 'N/A')}

## Description
{agent['description']}

## When to Use
{agent['when_to_use']}

## Capabilities
{', '.join(agent.get('capabilities', []))}

## Outputs
{', '.join(agent.get('outputs', []))}

## Next Agents
{', '.join(agent.get('next_agents', ['Any']))}
        """
        
        console.print(Panel(Markdown(details), title=f"Agent: {agent_id}", border_style="blue"))
    
    def select_agent(self) -> Optional[str]:
        """Interactive agent selection"""
        console.print("\n[bold cyan]Select an agent:[/bold cyan]")
        
        # Show categories
        categories = set(a.get('category', 'general') for a in self.agents_config['agents'].values())
        console.print("\nCategories: " + ", ".join(categories))
        
        category = Prompt.ask("Filter by category (or 'all')", default="all")
        
        if category != 'all':
            self.list_agents(category)
        else:
            self.list_agents()
        
        agent_id = Prompt.ask("\nEnter agent ID (or 'help' for details)")
        
        if agent_id == 'help':
            help_agent = Prompt.ask("Which agent do you want details for?")
            self.show_agent_details(help_agent)
            return self.select_agent()
        
        if agent_id not in self.agents_config['agents']:
            console.print(f"[red]Invalid agent ID: {agent_id}[/red]")
            return self.select_agent()
        
        return agent_id
    
    def get_agent_prompt(self, agent_id: str) -> str:
        """Load the full agent prompt from markdown file"""
        agent = self.agents_config['agents'][agent_id]
        
        # Get the prompt path from the configuration
        if 'prompt_path' in agent:
            prompt_file = self.base_path / agent['prompt_path']
        else:
            # Fallback for agents without prompt_path in config
            # Map agent IDs to file paths (with both dash and underscore versions)
            prompt_files = {
                'project_architect': 'agents/core/project_architect.md',
                'project-architect': 'agents/core/project_architect.md',
                'technical_writer_phase1': 'agents/core/technical_writer.md',
                'technical-writer-phase1': 'agents/core/technical_writer.md',
                'technical_writer_phase2': 'agents/core/technical_writer.md',
                'technical-writer-phase2': 'agents/core/technical_writer.md',
                'model_strategy_specialist': 'agents/specialists/model_strategy_specialist.md',
                'model-strategy-specialist': 'agents/specialists/model_strategy_specialist.md'
            }
            
            # Check if we have a specific mapping
            if agent_id in prompt_files:
                prompt_file = self.base_path / prompt_files[agent_id]
            else:
                # Default to specialists folder
                prompt_file = self.base_path / f'agents/specialists/{agent_id.replace("-", "_")}.md'
        
        if not prompt_file.exists():
            return f"Agent prompt file not found: {prompt_file}"
        
        with open(prompt_file, 'r') as f:
            content = f.read()
        
        # Extract the prompt section from the markdown
        if "## Prompt" in content:
            prompt_start = content.find("## Prompt")
            prompt_content = content[prompt_start:]
            
            # Find the actual prompt between ``` markers
            if "```" in prompt_content:
                start = prompt_content.find("```") + 3
                end = prompt_content.find("```", start)
                if end > start:
                    return prompt_content[start:end].strip()
        
        return content
    
    async def initialize_mcp(self) -> bool:
        """Initialize MCP client connections"""
        if not self.mcp_enabled or not self.mcp_client:
            return False
        
        try:
            await self.mcp_client.initialize()
            console.print("[green]✓ MCP client initialized[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Failed to initialize MCP: {e}[/red]")
            return False
    
    async def get_agent_bridge(self, agent_id: str, mcp_enabled: bool = True) -> Optional[AgentMCPBridge]:
        """Get or create an MCP bridge for an agent"""
        if not mcp_enabled or not self.mcp_enabled or not MCP_AVAILABLE:
            return None
        
        # Check if we already have a bridge for this agent
        if agent_id in self.active_bridges:
            return self.active_bridges[agent_id]
        
        try:
            # Initialize MCP if not done yet
            if not self.mcp_client.initialized:
                await self.initialize_mcp()
            
            # Create new bridge
            bridge = AgentMCPBridge(agent_id, self.mcp_client)
            self.active_bridges[agent_id] = bridge
            
            console.print(f"[green]✓ MCP bridge created for {agent_id}[/green]")
            return bridge
            
        except Exception as e:
            console.print(f"[yellow]Failed to create MCP bridge for {agent_id}: {e}[/yellow]")
            return None
    
    async def close_agent_bridge(self, agent_id: str):
        """Close and cleanup an agent's MCP bridge"""
        if agent_id in self.active_bridges:
            bridge = self.active_bridges[agent_id]
            try:
                await bridge.close()
                console.print(f"[green]✓ MCP bridge closed for {agent_id}[/green]")
            except Exception as e:
                console.print(f"[yellow]Error closing MCP bridge for {agent_id}: {e}[/yellow]")
            finally:
                del self.active_bridges[agent_id]
    
    async def close_all_bridges(self):
        """Close all active MCP bridges"""
        for agent_id in list(self.active_bridges.keys()):
            await self.close_agent_bridge(agent_id)
        
        if self.mcp_client:
            try:
                await self.mcp_client.shutdown()
                console.print("[green]✓ MCP client shutdown complete[/green]")
            except Exception as e:
                console.print(f"[yellow]Error during MCP shutdown: {e}[/yellow]")
    
    def add_mcp_enabled_flag(self, parser: argparse.ArgumentParser):
        """Add MCP-related command line flags"""
        parser.add_argument('--mcp-enabled', action='store_true', default=True,
                           help='Enable MCP tool integration (default: True)')
        parser.add_argument('--no-mcp', dest='mcp_enabled', action='store_false',
                           help='Disable MCP tool integration')
    
    async def run_agent(self, agent_id: str, task: str, project_context: Optional[Dict] = None, non_interactive: bool = False,
                      provider: Optional[str] = None, deliver: Optional[str] = None, mcp_enabled: bool = True) -> Dict:
        """Execute an agent with a specific task"""
        start_time = time.time()
        
        # Record agent start in state manager
        self.state_manager.record_agent_start(agent_id, task, project_context)
        
        agent = self.agents_config['agents'][agent_id]
        console.print(f"\n[bold green]🚀 Running {agent['name']}...[/bold green]")
        
        # Get the full agent prompt
        agent_prompt = self.get_agent_prompt(agent_id)
        
        # Combine agent prompt with task
        if 'phase1' in agent_id:
            phase_instruction = "Use PHASE 1 DOCUMENTATION FOUNDATION approach."
        elif 'phase2' in agent_id:
            phase_instruction = "Use PHASE 2 USER DOCUMENTATION approach."
        else:
            phase_instruction = ""
        
        # Add MCP tools if available
        mcp_tools_section = ""
        agent_bridge = None
        
        if mcp_enabled and self.mcp_enabled:
            try:
                agent_bridge = await self.get_agent_bridge(agent_id, mcp_enabled)
                if agent_bridge:
                    # Generate comprehensive MCP tools documentation
                    prompt_generator = MCPToolsPromptGenerator(agent_bridge)
                    mcp_tools_section = await prompt_generator.generate_tools_section()
                    
                    if mcp_tools_section:
                        console.print(f"[green]✓ MCP tools available for {agent_id}[/green]")
                    else:
                        console.print(f"[yellow]No MCP tools available for {agent_id}[/yellow]")
            except Exception as e:
                console.print(f"[yellow]Failed to setup MCP tools: {e}[/yellow]")
        
        full_prompt = f"""
{agent_prompt}

{phase_instruction}

PROJECT CONTEXT:
{json.dumps(project_context, indent=2) if project_context else 'New project'}

{mcp_tools_section}

TASK:
{task}

Please complete this task following your specialized expertise and provide clear handoff instructions if applicable.
"""
        
        # Display the task
        console.print(Panel(task, title="Task", border_style="yellow"))

        # Adapter path: if a provider is specified, render+deliver via adapter with budgeting support
        if provider:
            try:
                from agent_prompt_service import compose, build_sections, TokenEstimator, chunk_text
                if provider == 'claude':
                    from providers.claude import ClaudeProvider as Provider
                elif provider == 'codex':
                    from providers.codex import CodexProvider as Provider
                else:
                    console.print(f"[yellow]Unknown provider '{provider}' - using default stdout rendering[/yellow]")
                    Provider = None  # type: ignore

                payload = compose(agent_id=agent_id, task=task, runner=self, project_context=project_context)

                # Token limits and streaming settings (env overrides CLI/defaults)
                max_input_tokens = int(os.environ.get('CORAL_MAX_INPUT_TOKENS', max_input_tokens))
                streaming_flag = bool(os.environ.get('CORAL_STREAMING', str(streaming)).lower() in ['1','true','yes'])
                expand = bool(os.environ.get('CORAL_EXPAND', str(expand)).lower() in ['1','true','yes'])

                estimator = TokenEstimator()
                sections = build_sections(payload, expand=expand)

                # Render full text with all sections; no truncation
                if Provider is None:
                    from providers.provider_base import BaseProvider
                    renderer = BaseProvider()
                else:
                    renderer = Provider()
                output_text = renderer.render_sections(sections)

                # Determine if batching is needed: default streaming, but if context alone + header can't fit, batch context
                total_tokens = estimator.estimate(output_text)
                mode = deliver or ('file' if non_interactive else 'stdout')
                filename_stub = f"agent_{agent_id}_{int(time.time())}"
                saved_path = None

                # Identify sections and tokens
                ctx_section = next((s for s in sections if s['key'] == 'project_context'), None)
                header_sections = [s for s in sections if s.get('key') != 'project_context']
                header_text = renderer.render_sections(header_sections)
                header_tokens = estimator.estimate(header_text)
                ctx_tokens = estimator.estimate(ctx_section['text']) if ctx_section else 0

                # Decide mode: default streaming; if context + header exceeds window, batch by context parts
                context_exceeds = (header_tokens + ctx_tokens) > max_input_tokens if ctx_section else False
                if validate_tokens:
                    console.print(f"[cyan]Token estimate[/cyan]: total={total_tokens}, cap={max_input_tokens}, header={header_tokens}, context={ctx_tokens}")
                if context_exceeds:
                    # Batch by slicing context to fit with header per part
                    available_for_ctx = max(1, max_input_tokens - header_tokens)
                    context_chunks = chunk_text(ctx_section['text'], estimator, chunk_tokens=available_for_ctx)
                    total_parts = len(context_chunks) if context_chunks else 1
                    for idx, ctx_chunk in enumerate(context_chunks or [""], start=1):
                        per_part_sections = []
                        # Keep role prompt and optional tools
                        for s in header_sections:
                            if s['key'] in ('role_prompt', 'mcp_tools'):
                                per_part_sections.append(s)
                        # Context part
                        if ctx_section:
                            per_part_sections.append({
                                'key': 'project_context',
                                'title': f"PROJECT CONTEXT (part {idx}/{total_parts})",
                                'text': ctx_chunk,
                                'required': False,
                            })
                        # Always include task at the end
                        task_sec = next((s for s in header_sections if s['key'] == 'task'), None)
                        if task_sec:
                            per_part_sections.append(task_sec)
                        part_text = renderer.render_sections(per_part_sections)
                        if validate_tokens:
                            console.print(f"[cyan]context part {idx}/{total_parts} tokens[/cyan]: {estimator.estimate(part_text)}")
                        stub = f"{filename_stub}.part{idx}"
                        renderer.deliver(part_text, mode=mode, base_dir=self.base_path / 'prompts', filename_stub=stub)
                else:
                    # Default streaming: if total fits window and user disabled streaming, single-shot; else stream by chunk_tokens
                    if total_tokens <= max_input_tokens and not streaming_flag:
                        saved_path = renderer.deliver(output_text, mode=mode, base_dir=self.base_path / 'prompts', filename_stub=filename_stub)
                    else:
                        chunk_size = int(os.environ.get('CORAL_CHUNK_TOKENS', chunk_tokens))
                        chunk_size = max(1, min(chunk_size, max_input_tokens))
                        chunks = chunk_text(output_text, estimator, chunk_tokens=chunk_size)
                        for idx, ch in enumerate(chunks, start=1):
                            if validate_tokens:
                                console.print(f"[cyan]chunk {idx} tokens[/cyan]: {estimator.estimate(ch)}")
                            stub = f"{filename_stub}.part{idx}"
                            renderer.deliver(ch, mode=mode, base_dir=self.base_path / 'prompts', filename_stub=stub)

                result = {
                    'agent': agent_id,
                    'task': task,
                    'provider': provider,
                    'deliver': mode,
                    'prompt_file': str(saved_path) if saved_path else None,
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                }

                # Store in session and return
                self.session_data['interactions'].append(result)
                return result
            except Exception as e:
                console.print(f"[red]Provider rendering failed: {e}[/red]")
                console.print("Falling back to default behavior.")

        # Prepare prompt for Claude Code agent execution
        try:
            import pyperclip
            pyperclip.copy(full_prompt)
            console.print("[green]✓ Prompt copied to clipboard![/green]")
        except:
            console.print("[yellow]! Could not copy to clipboard - install pyperclip[/yellow]")
        
        # Handle non-interactive mode
        if non_interactive:
            console.print("\n[bold cyan]Agent Prompt Generated (Non-Interactive Mode):[/bold cyan]")
            console.print(Panel(full_prompt[:2000] + ("..." if len(full_prompt) > 2000 else ""), 
                              title=f"{agent['name']} Prompt", border_style="green"))
            
            # Save prompt to file
            timestamp = int(time.time())
            prompt_file = self.base_path / f"prompts/agent_{agent_id}_{timestamp}.md"
            prompt_file.parent.mkdir(exist_ok=True)
            with open(prompt_file, 'w') as f:
                f.write(full_prompt)
            
            # Also save to a latest symlink for easy access
            latest_file = self.base_path / f"prompts/latest_{agent_id}.md"
            if latest_file.exists():
                latest_file.unlink()
            try:
                latest_file.symlink_to(prompt_file.name)
            except:
                # Fallback for Windows
                import shutil
                shutil.copy(prompt_file, latest_file)
            
            console.print(f"\n[green]✓ Prompt saved to: {prompt_file}[/green]")
            console.print(f"[green]✓ Latest prompt: {latest_file}[/green]")
            console.print(f"[cyan]Agent: {agent['name']} running in automation mode[/cyan]")
            
            # Record completion in state manager
            result = {
                'agent': agent_id,
                'agent_name': agent['name'],
                'task': task,
                'prompt_file': str(prompt_file),
                'latest_file': str(latest_file),
                'timestamp': timestamp,
                'success': True,
                'non_interactive': True,
                'mode': 'automated'
            }
            
            # Track in state manager
            self.state_manager.record_agent_completion(
                agent_id, 
                success=True,
                outputs=result,
                artifacts=[{
                    'type': 'prompt',
                    'path': str(prompt_file)
                }]
            )
            
            # Return success without waiting for any user input
            return result
        
        # Auto-enable non-interactive for certain contexts
        if os.environ.get('CI') or os.environ.get('CORAL_NON_INTERACTIVE') or os.environ.get('CORAL_AUTOMATION'):
            console.print("[yellow]Auto-detected automation environment - switching to non-interactive mode[/yellow]")
            return self.run_agent(agent_id, task, context, non_interactive=True)
        
        # Interactive mode - existing behavior
        if Confirm.ask("Show full prompt?", default=False):
            console.print(Panel(full_prompt[:1000] + "...", title="Agent Prompt Preview"))
        
        console.print("\n[bold cyan]Instructions:[/bold cyan]")
        console.print("1. The agent prompt has been copied to your clipboard")
        console.print("2. Paste this into Claude Code to run the agent")
        console.print("3. Complete the interaction and return here")
        
        input("\n[Press Enter when the agent task is complete...]")
        
        # Collect feedback
        success = Confirm.ask("Was the task completed successfully?", default=True)
        satisfaction = IntPrompt.ask("Rate your satisfaction (1-10)", default=8)
        
        # Calculate time
        completion_time = int((time.time() - start_time) / 60)
        
        # Determine task type
        task_types = {
            'project-architect': 'architecture',
            'backend-developer': 'backend_development',
            'frontend-developer': 'frontend_development',
            'full-stack-engineer': 'full_stack_development',
            'qa-testing': 'testing',
            'devops-deployment': 'deployment'
        }
        task_type = task_types.get(agent_id, 'general_task')
        
        # Record interaction
        self.collector.record_interaction(
            agent_id,
            success,
            satisfaction,
            task_type,
            completion_time
        )
        
        # Collect specific feedback if needed
        if satisfaction <= 6 or not success:
            collect_feedback = Confirm.ask("Would you like to provide specific feedback?", default=True)
            if collect_feedback:
                issue = Prompt.ask("What was the issue?")
                suggestion = Prompt.ask("What would improve this agent?")
                priority = Prompt.ask("Priority", choices=['low', 'medium', 'high', 'critical'], default='medium')
                
                self.collector.add_feedback(
                    agent_id,
                    issue,
                    suggestion,
                    priority,
                    'user'
                )
        
        # Get handoff information
        handoff = None
        if Confirm.ask("Did the agent provide handoff instructions?", default=False):
            next_agent = Prompt.ask("Recommended next agent", default="")
            next_task = Prompt.ask("Next task description", default="")
            handoff = {
                'next_agent': next_agent,
                'next_task': next_task
            }
        
        # Collect MCP metrics if bridge was used
        mcp_metrics = {}
        if agent_bridge:
            mcp_metrics = agent_bridge.get_session_metrics()
        
        result = {
            'agent': agent_id,
            'task': task,
            'success': success,
            'satisfaction': satisfaction,
            'completion_time': completion_time,
            'handoff': handoff,
            'timestamp': datetime.now().isoformat(),
            'mcp_metrics': mcp_metrics
        }
        
        # Store in session
        self.session_data['interactions'].append(result)
        
        return result
    
    def start_project(self, project_name: str, description: str) -> Dict:
        """Start a new project"""
        project = {
            'name': project_name,
            'description': description,
            'created': datetime.now().isoformat(),
            'agents_used': [],
            'current_phase': 1,
            'status': 'active'
        }
        
        # Save project
        dirs = self.get_project_directories()
        projects_dir = dirs['projects']
        projects_dir.mkdir(exist_ok=True, parents=True)
        
        project_file = projects_dir / f"{project_name.replace(' ', '_').lower()}.yaml"
        with open(project_file, 'w') as f:
            yaml.dump(project, f)
        
        self.current_project = project
        console.print(f"[green]✓ Project '{project_name}' created![/green]")
        
        return project
    
    def initialize_config(self) -> bool:
        """Initialize configuration from source if available"""
        # Try to find the source config in parent directories or package
        possible_paths = [
            Path(__file__).parent.parent / "coral_collective" / "claude_code_agents.json",
            Path(__file__).parent.parent / "claude_code_agents.json",
            Path.home() / ".coral_collective" / "claude_code_agents.json",
            Path("/usr/local/share/coral_collective/claude_code_agents.json"),
        ]
        
        for source_path in possible_paths:
            if source_path.exists():
                import shutil
                try:
                    shutil.copy(source_path, self.base_path / "claude_code_agents.json")
                    console.print(f"[green]Copied configuration from {source_path}[/green]")
                    return True
                except Exception as e:
                    console.print(f"[yellow]Failed to copy from {source_path}: {e}[/yellow]")
        
        return False
    
    def create_default_config(self):
        """Create a default configuration file"""
        default_config = {
            "agents": {
                "project_architect": {
                    "name": "Project Architect",
                    "category": "core",
                    "description": "System design and architecture planning",
                    "prompt_path": "agents/core/project_architect.md",
                    "capabilities": ["planning", "architecture", "structure", "handoff"]
                },
                "backend_developer": {
                    "name": "Backend Developer",
                    "category": "development",
                    "description": "Server-side and database specialist",
                    "prompt_path": "agents/specialists/backend_developer.md",
                    "capabilities": ["api", "auth", "models", "docs", "tests"]
                },
                "frontend_developer": {
                    "name": "Frontend Developer",
                    "category": "development",
                    "description": "UI/UX implementation specialist",
                    "prompt_path": "agents/specialists/frontend_developer.md",
                    "capabilities": ["ui", "accessibility", "integration", "performance"]
                },
                "full_stack_engineer": {
                    "name": "Full Stack Engineer",
                    "category": "development",
                    "description": "End-to-end development specialist",
                    "prompt_path": "agents/specialists/full_stack_engineer.md",
                    "capabilities": ["full_stack", "debugging", "production_ops"]
                },
                "qa_testing": {
                    "name": "QA & Testing",
                    "category": "quality",
                    "description": "Quality assurance and testing specialist",
                    "prompt_path": "agents/specialists/qa_testing.md",
                    "capabilities": ["unit", "integration", "coverage", "accessibility"]
                },
                "devops_deployment": {
                    "name": "DevOps & Deployment",
                    "category": "operations",
                    "description": "Infrastructure and deployment specialist",
                    "prompt_path": "agents/specialists/devops_deployment.md",
                    "capabilities": ["cicd", "infra", "deploy", "backups"]
                }
            },
            "project_templates": {
                "full_stack_web": {
                    "name": "Full-Stack Web Application",
                    "description": "Complete web application with frontend and backend",
                    "sequence": ["project_architect", "backend_developer", "frontend_developer", "qa_testing", "devops_deployment"]
                },
                "api_service": {
                    "name": "API Service",
                    "description": "RESTful or GraphQL API backend service",
                    "sequence": ["project_architect", "backend_developer", "qa_testing", "devops_deployment"]
                },
                "frontend_only": {
                    "name": "Frontend Only",
                    "description": "Single-page application or static website",
                    "sequence": ["project_architect", "frontend_developer", "qa_testing", "devops_deployment"]
                },
                "mvp": {
                    "name": "Quick MVP",
                    "description": "Minimal viable product",
                    "sequence": ["full_stack_engineer", "qa_testing", "devops_deployment"]
                },
                "custom": {
                    "name": "Custom Workflow",
                    "description": "Define your own agent sequence",
                    "sequence": []
                }
            },
            "categories": {
                "core": "Core Planning & Documentation",
                "development": "Development & Implementation",
                "quality": "Quality & Testing",
                "operations": "Operations & Infrastructure"
            }
        }
        
        config_path = self.base_path / "claude_code_agents.json"
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        console.print(f"[green]Created default configuration at {config_path}[/green]")
    
    def workflow_wizard(self):
        """Interactive workflow wizard for common project types"""
        console.print("\n[bold cyan]🧙 Workflow Wizard[/bold cyan]")
        
        workflows = {
            '1': ('Full-Stack Web App', 'full_stack_web'),
            '2': ('AI-Powered App', 'ai_powered_app'),
            '3': ('API Service', 'api_service'),
            '4': ('Frontend Only', 'frontend_only'),
            '5': ('Mobile App', 'mobile_app'),
            '6': ('Quick MVP', 'mvp'),
            '7': ('Custom Workflow', 'custom')
        }
        
        console.print("\nProject Types:")
        for key, (name, _) in workflows.items():
            console.print(f"{key}. {name}")
        
        choice = Prompt.ask("Select project type", choices=list(workflows.keys()))
        project_type = workflows[choice][1]
        
        # Get project details
        project_name = Prompt.ask("Project name")
        project_description = Prompt.ask("Brief description")
        
        # Start project
        project = self.start_project(project_name, project_description)
        
        # Get workflow sequence
        if project_type == 'mvp':
            sequence = ['full-stack-engineer', 'qa-testing', 'devops-deployment']
        elif project_type == 'custom':
            console.print("\n[yellow]Select agents in order (comma-separated):[/yellow]")
            self.list_agents()
            agent_list = Prompt.ask("Agent IDs")
            sequence = [a.strip() for a in agent_list.split(',')]
        else:
            sequence = self.agents_config['project_templates'][project_type]['sequence']
        
        console.print(f"\n[bold green]Workflow Sequence:[/bold green]")
        for i, agent_id in enumerate(sequence, 1):
            agent_name = self.agents_config['agents'][agent_id]['name']
            console.print(f"{i}. {agent_name} ({agent_id})")
        
        if Confirm.ask("\nStart workflow?", default=True):
            self.run_workflow(sequence, project)
    
    def run_workflow(self, sequence: List[str], project: Dict, non_interactive: bool = False):
        """Run a sequence of agents"""
        console.print("\n[bold cyan]Starting Workflow Execution[/bold cyan]")
        
        # Check for non-interactive environment
        if os.environ.get('CI') or os.environ.get('CORAL_NON_INTERACTIVE') or os.environ.get('CORAL_AUTOMATION'):
            non_interactive = True
            console.print("[yellow]Running workflow in non-interactive mode[/yellow]")
        
        context = {
            'project': project,
            'completed_agents': [],
            'outputs': {}
        }
        
        for i, agent_id in enumerate(sequence, 1):
            agent = self.agents_config['agents'][agent_id]
            
            console.print(f"\n[bold]Step {i}/{len(sequence)}: {agent['name']}[/bold]")
            
            # Determine task based on previous handoff or default
            if i == 1:
                task = f"Create initial setup for: {project['description']}"
            elif context.get('last_handoff'):
                task = context['last_handoff'].get('next_task', f"Continue from previous agent output")
            else:
                task = f"Continue project: {project['name']}"
            
            # Run the agent with non-interactive flag
            result = self.run_agent(agent_id, task, context, non_interactive=non_interactive)
            
            # Update context
            context['completed_agents'].append(agent_id)
            context['outputs'][agent_id] = result
            
            if result.get('handoff'):
                context['last_handoff'] = result['handoff']
            
            # Check if we should continue
            if not result.get('success', True):
                if non_interactive:
                    console.print(f"[yellow]Warning: {agent['name']} reported failure, continuing workflow in non-interactive mode[/yellow]")
                elif not Confirm.ask("Task failed. Continue workflow?", default=False):
                    console.print("[red]Workflow stopped[/red]")
                    break
            
            if i < len(sequence) and not non_interactive:
                if not Confirm.ask(f"Continue to next agent?", default=True):
                    console.print("[yellow]Workflow paused[/yellow]")
                    break
        
        console.print("\n[bold green]✓ Workflow Complete![/bold green]")
        self.show_session_summary()
    
    def show_session_summary(self):
        """Display session summary"""
        console.print("\n[bold cyan]📊 Session Summary[/bold cyan]")
        
        total_time = (datetime.now() - self.session_data['start_time']).seconds / 60
        interactions = self.session_data['interactions']
        
        if not interactions:
            console.print("No interactions recorded")
            return
        
        # Create summary table
        table = Table(title="Agent Interactions")
        table.add_column("Agent", style="cyan")
        table.add_column("Task", style="yellow")
        table.add_column("Success", style="green")
        table.add_column("Satisfaction", style="magenta")
        table.add_column("Time", style="blue")
        
        for interaction in interactions:
            agent_name = self.agents_config['agents'][interaction['agent']]['name']
            task_preview = interaction['task'][:40] + "..." if len(interaction['task']) > 40 else interaction['task']
            success = "✓" if interaction['success'] else "✗"
            satisfaction = f"{interaction['satisfaction']}/10"
            time_str = f"{interaction['completion_time']}min"
            
            table.add_row(agent_name, task_preview, success, satisfaction, time_str)
        
        console.print(table)
        
        # Summary stats
        avg_satisfaction = sum(i['satisfaction'] for i in interactions) / len(interactions)
        success_rate = sum(1 for i in interactions if i['success']) / len(interactions) * 100
        
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"• Total session time: {total_time:.0f} minutes")
        console.print(f"• Agents used: {len(interactions)}")
        console.print(f"• Success rate: {success_rate:.0f}%")
        console.print(f"• Average satisfaction: {avg_satisfaction:.1f}/10")
    
    def dashboard(self):
        """Show performance dashboard"""
        console.print("\n[bold cyan]📈 Agent Force Dashboard[/bold cyan]")
        
        # Load metrics
        metrics_path = self.base_path / "metrics" / "agent_metrics.yaml"
        if metrics_path.exists():
            with open(metrics_path, 'r') as f:
                metrics = yaml.safe_load(f)
            
            if 'performance_summary' in metrics:
                summary = metrics['performance_summary']
                
                console.print("\n[bold]Overall Performance:[/bold]")
                console.print(f"• Total interactions: {summary.get('total_interactions', 0)}")
                console.print(f"• Success rate: {summary.get('overall_success_rate', 'N/A')}")
                console.print(f"• Average satisfaction: {summary.get('average_satisfaction', 'N/A')}")
                
                if 'most_used_agents' in summary:
                    console.print("\n[bold]Most Used Agents:[/bold]")
                    for agent_info in summary['most_used_agents'][:5]:
                        console.print(f"• {agent_info}")
                
                if 'highest_rated_agents' in summary:
                    console.print("\n[bold]Highest Rated Agents:[/bold]")
                    for agent_info in summary['highest_rated_agents'][:3]:
                        console.print(f"• {agent_info}")
        
        # Show pending improvements
        feedback_path = self.base_path / "feedback" / "agent_feedback.yaml"
        if feedback_path.exists():
            with open(feedback_path, 'r') as f:
                feedback_data = yaml.safe_load(f)
            
            high_priority = []
            for agent, data in feedback_data.get('agents', {}).items():
                for feedback in data.get('feedback', []):
                    if feedback['priority'] == 'high' and feedback['status'] == 'pending':
                        high_priority.append(f"{agent}: {feedback['issue']}")
            
            if high_priority:
                console.print("\n[bold]High Priority Improvements:[/bold]")
                for item in high_priority[:5]:
                    console.print(f"• {item}")

async def async_main():
    """Async version of main for MCP support"""
    parser = argparse.ArgumentParser(description='CoralCollective Agent Runner')
    parser.add_argument('command', nargs='?', default='interactive',
                       choices=['run', 'workflow', 'list', 'dashboard', 'init', 'interactive', 'mcp-status'],
                       help='Command to execute')
    parser.add_argument('--agent', help='Agent ID for run command')
    parser.add_argument('--task', help='Task description for run command')
    parser.add_argument('--project', help='Project name')
    parser.add_argument('--non-interactive', action='store_true', 
                       help='Run without prompting for input')
    parser.add_argument('--provider', choices=['claude', 'codex'],
                       help='Render prompt via provider adapter')
    parser.add_argument('--deliver', choices=['stdout', 'clipboard', 'file'],
                       help='Delivery method for rendered prompt')
    parser.add_argument('--max-input-tokens', type=int, default=12000,
                       help='Max input tokens for composed prompt')
    parser.add_argument('--reserve-output-tokens', type=int, default=0,
                       help='Reserve tokens for model output (set 0 to ignore)')
    parser.add_argument('--streaming', action='store_true', default=True,
                       help='Stream prompt in chunks (default on)')
    parser.add_argument('--no-streaming', dest='streaming', action='store_false',
                       help='Disable streaming (single-part delivery when possible)')
    parser.add_argument('--chunk-tokens', type=int, default=4000,
                       help='Chunk size in tokens when streaming')
    parser.add_argument('--expand', action='store_true', default=True,
                       help='Include optional sections (context/tools) when budget allows')
    parser.add_argument('--no-expand', dest='expand', action='store_false',
                       help='Disable optional sections regardless of budget')
    parser.add_argument('--model', help='Tokenizer/model hint for token estimation (e.g., openai:gpt-4o, anthropic:claude-3.5-sonnet)')
    parser.add_argument('--validate-tokens', action='store_true',
                       help='Print token counts for total and parts/chunks')
    parser.add_argument('--mcp-enabled', action='store_true', default=True,
                       help='Enable MCP tool integration (default: True)')
    parser.add_argument('--no-mcp', dest='mcp_enabled', action='store_false',
                       help='Disable MCP tool integration')
    
    args = parser.parse_args()
    
    # Handle init command before creating runner
    if args.command == 'init':
        console.print("[bold cyan]🪸 Initializing CoralCollective[/bold cyan]")
        config_path = Path(__file__).parent / "claude_code_agents.json"
        
        if config_path.exists():
            console.print(f"[green]✓ Configuration already exists at {config_path}[/green]")
        else:
            # Create default config
            runner_temp = AgentRunner()
            console.print("[yellow]Configuration created. You can now use CoralCollective![/yellow]")
        
        # Create necessary directories based on mode
        base_path = Path(__file__).parent
        if base_path.name == ".coral" or (base_path / "standalone_config.json").exists():
            # Standalone mode - create directories inside .coral
            for dir_name in ['projects', 'feedback', 'metrics']:
                dir_path = base_path / dir_name
                dir_path.mkdir(exist_ok=True, parents=True)
                console.print(f"[green]✓ Created .coral/{dir_name}/ directory[/green]")
        else:
            # Normal mode
            for dir_name in ['projects', 'feedback', 'metrics']:
                Path(dir_name).mkdir(exist_ok=True)
                console.print(f"[green]✓ Created {dir_name}/ directory[/green]")
        
        console.print("\n[bold green]✅ CoralCollective initialized successfully![/bold green]")
        console.print("\nRun 'python agent_runner.py' to start")
        return
    
    runner = AgentRunner()
    
    if args.command == 'interactive':
        # Interactive menu
        while True:
            console.print("\n[bold cyan]🪸 CoralCollective Command Center[/bold cyan]")
            console.print("\n1. Run Single Agent")
            console.print("2. Run Workflow Wizard")
            console.print("3. List Agents")
            console.print("4. Show Dashboard")
            console.print("5. Exit")
            
            choice = Prompt.ask("Select option", choices=['1', '2', '3', '4', '5'])
            
            if choice == '1':
                agent_id = runner.select_agent()
                if agent_id:
                    task = Prompt.ask("Enter task description")
                    runner.run_agent(agent_id, task)
            elif choice == '2':
                runner.workflow_wizard()
            elif choice == '3':
                runner.list_agents()
            elif choice == '4':
                runner.dashboard()
            elif choice == '5':
                runner.show_session_summary()
                console.print("[yellow]Goodbye![/yellow]")
                break
    
    elif args.command == 'run':
        if not args.agent or not args.task:
            console.print("[red]Error: --agent and --task required for run command[/red]")
            sys.exit(1)
        try:
            result = await runner.run_agent(
                args.agent,
                args.task,
                non_interactive=args.non_interactive,
                provider=args.provider,
                deliver=args.deliver,
                mcp_enabled=args.mcp_enabled
            )
            
            # Display MCP metrics if available
            if result.get('mcp_metrics') and result['mcp_metrics'].get('usage_metrics', {}).get('total_calls', 0) > 0:
                metrics = result['mcp_metrics']['usage_metrics']
                console.print(f"\n[bold cyan]MCP Usage Summary:[/bold cyan]")
                console.print(f"• Tools used: {metrics['total_calls']} calls")
                console.print(f"• Success rate: {metrics.get('success_rate', 0):.1%}")
                console.print(f"• Servers: {', '.join(metrics.get('servers_used', []))}")
                
        except Exception as e:
            console.print(f"[red]Error running agent: {e}[/red]")
            sys.exit(1)
        finally:
            # Cleanup MCP connections
            await runner.close_all_bridges()
    
    elif args.command == 'workflow':
        runner.workflow_wizard()
    
    elif args.command == 'list':
        runner.list_agents()
    
    elif args.command == 'dashboard':
        runner.dashboard()
    
    elif args.command == 'mcp-status':
        console.print("\n[bold cyan]🔌 MCP Integration Status[/bold cyan]\n")
        
        if not MCP_AVAILABLE:
            console.print("[red]❌ MCP not available[/red]")
            console.print("\nTo enable MCP integration:")
            console.print("1. Install Node.js 18+")
            console.print("2. Run: cd mcp && ./setup_mcp.sh")
            console.print("3. Configure: cp mcp/.env.example mcp/.env")
            console.print("4. Edit mcp/.env with your API keys")
        else:
            console.print("[green]✅ MCP module available[/green]")
            
            if runner.mcp_client:
                console.print("[green]✅ MCP client initialized[/green]")
                
                try:
                    # Test MCP initialization
                    await runner.initialize_mcp()
                    
                    servers = runner.mcp_client.get_available_servers()
                    console.print(f"\n[bold]Available MCP Servers:[/bold]")
                    
                    for server_name in servers:
                        server_info = runner.mcp_client.get_server_info(server_name)
                        if server_info:
                            status = "🟢 Connected" if server_info.get('connection_stats', {}).get('connected') else "🔴 Disconnected"
                            console.print(f"  • {server_name}: {status}")
                            
                            # List features if available
                            features = server_info.get('features', [])
                            if features:
                                console.print(f"    Features: {', '.join(features)}")
                    
                    # Show agent permissions
                    console.print(f"\n[bold]Agent Permissions Sample:[/bold]")
                    sample_agents = ['backend_developer', 'frontend_developer', 'devops_deployment']
                    for agent in sample_agents:
                        tools = runner.mcp_client.get_tools_for_agent(agent)
                        if tools:
                            console.print(f"  • {agent}: {len(tools)} servers accessible")
                    
                except Exception as e:
                    console.print(f"[yellow]⚠️  MCP servers not running: {e}[/yellow]")
                    console.print("\nTo start MCP servers:")
                    console.print("1. cd mcp && ./setup_mcp.sh")
                    console.print("2. Configure: cp mcp/.env.example mcp/.env")
                    console.print("3. Edit mcp/.env with your API keys")
                finally:
                    await runner.close_all_bridges()
            else:
                console.print("[yellow]⚠️  MCP client not initialized[/yellow]")
                console.print("Check mcp/configs/mcp_config.yaml")

def main():
    """Synchronous main function wrapper"""
    import asyncio
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
