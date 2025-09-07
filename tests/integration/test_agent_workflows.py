"""
Integration tests for CoralCollective Agent Workflows

Tests complete agent workflow scenarios including:
1. Agent handoffs and context passing
2. Multi-agent collaboration sequences  
3. Workflow orchestration and state management
4. Error handling and recovery scenarios
5. Performance of agent chains
"""

import pytest
import asyncio
import tempfile
import json
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, List, Any

# Import system components
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from agent_runner import AgentRunner
from project_manager import ProjectManager
from tools.project_state import ProjectStateManager
from tools.feedback_collector import FeedbackCollector


class TestAgentWorkflowSequences:
    """Test complete agent workflow sequences"""
    
    def setup_method(self):
        """Set up test environment with temporary project"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_path = self.temp_dir / "test_project"
        self.project_path.mkdir(parents=True)
        
        # Create basic project structure
        (self.project_path / "src").mkdir(exist_ok=True)
        (self.project_path / "docs").mkdir(exist_ok=True)
        (self.project_path / "tests").mkdir(exist_ok=True)
        
        # Initialize project state manager
        self.state_manager = ProjectStateManager(self.project_path)
        
        # Mock agent runner with real workflow logic
        self.agent_runner = Mock(spec=AgentRunner)
        self.agent_runner.project_path = self.project_path
        self.agent_runner.state_manager = self.state_manager
        
    def teardown_method(self):
        """Clean up test environment"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_planning_to_development_workflow(self):
        """Test complete planning to development agent workflow"""
        
        # Phase 1: Project Architect starts planning
        architect_context = {
            "task": "Design web application architecture",
            "requirements": ["user authentication", "REST API", "React frontend"],
            "constraints": ["SQLite database", "Python backend"]
        }
        
        architect_record = self.state_manager.record_agent_start(
            "project_architect",
            "Design system architecture",
            architect_context
        )
        
        assert architect_record["agent_id"] == "project_architect"
        assert len(self.state_manager.state["agents"]["in_progress"]) == 1
        
        # Architect completes with outputs
        architect_outputs = {
            "architecture_type": "MVC",
            "components": ["backend_api", "frontend_spa", "database"],
            "tech_stack": {
                "backend": "FastAPI",
                "frontend": "React",
                "database": "SQLite"
            }
        }
        
        architect_artifacts = [
            {"type": "documentation", "path": "docs/architecture.md"},
            {"type": "documentation", "path": "docs/api_spec.md"},
            {"type": "documentation", "path": "docs/database_schema.md"}
        ]
        
        completion = self.state_manager.record_agent_completion(
            "project_architect",
            success=True,
            outputs=architect_outputs,
            artifacts=architect_artifacts
        )
        
        assert completion["success"] is True
        assert len(self.state_manager.state["agents"]["completed"]) == 1
        assert len(self.state_manager.state["agents"]["in_progress"]) == 0
        assert len(self.state_manager.state["artifacts"]) == 3
        
        # Phase 2: Handoff to Technical Writer (Phase 1)
        handoff_data = {
            "summary": "System architecture completed",
            "artifacts": ["docs/architecture.md", "docs/api_spec.md"],
            "next_steps": ["Create detailed requirements", "Define acceptance criteria"],
            "blockers": [],
            "estimated_effort": "1 week"
        }
        
        handoff = self.state_manager.record_handoff(
            "project_architect",
            "technical_writer",
            handoff_data
        )
        
        assert handoff["from_agent"] == "project_architect"
        assert handoff["to_agent"] == "technical_writer"
        assert len(self.state_manager.state["agents"]["pending"]) == 1
        
        # Technical Writer starts Phase 1
        writer_record = self.state_manager.record_agent_start(
            "technical_writer",
            "Create project requirements and specifications",
            {"phase": 1, "focus": "requirements"}
        )
        
        # Technical Writer completes Phase 1
        writer_outputs = {
            "requirements_document": "docs/requirements.md",
            "acceptance_criteria": "docs/acceptance_criteria.md",
            "user_stories": "docs/user_stories.md"
        }
        
        writer_completion = self.state_manager.record_agent_completion(
            "technical_writer",
            success=True,
            outputs=writer_outputs,
            artifacts=[
                {"type": "documentation", "path": "docs/requirements.md"},
                {"type": "documentation", "path": "docs/acceptance_criteria.md"}
            ]
        )
        
        # Verify workflow state
        assert len(self.state_manager.state["agents"]["completed"]) == 2
        assert len(self.state_manager.state["handoffs"]) == 1
        assert self.state_manager.state["metrics"]["success_rate"] == 1.0
        
        # Phase 3: Handoff to Backend Developer
        backend_handoff = self.state_manager.record_handoff(
            "technical_writer",
            "backend_developer",
            {
                "summary": "Requirements and specifications complete",
                "artifacts": ["docs/requirements.md", "docs/api_spec.md"],
                "next_steps": ["Implement FastAPI backend", "Set up database"],
                "priority_features": ["authentication", "user management"]
            }
        )
        
        # Backend Developer starts
        backend_record = self.state_manager.record_agent_start(
            "backend_developer",
            "Implement FastAPI backend with authentication",
            {"tech_stack": "FastAPI", "database": "SQLite"}
        )
        
        # Backend Developer completes
        backend_outputs = {
            "api_endpoints": 15,
            "authentication": "JWT",
            "database_tables": 5,
            "test_coverage": "85%"
        }
        
        backend_completion = self.state_manager.record_agent_completion(
            "backend_developer",
            success=True,
            outputs=backend_outputs,
            artifacts=[
                {"type": "source_code", "path": "src/main.py"},
                {"type": "source_code", "path": "src/models.py"},
                {"type": "source_code", "path": "src/auth.py"}
            ]
        )
        
        # Verify complete workflow metrics
        summary = self.state_manager.get_summary()
        assert summary["agents_completed"] == 3
        assert summary["success_rate"] == 1.0
        assert summary["total_artifacts"] == 8  # 3 + 2 + 3
        
        # Verify handoff chain integrity
        assert len(self.state_manager.state["handoffs"]) == 2
        
        # Verify all agents completed successfully
        completed_agents = [a["agent_id"] for a in self.state_manager.state["agents"]["completed"]]
        expected_agents = ["project_architect", "technical_writer", "backend_developer"]
        assert all(agent in completed_agents for agent in expected_agents)
    
    def test_development_to_deployment_workflow(self):
        """Test development to deployment workflow sequence"""
        
        # Start with backend completed (simulate previous workflow)
        self.state_manager.record_agent_start("backend_developer", "Backend implementation")
        self.state_manager.record_agent_completion("backend_developer", True, {
            "api_ready": True,
            "tests_passing": True
        })
        
        # Frontend Developer starts
        frontend_start = self.state_manager.record_agent_start(
            "frontend_developer",
            "Create React frontend",
            {"framework": "React", "styling": "TailwindCSS"}
        )
        
        # Frontend completes
        frontend_completion = self.state_manager.record_agent_completion(
            "frontend_developer",
            success=True,
            outputs={"components": 12, "pages": 8, "tests": "80% coverage"},
            artifacts=[
                {"type": "source_code", "path": "src/components/App.tsx"},
                {"type": "source_code", "path": "src/components/Login.tsx"}
            ]
        )
        
        # Handoff to QA Testing
        qa_handoff = self.state_manager.record_handoff(
            "frontend_developer",
            "qa_testing",
            {
                "summary": "Frontend development complete",
                "test_requirements": ["unit tests", "integration tests", "e2e tests"],
                "coverage_target": "90%"
            }
        )
        
        # QA Testing starts
        qa_start = self.state_manager.record_agent_start(
            "qa_testing",
            "Comprehensive testing and quality assurance",
            {"test_types": ["unit", "integration", "e2e", "performance"]}
        )
        
        # QA completes
        qa_completion = self.state_manager.record_agent_completion(
            "qa_testing",
            success=True,
            outputs={
                "test_coverage": "92%",
                "tests_passing": "100%",
                "performance_score": "A",
                "issues_found": 2,
                "issues_resolved": 2
            },
            artifacts=[
                {"type": "test_code", "path": "tests/test_api.py"},
                {"type": "test_code", "path": "tests/test_frontend.py"},
                {"type": "documentation", "path": "docs/test_report.md"}
            ]
        )
        
        # Handoff to DevOps
        devops_handoff = self.state_manager.record_handoff(
            "qa_testing",
            "devops_deployment",
            {
                "summary": "Testing complete, ready for deployment",
                "deployment_requirements": ["Docker", "CI/CD", "monitoring"],
                "quality_gates_passed": True
            }
        )
        
        # DevOps starts
        devops_start = self.state_manager.record_agent_start(
            "devops_deployment",
            "Setup deployment infrastructure and CI/CD",
            {"platform": "AWS", "containerization": "Docker"}
        )
        
        # DevOps completes
        devops_completion = self.state_manager.record_agent_completion(
            "devops_deployment",
            success=True,
            outputs={
                "deployment_ready": True,
                "ci_cd_setup": True,
                "monitoring_enabled": True,
                "security_scan_passed": True
            },
            artifacts=[
                {"type": "config", "path": "Dockerfile"},
                {"type": "config", "path": ".github/workflows/deploy.yml"},
                {"type": "config", "path": "docker-compose.yml"}
            ]
        )
        
        # Verify complete development to deployment workflow
        summary = self.state_manager.get_summary()
        assert summary["agents_completed"] == 4
        assert summary["success_rate"] == 1.0
        
        # Verify proper handoff sequence
        handoffs = self.state_manager.state["handoffs"]
        assert len(handoffs) == 2
        
        # Verify agent sequence
        completed_agents = [a["agent_id"] for a in self.state_manager.state["agents"]["completed"]]
        expected_sequence = ["backend_developer", "frontend_developer", "qa_testing", "devops_deployment"]
        assert completed_agents == expected_sequence
    
    def test_error_handling_and_recovery_workflow(self):
        """Test workflow error handling and agent recovery"""
        
        # Start agent that will fail
        self.state_manager.record_agent_start(
            "backend_developer",
            "Implement complex backend feature",
            {"complexity": "high", "dependencies": "external_api"}
        )
        
        # Agent fails
        failed_completion = self.state_manager.record_agent_completion(
            "backend_developer",
            success=False,
            outputs={
                "error": "External API integration failed",
                "completed_percentage": 60,
                "blockers": ["API authentication", "Rate limiting"]
            }
        )
        
        assert failed_completion["success"] is False
        assert self.state_manager.state["metrics"]["success_rate"] == 0.0
        
        # Record issue for resolution
        handoff_data = {
            "summary": "Backend implementation blocked",
            "blockers": ["External API issues"],
            "next_steps": ["Research alternative APIs", "Implement mock service"],
            "retry_required": True
        }
        
        recovery_handoff = self.state_manager.record_handoff(
            "backend_developer",
            "backend_developer",  # Same agent retry
            handoff_data
        )
        
        # Retry with different approach
        retry_start = self.state_manager.record_agent_start(
            "backend_developer",
            "Implement backend with mock external service",
            {"approach": "mock_first", "external_api": "mocked"}
        )
        
        # Successful completion on retry
        retry_completion = self.state_manager.record_agent_completion(
            "backend_developer",
            success=True,
            outputs={
                "mock_service_ready": True,
                "api_endpoints": 10,
                "integration_tests": "passing"
            }
        )
        
        # Verify recovery handled correctly
        assert len(self.state_manager.state["agents"]["completed"]) == 2
        success_count = sum(1 for a in self.state_manager.state["agents"]["completed"] if a["success"])
        assert success_count == 1
        assert self.state_manager.state["metrics"]["success_rate"] == 0.5
    
    def test_parallel_agent_coordination(self):
        """Test coordination between multiple agents working in parallel"""
        
        # Start multiple agents for parallel work
        frontend_start = self.state_manager.record_agent_start(
            "frontend_developer",
            "Create React components",
            {"priority": "high", "parallel_work": True}
        )
        
        backend_start = self.state_manager.record_agent_start(
            "backend_developer", 
            "Implement API endpoints",
            {"priority": "high", "parallel_work": True}
        )
        
        db_start = self.state_manager.record_agent_start(
            "database_specialist",
            "Design and implement database schema",
            {"priority": "medium", "parallel_work": True}
        )
        
        # Verify all agents are in progress
        assert len(self.state_manager.state["agents"]["in_progress"]) == 3
        
        # Database completes first (foundational)
        db_completion = self.state_manager.record_agent_completion(
            "database_specialist",
            success=True,
            outputs={"tables_created": 8, "relationships": 12, "indexes": 15}
        )
        
        # Backend completes (depends on database)
        backend_completion = self.state_manager.record_agent_completion(
            "backend_developer",
            success=True,
            outputs={"endpoints": 20, "database_connected": True}
        )
        
        # Frontend completes (integrates with backend)
        frontend_completion = self.state_manager.record_agent_completion(
            "frontend_developer", 
            success=True,
            outputs={"components": 15, "api_integration": "complete"}
        )
        
        # Verify coordination success
        assert len(self.state_manager.state["agents"]["completed"]) == 3
        assert len(self.state_manager.state["agents"]["in_progress"]) == 0
        assert self.state_manager.state["metrics"]["success_rate"] == 1.0
        
        # Verify completion times are reasonable for parallel work
        completed = self.state_manager.state["agents"]["completed"]
        completion_times = [a["duration_minutes"] for a in completed]
        
        # In parallel work, total time should be less than sum of individual times
        total_parallel_time = max(completion_times)
        total_sequential_time = sum(completion_times)
        assert total_parallel_time < total_sequential_time


