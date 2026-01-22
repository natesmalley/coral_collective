"""
Integration tests for CoralCollective Agent Workflows

Tests cover:
1. Multi-agent workflow execution
2. Agent coordination and sequencing
3. Workflow orchestration patterns
4. Error handling in workflows
5. Performance under load
"""

import pytest
import asyncio
import tempfile
import shutil
import yaml
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from coral_collective.agent_runner import AgentRunner
from coral_collective.tools.project_state import ProjectStateManager
from coral_collective.tools.feedback_collector import FeedbackCollector
# MultiAgentOrchestrator is not in coral_collective.tools
# from coral_collective.tools.multi_agent_orchestrator import MultiAgentOrchestrator
from tests.fixtures.test_data import MockProjectSetup, create_test_environment


@pytest.mark.integration
@pytest.mark.workflows
class TestBasicAgentWorkflows:
    """Test basic agent workflow patterns"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir, self.setup = create_test_environment()
        
        # Create agents configuration
        self.agents_config = {
            "version": 1,
            "agents": {
                "project_architect": {
                    "role": "architect",
                    "prompt_path": "agents/core/project_architect.md",
                    "capabilities": ["planning", "architecture", "handoff"]
                },
                "backend_developer": {
                    "role": "backend_developer",
                    "prompt_path": "agents/specialists/backend_developer.md", 
                    "capabilities": ["api", "database", "server"]
                },
                "frontend_developer": {
                    "role": "frontend_developer",
                    "prompt_path": "agents/specialists/frontend_developer.md",
                    "capabilities": ["ui", "components", "styling"]
                },
                "qa_testing": {
                    "role": "qa_testing",
                    "prompt_path": "agents/specialists/qa_testing.md",
                    "capabilities": ["testing", "validation", "quality"]
                },
                "devops_deployment": {
                    "role": "devops_deployment",
                    "prompt_path": "agents/specialists/devops_deployment.md",
                    "capabilities": ["deployment", "infrastructure", "monitoring"]
                }
            }
        }
        self.setup.create_agents_config(self.agents_config)
        
        # Create agent prompt files
        self.create_agent_prompts()
        
        # Initialize components
        self.state_manager = ProjectStateManager(self.temp_dir)
        self.feedback_collector = FeedbackCollector(base_path=self.temp_dir)
        
    def teardown_method(self):
        """Clean up test files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_agent_prompts(self):
        """Create sample agent prompt files"""
        agents_dir = self.temp_dir / "agents"
        agents_dir.mkdir(exist_ok=True)
        (agents_dir / "core").mkdir(exist_ok=True)
        (agents_dir / "specialists").mkdir(exist_ok=True)
        
        prompts = {
            "agents/core/project_architect.md": """# Project Architect
You are a Senior Project Architect AI agent specializing in system design.
## Deliverables
- Architecture documentation
- Project roadmap
- Agent workflow plan
""",
            "agents/specialists/backend_developer.md": """# Backend Developer
You are a Senior Backend Developer AI agent.
## Deliverables
- API implementations
- Database schemas
- Authentication systems
""",
            "agents/specialists/frontend_developer.md": """# Frontend Developer  
You are a Senior Frontend Developer AI agent.
## Deliverables
- UI components
- User interfaces
- Frontend applications
""",
            "agents/specialists/qa_testing.md": """# QA Testing
You are a Senior QA Engineer AI agent.
## Deliverables
- Test suites
- Quality reports
- Bug reports
""",
            "agents/specialists/devops_deployment.md": """# DevOps Deployment
You are a Senior DevOps Engineer AI agent.
## Deliverables
- Deployment pipelines
- Infrastructure code
- Monitoring setup
"""
        }
        
        for path, content in prompts.items():
            file_path = self.temp_dir / path
            with open(file_path, 'w') as f:
                f.write(content)
    
    def test_sequential_agent_workflow(self):
        """Test sequential execution of multiple agents"""
        with patch('agent_runner.Path') as mock_path:
            mock_path.return_value.parent = self.temp_dir
            
            runner = AgentRunner()
            
            # Define workflow sequence
            workflow_sequence = [
                ("project_architect", "Design system architecture"),
                ("backend_developer", "Implement REST API"),
                ("frontend_developer", "Build user interface"),
                ("qa_testing", "Write and run tests"),
                ("devops_deployment", "Deploy to production")
            ]
            
            workflow_results = []
            
            # Mock agent execution
            with patch.object(runner, 'run_agent') as mock_run:
                mock_run.return_value = "Agent completed successfully"
                
                # Execute workflow
                for agent_id, task in workflow_sequence:
                    # Record agent start
                    execution_id = self.state_manager.record_agent_start(agent_id, task)
                    
                    # Execute agent
                    result = runner.run_agent(agent_id, task)
                    
                    # Record completion
                    outputs = {f"{agent_id}_output": f"Completed {task}"}
                    self.state_manager.record_agent_completion(execution_id, True, outputs)
                    
                    workflow_results.append({
                        "agent_id": agent_id,
                        "task": task,
                        "result": result,
                        "execution_id": execution_id
                    })
                    
                    # Record handoff (except for last agent)
                    if agent_id != workflow_sequence[-1][0]:
                        next_agent_id = workflow_sequence[workflow_sequence.index((agent_id, task)) + 1][0]
                        handoff_data = {
                            "summary": f"{agent_id} completed, ready for {next_agent_id}",
                            "artifacts": [f"{agent_id}_artifacts.json"],
                            "next_steps": [f"Begin {next_agent_id} tasks"]
                        }
                        self.state_manager.record_agent_handoff(agent_id, next_agent_id, handoff_data)
            
            # Verify workflow execution
            assert len(workflow_results) == 5
            assert all(result["result"] == "Agent completed successfully" for result in workflow_results)
            
            # Verify state management
            final_state = self.state_manager.get_current_state()
            assert len(final_state.completed_agents) == 5
            assert len(final_state.handoffs) == 4  # 4 handoffs between 5 agents
            
            # Verify execution order
            completed_agents = [agent.agent_id for agent in final_state.completed_agents]
            expected_order = [agent_id for agent_id, _ in workflow_sequence]
            assert completed_agents == expected_order
    
    def test_workflow_with_failures(self):
        """Test workflow handling with agent failures"""
        with patch('agent_runner.Path') as mock_path:
            mock_path.return_value.parent = self.temp_dir
            
            runner = AgentRunner()
            
            workflow_sequence = [
                ("project_architect", "Design architecture"),
                ("backend_developer", "This will fail"),
                ("frontend_developer", "Should not execute")
            ]
            
            # Mock agent execution with failure
            def mock_run_agent(agent_id, task, options=None):
                if agent_id == "backend_developer":
                    raise Exception("Backend development failed")
                return "Agent completed successfully"
            
            with patch.object(runner, 'run_agent', side_effect=mock_run_agent):
                # Execute workflow
                for i, (agent_id, task) in enumerate(workflow_sequence):
                    execution_id = self.state_manager.record_agent_start(agent_id, task)
                    
                    try:
                        result = runner.run_agent(agent_id, task)
                        self.state_manager.record_agent_completion(execution_id, True, {"success": True})
                    except Exception as e:
                        # Record failure
                        self.state_manager.record_agent_completion(
                            execution_id, 
                            False, 
                            {"error": str(e)}
                        )
                        # Stop workflow on failure
                        break
            
            # Verify failure handling
            final_state = self.state_manager.get_current_state()
            assert len(final_state.completed_agents) == 2  # architect + failed backend
            assert final_state.completed_agents[0].success is True  # architect succeeded
            assert final_state.completed_agents[1].success is False  # backend failed
            
            # Verify metrics reflect failure
            metrics = self.state_manager.get_project_metrics()
            assert metrics["successful_completions"] == 1
            assert metrics["failed_completions"] == 1
            assert metrics["success_rate"] == 0.5
    
    def test_workflow_with_conditional_branches(self):
        """Test workflow with conditional execution paths"""
        with patch('agent_runner.Path') as mock_path:
            mock_path.return_value.parent = self.temp_dir
            
            runner = AgentRunner()
            
            # Start with architecture
            arch_execution_id = self.state_manager.record_agent_start(
                "project_architect", 
                "Design architecture"
            )
            
            # Mock architecture result that determines branch
            architecture_result = {
                "architecture_type": "microservices",
                "requires_database": True,
                "deployment_complexity": "high"
            }
            
            with patch.object(runner, 'run_agent') as mock_run:
                mock_run.return_value = "Architecture completed"
                
                # Execute architect
                runner.run_agent("project_architect", "Design architecture")
                self.state_manager.record_agent_completion(
                    arch_execution_id, 
                    True, 
                    architecture_result
                )
                
                # Determine next agents based on architecture
                next_agents = []
                
                if architecture_result["requires_database"]:
                    next_agents.append("database_specialist")
                    
                if architecture_result["deployment_complexity"] == "high":
                    next_agents.append("devops_deployment")
                    
                next_agents.extend(["backend_developer", "frontend_developer", "qa_testing"])
                
                # Execute conditional agents
                for agent_id in next_agents:
                    execution_id = self.state_manager.record_agent_start(
                        agent_id, 
                        f"Execute {agent_id} tasks"
                    )
                    
                    result = runner.run_agent(agent_id, f"Execute {agent_id} tasks")
                    self.state_manager.record_agent_completion(execution_id, True, {"completed": True})
            
            # Verify conditional execution
            final_state = self.state_manager.get_current_state()
            executed_agents = [agent.agent_id for agent in final_state.completed_agents]
            
            assert "project_architect" in executed_agents
            assert "database_specialist" in executed_agents  # Should be included
            assert "devops_deployment" in executed_agents   # Should be included
            assert "backend_developer" in executed_agents
            assert "frontend_developer" in executed_agents
            assert "qa_testing" in executed_agents


