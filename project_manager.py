#!/usr/bin/env python3
"""
Project Manager - Manage multiple projects with Agent Force
"""

import yaml
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.tree import Tree

console = Console()

class ProjectManager:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.projects_dir = self.base_path / "projects"
        self.projects_dir.mkdir(exist_ok=True)
        self.active_projects = self.load_projects()
    
    def load_projects(self) -> Dict:
        """Load all projects"""
        projects = {}
        for project_file in self.projects_dir.glob("*.yaml"):
            with open(project_file, 'r') as f:
                project = yaml.safe_load(f)
                projects[project['name']] = project
        return projects
    
    def save_project(self, project: Dict):
        """Save a project"""
        project_file = self.projects_dir / f"{project['name'].replace(' ', '_').lower()}.yaml"
        with open(project_file, 'w') as f:
            yaml.dump(project, f, default_flow_style=False)
    
    def create_project(self) -> Dict:
        """Create a new project"""
        console.print("\n[bold cyan]📁 Create New Project[/bold cyan]")
        
        name = Prompt.ask("Project name")
        description = Prompt.ask("Project description")
        
        # Select project type
        project_types = {
            '1': 'Full-Stack Web Application',
            '2': 'AI-Powered Application', 
            '3': 'API Service',
            '4': 'Frontend Application',
            '5': 'Mobile Application',
            '6': 'MVP/Prototype',
            '7': 'Custom'
        }
        
        console.print("\nProject Types:")
        for key, ptype in project_types.items():
            console.print(f"{key}. {ptype}")
        
        type_choice = Prompt.ask("Select project type", choices=list(project_types.keys()))
        project_type = project_types[type_choice]
        
        # Set up project structure
        project = {
            'name': name,
            'description': description,
            'type': project_type,
            'created': datetime.now().isoformat(),
            'status': 'planning',
            'current_phase': 1,
            'phases': {
                1: {'name': 'Planning & Foundation', 'status': 'pending', 'agents': []},
                2: {'name': 'Development', 'status': 'pending', 'agents': []},
                3: {'name': 'Quality & Deployment', 'status': 'pending', 'agents': []},
                4: {'name': 'Documentation', 'status': 'pending', 'agents': []}
            },
            'agents_used': [],
            'tasks_completed': [],
            'metrics': {
                'total_time': 0,
                'success_rate': 0,
                'satisfaction': []
            },
            'notes': [],
            'repository': Prompt.ask("Repository URL (optional)", default=""),
            'deployment_url': ""
        }
        
        # Add requirements if needed
        if Confirm.ask("Add initial requirements?", default=True):
            requirements = []
            console.print("Enter requirements (empty line to finish):")
            while True:
                req = Prompt.ask(">", default="")
                if not req:
                    break
                requirements.append(req)
            project['requirements'] = requirements
        
        # Save project
        self.save_project(project)
        self.active_projects[name] = project
        
        console.print(f"[green]✓ Project '{name}' created successfully![/green]")
        return project
    
    def list_projects(self, status_filter: Optional[str] = None):
        """List all projects"""
        if not self.active_projects:
            console.print("[yellow]No projects found. Create one first![/yellow]")
            return
        
        table = Table(title="📋 Active Projects")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Type", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Phase", style="yellow")
        table.add_column("Created", style="blue")
        table.add_column("Agents Used", style="red")
        
        for name, project in self.active_projects.items():
            if status_filter and project['status'] != status_filter:
                continue
            
            phase_name = project['phases'][project['current_phase']]['name']
            agents_count = len(project['agents_used'])
            created_date = datetime.fromisoformat(project['created']).strftime("%Y-%m-%d")
            
            # Color code status
            status = project['status']
            if status == 'completed':
                status = f"[green]{status}[/green]"
            elif status == 'active':
                status = f"[yellow]{status}[/yellow]"
            elif status == 'planning':
                status = f"[cyan]{status}[/cyan]"
            
            table.add_row(
                name,
                project['type'],
                status,
                f"Phase {project['current_phase']}: {phase_name}",
                created_date,
                str(agents_count)
            )
        
        console.print(table)
    
    def show_project_details(self, project_name: str):
        """Show detailed project information"""
        if project_name not in self.active_projects:
            console.print(f"[red]Project '{project_name}' not found![/red]")
            return
        
        project = self.active_projects[project_name]
        
        # Create project tree
        tree = Tree(f"📁 {project['name']}")
        
        # Basic info
        info = tree.add("ℹ️ Information")
        info.add(f"Type: {project['type']}")
        info.add(f"Status: {project['status']}")
        info.add(f"Created: {project['created'][:10]}")
        if project.get('repository'):
            info.add(f"Repo: {project['repository']}")
        
        # Phases
        phases = tree.add(f"📊 Phases (Current: {project['current_phase']})")
        for phase_num, phase_data in project['phases'].items():
            phase_node = phases.add(f"Phase {phase_num}: {phase_data['name']} [{phase_data['status']}]")
            if phase_data['agents']:
                for agent in phase_data['agents']:
                    phase_node.add(f"✓ {agent}")
        
        # Requirements
        if project.get('requirements'):
            reqs = tree.add("📋 Requirements")
            for req in project['requirements']:
                reqs.add(f"• {req}")
        
        # Agents used
        if project['agents_used']:
            agents = tree.add("🤖 Agents Used")
            for agent_entry in project['agents_used']:
                agents.add(f"• {agent_entry['agent']} - {agent_entry.get('task', 'N/A')[:50]}...")
        
        # Metrics
        metrics = tree.add("📈 Metrics")
        metrics.add(f"Total Time: {project['metrics']['total_time']} minutes")
        metrics.add(f"Success Rate: {project['metrics']['success_rate']}%")
        if project['metrics']['satisfaction']:
            avg_satisfaction = sum(project['metrics']['satisfaction']) / len(project['metrics']['satisfaction'])
            metrics.add(f"Avg Satisfaction: {avg_satisfaction:.1f}/10")
        
        # Notes
        if project.get('notes'):
            notes = tree.add("📝 Notes")
            for note in project['notes'][-5:]:  # Show last 5 notes
                notes.add(f"• {note['date'][:10]}: {note['text'][:50]}...")
        
        console.print(Panel(tree, title=f"Project: {project_name}", border_style="blue"))
    
    def update_project_status(self, project_name: str, status: str):
        """Update project status"""
        if project_name not in self.active_projects:
            console.print(f"[red]Project '{project_name}' not found![/red]")
            return
        
        valid_statuses = ['planning', 'active', 'paused', 'completed', 'archived']
        if status not in valid_statuses:
            console.print(f"[red]Invalid status. Choose from: {', '.join(valid_statuses)}[/red]")
            return
        
        self.active_projects[project_name]['status'] = status
        self.save_project(self.active_projects[project_name])
        console.print(f"[green]✓ Project status updated to '{status}'[/green]")
    
    def add_agent_interaction(self, project_name: str, agent_id: str, 
                            task: str, success: bool, satisfaction: int,
                            completion_time: int):
        """Record an agent interaction for a project"""
        if project_name not in self.active_projects:
            return
        
        project = self.active_projects[project_name]
        
        interaction = {
            'agent': agent_id,
            'task': task,
            'success': success,
            'satisfaction': satisfaction,
            'completion_time': completion_time,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add to agents used
        project['agents_used'].append(interaction)
        
        # Update current phase agents
        current_phase = project['current_phase']
        if agent_id not in project['phases'][current_phase]['agents']:
            project['phases'][current_phase]['agents'].append(agent_id)
        
        # Update metrics
        project['metrics']['total_time'] += completion_time
        project['metrics']['satisfaction'].append(satisfaction)
        
        # Calculate success rate
        total_interactions = len(project['agents_used'])
        successful = sum(1 for i in project['agents_used'] if i['success'])
        project['metrics']['success_rate'] = int((successful / total_interactions) * 100)
        
        # Save project
        self.save_project(project)
    
    def advance_phase(self, project_name: str):
        """Move project to next phase"""
        if project_name not in self.active_projects:
            return
        
        project = self.active_projects[project_name]
        current_phase = project['current_phase']
        
        # Mark current phase as completed
        project['phases'][current_phase]['status'] = 'completed'
        
        # Move to next phase if available
        if current_phase < 4:
            project['current_phase'] = current_phase + 1
            project['phases'][current_phase + 1]['status'] = 'active'
            console.print(f"[green]✓ Advanced to Phase {current_phase + 1}[/green]")
        else:
            project['status'] = 'completed'
            console.print(f"[green]✓ Project completed![/green]")
        
        self.save_project(project)
    
    def add_note(self, project_name: str, note_text: str):
        """Add a note to a project"""
        if project_name not in self.active_projects:
            return
        
        project = self.active_projects[project_name]
        
        if 'notes' not in project:
            project['notes'] = []
        
        note = {
            'date': datetime.now().isoformat(),
            'text': note_text
        }
        
        project['notes'].append(note)
        self.save_project(project)
        console.print(f"[green]✓ Note added to project[/green]")
    
    def generate_project_report(self, project_name: str) -> str:
        """Generate a comprehensive project report"""
        if project_name not in self.active_projects:
            return "Project not found"
        
        project = self.active_projects[project_name]
        
        report = []
        report.append(f"# Project Report: {project['name']}")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        
        report.append("## Overview")
        report.append(f"- **Type**: {project['type']}")
        report.append(f"- **Status**: {project['status']}")
        report.append(f"- **Current Phase**: {project['current_phase']} - {project['phases'][project['current_phase']]['name']}")
        report.append(f"- **Created**: {project['created'][:10]}")
        
        if project.get('repository'):
            report.append(f"- **Repository**: {project['repository']}")
        
        report.append("\n## Requirements")
        if project.get('requirements'):
            for req in project['requirements']:
                report.append(f"- {req}")
        else:
            report.append("No requirements specified")
        
        report.append("\n## Phase Progress")
        for phase_num, phase_data in project['phases'].items():
            status_emoji = "✅" if phase_data['status'] == 'completed' else "⏳" if phase_data['status'] == 'active' else "⏸️"
            report.append(f"\n### {status_emoji} Phase {phase_num}: {phase_data['name']}")
            report.append(f"**Status**: {phase_data['status']}")
            if phase_data['agents']:
                report.append("**Agents Used**:")
                for agent in phase_data['agents']:
                    report.append(f"- {agent}")
        
        report.append("\n## Metrics")
        report.append(f"- **Total Time**: {project['metrics']['total_time']} minutes")
        report.append(f"- **Success Rate**: {project['metrics']['success_rate']}%")
        if project['metrics']['satisfaction']:
            avg_satisfaction = sum(project['metrics']['satisfaction']) / len(project['metrics']['satisfaction'])
            report.append(f"- **Average Satisfaction**: {avg_satisfaction:.1f}/10")
        report.append(f"- **Total Agent Interactions**: {len(project['agents_used'])}")
        
        report.append("\n## Agent Activity Log")
        for entry in project['agents_used'][-10:]:  # Last 10 interactions
            success_mark = "✓" if entry['success'] else "✗"
            report.append(f"- {success_mark} **{entry['agent']}**: {entry['task'][:60]}... (Satisfaction: {entry['satisfaction']}/10)")
        
        if project.get('notes'):
            report.append("\n## Notes")
            for note in project['notes'][-5:]:  # Last 5 notes
                report.append(f"- {note['date'][:10]}: {note['text']}")
        
        report.append("\n## Next Steps")
        current_phase = project['current_phase']
        if current_phase < 4 and project['status'] != 'completed':
            next_phase = project['phases'][current_phase + 1]
            report.append(f"Prepare for Phase {current_phase + 1}: {next_phase['name']}")
        elif project['status'] == 'completed':
            report.append("Project completed! Consider deployment and maintenance.")
        
        return '\n'.join(report)
    
    def export_project(self, project_name: str, format: str = 'yaml'):
        """Export project data"""
        if project_name not in self.active_projects:
            console.print(f"[red]Project '{project_name}' not found![/red]")
            return
        
        project = self.active_projects[project_name]
        export_dir = self.base_path / "exports"
        export_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{project_name.replace(' ', '_').lower()}_{timestamp}"
        
        if format == 'yaml':
            export_file = export_dir / f"{filename}.yaml"
            with open(export_file, 'w') as f:
                yaml.dump(project, f, default_flow_style=False)
        elif format == 'json':
            export_file = export_dir / f"{filename}.json"
            with open(export_file, 'w') as f:
                json.dump(project, f, indent=2)
        elif format == 'markdown':
            export_file = export_dir / f"{filename}.md"
            report = self.generate_project_report(project_name)
            with open(export_file, 'w') as f:
                f.write(report)
        
        console.print(f"[green]✓ Project exported to {export_file}[/green]")

def main():
    manager = ProjectManager()
    
    while True:
        console.print("\n[bold cyan]📊 Project Manager[/bold cyan]")
        console.print("\n1. Create Project")
        console.print("2. List Projects")
        console.print("3. View Project Details")
        console.print("4. Update Project Status")
        console.print("5. Add Note to Project")
        console.print("6. Generate Project Report")
        console.print("7. Export Project")
        console.print("8. Exit")
        
        choice = Prompt.ask("Select option", choices=['1', '2', '3', '4', '5', '6', '7', '8'])
        
        if choice == '1':
            manager.create_project()
        
        elif choice == '2':
            manager.list_projects()
        
        elif choice == '3':
            manager.list_projects()
            project_name = Prompt.ask("\nEnter project name")
            manager.show_project_details(project_name)
        
        elif choice == '4':
            manager.list_projects()
            project_name = Prompt.ask("\nEnter project name")
            status = Prompt.ask("New status", 
                              choices=['planning', 'active', 'paused', 'completed', 'archived'])
            manager.update_project_status(project_name, status)
        
        elif choice == '5':
            manager.list_projects()
            project_name = Prompt.ask("\nEnter project name")
            note = Prompt.ask("Enter note")
            manager.add_note(project_name, note)
        
        elif choice == '6':
            manager.list_projects()
            project_name = Prompt.ask("\nEnter project name")
            report = manager.generate_project_report(project_name)
            console.print(Panel(report, title="Project Report", border_style="green"))
            
            if Confirm.ask("Save report to file?", default=True):
                manager.export_project(project_name, 'markdown')
        
        elif choice == '7':
            manager.list_projects()
            project_name = Prompt.ask("\nEnter project name")
            format_choice = Prompt.ask("Export format", choices=['yaml', 'json', 'markdown'])
            manager.export_project(project_name, format_choice)
        
        elif choice == '8':
            console.print("[yellow]Goodbye![/yellow]")
            break

if __name__ == "__main__":
    main()