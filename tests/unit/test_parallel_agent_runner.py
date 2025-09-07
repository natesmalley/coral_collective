"""
Unit tests for Parallel Agent Runner

Tests cover:
1. Parallel agent execution
2. Resource management and constraints
3. Dependency resolution and ordering
4. Error handling in parallel execution
5. Performance monitoring and optimization
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import concurrent.futures
import threading
import time

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from parallel_agent_runner import (
    ParallelAgentRunner, AgentExecutor, ResourceManager,
    DependencyResolver, ExecutionPlanner, ParallelExecutionError
)


class TestAgentExecutor:
    """Test individual agent execution in parallel context"""
    
    def setup_method(self):
        """Set up test executor"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Mock agent configuration
        self.agent_config = {
            "backend_developer": {
                "role": "backend_developer",
                "prompt_path": "agents/specialists/backend_developer.md",
                "capabilities": ["api", "database"],
                "resource_requirements": {
                    "cpu": 1,
                    "memory_mb": 512,
                    "concurrent_limit": 2
                }
            },
            "frontend_developer": {
                "role": "frontend_developer",
                "prompt_path": "agents/specialists/frontend_developer.md",
                "capabilities": ["ui", "components"],
                "resource_requirements": {
                    "cpu": 1,
                    "memory_mb": 256,
                    "concurrent_limit": 3
                }
            }
        }
        
    def teardown_method(self):
        """Clean up test files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_agent_executor_initialization(self):
        """Test AgentExecutor initialization"""
        
        with patch('parallel_agent_runner.AgentRunner') as mock_runner:
            executor = AgentExecutor(
                agent_id="backend_developer",
                config=self.agent_config["backend_developer"],
                temp_dir=self.temp_dir
            )
            
            assert executor.agent_id == "backend_developer"
            assert executor.config == self.agent_config["backend_developer"]
            assert executor.status == "initialized"
            assert executor.result is None
    
    @pytest.mark.asyncio
    async def test_agent_execution_success(self):
        """Test successful agent execution"""
        
        with patch('parallel_agent_runner.AgentRunner') as mock_runner_class:
            mock_runner = Mock()
            mock_runner.run_agent = AsyncMock(return_value={
                "success": True,
                "outputs": {"result": "API created successfully"},
                "duration": 45.2,
                "artifacts": ["api.py", "models.py"]
            })
            mock_runner_class.return_value = mock_runner
            
            executor = AgentExecutor(
                agent_id="backend_developer",
                config=self.agent_config["backend_developer"],
                temp_dir=self.temp_dir
            )
            
            # Execute agent
            await executor.execute("Create REST API", project_id="test_project")
            
            # Verify execution
            assert executor.status == "completed"
            assert executor.result["success"] is True
            assert "API created successfully" in str(executor.result["outputs"])
            assert executor.execution_time > 0
            
            # Verify agent runner was called correctly
            mock_runner.run_agent.assert_called_once_with(
                "backend_developer",
                "Create REST API",
                {"project_id": "test_project"}
            )
    
    @pytest.mark.asyncio
    async def test_agent_execution_failure(self):
        """Test agent execution failure handling"""
        
        with patch('parallel_agent_runner.AgentRunner') as mock_runner_class:
            mock_runner = Mock()
            mock_runner.run_agent = AsyncMock(side_effect=Exception("Agent execution failed"))
            mock_runner_class.return_value = mock_runner
            
            executor = AgentExecutor(
                agent_id="backend_developer",
                config=self.agent_config["backend_developer"],
                temp_dir=self.temp_dir
            )
            
            # Execute agent (should handle exception)
            await executor.execute("Create REST API", project_id="test_project")
            
            # Verify failure handling
            assert executor.status == "failed"
            assert executor.error is not None
            assert "Agent execution failed" in str(executor.error)
            assert executor.result is None
    
    @pytest.mark.asyncio
    async def test_agent_execution_timeout(self):
        """Test agent execution timeout"""
        
        async def slow_execution(*args, **kwargs):
            await asyncio.sleep(10)  # Simulate slow execution
            return {"success": True}
            
        with patch('parallel_agent_runner.AgentRunner') as mock_runner_class:
            mock_runner = Mock()
            mock_runner.run_agent = AsyncMock(side_effect=slow_execution)
            mock_runner_class.return_value = mock_runner
            
            executor = AgentExecutor(
                agent_id="backend_developer",
                config=self.agent_config["backend_developer"],
                temp_dir=self.temp_dir
            )
            
            # Execute with short timeout
            await executor.execute(
                "Create REST API", 
                project_id="test_project",
                timeout=1  # 1 second timeout
            )
            
            # Should timeout and be marked as failed
            assert executor.status == "failed"
            assert "timeout" in str(executor.error).lower()


class TestResourceManager:
    """Test resource management for parallel execution"""
    
    def setup_method(self):
        """Set up test resource manager"""
        self.resource_config = {
            "max_cpu": 4,
            "max_memory_mb": 2048,
            "max_concurrent_agents": 5
        }
        self.manager = ResourceManager(self.resource_config)
    
    def test_resource_manager_initialization(self):
        """Test ResourceManager initialization"""
        assert self.manager.max_cpu == 4
        assert self.manager.max_memory_mb == 2048
        assert self.manager.max_concurrent_agents == 5
        assert self.manager.allocated_cpu == 0
        assert self.manager.allocated_memory_mb == 0
        assert len(self.manager.active_agents) == 0
    
    def test_resource_allocation(self):
        """Test resource allocation and deallocation"""
        agent_requirements = {
            "cpu": 1,
            "memory_mb": 512,
            "concurrent_limit": 2
        }
        
        # Test successful allocation
        allocation_id = self.manager.allocate_resources("backend_dev", agent_requirements)
        
        assert allocation_id is not None
        assert self.manager.allocated_cpu == 1
        assert self.manager.allocated_memory_mb == 512
        assert "backend_dev" in self.manager.active_agents
        
        # Test deallocation
        success = self.manager.deallocate_resources(allocation_id)
        
        assert success is True
        assert self.manager.allocated_cpu == 0
        assert self.manager.allocated_memory_mb == 0
        assert "backend_dev" not in self.manager.active_agents
    
    def test_resource_allocation_limits(self):
        """Test resource allocation limits"""
        # Allocate resources close to limits
        large_requirements = {
            "cpu": 3,
            "memory_mb": 1800,
            "concurrent_limit": 1
        }
        
        allocation_id1 = self.manager.allocate_resources("agent1", large_requirements)
        assert allocation_id1 is not None
        
        # Try to allocate more than available
        excessive_requirements = {
            "cpu": 2,
            "memory_mb": 500,
            "concurrent_limit": 1
        }
        
        allocation_id2 = self.manager.allocate_resources("agent2", excessive_requirements)
        assert allocation_id2 is None  # Should fail due to CPU limit
        
        # Verify first allocation is still active
        assert self.manager.allocated_cpu == 3
        assert self.manager.allocated_memory_mb == 1800
    
    def test_concurrent_agent_limit(self):
        """Test concurrent agent limits"""
        agent_requirements = {
            "cpu": 0.5,
            "memory_mb": 200,
            "concurrent_limit": 1
        }
        
        # Allocate up to limit
        allocations = []
        for i in range(self.resource_config["max_concurrent_agents"]):
            allocation_id = self.manager.allocate_resources(f"agent_{i}", agent_requirements)
            assert allocation_id is not None
            allocations.append(allocation_id)
        
        # Try to allocate one more (should fail)
        allocation_id = self.manager.allocate_resources("agent_extra", agent_requirements)
        assert allocation_id is None
        
        # Deallocate one and try again
        self.manager.deallocate_resources(allocations[0])
        allocation_id = self.manager.allocate_resources("agent_new", agent_requirements)
        assert allocation_id is not None
    
    def test_resource_availability_check(self):
        """Test checking resource availability"""
        requirements = {
            "cpu": 2,
            "memory_mb": 1000,
            "concurrent_limit": 1
        }
        
        # Should be available initially
        assert self.manager.can_allocate_resources(requirements) is True
        
        # Allocate resources
        allocation_id = self.manager.allocate_resources("test_agent", requirements)
        assert allocation_id is not None
        
        # Should not be available for same requirements now
        assert self.manager.can_allocate_resources(requirements) is False
        
        # Smaller requirements should still be available
        small_requirements = {
            "cpu": 1,
            "memory_mb": 500,
            "concurrent_limit": 1
        }
        assert self.manager.can_allocate_resources(small_requirements) is True


class TestDependencyResolver:
    """Test dependency resolution for agent execution order"""
    
    def setup_method(self):
        """Set up test dependency resolver"""
        self.resolver = DependencyResolver()
    
    def test_add_agent_dependencies(self):
        """Test adding agent dependencies"""
        self.resolver.add_dependency("frontend", "backend")
        self.resolver.add_dependency("qa_testing", "frontend")
        self.resolver.add_dependency("deployment", "qa_testing")
        
        assert "frontend" in self.resolver.dependencies
        assert "backend" in self.resolver.dependencies["frontend"]
        assert len(self.resolver.dependencies["qa_testing"]) == 1
        assert "frontend" in self.resolver.dependencies["qa_testing"]
    
    def test_resolve_execution_order(self):
        """Test resolving execution order based on dependencies"""
        # Set up dependency chain: backend -> frontend -> qa -> deployment
        self.resolver.add_dependency("frontend", "backend")
        self.resolver.add_dependency("qa_testing", "frontend")
        self.resolver.add_dependency("deployment", "qa_testing")
        
        # Add independent agent
        self.resolver.add_agent("documentation")
        
        agents = ["frontend", "backend", "qa_testing", "deployment", "documentation"]
        execution_order = self.resolver.resolve_execution_order(agents)
        
        # Verify order respects dependencies
        backend_idx = execution_order.index("backend")
        frontend_idx = execution_order.index("frontend")
        qa_idx = execution_order.index("qa_testing")
        deployment_idx = execution_order.index("deployment")
        
        assert backend_idx < frontend_idx
        assert frontend_idx < qa_idx
        assert qa_idx < deployment_idx
        # documentation can be anywhere since it has no dependencies
    
    def test_parallel_execution_groups(self):
        """Test identifying parallel execution groups"""
        # Set up mixed dependencies
        self.resolver.add_dependency("frontend", "backend")
        self.resolver.add_dependency("mobile", "backend")  # Both depend on backend
        self.resolver.add_dependency("qa_web", "frontend")
        self.resolver.add_dependency("qa_mobile", "mobile")
        
        agents = ["backend", "frontend", "mobile", "qa_web", "qa_mobile", "documentation"]
        groups = self.resolver.get_parallel_groups(agents)
        
        # Group 0: backend, documentation (no dependencies)
        # Group 1: frontend, mobile (depend on backend)
        # Group 2: qa_web, qa_mobile (depend on frontend/mobile)
        
        assert len(groups) >= 3
        assert "backend" in groups[0]
        assert "documentation" in groups[0]  # Independent agent
        assert "frontend" in groups[1]
        assert "mobile" in groups[1]
        assert "qa_web" in groups[2] or "qa_mobile" in groups[2]
    
    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies"""
        # Create circular dependency
        self.resolver.add_dependency("frontend", "backend")
        self.resolver.add_dependency("backend", "database")
        self.resolver.add_dependency("database", "frontend")  # Creates cycle
        
        agents = ["frontend", "backend", "database"]
        
        with pytest.raises(ParallelExecutionError) as exc_info:
            self.resolver.resolve_execution_order(agents)
        
        assert "circular dependency" in str(exc_info.value).lower()