@pytest.mark.integration
@pytest.mark.workflows
class TestParallelWorkflows:
    """Test parallel agent execution workflows"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir, self.setup = create_test_environment()
        self.setup.create_agents_config({
            "version": 1,
            "agents": {
                "backend_developer": {"role": "backend", "prompt_path": "agents/backend.md", "capabilities": ["api"]},
                "frontend_developer": {"role": "frontend", "prompt_path": "agents/frontend.md", "capabilities": ["ui"]},
                "database_specialist": {"role": "database", "prompt_path": "agents/database.md", "capabilities": ["schema"]},
                "security_specialist": {"role": "security", "prompt_path": "agents/security.md", "capabilities": ["auth"]}
            }
        })
        
        
    def teardown_method(self):
        """Clean up test files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_parallel_task_execution(self):
        """Test executing tasks in parallel"""
        # Create parallel tasks
        tasks = [
            AgentTask(
                task_id="backend_task",
                agent_id="backend_developer",
                task_description="Create API endpoints",
                parameters={"framework": "fastapi"},
                dependencies=[],
                priority=1
            ),
            AgentTask(
                task_id="frontend_task", 
                agent_id="frontend_developer",
                task_description="Build UI components",
                parameters={"framework": "react"},
                dependencies=[],
                priority=1
            ),
            AgentTask(
                task_id="database_task",
                agent_id="database_specialist", 
                task_description="Design database schema",
                parameters={"database": "postgresql"},
                dependencies=[],
                priority=1
            )
        ]
        
        # Mock agent execution
        async def mock_run_agent(agent_id, task, params):
            # Simulate different execution times
            execution_times = {
                "backend_developer": 0.1,
                "frontend_developer": 0.15,
                "database_specialist": 0.08
            }
            
            await asyncio.sleep(execution_times.get(agent_id, 0.1))
            
            return {
                "success": True,
                "outputs": {f"{agent_id}_result": f"Completed {task}"},
                "execution_time": execution_times[agent_id] * 1000
            }
        
        with patch.object(self.parallel_runner, '_run_agent', side_effect=mock_run_agent):
            start_time = asyncio.get_event_loop().time()
            results = await self.parallel_runner.execute_parallel_tasks(tasks, max_concurrent=3)
            end_time = asyncio.get_event_loop().time()
            
            execution_time = end_time - start_time
            
            # Verify all tasks completed
            assert len(results) == 3
            assert all(result["success"] for result in results)
            
            # Verify parallel execution was faster than sequential
            max_individual_time = max(0.1, 0.15, 0.08)  # Longest individual task
            assert execution_time < (max_individual_time * 3)  # Should be much faster than sequential
            
            # Verify each task result
            task_ids = [result["task_id"] for result in results]
            assert "backend_task" in task_ids
            assert "frontend_task" in task_ids 
            assert "database_task" in task_ids
    
    @pytest.mark.asyncio
    async def test_dependent_task_scheduling(self):
        """Test scheduling tasks with dependencies"""
        # Create tasks with dependencies
        tasks = [
            AgentTask(
                task_id="architect_task",
                agent_id="project_architect",
                task_description="Design system",
                parameters={},
                dependencies=[],
                priority=1
            ),
            AgentTask(
                task_id="backend_task",
                agent_id="backend_developer",
                task_description="Implement backend",
                parameters={},
                dependencies=["architect_task"],  # Depends on architecture
                priority=1
            ),
            AgentTask(
                task_id="frontend_task",
                agent_id="frontend_developer", 
                task_description="Implement frontend",
                parameters={},
                dependencies=["architect_task"],  # Also depends on architecture
                priority=1
            ),
            AgentTask(
                task_id="integration_task",
                agent_id="qa_testing",
                task_description="Integration testing",
                parameters={},
                dependencies=["backend_task", "frontend_task"],  # Depends on both implementations
                priority=1
            )
        ]
        
        # Resolve dependencies
        execution_order = self.parallel_runner.resolve_task_dependencies(tasks)
        
        # Verify dependency resolution
        execution_ids = [task.task_id for task in execution_order]
        
        # Architect should be first
        assert execution_ids[0] == "architect_task"
        
        # Backend and frontend should come after architect
        architect_index = execution_ids.index("architect_task")
        backend_index = execution_ids.index("backend_task")
        frontend_index = execution_ids.index("frontend_task")
        
        assert backend_index > architect_index
        assert frontend_index > architect_index
        
        # Integration should come after both backend and frontend
        integration_index = execution_ids.index("integration_task")
        assert integration_index > backend_index
        assert integration_index > frontend_index
    
    @pytest.mark.asyncio
    async def test_resource_constrained_execution(self):
        """Test execution with resource constraints"""
        # Create more tasks than allowed concurrent execution
        tasks = [
            AgentTask(
                task_id=f"task_{i}",
                agent_id=f"agent_{i % 4}",  # Cycle through 4 agents
                task_description=f"Execute task {i}",
                parameters={},
                dependencies=[],
                priority=1
            ) for i in range(8)  # 8 tasks
        ]
        
        # Track concurrent execution
        concurrent_count = 0
        max_concurrent_observed = 0
        
        async def mock_run_agent_with_tracking(agent_id, task, params):
            nonlocal concurrent_count, max_concurrent_observed
            
            concurrent_count += 1
            max_concurrent_observed = max(max_concurrent_observed, concurrent_count)
            
            await asyncio.sleep(0.05)  # Short execution time
            
            concurrent_count -= 1
            
            return {
                "success": True,
                "outputs": {"result": f"Completed {task}"},
                "execution_time": 50
            }
        
        with patch.object(self.parallel_runner, '_run_agent', side_effect=mock_run_agent_with_tracking):
            # Execute with concurrency limit
            results = await self.parallel_runner.execute_parallel_tasks(tasks, max_concurrent=3)
            
            # Verify all tasks completed
            assert len(results) == 8
            assert all(result["success"] for result in results)
            
            # Verify concurrency was respected
            assert max_concurrent_observed <= 3


