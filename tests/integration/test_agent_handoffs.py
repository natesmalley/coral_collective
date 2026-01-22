"""
Integration tests for CoralCollective Agent Handoffs

Tests cover:
1. Agent-to-agent handoff protocols
2. Context and data passing between agents
3. Handoff validation and error handling
4. Memory preservation across handoffs
5. Complex multi-agent handoff scenarios
"""

import pytest
import asyncio
import tempfile
import shutil
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from coral_collective.agent_runner import AgentRunner
from coral_collective.tools.project_state import ProjectStateManager, AgentHandoff
from tests.fixtures.test_data import create_test_environment

# Try to import memory system if available
try:
    from memory.coral_memory_integration import CoralMemoryIntegration
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False


@pytest.mark.integration
@pytest.mark.handoffs
class TestBasicAgentHandoffs:
    """Test basic agent handoff functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir, self.setup = create_test_environment()
        
        # Create agents configuration with handoff-capable agents
        self.agents_config = {
            "version": 1,
            "agents": {
                "project_architect": {
                    "role": "architect",
                    "prompt_path": "agents/core/project_architect.md",
                    "capabilities": ["planning", "architecture", "handoff"],
                    "handoff_outputs": ["architecture_doc", "requirements", "agent_workflow"]
                },
                "backend_developer": {
                    "role": "backend_developer",
                    "prompt_path": "agents/specialists/backend_developer.md",
                    "capabilities": ["api", "database", "handoff"],
                    "handoff_outputs": ["api_spec", "database_schema", "backend_code"],
                    "handoff_inputs": ["architecture_doc", "requirements"]
                },
                "frontend_developer": {
                    "role": "frontend_developer", 
                    "prompt_path": "agents/specialists/frontend_developer.md",
                    "capabilities": ["ui", "components", "handoff"],
                    "handoff_outputs": ["ui_components", "frontend_code", "style_guide"],
                    "handoff_inputs": ["architecture_doc", "api_spec"]
                },
                "qa_testing": {
                    "role": "qa_testing",
                    "prompt_path": "agents/specialists/qa_testing.md",
                    "capabilities": ["testing", "validation", "handoff"],
                    "handoff_outputs": ["test_suites", "quality_report"],
                    "handoff_inputs": ["backend_code", "frontend_code", "api_spec"]
                }
            }
        }
        self.setup.create_agents_config(self.agents_config)
        
        # Initialize state manager
        self.state_manager = ProjectStateManager(self.temp_dir)
        
    def teardown_method(self):
        """Clean up test files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_simple_handoff_between_two_agents(self):
        """Test basic handoff from architect to backend developer"""
        with patch('agent_runner.Path') as mock_path:
            mock_path.return_value.parent = self.temp_dir
            
            runner = AgentRunner()
            
            # Execute architect agent
            architect_execution_id = self.state_manager.record_agent_start(
                "project_architect",
                "Design system architecture"
            )
            
            # Mock architect outputs
            architect_outputs = {
                "architecture_doc": "/docs/architecture.md",
                "requirements": "/docs/requirements.md", 
                "agent_workflow": "/docs/workflow.md",
                "tech_stack": "Python/FastAPI + React + PostgreSQL",
                "deployment_strategy": "Docker containers"
            }
            
            with patch.object(runner, 'run_agent') as mock_run:
                mock_run.return_value = "Architecture design completed"
                
                # Complete architect
                result = runner.run_agent("project_architect", "Design system architecture")
                self.state_manager.record_agent_completion(
                    architect_execution_id,
                    True,
                    architect_outputs
                )
                
                # Create handoff data
                handoff_data = {
                    "summary": "System architecture designed with microservices pattern",
                    "artifacts": [
                        architect_outputs["architecture_doc"],
                        architect_outputs["requirements"],
                        architect_outputs["agent_workflow"]
                    ],
                    "next_steps": [
                        "Implement REST API endpoints",
                        "Set up database schema",
                        "Configure authentication system"
                    ],
                    "context": {
                        "tech_stack": architect_outputs["tech_stack"],
                        "deployment_strategy": architect_outputs["deployment_strategy"]
                    },
                    "dependencies_provided": ["architecture_doc", "requirements"]
                }
                
                # Record handoff
                handoff_id = self.state_manager.record_agent_handoff(
                    from_agent="project_architect",
                    to_agent="backend_developer",
                    handoff_data=handoff_data
                )
                
                # Execute backend developer with handoff context
                backend_execution_id = self.state_manager.record_agent_start(
                    "backend_developer",
                    "Implement backend based on architecture"
                )
                
                # Backend should have access to architect's outputs
                handoff_context = self.get_handoff_context_for_agent("backend_developer")
                
                # Mock backend execution with handoff context
                mock_run.return_value = "Backend implementation completed"
                result = runner.run_agent(
                    "backend_developer", 
                    "Implement backend based on architecture",
                    {"handoff_context": handoff_context}
                )
                
                backend_outputs = {
                    "api_spec": "/docs/api_spec.yaml",
                    "database_schema": "/src/database/schema.sql",
                    "backend_code": "/src/api/",
                    "auth_system": "/src/auth/",
                    "base_tech_stack": handoff_context["context"]["tech_stack"]
                }
                
                self.state_manager.record_agent_completion(
                    backend_execution_id,
                    True,
                    backend_outputs
                )
        
        # Verify handoff was recorded correctly
        final_state = self.state_manager.get_current_state()
        assert len(final_state.handoffs) == 1
        
        handoff = final_state.handoffs[0]
        assert handoff.from_agent == "project_architect"
        assert handoff.to_agent == "backend_developer"
        assert handoff.data["summary"] == "System architecture designed with microservices pattern"
        assert len(handoff.data["artifacts"]) == 3
        assert len(handoff.data["next_steps"]) == 3
        
        # Verify both agents completed successfully
        assert len(final_state.completed_agents) == 2
        assert final_state.completed_agents[0].agent_id == "project_architect"
        assert final_state.completed_agents[1].agent_id == "backend_developer"
        assert all(agent.success for agent in final_state.completed_agents)
    
    def get_handoff_context_for_agent(self, agent_id):
        """Helper method to get handoff context for an agent"""
        state = self.state_manager.get_current_state()
        
        # Find handoffs targeting this agent
        relevant_handoffs = [
            handoff for handoff in state.handoffs
            if handoff.to_agent == agent_id
        ]
        
        if not relevant_handoffs:
            return {}
        
        # Combine context from all relevant handoffs
        combined_context = {
            "handoffs": [],
            "artifacts": [],
            "context": {},
            "next_steps": []
        }
        
        for handoff in relevant_handoffs:
            combined_context["handoffs"].append({
                "from_agent": handoff.from_agent,
                "summary": handoff.data.get("summary", ""),
                "timestamp": handoff.timestamp.isoformat()
            })
            
            combined_context["artifacts"].extend(handoff.data.get("artifacts", []))
            combined_context["context"].update(handoff.data.get("context", {}))
            combined_context["next_steps"].extend(handoff.data.get("next_steps", []))
        
        return combined_context
    
    def test_multi_agent_handoff_chain(self):
        """Test handoffs across multiple agents in sequence"""
        with patch('agent_runner.Path') as mock_path:
            mock_path.return_value.parent = self.temp_dir
            
            runner = AgentRunner()
            
            # Define handoff chain: architect -> backend -> frontend -> qa
            handoff_chain = [
                {
                    "agent_id": "project_architect",
                    "task": "Design system architecture",
                    "outputs": {
                        "architecture_doc": "/docs/architecture.md",
                        "requirements": "/docs/requirements.md"
                    }
                },
                {
                    "agent_id": "backend_developer", 
                    "task": "Implement backend API",
                    "outputs": {
                        "api_spec": "/docs/api_spec.yaml",
                        "backend_code": "/src/api/"
                    }
                },
                {
                    "agent_id": "frontend_developer",
                    "task": "Build user interface", 
                    "outputs": {
                        "ui_components": "/src/components/",
                        "frontend_code": "/src/frontend/"
                    }
                },
                {
                    "agent_id": "qa_testing",
                    "task": "Test complete application",
                    "outputs": {
                        "test_suites": "/tests/",
                        "quality_report": "/reports/quality.md"
                    }
                }
            ]
            
            with patch.object(runner, 'run_agent') as mock_run:
                mock_run.return_value = "Agent completed successfully"
                
                previous_agent = None
                all_artifacts = []
                
                for i, agent_info in enumerate(handoff_chain):
                    agent_id = agent_info["agent_id"]
                    task = agent_info["task"]
                    outputs = agent_info["outputs"]
                    
                    # Start agent execution
                    execution_id = self.state_manager.record_agent_start(agent_id, task)
                    
                    # Get handoff context if not first agent
                    handoff_context = {}
                    if previous_agent:
                        handoff_context = self.get_handoff_context_for_agent(agent_id)
                    
                    # Execute agent
                    result = runner.run_agent(agent_id, task, {"handoff_context": handoff_context})
                    
                    # Complete agent
                    self.state_manager.record_agent_completion(execution_id, True, outputs)
                    
                    # Create handoff to next agent (if not last)
                    if i < len(handoff_chain) - 1:
                        next_agent = handoff_chain[i + 1]["agent_id"]
                        
                        all_artifacts.extend(outputs.values())
                        
                        handoff_data = {
                            "summary": f"{agent_id} completed {task}",
                            "artifacts": list(outputs.values()),
                            "next_steps": [f"Begin {next_agent} tasks"],
                            "context": {
                                "completed_by": agent_id,
                                "completion_time": datetime.now().isoformat(),
                                "all_artifacts_so_far": all_artifacts.copy()
                            }
                        }
                        
                        self.state_manager.record_agent_handoff(
                            from_agent=agent_id,
                            to_agent=next_agent,
                            handoff_data=handoff_data
                        )
                    
                    previous_agent = agent_id
        
        # Verify complete handoff chain
        final_state = self.state_manager.get_current_state()
        
        # Should have 3 handoffs (4 agents = 3 handoffs between them)
        assert len(final_state.handoffs) == 3
        
        # Verify handoff sequence
        handoff_pairs = [(h.from_agent, h.to_agent) for h in final_state.handoffs]
        expected_pairs = [
            ("project_architect", "backend_developer"),
            ("backend_developer", "frontend_developer"), 
            ("frontend_developer", "qa_testing")
        ]
        assert handoff_pairs == expected_pairs
        
        # Verify all agents completed
        assert len(final_state.completed_agents) == 4
        
        # Verify final agent had access to all artifacts
        final_handoff = final_state.handoffs[-1]
        all_artifacts = final_handoff.data["context"]["all_artifacts_so_far"]
        assert "/docs/architecture.md" in all_artifacts
        assert "/docs/api_spec.yaml" in all_artifacts
        assert "/src/components/" in all_artifacts
    
    def test_parallel_handoffs_to_multiple_agents(self):
        """Test handoff from one agent to multiple agents in parallel"""
        with patch('agent_runner.Path') as mock_path:
            mock_path.return_value.parent = self.temp_dir
            
            runner = AgentRunner()
            
            # Architect creates outputs that both backend and frontend need
            architect_execution_id = self.state_manager.record_agent_start(
                "project_architect",
                "Design architecture for parallel development"
            )
            
            architect_outputs = {
                "architecture_doc": "/docs/architecture.md",
                "requirements": "/docs/requirements.md",
                "api_contracts": "/docs/api_contracts.yaml",
                "ui_wireframes": "/docs/wireframes.md"
            }
            
            with patch.object(runner, 'run_agent') as mock_run:
                mock_run.return_value = "Architecture completed"
                
                # Complete architect
                result = runner.run_agent("project_architect", "Design architecture")
                self.state_manager.record_agent_completion(
                    architect_execution_id,
                    True, 
                    architect_outputs
                )
                
                # Create handoffs to both backend and frontend
                backend_handoff_data = {
                    "summary": "Architecture ready for backend development",
                    "artifacts": [
                        architect_outputs["architecture_doc"],
                        architect_outputs["requirements"],
                        architect_outputs["api_contracts"]
                    ],
                    "next_steps": [
                        "Implement API endpoints per contracts",
                        "Set up database schema",
                        "Configure authentication"
                    ],
                    "context": {
                        "focus": "backend",
                        "priority_artifacts": ["api_contracts", "requirements"]
                    }
                }
                
                frontend_handoff_data = {
                    "summary": "Architecture ready for frontend development", 
                    "artifacts": [
                        architect_outputs["architecture_doc"],
                        architect_outputs["requirements"],
                        architect_outputs["ui_wireframes"],
                        architect_outputs["api_contracts"]
                    ],
                    "next_steps": [
                        "Build UI components per wireframes",
                        "Implement API integration",
                        "Create responsive design"
                    ],
                    "context": {
                        "focus": "frontend",
                        "priority_artifacts": ["ui_wireframes", "api_contracts"]
                    }
                }
                
                # Record parallel handoffs
                backend_handoff_id = self.state_manager.record_agent_handoff(
                    from_agent="project_architect",
                    to_agent="backend_developer",
                    handoff_data=backend_handoff_data
                )
                
                frontend_handoff_id = self.state_manager.record_agent_handoff(
                    from_agent="project_architect", 
                    to_agent="frontend_developer",
                    handoff_data=frontend_handoff_data
                )
                
                # Execute both agents in parallel (simulated)
                backend_execution_id = self.state_manager.record_agent_start(
                    "backend_developer",
                    "Develop backend from architecture"
                )
                
                frontend_execution_id = self.state_manager.record_agent_start(
                    "frontend_developer",
                    "Develop frontend from architecture"
                )
                
                # Get handoff contexts
                backend_context = self.get_handoff_context_for_agent("backend_developer")
                frontend_context = self.get_handoff_context_for_agent("frontend_developer")
                
                # Verify contexts are different and focused
                assert backend_context["context"]["focus"] == "backend"
                assert frontend_context["context"]["focus"] == "frontend"
                assert "api_contracts" in backend_context["context"]["priority_artifacts"]
                assert "ui_wireframes" in frontend_context["context"]["priority_artifacts"]
                
                # Complete both agents
                mock_run.return_value = "Development completed"
                
                runner.run_agent("backend_developer", "Develop backend", {"handoff_context": backend_context})
                self.state_manager.record_agent_completion(
                    backend_execution_id,
                    True,
                    {"api_implementation": "/src/api/", "database_schema": "/src/db/"}
                )
                
                runner.run_agent("frontend_developer", "Develop frontend", {"handoff_context": frontend_context})
                self.state_manager.record_agent_completion(
                    frontend_execution_id, 
                    True,
                    {"ui_components": "/src/ui/", "frontend_app": "/src/app/"}
                )
        
        # Verify parallel handoffs
        final_state = self.state_manager.get_current_state()
        
        # Should have 2 handoffs from architect
        assert len(final_state.handoffs) == 2
        
        architect_handoffs = [h for h in final_state.handoffs if h.from_agent == "project_architect"]
        assert len(architect_handoffs) == 2
        
        target_agents = [h.to_agent for h in architect_handoffs]
        assert "backend_developer" in target_agents
        assert "frontend_developer" in target_agents
        
        # Both handoffs should have occurred around the same time
        handoff_times = [h.timestamp for h in architect_handoffs]
        time_diff = abs((handoff_times[1] - handoff_times[0]).total_seconds())
        assert time_diff < 5  # Should be within 5 seconds of each other
        
        # Verify all agents completed successfully
        assert len(final_state.completed_agents) == 3
        completed_agents = [a.agent_id for a in final_state.completed_agents]
        assert "project_architect" in completed_agents
        assert "backend_developer" in completed_agents
        assert "frontend_developer" in completed_agents


