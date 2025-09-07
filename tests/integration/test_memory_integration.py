"""
Integration tests for Memory System with CoralCollective

Tests cover:
1. Memory system integration with agents
2. Cross-session memory persistence 
3. Memory-driven agent context
4. Handoff memory recording and retrieval
5. Memory system performance under load
6. Memory consolidation workflows
"""

import pytest
import asyncio
import tempfile
import shutil
import json
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Mock memory system imports to avoid dependency issues
try:
    from memory.coral_memory_integration import CoralMemoryIntegration
    from memory.memory_system import MemorySystem, MemoryItem, MemoryType, ImportanceLevel
    from memory.migration_strategy import MemoryMigrationStrategy
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False


@pytest.mark.skipif(not MEMORY_AVAILABLE, reason="Memory system not available")
@pytest.mark.integration
@pytest.mark.memory
class TestMemoryAgentIntegration:
    """Test memory system integration with agents"""
    
    async def setup_method(self):
        """Set up memory-agent integration test"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_id = "memory_integration_test"
        
        # Create project structure
        self.coral_dir = self.temp_dir / '.coral'
        self.coral_dir.mkdir(parents=True)
        (self.coral_dir / 'memory').mkdir()
        (self.coral_dir / 'state').mkdir()
        
        # Mock memory system configuration
        self.memory_config = {
            "short_term": {
                "buffer_size": 50,
                "max_tokens": 10000
            },
            "long_term": {
                "type": "chroma",
                "collection_name": f"test_memory_{self.project_id}",
                "persist_directory": str(self.coral_dir / "memory" / "chroma")
            },
            "orchestrator": {
                "short_term_limit": 50,
                "consolidation_threshold": 0.7,
                "importance_decay_hours": 24
            }
        }
        
        # Save memory config
        config_file = self.coral_dir / 'memory_config.json'
        with open(config_file, 'w') as f:
            json.dump(self.memory_config, f)
        
        # Initialize memory integration with mocks
        with patch('memory.memory_system.chromadb'), \
             patch('memory.coral_memory_integration.ProjectStateManager'):
            self.memory_integration = CoralMemoryIntegration(
                project_path=self.temp_dir,
                project_id=self.project_id
            )
            
            # Mock the memory system
            self.memory_integration.memory_system = Mock()
            self.memory_integration.memory_system.add_memory = AsyncMock(return_value="test_memory_id")
            self.memory_integration.memory_system.search_memories = AsyncMock(return_value=[])
            self.memory_integration.memory_system.get_agent_context = AsyncMock(return_value={
                "recent_memories": [],
                "relevant_memories": [],
                "working_memory": {},
                "session_context": {}
            })
    
    def teardown_method(self):
        """Clean up memory test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_agent_memory_lifecycle(self):
        """Test complete agent execution with memory recording"""
        
        agent_id = "backend_developer"
        task = "Create REST API for user management"
        
        # Start agent execution
        start_memory_id = await self.memory_integration.record_agent_start(
            agent_id=agent_id,
            task=task,
            context={"priority": "high", "estimated_duration": 60}
        )
        
        assert start_memory_id == "test_memory_id"
        
        # Verify agent start was recorded
        self.memory_integration.memory_system.add_memory.assert_called_once()
        call_args = self.memory_integration.memory_system.add_memory.call_args
        
        assert agent_id in call_args.kwargs["content"]
        assert task in call_args.kwargs["content"]
        assert call_args.kwargs["agent_id"] == agent_id
        assert call_args.kwargs["context"]["type"] == "agent_start"
        assert call_args.kwargs["tags"] == ["agent", "start", agent_id]
        
        # Reset mock for completion test
        self.memory_integration.memory_system.add_memory.reset_mock()
        
        # Complete agent execution
        completion_outputs = {
            "api_endpoints": ["POST /users", "GET /users", "PUT /users/:id"],
            "files_created": ["src/api/users.py", "src/models/user.py"],
            "tests_created": ["tests/test_users_api.py"]
        }
        
        completion_artifacts = [
            {"type": "code", "path": "src/api/users.py", "language": "python"},
            {"type": "test", "path": "tests/test_users_api.py", "framework": "pytest"}
        ]
        
        completion_memory_id = await self.memory_integration.record_agent_completion(
            agent_id=agent_id,
            success=True,
            outputs=completion_outputs,
            artifacts=completion_artifacts,
            duration_minutes=45
        )
        
        # Verify completion recording
        assert completion_memory_id == "test_memory_id"
        
        # Should record both completion memory and artifact memories
        call_count = self.memory_integration.memory_system.add_memory.call_count
        assert call_count >= 2  # At least completion + artifacts
    
    @pytest.mark.asyncio
    async def test_agent_context_retrieval_with_memory(self):
        """Test retrieving agent context enriched with memory"""
        
        # Mock memory search results
        mock_memories = [
            {
                "id": "mem_001",
                "content": "Previous API implementation used FastAPI framework",
                "agent_id": "backend_developer",
                "timestamp": datetime.now() - timedelta(hours=2),
                "importance": "high",
                "tags": ["api", "framework", "previous"]
            },
            {
                "id": "mem_002", 
                "content": "User model should include email, username, and timestamps",
                "agent_id": "backend_developer",
                "timestamp": datetime.now() - timedelta(hours=1),
                "importance": "medium",
                "tags": ["model", "user", "requirements"]
            }
        ]
        
        self.memory_integration.memory_system.search_memories.return_value = mock_memories
        self.memory_integration.memory_system.get_agent_context.return_value = {
            "recent_memories": mock_memories[:1],
            "relevant_memories": mock_memories,
            "working_memory": {"current_task": "user_api", "progress": 0.5},
            "session_context": {"session_id": "test_session", "start_time": datetime.now()}
        }
        
        # Get agent context
        context = await self.memory_integration.get_agent_context(
            agent_id="backend_developer",
            project_id=self.project_id,
            current_task="Create user management API"
        )
        
        # Verify context retrieval
        assert "recent_memories" in context
        assert "relevant_memories" in context
        assert "working_memory" in context
        assert "session_context" in context
        
        # Verify memory search was called with appropriate query
        self.memory_integration.memory_system.search_memories.assert_called_once()
        
        # Verify context structure
        assert len(context["relevant_memories"]) == 2
        assert context["working_memory"]["current_task"] == "user_api"
    
    @pytest.mark.asyncio
    async def test_handoff_memory_integration(self):
        """Test memory recording and retrieval during agent handoffs"""
        
        # Record handoff from backend to frontend
        handoff_data = {
            "summary": "Backend API completed with user management endpoints",
            "artifacts": [
                "src/api/users.py",
                "src/models/user.py",
                "docs/api_specification.yaml"
            ],
            "next_steps": [
                "Implement user registration form",
                "Create user profile page", 
                "Add authentication UI"
            ],
            "api_endpoints": ["POST /auth/register", "GET /users/profile"],
            "context": {"database_schema": "users table created", "auth_method": "JWT"}
        }
        
        handoff_memory_id = await self.memory_integration.record_handoff(
            from_agent="backend_developer",
            to_agent="frontend_developer",
            project_id=self.project_id,
            handoff_data=handoff_data
        )
        
        assert handoff_memory_id == "test_memory_id"
        
        # Verify handoff memory recording
        self.memory_integration.memory_system.add_memory.assert_called_once()
        call_args = self.memory_integration.memory_system.add_memory.call_args
        
        assert "handoff" in call_args.kwargs["content"]
        assert "backend_developer" in call_args.kwargs["content"]
        assert "frontend_developer" in call_args.kwargs["content"]
        assert call_args.kwargs["context"]["type"] == "agent_handoff"
        assert call_args.kwargs["context"]["from_agent"] == "backend_developer"
        assert call_args.kwargs["context"]["to_agent"] == "frontend_developer"
        assert "handoff" in call_args.kwargs["tags"]
        
        # Reset mock for retrieval test
        self.memory_integration.memory_system.search_memories.reset_mock()
        
        # Mock handoff memory retrieval
        handoff_memory = {
            "id": "handoff_mem_001",
            "content": "Handoff: backend_developer → frontend_developer",
            "context": {
                "type": "agent_handoff",
                "from_agent": "backend_developer",
                "to_agent": "frontend_developer",
                "handoff_data": handoff_data
            },
            "tags": ["handoff", "backend_developer", "frontend_developer"]
        }
        
        self.memory_integration.memory_system.search_memories.return_value = [handoff_memory]
        
        # Retrieve handoff context for frontend agent
        frontend_context = await self.memory_integration.get_handoff_context(
            agent_id="frontend_developer",
            project_id=self.project_id
        )
        
        # Verify handoff context retrieval
        assert frontend_context is not None
        assert len(frontend_context) >= 1
        assert frontend_context[0]["context"]["from_agent"] == "backend_developer"
        assert "api_endpoints" in frontend_context[0]["context"]["handoff_data"]
    
    @pytest.mark.asyncio
    async def test_memory_driven_agent_decisions(self):
        """Test how memory influences agent decision making"""
        
        # Mock relevant memories that should influence agent behavior
        relevant_memories = [
            {
                "id": "decision_mem_001",
                "content": "Previous attempt to use MongoDB failed due to scaling issues",
                "importance": "high",
                "tags": ["database", "mongodb", "scaling", "failure"],
                "context": {"decision_outcome": "negative", "alternative": "postgresql"}
            },
            {
                "id": "decision_mem_002",
                "content": "PostgreSQL performed well in load testing with 10k concurrent users",
                "importance": "high",
                "tags": ["database", "postgresql", "performance", "success"],
                "context": {"decision_outcome": "positive", "metrics": {"rps": 1500}}
            },
            {
                "id": "decision_mem_003",
                "content": "Team prefers SQLAlchemy ORM for database interactions",
                "importance": "medium",
                "tags": ["orm", "sqlalchemy", "team_preference"],
                "context": {"decision_outcome": "positive", "consensus": True}
            }
        ]
        
        self.memory_integration.memory_system.search_memories.return_value = relevant_memories
        
        # Get decision context for database selection
        decision_context = await self.memory_integration.get_decision_context(
            agent_id="backend_developer",
            project_id=self.project_id,
            decision_topic="database_selection"
        )
        
        # Verify decision context
        assert "relevant_experiences" in decision_context
        assert "recommendations" in decision_context
        assert "risk_factors" in decision_context
        
        # Should identify PostgreSQL as recommended and MongoDB as risky
        recommendations = decision_context["recommendations"]
        risk_factors = decision_context["risk_factors"]
        
        assert any("postgresql" in rec.lower() for rec in recommendations)
        assert any("mongodb" in risk.lower() for risk in risk_factors)
    
    @pytest.mark.asyncio
    async def test_cross_session_memory_persistence(self):
        """Test memory persistence across agent sessions"""
        
        # Simulate first session
        session_1_id = "session_001"
        await self.memory_integration.start_agent_session(
            agent_id="backend_developer",
            session_id=session_1_id,
            context={"phase": "initial_development"}
        )
        
        # Record some memories in session 1
        await self.memory_integration.record_agent_progress(
            agent_id="backend_developer",
            session_id=session_1_id,
            progress_data={
                "task": "API design",
                "completion": 0.6,
                "insights": ["REST pattern works well", "Need rate limiting"]
            }
        )
        
        # End session 1
        await self.memory_integration.end_agent_session(
            agent_id="backend_developer", 
            session_id=session_1_id,
            summary="Completed API design phase with 60% progress"
        )
        
        # Start session 2 (simulating later time)
        session_2_id = "session_002"
        await self.memory_integration.start_agent_session(
            agent_id="backend_developer",
            session_id=session_2_id,
            context={"phase": "implementation", "previous_session": session_1_id}
        )
        
        # Mock memory retrieval showing previous session data
        previous_session_memories = [
            {
                "id": "session_1_mem",
                "content": "API design completed with REST pattern",
                "session_id": session_1_id,
                "context": {"phase": "initial_development", "progress": 0.6}
            }
        ]
        
        self.memory_integration.memory_system.search_memories.return_value = previous_session_memories
        
        # Get session context that should include previous session memories
        session_context = await self.memory_integration.get_session_context(
            agent_id="backend_developer",
            session_id=session_2_id,
            project_id=self.project_id
        )
        
        # Verify cross-session memory retrieval
        assert "previous_sessions" in session_context
        assert "session_continuity" in session_context
        assert session_context["session_continuity"]["has_previous"] is True
        
        # Should have insights from previous session
        previous_insights = session_context.get("previous_insights", [])
        assert any("REST pattern" in insight for insight in previous_insights)