@pytest.mark.integration
@pytest.mark.workflows
@pytest.mark.skip(reason="MultiAgentOrchestrator not available in coral_collective.tools")
class TestWorkflowOrchestration:
    """Test high-level workflow orchestration"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir, self.setup = create_test_environment()
        # self.orchestrator = MultiAgentOrchestrator(base_path=self.temp_dir)
        self.orchestrator = None  # Placeholder since class is not available
        
    def teardown_method(self):
        """Clean up test files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_full_stack_web_app_orchestration(self):
        """Test orchestrating a full-stack web application workflow"""
        project_requirements = {
            "type": "web_application",
            "features": [
                "user_authentication",
                "user_management", 
                "data_persistence",
                "responsive_ui",
                "api_endpoints"
            ],
            "technology_stack": {
                "frontend": "react",
                "backend": "python/fastapi",
                "database": "postgresql",
                "deployment": "docker"
            },
            "scale": "medium",
            "timeline": "6_weeks"
        }
        
        # Create orchestration plan
        plan = self.orchestrator.create_orchestration_plan(
            task="Build full-stack web application",
            requirements=project_requirements
        )
        
        # Verify plan structure
        assert plan is not None
        assert len(plan.phases) > 0
        assert len(plan.agent_sequence) > 0
        
        # Verify required agents are included
        agent_ids = [step["agent_id"] for step in plan.agent_sequence]
        
        # Should include core agents
        assert "project_architect" in agent_ids
        
        # Should include specialist agents based on requirements
        assert any("backend" in agent_id for agent_id in agent_ids)
        assert any("frontend" in agent_id for agent_id in agent_ids)
        assert any("database" in agent_id for agent_id in agent_ids)
        
        # Should include QA and deployment
        assert any("qa" in agent_id or "testing" in agent_id for agent_id in agent_ids)
        assert any("devops" in agent_id or "deployment" in agent_id for agent_id in agent_ids)
        
        # Verify phases are logical
        phase_names = [phase["name"] for phase in plan.phases]
        assert any("planning" in phase.lower() for phase in phase_names)
        assert any("development" in phase.lower() for phase in phase_names)
        assert any("testing" in phase.lower() or "qa" in phase.lower() for phase in phase_names)
        assert any("deployment" in phase.lower() for phase in phase_names)
        
    def test_microservices_orchestration(self):
        """Test orchestrating a microservices architecture workflow"""
        project_requirements = {
            "type": "microservices_architecture",
            "services": [
                "user_service",
                "product_service", 
                "order_service",
                "notification_service"
            ],
            "infrastructure": {
                "containerization": "docker",
                "orchestration": "kubernetes",
                "api_gateway": "nginx",
                "database": "postgresql",
                "message_queue": "rabbitmq"
            },
            "scale": "enterprise",
            "compliance": ["GDPR", "SOC2"]
        }
        
        plan = self.orchestrator.create_orchestration_plan(
            task="Build microservices platform",
            requirements=project_requirements
        )
        
        # Verify microservices-specific agents
        agent_ids = [step["agent_id"] for step in plan.agent_sequence]
        
        # Should include specialized agents
        assert any("architecture" in agent_id for agent_id in agent_ids)
        assert any("backend" in agent_id for agent_id in agent_ids)
        assert any("database" in agent_id for agent_id in agent_ids)
        assert any("devops" in agent_id for agent_id in agent_ids)
        
        # Should include compliance/security for enterprise requirements
        assert any("security" in agent_id for agent_id in agent_ids)
        
        # Verify parallel execution opportunities
        parallel_groups = self.orchestrator.identify_parallel_opportunities(plan.agent_sequence)
        
        # Microservices should have good parallelization
        assert len(parallel_groups) > 1
        
        # Should have parallel service development phase
        service_development_group = next(
            (group for group in parallel_groups 
             if any("backend" in agent for agent in group.get("agents", []))), 
            None
        )
        assert service_development_group is not None
    
    def test_workflow_optimization(self):
        """Test workflow optimization and performance estimation"""
        # Create a complex workflow
        agent_sequence = [
            {"agent_id": "project_architect", "dependencies": [], "estimated_duration": 4},
            {"agent_id": "backend_developer", "dependencies": ["project_architect"], "estimated_duration": 12},
            {"agent_id": "frontend_developer", "dependencies": ["project_architect"], "estimated_duration": 10},
            {"agent_id": "database_specialist", "dependencies": ["project_architect"], "estimated_duration": 8},
            {"agent_id": "security_specialist", "dependencies": ["backend_developer"], "estimated_duration": 6},
            {"agent_id": "qa_testing", "dependencies": ["frontend_developer", "backend_developer"], "estimated_duration": 8},
            {"agent_id": "devops_deployment", "dependencies": ["qa_testing", "security_specialist"], "estimated_duration": 4}
        ]
        
        # Optimize the sequence
        optimized_sequence = self.orchestrator.optimize_agent_sequence(agent_sequence)
        
        # Verify optimization preserved dependencies
        assert self.orchestrator.validate_agent_dependencies(optimized_sequence)
        
        # Create a plan for time estimation
        from coral_collective.tools.multi_agent_orchestrator import OrchestrationPlan
        plan = OrchestrationPlan(
            task="Test optimization",
            phases=[
                {"name": "Planning", "estimated_hours": 4},
                {"name": "Development", "estimated_hours": 30},
                {"name": "Testing", "estimated_hours": 8},
                {"name": "Deployment", "estimated_hours": 4}
            ],
            agent_sequence=optimized_sequence
        )
        
        # Estimate completion time
        estimated_time = self.orchestrator.estimate_completion_time(plan)
        
        # Should be less than sum of all individual times (due to parallelization)
        total_individual_time = sum(step["estimated_duration"] for step in agent_sequence)
        assert estimated_time < total_individual_time
        
        # Should be reasonable (greater than critical path)
        critical_path_time = max(
            4,  # architect
            4 + 12 + 6,  # architect -> backend -> security
            4 + 10 + 8,  # architect -> frontend -> qa
            4 + 8  # architect -> database
        )
        assert estimated_time >= critical_path_time


