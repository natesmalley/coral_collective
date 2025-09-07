#!/usr/bin/env python3
"""
Parallel Agent Runner - Execute multiple agents efficiently

Enables running agents in parallel when tasks are independent,
significantly reducing total execution time.
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agent_runner import AgentRunner
from tools.project_state import ProjectStateManager
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()


@dataclass
class ParallelTask:
    """Represents a task that can be run in parallel"""
    agent_id: str
    task: str
    context: Dict = None
    group: int = 0  # Tasks in same group run in parallel
    depends_on: List[str] = None  # Agent IDs this depends on


class ParallelAgentRunner:
    """Run multiple agents in parallel for efficiency"""
    
    def __init__(self, max_workers: int = 4):
        self.runner = AgentRunner()
        self.state_manager = ProjectStateManager()
        self.max_workers = max_workers
        self.results = {}
        
    def create_parallel_plan(self, project_type: str, description: str) -> List[List[ParallelTask]]:
        """
        Create a parallel execution plan for a project
        
        Returns:
            List of task groups where each group can run in parallel
        """
        plans = {
            "full_stack": [
                # Group 1: Initial planning (sequential)
                [ParallelTask("project-architect", f"Design architecture for {description}", group=1)],
                
                # Group 2: Documentation (sequential after architect)
                [ParallelTask("technical-writer-phase1", f"Create requirements for {description}", 
                            group=2, depends_on=["project-architect"])],
                
                # Group 3: Core development (parallel)
                [
                    ParallelTask("database-specialist", f"Design database schema for {description}", 
                               group=3, depends_on=["technical-writer-phase1"]),
                    ParallelTask("api-designer", f"Design API endpoints for {description}", 
                               group=3, depends_on=["technical-writer-phase1"]),
                    ParallelTask("ui-designer", f"Create UI mockups for {description}", 
                               group=3, depends_on=["technical-writer-phase1"])
                ],
                
                # Group 4: Implementation (parallel)
                [
                    ParallelTask("backend-developer", f"Implement backend for {description}", 
                               group=4, depends_on=["database-specialist", "api-designer"]),
                    ParallelTask("frontend-developer", f"Implement frontend for {description}", 
                               group=4, depends_on=["ui-designer"])
                ],
                
                # Group 5: Integration & Testing (parallel)
                [
                    ParallelTask("full-stack-engineer", f"Integrate frontend and backend for {description}", 
                               group=5, depends_on=["backend-developer", "frontend-developer"]),
                    ParallelTask("qa-testing", f"Test implementation of {description}", 
                               group=5, depends_on=["backend-developer", "frontend-developer"])
                ],
                
                # Group 6: Deployment
                [ParallelTask("devops-deployment", f"Deploy {description}", 
                            group=6, depends_on=["full-stack-engineer", "qa-testing"])]
            ],
            
            "api": [
                # Group 1: Planning
                [ParallelTask("project-architect", f"Design API architecture for {description}", group=1)],
                
                # Group 2: Specification (parallel)
                [
                    ParallelTask("api-designer", f"Design API specification for {description}", 
                               group=2, depends_on=["project-architect"]),
                    ParallelTask("database-specialist", f"Design data models for {description}", 
                               group=2, depends_on=["project-architect"])
                ],
                
                # Group 3: Implementation (parallel)
                [
                    ParallelTask("backend-developer", f"Implement API endpoints for {description}", 
                               group=3, depends_on=["api-designer", "database-specialist"]),
                    ParallelTask("security-specialist", f"Implement authentication for {description}", 
                               group=3, depends_on=["api-designer"])
                ],
                
                # Group 4: Testing & Deployment
                [
                    ParallelTask("qa-testing", f"Test API endpoints for {description}", 
                               group=4, depends_on=["backend-developer", "security-specialist"]),
                    ParallelTask("devops-deployment", f"Deploy API for {description}", 
                               group=4, depends_on=["backend-developer", "security-specialist"])
                ]
            ],
            
            "frontend": [
                # Group 1: Design (parallel)
                [
                    ParallelTask("ui-designer", f"Create design system for {description}", group=1),
                    ParallelTask("project-architect", f"Plan frontend architecture for {description}", group=1)
                ],
                
                # Group 2: Component Development (parallel)
                [
                    ParallelTask("frontend-developer", f"Build components for {description}", 
                               group=2, depends_on=["ui-designer", "project-architect"]),
                    ParallelTask("accessibility-specialist", f"Ensure accessibility for {description}", 
                               group=2, depends_on=["ui-designer"])
                ],
                
                # Group 3: Integration & Testing
                [
                    ParallelTask("full-stack-engineer", f"Integrate and optimize {description}", 
                               group=3, depends_on=["frontend-developer"]),
                    ParallelTask("qa-testing", f"Test UI components for {description}", 
                               group=3, depends_on=["frontend-developer"])
                ]
            ]
        }
        
        return plans.get(project_type, self._default_plan(description))
    
    def _default_plan(self, description: str) -> List[List[ParallelTask]]:
        """Default plan for unknown project types"""
        return [
            [ParallelTask("project-architect", f"Plan {description}", group=1)],
            [ParallelTask("full-stack-engineer", f"Implement {description}", 
                        group=2, depends_on=["project-architect"])],
            [ParallelTask("qa-testing", f"Test {description}", 
                        group=3, depends_on=["full-stack-engineer"])]
        ]
    
    def run_agent_task(self, task: ParallelTask) -> Dict:
        """
        Run a single agent task
        
        Returns:
            Result dictionary from agent execution
        """
        # Set non-interactive mode for parallel execution
        os.environ['CORAL_NON_INTERACTIVE'] = '1'
        
        try:
            # Update scratchpad with task info
            self._update_scratchpad(task)
            
            # Run the agent
            result = self.runner.run_agent(
                task.agent_id,
                task.task,
                task.context or {},
                non_interactive=True
            )
            
            # Update activity tracker
            self._update_activity_tracker(task, result)
            
            return result
            
        except Exception as e:
            console.print(f"[red]Error running {task.agent_id}: {e}[/red]")
            return {
                'agent': task.agent_id,
                'task': task.task,
                'success': False,
                'error': str(e)
            }
    
    def run_parallel_group(self, tasks: List[ParallelTask]) -> List[Dict]:
        """
        Run a group of tasks in parallel
        
        Returns:
            List of results from all tasks
        """
        with ThreadPoolExecutor(max_workers=min(len(tasks), self.max_workers)) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self.run_agent_task, task): task 
                for task in tasks
            }
            
            results = []
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=console
            ) as progress:
                
                task_progress = progress.add_task(
                    f"Running {len(tasks)} agents in parallel...", 
                    total=len(tasks)
                )
                
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    try:
                        result = future.result()
                        results.append(result)
                        self.results[task.agent_id] = result
                        
                        status = "✅" if result.get('success', True) else "❌"
                        console.print(f"{status} {task.agent_id} completed")
                        
                    except Exception as e:
                        console.print(f"[red]❌ {task.agent_id} failed: {e}[/red]")
                        results.append({
                            'agent': task.agent_id,
                            'success': False,
                            'error': str(e)
                        })
                    
                    progress.update(task_progress, advance=1)
            
            return results
    
    def execute_plan(self, plan: List[List[ParallelTask]]) -> Dict:
        """
        Execute a complete parallel execution plan
        
        Returns:
            Summary of execution
        """
        console.print("\n[bold cyan]🚀 Starting Parallel Agent Execution[/bold cyan]\n")
        
        total_start = time.time()
        all_results = []
        
        for group_num, task_group in enumerate(plan, 1):
            console.print(f"\n[bold]Phase {group_num}/{len(plan)}[/bold]")
            
            # Show what's running
            agents = [task.agent_id for task in task_group]
            if len(agents) == 1:
                console.print(f"Running: {agents[0]}")
            else:
                console.print(f"Running in parallel: {', '.join(agents)}")
            
            # Run the group
            group_start = time.time()
            
            if len(task_group) == 1:
                # Single task, run normally
                results = [self.run_agent_task(task_group[0])]
            else:
                # Multiple tasks, run in parallel
                results = self.run_parallel_group(task_group)
            
            group_time = time.time() - group_start
            all_results.extend(results)
            
            # Report group results
            console.print(f"Phase {group_num} completed in {group_time:.1f} seconds")
            
            # Check for failures
            failures = [r for r in results if not r.get('success', True)]
            if failures:
                console.print(f"[yellow]⚠️ {len(failures)} tasks failed in this phase[/yellow]")
        
        total_time = time.time() - total_start
        
        # Generate summary
        summary = self._generate_summary(all_results, total_time, plan)
        self._print_summary(summary)
        
        return summary
    
    def _update_scratchpad(self, task: ParallelTask):
        """Update scratchpad.md with task information"""
        scratchpad_path = Path("scratchpad.md")
        
        if not scratchpad_path.exists():
            scratchpad_path.write_text("# Scratchpad\n\n")
        
        with open(scratchpad_path, 'a') as f:
            f.write(f"\n## {task.agent_id} - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"Task: {task.task}\n")
            if task.depends_on:
                f.write(f"Dependencies: {', '.join(task.depends_on)}\n")
            f.write("\n")
    
    def _update_activity_tracker(self, task: ParallelTask, result: Dict):
        """Update activity_tracker.md with results"""
        tracker_path = Path("activity_tracker.md")
        
        if not tracker_path.exists():
            tracker_path.write_text("# Activity Tracker\n\n")
        
        with open(tracker_path, 'a') as f:
            f.write(f"\n### [{datetime.now().strftime('%Y-%m-%d %H:%M')}] {task.agent_id}\n")
            f.write(f"**Task**: {task.task}\n")
            f.write(f"**Status**: {'✅ Completed' if result.get('success', True) else '❌ Failed'}\n")
            if result.get('prompt_file'):
                f.write(f"**Prompt File**: {result['prompt_file']}\n")
            if result.get('error'):
                f.write(f"**Error**: {result['error']}\n")
            f.write("\n---\n")
    
    def _generate_summary(self, results: List[Dict], total_time: float, plan: List[List[ParallelTask]]) -> Dict:
        """Generate execution summary"""
        successful = sum(1 for r in results if r.get('success', True))
        failed = len(results) - successful
        
        # Calculate time saved
        # Estimate sequential time (each task would take ~30 seconds)
        sequential_estimate = len(results) * 30
        time_saved = sequential_estimate - total_time
        efficiency = (time_saved / sequential_estimate * 100) if sequential_estimate > 0 else 0
        
        return {
            'total_agents': len(results),
            'successful': successful,
            'failed': failed,
            'success_rate': successful / len(results) if results else 0,
            'total_time_seconds': total_time,
            'sequential_estimate_seconds': sequential_estimate,
            'time_saved_seconds': time_saved,
            'efficiency_gain_percent': efficiency,
            'phases': len(plan),
            'max_parallel': max(len(group) for group in plan),
            'results': results
        }
    
    def _print_summary(self, summary: Dict):
        """Print execution summary"""
        console.print("\n[bold green]✅ Execution Complete![/bold green]\n")
        
        table = Table(title="Execution Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Agents", str(summary['total_agents']))
        table.add_row("Successful", str(summary['successful']))
        table.add_row("Failed", str(summary['failed']))
        table.add_row("Success Rate", f"{summary['success_rate']*100:.1f}%")
        table.add_row("Total Time", f"{summary['total_time_seconds']:.1f} seconds")
        table.add_row("Sequential Estimate", f"{summary['sequential_estimate_seconds']:.1f} seconds")
        table.add_row("Time Saved", f"{summary['time_saved_seconds']:.1f} seconds")
        table.add_row("Efficiency Gain", f"{summary['efficiency_gain_percent']:.1f}%")
        table.add_row("Phases", str(summary['phases']))
        table.add_row("Max Parallel", str(summary['max_parallel']))
        
        console.print(table)


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run agents in parallel for efficiency")
    parser.add_argument('project_type', choices=['full_stack', 'api', 'frontend', 'custom'],
                       help="Type of project to build")
    parser.add_argument('description', help="Project description")
    parser.add_argument('--max-workers', type=int, default=4,
                       help="Maximum parallel workers (default: 4)")
    parser.add_argument('--show-plan', action='store_true',
                       help="Show execution plan without running")
    
    args = parser.parse_args()
    
    runner = ParallelAgentRunner(max_workers=args.max_workers)
    
    # Create execution plan
    plan = runner.create_parallel_plan(args.project_type, args.description)
    
    if args.show_plan:
        # Just show the plan
        console.print("\n[bold cyan]Execution Plan:[/bold cyan]\n")
        for i, group in enumerate(plan, 1):
            console.print(f"[bold]Phase {i}:[/bold]")
            for task in group:
                deps = f" (depends on: {', '.join(task.depends_on)})" if task.depends_on else ""
                console.print(f"  - {task.agent_id}: {task.task}{deps}")
        console.print(f"\n[cyan]Total phases: {len(plan)}[/cyan]")
        console.print(f"[cyan]Max parallelism: {max(len(g) for g in plan)} agents[/cyan]")
    else:
        # Execute the plan
        summary = runner.execute_plan(plan)
        
        # Save summary to file
        summary_path = Path("parallel_execution_summary.json")
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        console.print(f"\n[green]Summary saved to: {summary_path}[/green]")


if __name__ == "__main__":
    main()