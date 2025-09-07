"""
Multi-Agent Orchestrator for Parallel and Efficient Task Execution

Enables breaking down complex tasks into smaller pieces that can be
executed by multiple agents in parallel or in optimized sequences.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime
import networkx as nx
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml

from tools.project_state import ProjectStateManager


class ExecutionMode(Enum):
    """Agent execution modes"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    DEPENDENCY_BASED = "dependency_based"
    ROUND_ROBIN = "round_robin"
    PIPELINE = "pipeline"


@dataclass
class AgentTask:
    """Represents a single task for an agent"""
    id: str
    agent_id: str
    task: str
    context: Dict = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # Task IDs this depends on
    priority: int = 0  # Higher = more important
    estimated_time: int = 10  # Minutes
    can_parallelize: bool = True
    retry_on_failure: bool = False
    max_retries: int = 2
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class TaskResult:
    """Result from an agent task execution"""
    task_id: str
    agent_id: str
    success: bool
    duration_minutes: float
    outputs: Dict = field(default_factory=dict)
    artifacts: List[Dict] = field(default_factory=list)
    error: Optional[str] = None


class TaskDecomposer:
    """Breaks down complex tasks into smaller agent tasks"""
    
    def __init__(self):
        self.decomposition_rules = self._load_decomposition_rules()
    
    def _load_decomposition_rules(self) -> Dict:
        """Load task decomposition rules"""
        return {
            "full_stack_app": {
                "parallel_groups": [
                    ["database_schema", "api_design", "ui_mockups"],
                    ["backend_crud", "frontend_components"],
                    ["api_integration", "state_management"],
                    ["testing", "documentation"]
                ],
                "agents": {
                    "database_schema": "database-specialist",
                    "api_design": "api-designer",
                    "ui_mockups": "ui-designer",
                    "backend_crud": "backend-developer",
                    "frontend_components": "frontend-developer",
                    "api_integration": "frontend-developer",
                    "state_management": "frontend-developer",
                    "testing": "qa-testing",
                    "documentation": "technical-writer-phase2"
                }
            },
            "api_service": {
                "parallel_groups": [
                    ["database_design", "api_specification"],
                    ["endpoint_implementation", "data_models"],
                    ["authentication", "validation"],
                    ["testing", "documentation"]
                ],
                "agents": {
                    "database_design": "database-specialist",
                    "api_specification": "api-designer",
                    "endpoint_implementation": "backend-developer",
                    "data_models": "backend-developer",
                    "authentication": "security-specialist",
                    "validation": "backend-developer",
                    "testing": "qa-testing",
                    "documentation": "technical-writer-phase2"
                }
            },
            "frontend_ui": {
                "parallel_groups": [
                    ["design_system", "component_library"],
                    ["page_layouts", "routing"],
                    ["state_management", "api_integration"],
                    ["testing", "accessibility"]
                ],
                "agents": {
                    "design_system": "ui-designer",
                    "component_library": "frontend-developer",
                    "page_layouts": "frontend-developer",
                    "routing": "frontend-developer",
                    "state_management": "frontend-developer",
                    "api_integration": "frontend-developer",
                    "testing": "qa-testing",
                    "accessibility": "accessibility-specialist"
                }
            }
        }
    
    def decompose(self, project_type: str, project_description: str) -> List[List[AgentTask]]:
        """
        Decompose a project into parallel task groups
        
        Returns:
            List of task groups where each group can run in parallel
        """
        if project_type not in self.decomposition_rules:
            # Default decomposition for unknown types
            return self._default_decomposition(project_description)
        
        rules = self.decomposition_rules[project_type]
        task_groups = []
        
        for group_idx, parallel_tasks in enumerate(rules["parallel_groups"]):
            group = []
            for task_name in parallel_tasks:
                agent_id = rules["agents"][task_name]
                task = AgentTask(
                    id=f"{task_name}_{group_idx}",
                    agent_id=agent_id,
                    task=f"{task_name.replace('_', ' ').title()}: {project_description}",
                    priority=len(rules["parallel_groups"]) - group_idx,  # Earlier groups = higher priority
                    can_parallelize=True
                )
                
                # Add dependencies from previous groups
                if group_idx > 0:
                    prev_group_tasks = rules["parallel_groups"][group_idx - 1]
                    task.dependencies = [f"{t}_{group_idx-1}" for t in prev_group_tasks]
                
                group.append(task)
            
            task_groups.append(group)
        
        return task_groups
    
    def _default_decomposition(self, description: str) -> List[List[AgentTask]]:
        """Default decomposition for unknown project types"""
        return [
            [AgentTask(
                id="architect_0",
                agent_id="project-architect",
                task=f"Design architecture for: {description}",
                priority=10
            )],
            [AgentTask(
                id="requirements_1",
                agent_id="technical-writer-phase1",
                task=f"Document requirements for: {description}",
                priority=9,
                dependencies=["architect_0"]
            )],
            [
                AgentTask(
                    id="backend_2",
                    agent_id="backend-developer",
                    task=f"Implement backend for: {description}",
                    priority=8,
                    dependencies=["requirements_1"]
                ),
                AgentTask(
                    id="frontend_2",
                    agent_id="frontend-developer",
                    task=f"Implement frontend for: {description}",
                    priority=8,
                    dependencies=["requirements_1"]
                )
            ],
            [AgentTask(
                id="testing_3",
                agent_id="qa-testing",
                task=f"Test implementation of: {description}",
                priority=7,
                dependencies=["backend_2", "frontend_2"]
            )]
        ]