class TestAgentHandoffMechanisms:
    """Test agent handoff mechanisms and context passing"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_path = self.temp_dir / "test_project"
        self.project_path.mkdir(parents=True)
        self.state_manager = ProjectStateManager(self.project_path)
    
    def teardown_method(self):
        """Clean up test environment"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_context_preservation_across_handoffs(self):
        """Test that context is properly preserved across agent handoffs"""
        
        # Initial context from Project Architect
        initial_context = {
            "project_type": "web_application",
            "tech_stack": {
                "backend": "FastAPI",
                "frontend": "React", 
                "database": "PostgreSQL"
            },
            "requirements": {
                "authentication": True,
                "real_time_features": True,
                "mobile_responsive": True
            },
            "constraints": {
                "budget": "medium",
                "timeline": "8 weeks",
                "team_size": "small"
            }
        }
        
        # Project Architect completes
        self.state_manager.record_agent_start("project_architect", "Architecture design", initial_context)
        self.state_manager.record_agent_completion("project_architect", True, {
            "architecture_complete": True,
            "tech_decisions_made": True
        })
        
        # Handoff to Backend Developer with context
        handoff_data = {
            "summary": "Architecture phase completed",
            "context": initial_context,
            "specific_instructions": {
                "auth_method": "JWT",
                "database_orm": "SQLAlchemy",
                "api_documentation": "OpenAPI"
            },
            "artifacts": ["docs/architecture.md", "docs/api_spec.md"]
        }
        
        backend_handoff = self.state_manager.record_handoff(
            "project_architect",
            "backend_developer",
            handoff_data
        )
        
        # Backend Developer receives and uses context
        backend_context = backend_handoff["data"]["context"]
        assert backend_context["tech_stack"]["backend"] == "FastAPI"
        assert backend_context["requirements"]["authentication"] is True
        
        # Backend Developer starts with inherited context
        self.state_manager.record_agent_start(
            "backend_developer",
            "Implement backend based on architecture",
            {
                **backend_context,
                "implementation_phase": "backend",
                "auth_method": handoff_data["specific_instructions"]["auth_method"]
            }
        )
        
        # Verify context continuity
        last_handoff = self.state_manager.get_last_handoff_for("backend_developer")
        assert last_handoff["data"]["context"]["project_type"] == "web_application"
        assert last_handoff["data"]["specific_instructions"]["auth_method"] == "JWT"
    
    def test_artifact_handoff_chain(self):
        """Test artifact creation and handoff through agent chain"""
        
        # Create initial artifacts
        architect_artifacts = [
            {"type": "documentation", "path": "docs/architecture.md", "metadata": {"phase": "planning"}},
            {"type": "documentation", "path": "docs/database_design.md", "metadata": {"phase": "planning"}},
            {"type": "documentation", "path": "docs/api_specification.md", "metadata": {"phase": "planning"}}
        ]
        
        # Project Architect creates artifacts
        self.state_manager.record_agent_start("project_architect", "Create architecture")
        for artifact in architect_artifacts:
            self.state_manager.add_artifact(
                artifact["type"],
                artifact["path"],
                "project_architect",
                artifact.get("metadata", {})
            )
        
        self.state_manager.record_agent_completion("project_architect", True, {
            "artifacts_created": len(architect_artifacts)
        })
        
        # Handoff to Backend Developer with artifact references
        self.state_manager.record_handoff(
            "project_architect",
            "backend_developer",
            {
                "summary": "Architecture complete",
                "required_artifacts": [a["path"] for a in architect_artifacts],
                "next_artifacts_needed": [
                    "src/models.py",
                    "src/database.py",
                    "src/auth.py"
                ]
            }
        )
        
        # Backend Developer creates implementation artifacts
        backend_artifacts = [
            {"type": "source_code", "path": "src/models.py", "metadata": {"language": "python"}},
            {"type": "source_code", "path": "src/database.py", "metadata": {"language": "python"}},
            {"type": "source_code", "path": "src/auth.py", "metadata": {"language": "python"}},
            {"type": "test_code", "path": "tests/test_api.py", "metadata": {"test_type": "integration"}}
        ]
        
        self.state_manager.record_agent_start("backend_developer", "Implement backend")
        for artifact in backend_artifacts:
            self.state_manager.add_artifact(
                artifact["type"],
                artifact["path"],
                "backend_developer",
                artifact.get("metadata", {})
            )
        
        self.state_manager.record_agent_completion("backend_developer", True)
        
        # Verify artifact chain
        all_artifacts = self.state_manager.state["artifacts"]
        assert len(all_artifacts) == 7  # 3 + 4
        
        # Verify artifact types and creators
        docs_by_architect = self.state_manager.get_artifacts_by_agent("project_architect")
        code_by_backend = self.state_manager.get_artifacts_by_agent("backend_developer")
        
        assert len(docs_by_architect) == 3
        assert len(code_by_backend) == 4
        
        # Verify artifact types
        documentation = self.state_manager.get_artifacts_by_type("documentation")
        source_code = self.state_manager.get_artifacts_by_type("source_code")
        test_code = self.state_manager.get_artifacts_by_type("test_code")
        
        assert len(documentation) == 3
        assert len(source_code) == 3
        assert len(test_code) == 1
    
    def test_failure_handoff_scenarios(self):
        """Test handoff scenarios when agents fail or encounter blockers"""
        
        # Agent starts but encounters blocker
        self.state_manager.record_agent_start(
            "backend_developer",
            "Implement payment processing",
            {"integration": "stripe", "complexity": "high"}
        )
        
        # Agent fails with specific blocker
        self.state_manager.record_agent_completion(
            "backend_developer",
            success=False,
            outputs={
                "error": "Stripe API integration failed",
                "blocker_type": "external_dependency",
                "completion_percentage": 30,
                "partial_artifacts": ["src/payment_base.py"]
            }
        )
        
        # Create failure handoff to specialist
        failure_handoff = self.state_manager.record_handoff(
            "backend_developer",
            "api_integration_specialist",
            {
                "summary": "Payment integration blocked",
                "failure_reason": "Stripe API authentication issues",
                "recovery_strategy": "alternative_payment_provider",
                "partial_work": ["src/payment_base.py"],
                "blocker_details": {
                    "api_errors": ["authentication_failed", "webhook_validation"],
                    "documentation_gaps": ["webhook_setup", "test_mode_config"]
                }
            }
        )
        
        # Specialist takes over
        self.state_manager.record_agent_start(
            "api_integration_specialist",
            "Resolve payment integration issues",
            {
                "previous_attempt": "stripe_failed",
                "alternative_approach": "paypal_integration",
                "recovery_mode": True
            }
        )
        
        # Specialist succeeds
        self.state_manager.record_agent_completion(
            "api_integration_specialist",
            success=True,
            outputs={
                "integration_successful": True,
                "provider": "paypal",
                "fallback_ready": True
            }
        )
        
        # Verify failure recovery workflow
        handoffs = self.state_manager.state["handoffs"]
        assert len(handoffs) == 1
        assert handoffs[0]["data"]["failure_reason"] == "Stripe API authentication issues"
        
        # Verify recovery success
        completed_agents = self.state_manager.state["agents"]["completed"]
        assert len(completed_agents) == 2
        
        # Verify success rate calculation includes failures
        expected_success_rate = 1/2  # 1 success, 1 failure
        assert self.state_manager.state["metrics"]["success_rate"] == expected_success_rate