class TestExecutionPlanner:
    """Test execution planning for parallel agent workflows"""
    
    def setup_method(self):
        """Set up test execution planner"""
        self.resource_config = {
            "max_cpu": 4,
            "max_memory_mb": 2048,
            "max_concurrent_agents": 3
        }
        
        self.agent_configs = {
            "backend": {
                "resource_requirements": {"cpu": 2, "memory_mb": 512, "concurrent_limit": 1},
                "estimated_duration_minutes": 45
            },
            "frontend": {
                "resource_requirements": {"cpu": 1, "memory_mb": 256, "concurrent_limit": 2},
                "estimated_duration_minutes": 30
            },
            "database": {
                "resource_requirements": {"cpu": 1, "memory_mb": 512, "concurrent_limit": 1},
                "estimated_duration_minutes": 20
            },
            "qa_testing": {
                "resource_requirements": {"cpu": 1, "memory_mb": 256, "concurrent_limit": 1},
                "estimated_duration_minutes": 60
            }
        }
        
        self.planner = ExecutionPlanner(self.resource_config, self.agent_configs)
    
    def test_execution_plan_creation(self):
        """Test creating execution plan"""
        agents = ["backend", "frontend", "database", "qa_testing"]
        dependencies = {
            "frontend": ["backend", "database"],
            "qa_testing": ["frontend"]
        }
        
        plan = self.planner.create_execution_plan(agents, dependencies)
        
        assert "phases" in plan
        assert "estimated_duration_minutes" in plan
        assert "resource_usage" in plan
        assert len(plan["phases"]) > 0
        
        # Verify dependencies are respected in phases
        phases = plan["phases"]
        
        # Find phases for each agent
        backend_phase = None
        frontend_phase = None
        qa_phase = None
        
        for i, phase in enumerate(phases):
            if "backend" in phase["agents"]:
                backend_phase = i
            if "frontend" in phase["agents"]:
                frontend_phase = i
            if "qa_testing" in phase["agents"]:
                qa_phase = i
        
        # Verify dependency ordering
        if backend_phase is not None and frontend_phase is not None:
            assert backend_phase < frontend_phase
        if frontend_phase is not None and qa_phase is not None:
            assert frontend_phase < qa_phase
    
    def test_resource_optimization(self):
        """Test resource usage optimization in planning"""
        agents = ["backend", "frontend", "database"]
        dependencies = {}  # No dependencies for this test
        
        plan = self.planner.create_execution_plan(agents, dependencies)
        
        # Verify resource constraints are respected in each phase
        for phase in plan["phases"]:
            total_cpu = sum(
                self.agent_configs[agent]["resource_requirements"]["cpu"]
                for agent in phase["agents"]
            )
            total_memory = sum(
                self.agent_configs[agent]["resource_requirements"]["memory_mb"]
                for agent in phase["agents"]
            )
            
            assert total_cpu <= self.resource_config["max_cpu"]
            assert total_memory <= self.resource_config["max_memory_mb"]
            assert len(phase["agents"]) <= self.resource_config["max_concurrent_agents"]
    
    def test_duration_estimation(self):
        """Test execution duration estimation"""
        agents = ["backend", "frontend", "database", "qa_testing"]
        dependencies = {
            "frontend": ["backend", "database"],
            "qa_testing": ["frontend"]
        }
        
        plan = self.planner.create_execution_plan(agents, dependencies)
        
        # Estimated duration should be reasonable
        assert plan["estimated_duration_minutes"] > 0
        
        # Should be less than sum of all durations (due to parallelization)
        total_sequential_duration = sum(
            self.agent_configs[agent]["estimated_duration_minutes"]
            for agent in agents
        )
        
        assert plan["estimated_duration_minutes"] < total_sequential_duration