class MultiAgentOrchestrator:
    """Orchestrates multiple agent executions efficiently"""
    
    def __init__(self, project_path: Path = None):
        self.project_path = project_path or Path.cwd()
        self.state_manager = ProjectStateManager(self.project_path)
        self.decomposer = TaskDecomposer()
        self.task_graph = nx.DiGraph()
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.results: Dict[str, TaskResult] = {}
    
    def plan_execution(self, tasks: List[AgentTask]) -> nx.DiGraph:
        """
        Create an execution plan as a directed graph
        
        Args:
            tasks: List of agent tasks
            
        Returns:
            Directed graph showing task dependencies
        """
        graph = nx.DiGraph()
        
        # Add all tasks as nodes
        for task in tasks:
            graph.add_node(
                task.id,
                agent=task.agent_id,
                task=task.task,
                priority=task.priority,
                can_parallelize=task.can_parallelize
            )
        
        # Add dependency edges
        for task in tasks:
            for dep_id in task.dependencies:
                graph.add_edge(dep_id, task.id)
        
        self.task_graph = graph
        return graph
    
    def get_execution_order(self) -> List[List[str]]:
        """
        Get optimal execution order respecting dependencies
        
        Returns:
            List of task groups that can run in parallel
        """
        if not self.task_graph:
            return []
        
        # Topological generations give us parallel groups
        try:
            generations = list(nx.topological_generations(self.task_graph))
            return generations
        except nx.NetworkXError:
            # Cycle detected
            raise ValueError("Circular dependency detected in task graph")
    
    def execute_task(self, task: AgentTask) -> TaskResult:
        """
        Execute a single agent task
        
        Args:
            task: The task to execute
            
        Returns:
            Task execution result
        """
        start_time = datetime.now()
        
        # Record start in state manager
        self.state_manager.record_agent_start(
            task.agent_id,
            task.task,
            task.context
        )
        
        try:
            # In real implementation, this would call the actual agent
            # For now, simulate execution
            import time
            import random
            
            # Simulate work (in production, call agent_runner.run_agent)
            time.sleep(random.uniform(0.1, 0.5))
            
            # Simulate success/failure
            success = random.random() > 0.1  # 90% success rate
            
            duration = (datetime.now() - start_time).total_seconds() / 60
            
            # Record completion
            self.state_manager.record_agent_completion(
                task.agent_id,
                success=success,
                outputs={"task_id": task.id},
                artifacts=[]
            )
            
            return TaskResult(
                task_id=task.id,
                agent_id=task.agent_id,
                success=success,
                duration_minutes=duration,
                outputs={"completed": True},
                error=None if success else "Simulated failure"
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() / 60
            return TaskResult(
                task_id=task.id,
                agent_id=task.agent_id,
                success=False,
                duration_minutes=duration,
                error=str(e)
            )
    
    def execute_parallel_group(self, tasks: List[AgentTask]) -> List[TaskResult]:
        """
        Execute a group of tasks in parallel
        
        Args:
            tasks: Tasks that can run in parallel
            
        Returns:
            List of results
        """
        futures = []
        for task in tasks:
            if task.can_parallelize:
                future = self.executor.submit(self.execute_task, task)
                futures.append((task, future))
            else:
                # Execute sequentially if not parallelizable
                result = self.execute_task(task)
                self.results[task.id] = result
        
        # Collect parallel results
        results = []
        for task, future in futures:
            try:
                result = future.result(timeout=task.estimated_time * 60)
                self.results[task.id] = result
                results.append(result)
            except Exception as e:
                result = TaskResult(
                    task_id=task.id,
                    agent_id=task.agent_id,
                    success=False,
                    duration_minutes=0,
                    error=str(e)
                )
                self.results[task.id] = result
                results.append(result)
        
        return results
    
    def execute_workflow(self, 
                        project_type: str,
                        project_description: str,
                        mode: ExecutionMode = ExecutionMode.DEPENDENCY_BASED) -> Dict:
        """
        Execute a complete workflow with multiple agents
        
        Args:
            project_type: Type of project (full_stack_app, api_service, etc.)
            project_description: Description of what to build
            mode: Execution mode
            
        Returns:
            Execution summary
        """
        print(f"\n🚀 Starting Multi-Agent Workflow: {project_type}")
        print(f"📋 Project: {project_description}")
        print(f"⚙️ Mode: {mode.value}\n")
        
        # Decompose into tasks
        task_groups = self.decomposer.decompose(project_type, project_description)
        all_tasks = [task for group in task_groups for task in group]
        
        # Create execution plan
        self.plan_execution(all_tasks)
        
        # Get execution order
        execution_order = self.get_execution_order()
        
        print(f"📊 Execution Plan:")
        for i, group in enumerate(execution_order):
            agents = [self.task_graph.nodes[tid]['agent'] for tid in group]
            print(f"  Phase {i+1}: {', '.join(agents)} (parallel)")
        print()
        
        # Execute based on mode
        if mode == ExecutionMode.DEPENDENCY_BASED:
            results = self._execute_dependency_based(execution_order, all_tasks)
        elif mode == ExecutionMode.PARALLEL:
            results = self._execute_full_parallel(all_tasks)
        elif mode == ExecutionMode.SEQUENTIAL:
            results = self._execute_sequential(all_tasks)
        else:
            results = self._execute_dependency_based(execution_order, all_tasks)
        
        # Generate summary
        summary = self._generate_summary(results)
        return summary
    
    def _execute_dependency_based(self, 
                                  execution_order: List[List[str]], 
                                  all_tasks: List[AgentTask]) -> List[TaskResult]:
        """Execute tasks respecting dependencies"""
        results = []
        task_map = {task.id: task for task in all_tasks}
        
        for phase_num, task_ids in enumerate(execution_order, 1):
            print(f"\n🔄 Phase {phase_num}/{len(execution_order)}")
            
            # Get tasks for this phase
            phase_tasks = [task_map[tid] for tid in task_ids]
            
            # Execute in parallel
            phase_results = self.execute_parallel_group(phase_tasks)
            results.extend(phase_results)
            
            # Report results
            for result in phase_results:
                status = "✅" if result.success else "❌"
                print(f"  {status} {result.agent_id}: {result.duration_minutes:.2f} min")
            
            # Check for failures
            failures = [r for r in phase_results if not r.success]
            if failures and phase_num < len(execution_order):
                print(f"  ⚠️ {len(failures)} tasks failed, continuing with degraded mode")
        
        return results
    
    def _execute_full_parallel(self, tasks: List[AgentTask]) -> List[TaskResult]:
        """Execute all parallelizable tasks at once"""
        parallel_tasks = [t for t in tasks if t.can_parallelize]
        sequential_tasks = [t for t in tasks if not t.can_parallelize]
        
        print(f"🚀 Executing {len(parallel_tasks)} tasks in parallel")
        results = self.execute_parallel_group(parallel_tasks)
        
        print(f"📝 Executing {len(sequential_tasks)} tasks sequentially")
        for task in sequential_tasks:
            results.append(self.execute_task(task))
        
        return results
    
    def _execute_sequential(self, tasks: List[AgentTask]) -> List[TaskResult]:
        """Execute all tasks sequentially"""
        results = []
        for i, task in enumerate(tasks, 1):
            print(f"📝 Task {i}/{len(tasks)}: {task.agent_id}")
            results.append(self.execute_task(task))
        return results
    
    def _generate_summary(self, results: List[TaskResult]) -> Dict:
        """Generate execution summary"""
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        total_time = sum(r.duration_minutes for r in results)
        
        # Calculate time saved by parallelization
        sequential_time = sum(r.duration_minutes for r in results)
        parallel_time = max(r.duration_minutes for r in results) if results else 0
        time_saved = sequential_time - parallel_time
        
        summary = {
            "total_tasks": len(results),
            "successful": successful,
            "failed": failed,
            "success_rate": successful / len(results) if results else 0,
            "total_time_minutes": total_time,
            "sequential_time_estimate": sequential_time,
            "time_saved_minutes": time_saved,
            "efficiency_gain": f"{(time_saved / sequential_time * 100):.1f}%" if sequential_time > 0 else "0%",
            "results": results,
            "task_graph": self.task_graph
        }
        
        return summary
    
    def visualize_execution_plan(self, output_path: Path = None):
        """
        Create a visual representation of the execution plan
        
        Args:
            output_path: Where to save the visualization
        """
        try:
            import matplotlib.pyplot as plt
            
            if not self.task_graph:
                return
            
            plt.figure(figsize=(12, 8))
            
            # Layout the graph
            pos = nx.spring_layout(self.task_graph)
            
            # Draw nodes
            nx.draw_networkx_nodes(self.task_graph, pos, node_size=3000, node_color='lightblue')
            
            # Draw edges
            nx.draw_networkx_edges(self.task_graph, pos, edge_color='gray', arrows=True)
            
            # Draw labels
            labels = {node: f"{data['agent'].split('-')[0]}\n{node}" 
                     for node, data in self.task_graph.nodes(data=True)}
            nx.draw_networkx_labels(self.task_graph, pos, labels, font_size=8)
            
            plt.title("Agent Execution Plan")
            plt.axis('off')
            
            if output_path:
                plt.savefig(output_path)
            else:
                plt.show()
                
        except ImportError:
            print("Matplotlib not available for visualization")


# Example usage and testing
if __name__ == "__main__":
    orchestrator = MultiAgentOrchestrator()
    
    # Example 1: Full stack application
    print("=" * 60)
    print("Example 1: Full Stack Application")
    print("=" * 60)
    
    summary = orchestrator.execute_workflow(
        project_type="full_stack_app",
        project_description="Todo list app with authentication",
        mode=ExecutionMode.DEPENDENCY_BASED
    )
    
    print(f"\n📊 Summary:")
    print(f"  ✅ Success Rate: {summary['success_rate']*100:.1f}%")
    print(f"  ⏱️ Total Time: {summary['total_time_minutes']:.2f} minutes")
    print(f"  🚀 Time Saved: {summary['time_saved_minutes']:.2f} minutes")
    print(f"  📈 Efficiency Gain: {summary['efficiency_gain']}")
    
    # Example 2: API Service
    print("\n" + "=" * 60)
    print("Example 2: API Service")
    print("=" * 60)
    
    summary = orchestrator.execute_workflow(
        project_type="api_service",
        project_description="RESTful API for blog platform",
        mode=ExecutionMode.DEPENDENCY_BASED
    )
    
    print(f"\n📊 Summary:")
    print(f"  ✅ Success Rate: {summary['success_rate']*100:.1f}%")
    print(f"  ⏱️ Total Time: {summary['total_time_minutes']:.2f} minutes")
    print(f"  🚀 Time Saved: {summary['time_saved_minutes']:.2f} minutes")
    print(f"  📈 Efficiency Gain: {summary['efficiency_gain']}")