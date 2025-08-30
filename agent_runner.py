#!/usr/bin/env python3
"""
Agent Force Runner - Main operational interface for running agents with automatic tracking
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

console = Console()

class AgentRunner:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.agents_config = self.load_agents_config()
        self.collector = FeedbackCollector()
        self.current_project = None
        self.session_data = {
            'start_time': datetime.now(),
            'interactions': []
        }
    
    def load_agents_config(self) -> Dict:
        """Load agent configurations"""
        config_path = self.base_path / "claude_code_agents.json"
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def list_agents(self, category: Optional[str] = None):
        """Display available agents in a nice table"""
        table = Table(title="🤖 Available Agent Force Specialists")
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
        
        # Map agent IDs to file paths
        prompt_files = {
            'project-architect': 'agents/core/project_architect.md',
            'technical-writer-phase1': 'agents/core/technical_writer.md',
            'technical-writer-phase2': 'agents/core/technical_writer.md',
            'full-stack-engineer': 'agents/specialists/full_stack_engineer.md',
            'backend-developer': 'agents/specialists/backend_developer.md',
            'frontend-developer': 'agents/specialists/frontend_developer.md',
            'mobile-developer': 'agents/specialists/mobile_developer.md',
            'ai-ml-specialist': 'agents/specialists/ai_ml_specialist.md',
            'security-specialist': 'agents/specialists/security_specialist.md',
            'performance-engineer': 'agents/specialists/performance_engineer.md',
            'accessibility-specialist': 'agents/specialists/accessibility_specialist.md',
            'qa-testing': 'agents/specialists/qa_testing.md',
            'devops-deployment': 'agents/specialists/devops_deployment.md',
            'api-designer': 'agents/specialists/api_designer.md',
            'database-specialist': 'agents/specialists/database_specialist.md',
            'data-engineer': 'agents/specialists/data_engineer.md',
            'ui-designer': 'agents/specialists/ui_designer.md',
            'analytics-engineer': 'agents/specialists/analytics_engineer.md',
            'compliance-specialist': 'agents/specialists/compliance_specialist.md',
            'site-reliability-engineer': 'agents/specialists/site_reliability_engineer.md'
        }
        
        prompt_file = self.base_path / prompt_files.get(agent_id, f'agents/specialists/{agent_id.replace("-", "_")}.md')
        
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
    
    def run_agent(self, agent_id: str, task: str, project_context: Optional[Dict] = None) -> Dict:
        """Execute an agent with a specific task"""
        start_time = time.time()
        
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
        
        full_prompt = f"""
{agent_prompt}

{phase_instruction}

PROJECT CONTEXT:
{json.dumps(project_context, indent=2) if project_context else 'New project'}

TASK:
{task}

Please complete this task following your specialized expertise and provide clear handoff instructions if applicable.
"""
        
        # Display the task
        console.print(Panel(task, title="Task", border_style="yellow"))
        
        # Prepare prompt for Claude Code agent execution
        try:
            import pyperclip
            pyperclip.copy(full_prompt)
            console.print("[green]✓ Prompt copied to clipboard![/green]")
        except:
            console.print("[yellow]! Could not copy to clipboard - install pyperclip[/yellow]")
        
        # Show prompt preview
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
        
        result = {
            'agent': agent_id,
            'task': task,
            'success': success,
            'satisfaction': satisfaction,
            'completion_time': completion_time,
            'handoff': handoff,
            'timestamp': datetime.now().isoformat()
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
        projects_dir = self.base_path / "projects"
        projects_dir.mkdir(exist_ok=True)
        
        project_file = projects_dir / f"{project_name.replace(' ', '_').lower()}.yaml"
        with open(project_file, 'w') as f:
            yaml.dump(project, f)
        
        self.current_project = project
        console.print(f"[green]✓ Project '{project_name}' created![/green]")
        
        return project
    
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
    
    def run_workflow(self, sequence: List[str], project: Dict):
        """Run a sequence of agents"""
        console.print("\n[bold cyan]Starting Workflow Execution[/bold cyan]")
        
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
            
            # Run the agent
            result = self.run_agent(agent_id, task, context)
            
            # Update context
            context['completed_agents'].append(agent_id)
            context['outputs'][agent_id] = result
            
            if result.get('handoff'):
                context['last_handoff'] = result['handoff']
            
            # Check if we should continue
            if not result['success']:
                if not Confirm.ask("Task failed. Continue workflow?", default=False):
                    console.print("[red]Workflow stopped[/red]")
                    break
            
            if i < len(sequence):
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

def main():
    parser = argparse.ArgumentParser(description='Agent Force Runner')
    parser.add_argument('command', nargs='?', default='interactive',
                       choices=['run', 'workflow', 'list', 'dashboard', 'interactive'],
                       help='Command to execute')
    parser.add_argument('--agent', help='Agent ID for run command')
    parser.add_argument('--task', help='Task description for run command')
    parser.add_argument('--project', help='Project name')
    
    args = parser.parse_args()
    runner = AgentRunner()
    
    if args.command == 'interactive':
        # Interactive menu
        while True:
            console.print("\n[bold cyan]🤖 Agent Force Command Center[/bold cyan]")
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
        runner.run_agent(args.agent, args.task)
    
    elif args.command == 'workflow':
        runner.workflow_wizard()
    
    elif args.command == 'list':
        runner.list_agents()
    
    elif args.command == 'dashboard':
        runner.dashboard()

if __name__ == "__main__":
    main()