@pytest.mark.skipif(not MEMORY_AVAILABLE, reason="Memory system not available")
@pytest.mark.integration
@pytest.mark.memory
class TestMemoryWorkflowIntegration:
    """Test memory system integration with complete workflows"""
    
    async def setup_method(self):
        """Set up workflow memory integration test"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_id = "workflow_memory_test"
        
        # Create project structure
        self.coral_dir = self.temp_dir / '.coral'
        self.coral_dir.mkdir(parents=True)
        (self.coral_dir / 'memory').mkdir()
        
        # Mock workflow definition
        self.workflow_definition = {
            "name": "full_stack_development",
            "phases": [
                {
                    "name": "planning",
                    "agents": ["project_architect", "technical_writer"],
                    "memory_requirements": ["architecture_knowledge", "requirements"]
                },
                {
                    "name": "development", 
                    "agents": ["backend_developer", "frontend_developer"],
                    "memory_requirements": ["implementation_patterns", "api_specifications"]
                },
                {
                    "name": "testing",
                    "agents": ["qa_testing"],
                    "memory_requirements": ["test_strategies", "quality_metrics"]
                }
            ]
        }
        
        # Initialize with mocks
        with patch('memory.memory_system.chromadb'):
            self.memory_integration = CoralMemoryIntegration(
                project_path=self.temp_dir,
                project_id=self.project_id
            )
            
            # Mock memory system
            self.memory_integration.memory_system = Mock()
            self.memory_integration.memory_system.add_memory = AsyncMock(return_value="workflow_memory_id")
            self.memory_integration.memory_system.search_memories = AsyncMock(return_value=[])
            self.memory_integration.memory_system.consolidate_memories = AsyncMock(return_value={
                "consolidated_count": 10,
                "summary": "Workflow phase memories consolidated"
            })
    
    def teardown_method(self):
        """Clean up workflow memory test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_workflow_phase_memory_consolidation(self):
        """Test memory consolidation at end of workflow phases"""
        
        # Simulate planning phase completion
        planning_memories = [
            {
                "agent_id": "project_architect",
                "content": "System architecture designed with microservices pattern",
                "phase": "planning",
                "importance": "high"
            },
            {
                "agent_id": "technical_writer",
                "content": "Requirements documented with 15 user stories",
                "phase": "planning", 
                "importance": "medium"
            }
        ]
        
        # Record phase completion and trigger consolidation
        consolidation_result = await self.memory_integration.consolidate_phase_memory(
            phase_name="planning",
            phase_memories=planning_memories,
            project_id=self.project_id
        )
        
        # Verify consolidation was triggered
        self.memory_integration.memory_system.consolidate_memories.assert_called_once()
        
        # Verify consolidation result
        assert consolidation_result["phase"] == "planning"
        assert consolidation_result["memories_processed"] == 2
        assert "consolidated_summary" in consolidation_result
    
    @pytest.mark.asyncio
    async def test_inter_phase_knowledge_transfer(self):
        """Test knowledge transfer between workflow phases"""
        
        # Mock memories from planning phase
        planning_phase_memories = [
            {
                "id": "planning_001",
                "content": "API specification: REST endpoints for user management",
                "phase": "planning",
                "agent_id": "technical_writer",
                "tags": ["api", "specification", "users"]
            },
            {
                "id": "planning_002",
                "content": "Architecture decision: PostgreSQL for user data persistence",
                "phase": "planning", 
                "agent_id": "project_architect",
                "tags": ["database", "postgresql", "architecture"]
            }
        ]
        
        self.memory_integration.memory_system.search_memories.return_value = planning_phase_memories
        
        # Get development phase context (should include planning insights)
        development_context = await self.memory_integration.get_phase_transition_context(
            from_phase="planning",
            to_phase="development",
            project_id=self.project_id
        )
        
        # Verify knowledge transfer
        assert "previous_phase_insights" in development_context
        assert "architectural_decisions" in development_context
        assert "specifications" in development_context
        
        # Should contain key decisions and specs from planning
        insights = development_context["previous_phase_insights"]
        assert any("PostgreSQL" in insight["content"] for insight in insights)
        assert any("REST endpoints" in insight["content"] for insight in insights)
        
        # Verify search was performed for phase-specific knowledge
        search_call = self.memory_integration.memory_system.search_memories.call_args
        assert "planning" in search_call.kwargs.get("query", "")
    
    @pytest.mark.asyncio
    async def test_workflow_knowledge_graph_building(self):
        """Test building knowledge graph from workflow execution"""
        
        # Mock workflow execution memories
        workflow_memories = [
            {
                "id": "wf_001",
                "content": "Backend API uses JWT authentication",
                "relationships": ["connects_to:frontend", "implements:authentication"],
                "entities": ["Backend API", "JWT", "Authentication"]
            },
            {
                "id": "wf_002", 
                "content": "Frontend uses React with Redux for state management",
                "relationships": ["connects_to:backend", "uses:react", "uses:redux"],
                "entities": ["Frontend", "React", "Redux", "State Management"]
            },
            {
                "id": "wf_003",
                "content": "Database schema includes users, sessions, and audit_logs tables",
                "relationships": ["stores:user_data", "tracks:sessions", "logs:audit_events"],
                "entities": ["Database", "Users Table", "Sessions Table", "Audit Logs"]
            }
        ]
        
        # Build knowledge graph
        knowledge_graph = await self.memory_integration.build_workflow_knowledge_graph(
            workflow_memories=workflow_memories,
            project_id=self.project_id
        )
        
        # Verify knowledge graph structure
        assert "entities" in knowledge_graph
        assert "relationships" in knowledge_graph
        assert "clusters" in knowledge_graph
        
        # Should identify key entities
        entities = knowledge_graph["entities"]
        entity_names = [entity["name"] for entity in entities]
        assert "Backend API" in entity_names
        assert "Frontend" in entity_names
        assert "Database" in entity_names
        
        # Should identify relationships
        relationships = knowledge_graph["relationships"]
        assert len(relationships) > 0
        
        # Should cluster related components
        clusters = knowledge_graph["clusters"]
        assert any(cluster["type"] == "authentication" for cluster in clusters)
        assert any(cluster["type"] == "data_storage" for cluster in clusters)
    
    @pytest.mark.asyncio
    async def test_memory_based_quality_assessment(self):
        """Test using memory for workflow quality assessment"""
        
        # Mock quality-related memories
        quality_memories = [
            {
                "id": "qual_001",
                "content": "Unit test coverage: 87% for backend API",
                "type": "quality_metric",
                "component": "backend",
                "metric_value": 0.87
            },
            {
                "id": "qual_002",
                "content": "Frontend accessibility audit: 3 minor issues identified",
                "type": "quality_issue",
                "component": "frontend", 
                "severity": "minor",
                "count": 3
            },
            {
                "id": "qual_003",
                "content": "Performance test: API response time p95 < 200ms",
                "type": "quality_metric",
                "component": "backend",
                "metric_value": 0.18  # 180ms in seconds
            }
        ]
        
        self.memory_integration.memory_system.search_memories.return_value = quality_memories
        
        # Generate quality assessment from memory
        quality_assessment = await self.memory_integration.generate_quality_assessment(
            project_id=self.project_id,
            assessment_type="comprehensive"
        )
        
        # Verify quality assessment
        assert "overall_score" in quality_assessment
        assert "component_scores" in quality_assessment
        assert "issues" in quality_assessment
        assert "recommendations" in quality_assessment
        
        # Should identify components
        components = quality_assessment["component_scores"]
        assert "backend" in components
        assert "frontend" in components
        
        # Should calculate reasonable overall score
        overall_score = quality_assessment["overall_score"]
        assert 0 <= overall_score <= 1
        
        # Should identify issues
        issues = quality_assessment["issues"]
        assert any(issue["component"] == "frontend" for issue in issues)