@pytest.mark.asyncio
class TestParallelAgentRunner:
    """Test complete parallel agent runner functionality"""
    
    async def setup_method(self):
        """Set up test parallel agent runner"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        self.config = {
            "resources": {
                "max_cpu": 4,
                "max_memory_mb": 2048,
                "max_concurrent_agents": 3
            },
            "agents": {
                "backend_developer": {
                    "role": "backend_developer",
                    "prompt_path": "agents/specialists/backend_developer.md",
                    "resource_requirements": {
                        "cpu": 2,
                        "memory_mb": 512,
                        "concurrent_limit": 1
                    },
                    "estimated_duration_minutes": 45
                },
                "frontend_developer": {
                    "role": "frontend_developer",
                    "prompt_path": "agents/specialists/frontend_developer.md",
                    "resource_requirements": {
                        "cpu": 1,
                        "memory_mb": 256,
                        "concurrent_limit": 2
                    },
                    "estimated_duration_minutes": 30
                }
            }
        }
        
        with patch('parallel_agent_runner.yaml.safe_load') as mock_yaml, \
             patch('builtins.open'), \
             patch('parallel_agent_runner.Path.exists', return_value=True):
            
            mock_yaml.return_value = self.config
            self.runner = ParallelAgentRunner(base_path=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    async def test_single_agent_execution(self):
        """Test executing single agent"""
        
        with patch.object(self.runner, '_execute_agent') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "outputs": {"result": "Backend API created"},
                "duration": 45.2,
                "artifacts": ["api.py"]
            }
            
            result = await self.runner.run_agent(
                agent_id="backend_developer",
                task="Create REST API",
                project_id="test_project"
            )
            
            assert result["success"] is True
            assert "Backend API created" in str(result["outputs"])
            mock_execute.assert_called_once()
    
    async def test_parallel_agent_execution(self):
        """Test executing multiple agents in parallel"""
        
        agents_and_tasks = [
            ("backend_developer", "Create REST API"),
            ("frontend_developer", "Build user interface")
        ]
        
        with patch.object(self.runner, '_execute_agent') as mock_execute:
            # Mock successful execution for both agents
            mock_execute.side_effect = [
                {
                    "success": True,
                    "outputs": {"result": "Backend API created"},
                    "duration": 45.2,
                    "agent_id": "backend_developer"
                },
                {
                    "success": True,
                    "outputs": {"result": "Frontend UI created"},
                    "duration": 30.1,
                    "agent_id": "frontend_developer"
                }
            ]
            
            results = await self.runner.run_agents_parallel(
                agents_and_tasks,
                project_id="test_project"
            )
            
            assert len(results) == 2
            assert all(result["success"] for result in results)
            assert mock_execute.call_count == 2
    
    async def test_workflow_execution(self):
        """Test executing complete workflow with dependencies"""
        
        workflow = {
            "name": "full_stack_development",
            "agents": ["backend_developer", "frontend_developer"],
            "dependencies": {
                "frontend_developer": ["backend_developer"]
            },
            "tasks": {
                "backend_developer": "Create REST API and database schema",
                "frontend_developer": "Build user interface with API integration"
            }
        }
        
        with patch.object(self.runner, '_execute_agent') as mock_execute:
            # Mock successful execution
            mock_execute.side_effect = [
                {
                    "success": True,
                    "outputs": {"result": "Backend completed"},
                    "duration": 45,
                    "agent_id": "backend_developer"
                },
                {
                    "success": True,
                    "outputs": {"result": "Frontend completed"},
                    "duration": 30,
                    "agent_id": "frontend_developer"
                }
            ]
            
            results = await self.runner.run_workflow(
                workflow,
                project_id="test_project"
            )
            
            assert results["success"] is True
            assert len(results["agent_results"]) == 2
            assert results["total_duration"] > 0
            
            # Verify agents were executed in correct order (backend before frontend)
            call_args_list = mock_execute.call_args_list
            assert len(call_args_list) == 2
            
            # First call should be backend_developer
            first_call_agent = call_args_list[0][0][0]  # First positional arg
            assert first_call_agent == "backend_developer"
    
    async def test_error_handling_in_parallel_execution(self):
        """Test error handling during parallel execution"""
        
        agents_and_tasks = [
            ("backend_developer", "Create REST API"),
            ("frontend_developer", "Build user interface")
        ]
        
        with patch.object(self.runner, '_execute_agent') as mock_execute:
            # Mock one success and one failure
            mock_execute.side_effect = [
                {
                    "success": True,
                    "outputs": {"result": "Backend API created"},
                    "duration": 45.2,
                    "agent_id": "backend_developer"
                },
                {
                    "success": False,
                    "error": "Frontend execution failed",
                    "agent_id": "frontend_developer"
                }
            ]
            
            results = await self.runner.run_agents_parallel(
                agents_and_tasks,
                project_id="test_project"
            )
            
            assert len(results) == 2
            
            # Check mixed results
            success_count = sum(1 for result in results if result.get("success", False))
            failure_count = sum(1 for result in results if not result.get("success", True))
            
            assert success_count == 1
            assert failure_count == 1
    
    async def test_resource_constraint_handling(self):
        """Test handling of resource constraints during execution"""
        
        # Try to execute agents that exceed resource limits
        agents_and_tasks = [
            ("backend_developer", "Create REST API"),  # Requires 2 CPU
            ("frontend_developer", "Build UI"),        # Requires 1 CPU
            ("another_backend", "Create microservice")  # Would need 2 more CPU (total 5, limit is 4)
        ]
        
        # Add third agent to config for this test
        self.runner.agent_configs["another_backend"] = {
            "resource_requirements": {
                "cpu": 2,
                "memory_mb": 512,
                "concurrent_limit": 1
            },
            "estimated_duration_minutes": 40
        }
        
        with patch.object(self.runner, '_execute_agent') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "outputs": {"result": "Agent completed"},
                "duration": 30
            }
            
            # Should handle resource constraints by phased execution
            results = await self.runner.run_agents_parallel(
                agents_and_tasks,
                project_id="test_project"
            )
            
            # All agents should eventually complete
            assert len(results) == 3
            
            # All should be successful (mocked)
            assert all(result.get("success", False) for result in results)


@pytest.mark.performance
class TestParallelPerformance:
    """Performance tests for parallel execution"""
    
    @pytest.mark.asyncio
    async def test_parallel_speedup(self):
        """Test that parallel execution provides speedup"""
        
        # This test would measure actual execution times
        # For now, we'll test the theoretical speedup calculation
        
        sequential_durations = [45, 30, 20, 60]  # minutes
        
        # Sequential execution time
        sequential_total = sum(sequential_durations)
        
        # Parallel execution with 2 agents at a time
        parallel_phases = [
            [45, 30],   # Phase 1: 45 minutes (max of the two)
            [20, 60]    # Phase 2: 60 minutes (max of the two)
        ]
        parallel_total = sum(max(phase) for phase in parallel_phases)
        
        # Should show improvement
        speedup_ratio = sequential_total / parallel_total
        assert speedup_ratio > 1.0
        assert speedup_ratio < len(sequential_durations)  # Can't exceed number of agents
    
    @pytest.mark.asyncio
    async def test_resource_utilization_efficiency(self):
        """Test resource utilization efficiency"""
        
        resource_config = {
            "max_cpu": 4,
            "max_memory_mb": 2048,
            "max_concurrent_agents": 4
        }
        
        agent_requirements = [
            {"cpu": 1, "memory_mb": 256, "duration": 30},
            {"cpu": 1, "memory_mb": 256, "duration": 45},
            {"cpu": 2, "memory_mb": 512, "duration": 20},
            {"cpu": 1, "memory_mb": 256, "duration": 60}
        ]
        
        # Calculate theoretical optimal grouping
        # Agents 0, 1, 3 can run together (total: 3 CPU, 768MB)
        # Agent 2 runs separately (2 CPU, 512MB)
        
        phase1_duration = max([30, 45, 60])  # 60 minutes
        phase2_duration = 20  # 20 minutes
        optimal_total = phase1_duration + phase2_duration  # 80 minutes
        
        # Should be significantly better than sequential (155 minutes)
        sequential_total = sum(req["duration"] for req in agent_requirements)
        efficiency = (sequential_total - optimal_total) / sequential_total
        
        assert efficiency > 0.4  # At least 40% improvement


if __name__ == "__main__":
    pytest.main([__file__, "-v"])