class TestWorkflowPerformanceAndScaling:
    """Test workflow performance and scaling characteristics"""
    
    def setup_method(self):
        """Set up performance test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_path = self.temp_dir / "perf_test_project"
        self.project_path.mkdir(parents=True)
        self.state_manager = ProjectStateManager(self.project_path)
    
    def teardown_method(self):
        """Clean up performance test environment"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_large_workflow_performance(self):
        """Test performance with large number of agents in workflow"""
        import time
        
        start_time = time.time()
        
        # Simulate large project with many agents
        agent_sequence = [
            ("project_architect", "System architecture"),
            ("technical_writer", "Requirements documentation"),
            ("database_specialist", "Database design"),
            ("backend_developer", "API implementation"),
            ("frontend_developer", "UI implementation"),
            ("mobile_developer", "Mobile app"),
            ("api_integration_specialist", "External integrations"),
            ("security_specialist", "Security audit"),
            ("performance_specialist", "Performance optimization"),
            ("qa_testing", "Quality assurance"),
            ("devops_deployment", "Deployment setup"),
            ("monitoring_specialist", "Monitoring setup")
        ]
        
        # Execute workflow sequence
        for i, (agent_id, task) in enumerate(agent_sequence):
            # Start agent
            start_record = self.state_manager.record_agent_start(
                agent_id,
                task,
                {"sequence_position": i, "total_agents": len(agent_sequence)}
            )
            
            # Simulate some work time
            import time
            time.sleep(0.001)  # Minimal delay to simulate work
            
            # Complete agent
            completion_record = self.state_manager.record_agent_completion(
                agent_id,
                success=True,
                outputs={"task_completed": True, "sequence_position": i}
            )
            
            # Add handoff to next agent (except for last)
            if i < len(agent_sequence) - 1:
                next_agent = agent_sequence[i + 1][0]
                self.state_manager.record_handoff(
                    agent_id,
                    next_agent,
                    {
                        "summary": f"{task} completed",
                        "next_task": agent_sequence[i + 1][1],
                        "sequence_position": i
                    }
                )
        
        end_time = time.time()
        workflow_duration = end_time - start_time
        
        # Verify workflow completed successfully
        summary = self.state_manager.get_summary()
        assert summary["agents_completed"] == len(agent_sequence)
        assert summary["success_rate"] == 1.0
        
        # Verify performance metrics
        assert workflow_duration < 5.0  # Should complete within 5 seconds
        assert len(self.state_manager.state["handoffs"]) == len(agent_sequence) - 1
        
        # Verify state file size remains manageable
        state_file_size = self.state_manager.state_file.stat().st_size
        assert state_file_size < 100_000  # Less than 100KB for 12 agents
    
    def test_concurrent_workflow_handling(self):
        """Test handling of multiple concurrent workflows"""
        
        # Create multiple project state managers (simulating concurrent projects)
        project_managers = []
        for i in range(5):
            project_path = self.temp_dir / f"concurrent_project_{i}"
            project_path.mkdir(parents=True)
            manager = ProjectStateManager(project_path)
            project_managers.append(manager)
        
        # Start agents concurrently across projects
        for i, manager in enumerate(project_managers):
            manager.record_agent_start(
                "project_architect",
                f"Architecture for project {i}",
                {"project_id": i, "concurrent_test": True}
            )
        
        # Complete all agents
        for i, manager in enumerate(project_managers):
            manager.record_agent_completion(
                "project_architect",
                success=True,
                outputs={"project_id": i, "completed": True}
            )
        
        # Verify all projects handled correctly
        for i, manager in enumerate(project_managers):
            summary = manager.get_summary()
            assert summary["agents_completed"] == 1
            assert summary["success_rate"] == 1.0
            
            # Verify project isolation
            completed_agent = manager.state["agents"]["completed"][0]
            assert completed_agent["context"]["project_id"] == i
    
    def test_memory_usage_scaling(self):
        """Test memory usage with increasing workflow complexity"""
        import sys
        
        # Measure initial memory usage
        initial_objects = len(gc.get_objects()) if 'gc' in sys.modules else 0
        
        # Create increasing number of agents and artifacts
        for batch in range(10):
            # Add agents
            for agent_num in range(5):
                agent_id = f"agent_{batch}_{agent_num}"
                
                self.state_manager.record_agent_start(
                    agent_id,
                    f"Task {batch}_{agent_num}",
                    {"batch": batch, "agent_num": agent_num}
                )
                
                # Add multiple artifacts per agent
                for artifact_num in range(3):
                    self.state_manager.add_artifact(
                        "source_code",
                        f"src/{agent_id}/file_{artifact_num}.py",
                        agent_id,
                        {"artifact_num": artifact_num, "batch": batch}
                    )
                
                self.state_manager.record_agent_completion(
                    agent_id,
                    success=True,
                    outputs={"batch": batch, "agent_num": agent_num}
                )
        
        # Verify state remains manageable
        final_summary = self.state_manager.get_summary()
        assert final_summary["agents_completed"] == 50  # 10 batches * 5 agents
        assert final_summary["total_artifacts"] == 150  # 50 agents * 3 artifacts
        
        # Verify memory usage is reasonable
        if 'gc' in sys.modules:
            import gc
            gc.collect()
            final_objects = len(gc.get_objects())
            object_growth = final_objects - initial_objects
            assert object_growth < 10000  # Reasonable object growth


if __name__ == "__main__":
    pytest.main([__file__, "-v"])