@pytest.mark.integration
@pytest.mark.handoffs
class TestHandoffValidationAndErrors:
    """Test handoff validation and error handling"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir, self.setup = create_test_environment()
        self.state_manager = ProjectStateManager(self.temp_dir)
        
    def teardown_method(self):
        """Clean up test files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_handoff_validation_missing_dependencies(self):
        """Test validation when handoff dependencies are missing"""
        # Create handoff with missing required dependencies
        incomplete_handoff_data = {
            "summary": "Incomplete handoff",
            "artifacts": ["/some/file.md"],  # Missing required artifacts
            "next_steps": ["Do something"],
            "context": {}
            # Missing: dependencies_provided field
        }
        
        with pytest.raises(ValueError) as exc_info:
            handoff_id = self.state_manager.record_agent_handoff(
                from_agent="incomplete_agent",
                to_agent="backend_developer", 
                handoff_data=incomplete_handoff_data,
                validate_dependencies=True  # Enable validation
            )
        
        assert "missing required dependencies" in str(exc_info.value).lower()
    
    def test_handoff_with_invalid_artifacts(self):
        """Test handoff with non-existent artifact references"""
        # Create handoff data with invalid artifact paths
        invalid_handoff_data = {
            "summary": "Handoff with invalid artifacts",
            "artifacts": [
                "/nonexistent/file1.md",
                "/also/nonexistent/file2.json"
            ],
            "next_steps": ["Process invalid artifacts"],
            "context": {},
            "dependencies_provided": ["architecture"]
        }
        
        # Should still record handoff but mark artifacts as invalid
        handoff_id = self.state_manager.record_agent_handoff(
            from_agent="source_agent",
            to_agent="target_agent",
            handoff_data=invalid_handoff_data,
            validate_artifacts=True
        )
        
        # Handoff should be recorded with validation warnings
        state = self.state_manager.get_current_state()
        handoff = state.handoffs[0]
        
        # Should have validation metadata
        assert "validation_warnings" in handoff.data
        assert any("artifact not found" in warning.lower() 
                  for warning in handoff.data["validation_warnings"])
    
    def test_agent_execution_failure_after_handoff(self):
        """Test handling agent failure after receiving handoff"""
        with patch('agent_runner.Path') as mock_path:
            mock_path.return_value.parent = self.temp_dir
            
            runner = AgentRunner()
            
            # Successful first agent
            first_execution_id = self.state_manager.record_agent_start(
                "project_architect",
                "Create architecture"
            )
            
            first_outputs = {"architecture": "/docs/arch.md"}
            
            with patch.object(runner, 'run_agent') as mock_run:
                mock_run.return_value = "Architecture completed"
                
                runner.run_agent("project_architect", "Create architecture")
                self.state_manager.record_agent_completion(first_execution_id, True, first_outputs)
                
                # Create handoff
                handoff_data = {
                    "summary": "Architecture complete",
                    "artifacts": ["/docs/arch.md"],
                    "next_steps": ["Implement backend"],
                    "context": {"arch_type": "microservices"}
                }
                
                self.state_manager.record_agent_handoff(
                    from_agent="project_architect",
                    to_agent="backend_developer", 
                    handoff_data=handoff_data
                )
                
                # Second agent fails
                second_execution_id = self.state_manager.record_agent_start(
                    "backend_developer",
                    "Implement backend"
                )
                
                # Mock failure
                mock_run.side_effect = Exception("Backend implementation failed")
                
                try:
                    runner.run_agent("backend_developer", "Implement backend")
                except Exception as e:
                    # Record failure
                    self.state_manager.record_agent_completion(
                        second_execution_id,
                        False,
                        {"error": str(e), "failure_reason": "implementation_error"}
                    )
        
        # Verify failure is properly recorded
        final_state = self.state_manager.get_current_state()
        
        # Handoff should still exist
        assert len(final_state.handoffs) == 1
        
        # Should have both agents in completed list
        assert len(final_state.completed_agents) == 2
        
        # First agent succeeded, second failed
        assert final_state.completed_agents[0].success is True
        assert final_state.completed_agents[1].success is False
        
        # Verify failure details
        failed_agent = final_state.completed_agents[1]
        assert "implementation_error" in failed_agent.outputs["failure_reason"]
    
    def test_handoff_timeout_handling(self):
        """Test handling handoffs that timeout"""
        import time
        from unittest.mock import patch
        
        # Create a handoff with timeout simulation
        handoff_data = {
            "summary": "Handoff with timeout",
            "artifacts": ["/docs/spec.md"],
            "next_steps": ["Process with timeout"],
            "context": {"timeout_seconds": 1},
            "expected_completion": datetime.now() + timedelta(seconds=1)
        }
        
        handoff_id = self.state_manager.record_agent_handoff(
            from_agent="source_agent",
            to_agent="slow_agent",
            handoff_data=handoff_data
        )
        
        # Simulate agent taking too long to start processing handoff
        time.sleep(2)  # Wait longer than expected completion
        
        # Start agent after timeout
        execution_id = self.state_manager.record_agent_start(
            "slow_agent",
            "Process delayed handoff"
        )
        
        # Verify timeout is detected
        state = self.state_manager.get_current_state()
        handoff = state.handoffs[0]
        
        # Check if handoff is overdue
        expected_completion = handoff.data.get("expected_completion")
        if expected_completion and isinstance(expected_completion, str):
            expected_completion = datetime.fromisoformat(expected_completion)
        
        is_overdue = datetime.now() > expected_completion if expected_completion else False
        assert is_overdue  # Should be overdue
        
        # Complete the agent (late)
        self.state_manager.record_agent_completion(
            execution_id,
            True,
            {
                "result": "Completed after timeout", 
                "delay_reason": "Complex processing required"
            }
        )
        
        # Verify completion is marked as delayed
        final_state = self.state_manager.get_current_state()
        completed_agent = final_state.completed_agents[0]
        assert completed_agent.success is True
        assert "delay_reason" in completed_agent.outputs