@pytest.mark.integration
@pytest.mark.workflows
@pytest.mark.performance
class TestWorkflowPerformance:
    """Test workflow performance under various conditions"""
    
    def setup_method(self):
        """Set up performance test environment"""
        self.temp_dir, self.setup = create_test_environment()
        
    def teardown_method(self):
        """Clean up test files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_large_workflow_performance(self):
        """Test performance with large number of agents"""
        import time
        
        # Create a large workflow (50 tasks)
        tasks = [
            AgentTask(
                task_id=f"task_{i}",
                agent_id=f"agent_{i % 10}",  # Cycle through 10 different agents
                task_description=f"Execute large workflow task {i}",
                parameters={"task_number": i},
                dependencies=[f"task_{i-1}"] if i > 0 and i % 10 == 0 else [],  # Some dependencies
                priority=1 if i < 25 else 2  # Mix of priorities
            ) for i in range(50)
        ]
        
        # Mock fast agent execution
        async def mock_fast_agent(agent_id, task, params):
            await asyncio.sleep(0.01)  # Very fast execution
            return {
                "success": True,
                "outputs": {"result": f"Completed {task}"},
                "execution_time": 10
            }
        
        with patch.object(self.parallel_runner, '_run_agent', side_effect=mock_fast_agent):
            start_time = time.time()
            
            # Execute with high concurrency
            results = await self.parallel_runner.execute_parallel_tasks(tasks, max_concurrent=10)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Verify all tasks completed
            assert len(results) == 50
            assert all(result["success"] for result in results)
            
            # Verify reasonable performance (should complete in under 5 seconds)
            assert execution_time < 5.0
            
            # Calculate throughput
            throughput = len(tasks) / execution_time
            assert throughput > 10  # Should handle at least 10 tasks per second
    
    @pytest.mark.asyncio
    async def test_memory_usage_during_workflows(self):
        """Test memory usage during workflow execution"""
        import psutil
        import os
        
        # Get process for memory monitoring
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create memory-intensive workflow simulation
        tasks = [
            AgentTask(
                task_id=f"memory_task_{i}",
                agent_id="memory_intensive_agent",
                task_description="Memory intensive task",
                parameters={"data_size": 1024 * 100},  # 100KB of data per task
                dependencies=[],
                priority=1
            ) for i in range(20)
        ]
        
        async def mock_memory_intensive_agent(agent_id, task, params):
            # Simulate memory allocation
            data_size = params.get("data_size", 1024)
            large_data = bytearray(data_size)  # Allocate memory
            
            await asyncio.sleep(0.05)  # Processing time
            
            # Return result (keeping reference to prevent GC)
            return {
                "success": True,
                "outputs": {"data": large_data, "size": len(large_data)},
                "execution_time": 50
            }
        
        with patch.object(self.parallel_runner, '_run_agent', side_effect=mock_memory_intensive_agent):
            results = await self.parallel_runner.execute_parallel_tasks(tasks, max_concurrent=5)
            
            # Check memory usage after execution
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = peak_memory - initial_memory
            
            # Verify all tasks completed
            assert len(results) == 20
            assert all(result["success"] for result in results)
            
            # Memory increase should be reasonable (less than 50MB for this test)
            assert memory_increase < 50
            
            # Verify memory is managed properly
            del results  # Clean up results
            import gc
            gc.collect()  # Force garbage collection
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_after_cleanup = final_memory - initial_memory
            
            # Memory should be mostly reclaimed
            assert memory_after_cleanup < memory_increase * 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])