@pytest.mark.skipif(not MEMORY_AVAILABLE, reason="Memory system not available")
@pytest.mark.integration
@pytest.mark.memory
@pytest.mark.performance
class TestMemoryPerformanceIntegration:
    """Test memory system performance under realistic loads"""
    
    async def setup_method(self):
        """Set up memory performance test"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Initialize memory integration with performance focus
        with patch('memory.memory_system.chromadb'):
            self.memory_integration = CoralMemoryIntegration(
                project_path=self.temp_dir,
                project_id="performance_test"
            )
            
            # Mock memory system with performance simulation
            self.memory_integration.memory_system = self._create_performance_mock()
    
    def teardown_method(self):
        """Clean up performance test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def _create_performance_mock(self):
        """Create memory system mock with performance simulation"""
        mock_memory = Mock()
        
        # Simulate memory operations with realistic delays
        async def mock_add_memory(*args, **kwargs):
            await asyncio.sleep(0.01)  # 10ms simulated latency
            return f"memory_{len(args)}_{hash(str(kwargs)) % 1000}"
        
        async def mock_search_memories(query, limit=10, **kwargs):
            await asyncio.sleep(0.05)  # 50ms simulated search time
            # Return mock results based on query
            return [
                {
                    "id": f"search_result_{i}",
                    "content": f"Memory content matching '{query}' - result {i}",
                    "relevance": 0.9 - (i * 0.1)
                }
                for i in range(min(limit, 5))  # Return up to 5 results
            ]
        
        async def mock_consolidate_memories(memories, **kwargs):
            await asyncio.sleep(0.1 * len(memories))  # Longer for more memories
            return {
                "consolidated_count": len(memories),
                "processing_time": 0.1 * len(memories),
                "summary": f"Consolidated {len(memories)} memories"
            }
        
        mock_memory.add_memory = AsyncMock(side_effect=mock_add_memory)
        mock_memory.search_memories = AsyncMock(side_effect=mock_search_memories)
        mock_memory.consolidate_memories = AsyncMock(side_effect=mock_consolidate_memories)
        
        return mock_memory
    
    @pytest.mark.asyncio
    async def test_high_frequency_memory_operations(self):
        """Test memory system under high frequency operations"""
        
        import time
        
        # Simulate high-frequency agent activities
        start_time = time.time()
        
        tasks = []
        for i in range(100):  # 100 concurrent memory operations
            task = self.memory_integration.record_agent_activity(
                agent_id=f"agent_{i % 5}",  # 5 different agents
                activity_type="progress_update",
                activity_data={
                    "step": i,
                    "progress": i / 100.0,
                    "timestamp": datetime.now().isoformat()
                }
            )
            tasks.append(task)
        
        # Execute all operations concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        execution_time = time.time() - start_time
        
        # Performance assertions
        assert execution_time < 5.0  # Should complete within 5 seconds
        assert len(results) == 100
        
        # Most operations should succeed
        successful_operations = sum(1 for r in results if not isinstance(r, Exception))
        assert successful_operations >= 95  # At least 95% success rate
    
    @pytest.mark.asyncio
    async def test_large_memory_search_performance(self):
        """Test search performance with large memory datasets"""
        
        import time
        
        # Simulate large project with many memories
        project_size_simulation = {
            "agents_run": 50,
            "memories_per_agent": 20,
            "search_queries": 10
        }
        
        # Simulate search operations
        search_tasks = []
        start_time = time.time()
        
        for i in range(project_size_simulation["search_queries"]):
            query = f"search query {i} with various terms and context"
            task = self.memory_integration.search_project_knowledge(
                query=query,
                project_id="large_project",
                limit=20,
                include_context=True
            )
            search_tasks.append(task)
        
        # Execute searches
        search_results = await asyncio.gather(*search_tasks)
        
        search_time = time.time() - start_time
        
        # Performance assertions
        assert search_time < 2.0  # All searches within 2 seconds
        assert len(search_results) == project_size_simulation["search_queries"]
        
        # Verify search quality
        for results in search_results:
            assert isinstance(results, list)
            assert len(results) <= 20  # Respects limit
    
    @pytest.mark.asyncio
    async def test_memory_consolidation_performance(self):
        """Test memory consolidation performance with realistic data"""
        
        import time
        
        # Create realistic memory dataset for consolidation
        memories_to_consolidate = []
        
        for i in range(200):  # 200 memories to consolidate
            memory = {
                "id": f"consolidate_mem_{i}",
                "content": f"Agent activity {i}: completed task with various outputs and context",
                "agent_id": f"agent_{i % 10}",
                "timestamp": datetime.now() - timedelta(hours=i // 10),
                "importance": "medium" if i % 3 == 0 else "low",
                "tags": [f"tag_{i % 5}", "consolidation_test"],
                "context": {
                    "phase": "development" if i < 100 else "testing",
                    "iteration": i // 20
                }
            }
            memories_to_consolidate.append(memory)
        
        # Perform consolidation
        start_time = time.time()
        
        consolidation_result = await self.memory_integration.consolidate_project_memories(
            memories=memories_to_consolidate,
            project_id="consolidation_test",
            strategy="importance_based"
        )
        
        consolidation_time = time.time() - start_time
        
        # Performance assertions
        assert consolidation_time < 10.0  # Should complete within 10 seconds
        assert consolidation_result["success"] is True
        assert consolidation_result["memories_processed"] == 200
        assert "consolidation_summary" in consolidation_result
        
        # Efficiency metrics
        processing_rate = 200 / consolidation_time  # memories per second
        assert processing_rate > 10  # At least 10 memories per second


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])