@pytest.mark.integration
@pytest.mark.handoffs
@pytest.mark.skipif(not MEMORY_AVAILABLE, reason="Memory system not available")
class TestMemoryIntegratedHandoffs:
    """Test handoffs with memory system integration"""
    
    def setup_method(self):
        """Set up test environment with memory"""
        self.temp_dir, self.setup = create_test_environment()
        self.setup.create_memory_config()
        
        self.state_manager = ProjectStateManager(self.temp_dir)
        
        # Initialize memory integration if available
        if MEMORY_AVAILABLE:
            self.memory_integration = CoralMemoryIntegration(self.temp_dir)
        
    def teardown_method(self):
        """Clean up test files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_handoff_with_memory_persistence(self):
        """Test handoff with memory system recording context"""
        if not MEMORY_AVAILABLE:
            pytest.skip("Memory system not available")
        
        # Record agent start with memory
        await self.memory_integration.record_agent_start(
            agent_id="project_architect",
            task="Design system with memory integration"
        )
        
        # Create rich handoff data
        handoff_data = {
            "summary": "Comprehensive architecture with detailed context",
            "artifacts": ["/docs/architecture.md", "/docs/api_spec.yaml"],
            "next_steps": ["Implement microservices", "Set up databases"],
            "context": {
                "architecture_pattern": "microservices",
                "technology_decisions": {
                    "backend": "Python/FastAPI",
                    "frontend": "React/TypeScript", 
                    "database": "PostgreSQL",
                    "cache": "Redis"
                },
                "scalability_requirements": "10k concurrent users",
                "performance_targets": {
                    "api_response_time": "< 200ms",
                    "page_load_time": "< 2s"
                }
            },
            "memory_context": {
                "key_decisions": [
                    "Chose microservices for scalability",
                    "Selected FastAPI for performance",
                    "PostgreSQL for ACID compliance"
                ],
                "constraints": [
                    "Budget limitation: $50k/month",
                    "Timeline: 12 weeks",
                    "Team size: 5 developers"
                ]
            }
        }
        
        # Record handoff in both state and memory
        handoff_id = self.state_manager.record_agent_handoff(
            from_agent="project_architect",
            to_agent="backend_developer",
            handoff_data=handoff_data
        )
        
        # Record handoff in memory system
        await self.memory_integration.memory_system.record_agent_handoff(
            from_agent="project_architect",
            to_agent="backend_developer",
            project_id=self.memory_integration.project_id,
            handoff_data=handoff_data
        )
        
        # Start next agent and retrieve context
        await self.memory_integration.record_agent_start(
            agent_id="backend_developer",
            task="Implement backend based on architecture"
        )
        
        # Get comprehensive context for backend developer
        agent_context = await self.memory_integration.memory_system.get_agent_context(
            agent_id="backend_developer",
            project_id=self.memory_integration.project_id
        )
        
        # Verify memory contains handoff information
        assert "recent_memories" in agent_context
        assert "relevant_memories" in agent_context
        
        # Check for handoff-related memories
        handoff_memories = [
            memory for memory in agent_context["recent_memories"]
            if "handoff" in memory.tags
        ]
        assert len(handoff_memories) > 0
        
        # Verify rich context is preserved
        relevant_memories = agent_context["relevant_memories"]
        architecture_memories = [
            memory for memory in relevant_memories
            if "architecture" in memory.content.lower() or "microservices" in memory.content.lower()
        ]
        assert len(architecture_memories) > 0
    
    @pytest.mark.asyncio
    async def test_multi_handoff_memory_consolidation(self):
        """Test memory consolidation across multiple handoffs"""
        if not MEMORY_AVAILABLE:
            pytest.skip("Memory system not available")
        
        # Simulate multi-agent workflow with memory
        agents_workflow = [
            {
                "agent_id": "project_architect",
                "task": "Design architecture",
                "outputs": {"arch_doc": "/docs/arch.md"},
                "key_decisions": ["Microservices pattern", "Event-driven architecture"]
            },
            {
                "agent_id": "backend_developer", 
                "task": "Implement API services",
                "outputs": {"api_code": "/src/api/", "api_docs": "/docs/api.md"},
                "key_decisions": ["FastAPI framework", "PostgreSQL database", "JWT authentication"]
            },
            {
                "agent_id": "frontend_developer",
                "task": "Build user interface",
                "outputs": {"ui_code": "/src/ui/", "components": "/src/components/"},
                "key_decisions": ["React with TypeScript", "Material-UI components", "Redux for state"]
            }
        ]
        
        accumulated_context = {}
        
        for i, agent_info in enumerate(agents_workflow):
            agent_id = agent_info["agent_id"]
            task = agent_info["task"]
            outputs = agent_info["outputs"]
            key_decisions = agent_info["key_decisions"]
            
            # Record agent start
            await self.memory_integration.record_agent_start(agent_id=agent_id, task=task)
            
            # Record key decisions in memory
            for decision in key_decisions:
                await self.memory_integration.memory_system.add_memory(
                    content=f"Decision: {decision}",
                    agent_id=agent_id,
                    project_id=self.memory_integration.project_id,
                    context={"type": "decision", "importance": "high"},
                    tags=["decision", "architecture"]
                )
            
            # Record completion
            await self.memory_integration.record_agent_completion(
                agent_id=agent_id,
                success=True,
                outputs=outputs
            )
            
            # Create handoff to next agent (if not last)
            if i < len(agents_workflow) - 1:
                next_agent_id = agents_workflow[i + 1]["agent_id"]
                
                # Accumulate context
                accumulated_context.update({
                    f"{agent_id}_outputs": outputs,
                    f"{agent_id}_decisions": key_decisions
                })
                
                handoff_data = {
                    "summary": f"{agent_id} completed {task}",
                    "artifacts": list(outputs.values()),
                    "next_steps": [f"Begin {next_agent_id} implementation"],
                    "context": {
                        "completed_agent": agent_id,
                        "accumulated_context": accumulated_context.copy()
                    }
                }
                
                # Record handoff
                await self.memory_integration.memory_system.record_agent_handoff(
                    from_agent=agent_id,
                    to_agent=next_agent_id,
                    project_id=self.memory_integration.project_id,
                    handoff_data=handoff_data
                )
        
        # Final agent should have comprehensive context
        final_context = await self.memory_integration.memory_system.get_agent_context(
            agent_id="frontend_developer",
            project_id=self.memory_integration.project_id
        )
        
        # Verify accumulated knowledge
        all_memories = final_context["recent_memories"] + final_context["relevant_memories"]
        
        # Should have memories from all previous agents
        architect_memories = [m for m in all_memories if m.agent_id == "project_architect"]
        backend_memories = [m for m in all_memories if m.agent_id == "backend_developer"]
        
        assert len(architect_memories) > 0
        assert len(backend_memories) > 0
        
        # Should have decision memories
        decision_memories = [m for m in all_memories if "decision" in m.tags]
        assert len(decision_memories) >= 6  # 2 + 3 + 3 decisions from all agents
        
        # Should have handoff memories
        handoff_memories = [m for m in all_memories if "handoff" in m.tags]
        assert len(handoff_memories) >= 2  # 2 handoffs in the chain


if __name__ == "__main__":
    pytest.main([__file__, "-v"])