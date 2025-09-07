"""
Unit tests for CoralCollective Memory System

Tests cover:
1. Core memory system functionality
2. Short-term and long-term memory operations
3. Memory orchestration and consolidation
4. CoralCollective integration
5. Migration system
6. MCP server operations
"""

import pytest
import asyncio
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

# Import memory system components
import sys
sys.path.append(str(Path(__file__).parent.parent))

from memory.memory_system import (
    MemorySystem, MemoryOrchestrator, ShortTermMemory, ChromaLongTermMemory, 
    MemorySummarizer, MemoryItem, MemoryType, ImportanceLevel
)
from memory.coral_memory_integration import CoralMemoryIntegration
from memory.migration_strategy import MemoryMigrationStrategy, MemorySystemValidator

class TestMemoryItem:
    """Test MemoryItem data structure"""
    
    def test_memory_item_creation(self):
        """Test basic MemoryItem creation"""
        
        item = MemoryItem(
            id="test_id",
            content="Test memory content",
            memory_type=MemoryType.SHORT_TERM,
            timestamp=datetime.now(),
            agent_id="test_agent",
            project_id="test_project",
            importance=ImportanceLevel.MEDIUM,
            context={"type": "test"},
            tags=["test", "unit"]
        )
        
        assert item.id == "test_id"
        assert item.content == "Test memory content"
        assert item.memory_type == MemoryType.SHORT_TERM
        assert item.importance == ImportanceLevel.MEDIUM
        assert item.access_count == 0
        assert "test" in item.tags
        
    def test_memory_item_serialization(self):
        """Test MemoryItem serialization with datetime handling"""
        
        item = MemoryItem(
            id="test_id",
            content="Test content",
            memory_type=MemoryType.LONG_TERM,
            timestamp=datetime.now(),
            agent_id="test_agent",
            project_id="test_project",
            importance=ImportanceLevel.HIGH,
            context={},
            tags=[]
        )
        
        # Test that datetime fields are handled properly
        assert isinstance(item.timestamp, datetime)
        
        # Test post_init datetime conversion
        item_with_string_time = MemoryItem(
            id="test_id2",
            content="Test content",
            memory_type=MemoryType.LONG_TERM,
            timestamp="2023-12-01T10:00:00",
            agent_id="test_agent",
            project_id="test_project",
            importance=ImportanceLevel.HIGH,
            context={},
            tags=[]
        )
        
        assert isinstance(item_with_string_time.timestamp, datetime)

class TestMemoryOrchestrator:
    """Test MemoryOrchestrator functionality"""
    
    def setup_method(self):
        """Set up test orchestrator"""
        self.config = {
            'short_term_limit': 10,
            'consolidation_threshold': 0.7,
            'importance_decay_hours': 24
        }
        self.orchestrator = MemoryOrchestrator(self.config)
        
    def test_importance_calculation(self):
        """Test importance scoring logic"""
        
        # Test critical keywords
        critical_content = "Critical error in production deployment"
        critical_importance = self.orchestrator.calculate_importance(
            critical_content, {}
        )
        assert critical_importance == ImportanceLevel.CRITICAL
        
        # Test high importance keywords
        high_content = "Implement new API endpoint"
        high_importance = self.orchestrator.calculate_importance(
            high_content, {}
        )
        assert high_importance == ImportanceLevel.HIGH
        
        # Test context-based importance
        context_content = "Regular update"
        handoff_importance = self.orchestrator.calculate_importance(
            context_content, {'agent_handoff': True}
        )
        assert handoff_importance == ImportanceLevel.HIGH
        
    def test_consolidation_decision(self):
        """Test consolidation decision logic"""
        
        # Critical items should always consolidate
        critical_item = MemoryItem(
            id="critical_test",
            content="Critical memory",
            memory_type=MemoryType.SHORT_TERM,
            timestamp=datetime.now(),
            agent_id="test_agent",
            project_id="test_project",
            importance=ImportanceLevel.CRITICAL,
            context={},
            tags=[]
        )
        
        assert self.orchestrator.should_consolidate_to_long_term(critical_item)
        
        # Old, low importance items should not consolidate
        old_item = MemoryItem(
            id="old_test",
            content="Old memory",
            memory_type=MemoryType.SHORT_TERM,
            timestamp=datetime.now() - timedelta(days=2),
            agent_id="test_agent",
            project_id="test_project",
            importance=ImportanceLevel.LOW,
            context={},
            tags=[]
        )
        
        assert not self.orchestrator.should_consolidate_to_long_term(old_item)
        
    def test_attention_weights(self):
        """Test attention weight generation"""
        
        memories = [
            MemoryItem(
                id="relevant",
                content="API development and testing implementation",
                memory_type=MemoryType.SHORT_TERM,
                timestamp=datetime.now(),
                agent_id="test_agent",
                project_id="test_project",
                importance=ImportanceLevel.HIGH,
                context={},
                tags=[]
            ),
            MemoryItem(
                id="irrelevant",
                content="Random unrelated content",
                memory_type=MemoryType.SHORT_TERM,
                timestamp=datetime.now() - timedelta(days=1),
                agent_id="test_agent",
                project_id="test_project",
                importance=ImportanceLevel.LOW,
                context={},
                tags=[]
            )
        ]
        
        weights = self.orchestrator.generate_attention_weights("API testing", memories)
        
        # First memory should have higher weight (more relevant, higher importance, more recent)
        assert len(weights) == 2
        assert weights[0] > weights[1]

class TestShortTermMemory:
    """Test ShortTermMemory functionality"""
    
    def setup_method(self):
        """Set up test short-term memory"""
        self.config = {
            'buffer_size': 5,
            'max_tokens': 1000
        }
        self.summarizer = Mock()
        self.short_term = ShortTermMemory(self.config, self.summarizer)
        
    def test_add_memory(self):
        """Test adding memories to buffer"""
        
        memory_item = MemoryItem(
            id="test_memory",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            timestamp=datetime.now(),
            agent_id="test_agent",
            project_id="test_project",
            importance=ImportanceLevel.MEDIUM,
            context={},
            tags=[]
        )
        
        result = self.short_term.add_memory(memory_item)
        assert result is True
        assert len(self.short_term.buffer) == 1
        assert self.short_term.buffer[0] == memory_item
        
    def test_get_recent_memories(self):
        """Test retrieving recent memories"""
        
        # Add multiple memories
        for i in range(3):
            memory_item = MemoryItem(
                id=f"memory_{i}",
                content=f"Content {i}",
                memory_type=MemoryType.SHORT_TERM,
                timestamp=datetime.now() - timedelta(minutes=i),
                agent_id=f"agent_{i % 2}",  # Two different agents
                project_id="test_project",
                importance=ImportanceLevel.MEDIUM,
                context={},
                tags=[]
            )
            self.short_term.add_memory(memory_item)
            
        # Test getting all memories
        all_memories = self.short_term.get_recent_memories()
        assert len(all_memories) == 3
        
        # Test limit
        limited_memories = self.short_term.get_recent_memories(limit=2)
        assert len(limited_memories) == 2
        
        # Test agent filter
        agent_memories = self.short_term.get_recent_memories(agent_id="agent_0")
        assert len(agent_memories) == 2  # memories 0 and 2
        assert all(m.agent_id == "agent_0" for m in agent_memories)
        
    def test_working_memory(self):
        """Test working memory operations"""
        
        self.short_term.set_working_memory("current_task", "testing")
        self.short_term.set_working_memory("step_count", 5)
        
        working_memory = self.short_term.get_working_memory()
        assert working_memory["current_task"] == "testing"
        assert working_memory["step_count"] == 5
        
    def test_session_context(self):
        """Test session context operations"""
        
        context = {"session_id": "test_session", "user": "tester"}
        self.short_term.set_session_context(context)
        
        retrieved_context = self.short_term.get_session_context()
        assert retrieved_context["session_id"] == "test_session"
        assert retrieved_context["user"] == "tester"

@pytest.mark.asyncio
class TestMemorySystem:
    """Test integrated MemorySystem functionality"""
    
    async def setup_method(self):
        """Set up test memory system"""
        # Create temporary directory for testing
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create test configuration
        self.config = {
            "short_term": {
                "buffer_size": 10,
                "max_tokens": 5000
            },
            "long_term": {
                "type": "chroma",
                "collection_name": "test_memory",
                "persist_directory": str(self.temp_dir / "chroma_test")
            },
            "orchestrator": {
                "short_term_limit": 10,
                "consolidation_threshold": 0.5,
                "importance_decay_hours": 12
            }
        }
        
        # Create config file
        config_path = self.temp_dir / "memory_config.json"
        with open(config_path, 'w') as f:
            json.dump(self.config, f)
            
        # Mock ChromaDB to avoid dependency issues in tests
        with patch('memory.memory_system.chromadb'):
            self.memory_system = MemorySystem(str(config_path))
            
    def teardown_method(self):
        """Clean up test files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            
    async def test_add_memory(self):
        """Test adding memory to system"""
        
        memory_id = await self.memory_system.add_memory(
            content="Test memory content",
            agent_id="test_agent",
            project_id="test_project",
            context={"type": "test"},
            tags=["test", "unit"]
        )
        
        assert memory_id is not None
        assert len(self.memory_system.short_term.buffer) == 1
        
    async def test_search_memories(self):
        """Test memory search functionality"""
        
        # Add test memories
        await self.memory_system.add_memory(
            content="API development testing implementation",
            agent_id="backend_agent",
            project_id="test_project"
        )
        
        await self.memory_system.add_memory(
            content="Frontend component styling",
            agent_id="frontend_agent",
            project_id="test_project"
        )
        
        # Test search
        results = await self.memory_system.search_memories(
            query="API testing",
            limit=5
        )
        
        # Should find memories from short-term
        assert len(results) >= 1
        
    async def test_agent_context_retrieval(self):
        """Test getting agent context"""
        
        # Add some memories for the agent
        await self.memory_system.add_memory(
            content="Agent started task",
            agent_id="test_agent",
            project_id="test_project",
            context={"type": "start"}
        )
        
        await self.memory_system.add_memory(
            content="Agent completed task",
            agent_id="test_agent", 
            project_id="test_project",
            context={"type": "completion"}
        )
        
        # Get agent context
        context = await self.memory_system.get_agent_context(
            agent_id="test_agent",
            project_id="test_project"
        )
        
        assert "recent_memories" in context
        assert "working_memory" in context
        assert "relevant_memories" in context
        assert "session_context" in context
        
        # Should have memories for this agent
        assert len(context["recent_memories"]) == 2
        
    async def test_agent_handoff_recording(self):
        """Test recording agent handoffs"""
        
        handoff_data = {
            "summary": "Backend work completed, ready for frontend",
            "artifacts": ["api_spec.json"],
            "next_steps": ["Implement UI components"]
        }
        
        await self.memory_system.record_agent_handoff(
            from_agent="backend_agent",
            to_agent="frontend_agent",
            project_id="test_project",
            handoff_data=handoff_data
        )
        
        # Should have recorded handoff in memory
        assert len(self.memory_system.short_term.buffer) == 1
        handoff_memory = self.memory_system.short_term.buffer[0]
        assert handoff_memory.memory_type == MemoryType.EPISODIC
        assert "handoff" in handoff_memory.tags
        assert handoff_memory.context["from_agent"] == "backend_agent"
        assert handoff_memory.context["to_agent"] == "frontend_agent"
        
    async def test_memory_stats(self):
        """Test getting memory system statistics"""
        
        # Add some memories
        for i in range(3):
            await self.memory_system.add_memory(
                content=f"Test memory {i}",
                agent_id=f"agent_{i}",
                project_id="test_project"
            )
            
        stats = self.memory_system.get_memory_stats()
        
        assert "short_term_memories" in stats
        assert "long_term_memories" in stats
        assert "working_memory_keys" in stats
        assert stats["short_term_memories"] == 3

@pytest.mark.asyncio
class TestCoralMemoryIntegration:
    """Test CoralCollective memory integration"""
    
    async def setup_method(self):
        """Set up test integration"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Mock the CoralMemoryIntegration to avoid full system dependencies
        with patch('memory.coral_memory_integration.MemorySystem'), \
             patch('memory.coral_memory_integration.ProjectStateManager'):
            self.integration = CoralMemoryIntegration(self.temp_dir)
            self.integration.memory_system = Mock()
            self.integration.memory_system.add_memory = AsyncMock(return_value="test_memory_id")
            self.integration.state_manager = Mock()
            
    def teardown_method(self):
        """Clean up test files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            
    async def test_record_agent_start(self):
        """Test recording agent start"""
        
        memory_id = await self.integration.record_agent_start(
            agent_id="test_agent",
            task="Test task",
            context={"priority": "high"}
        )
        
        assert memory_id == "test_memory_id"
        
        # Verify memory was added with correct parameters
        self.integration.memory_system.add_memory.assert_called_once()
        call_args = self.integration.memory_system.add_memory.call_args
        
        assert "Agent test_agent started task" in call_args.kwargs["content"]
        assert call_args.kwargs["agent_id"] == "test_agent"
        assert call_args.kwargs["context"]["type"] == "agent_start"
        assert call_args.kwargs["context"]["task"] == "Test task"
        assert MemoryType.EPISODIC in call_args.args or call_args.kwargs.get("memory_type") == MemoryType.EPISODIC
        
    async def test_record_agent_completion(self):
        """Test recording agent completion"""
        
        outputs = {"result": "success", "files_created": 3}
        artifacts = [{"type": "code", "path": "main.py"}]
        
        await self.integration.record_agent_completion(
            agent_id="test_agent",
            success=True,
            outputs=outputs,
            artifacts=artifacts
        )
        
        # Verify completion was recorded
        call_count = self.integration.memory_system.add_memory.call_count
        assert call_count >= 1
        
        # Check the call for completion memory
        calls = self.integration.memory_system.add_memory.call_args_list
        completion_call = calls[-1]  # Last call should be completion
        
        assert "completed successfully" in completion_call.kwargs["content"]
        assert completion_call.kwargs["context"]["type"] == "agent_completion"
        assert completion_call.kwargs["context"]["success"] is True

@pytest.mark.asyncio 
class TestMemoryMigration:
    """Test memory migration functionality"""
    
    async def setup_method(self):
        """Set up test migration"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.coral_dir = self.temp_dir / '.coral'
        self.coral_dir.mkdir()
        
        # Create mock project state
        self.mock_state = {
            'project': {'name': 'test_project', 'current_phase': 'development'},
            'agents': {
                'completed': [
                    {
                        'agent_id': 'backend_agent',
                        'task': 'Create API',
                        'success': True,
                        'duration_minutes': 30,
                        'outputs': {'files': ['api.py']}
                    }
                ]
            },
            'handoffs': [
                {
                    'from_agent': 'backend_agent',
                    'to_agent': 'frontend_agent',
                    'data': {'summary': 'API ready for frontend integration'}
                }
            ],
            'artifacts': [
                {
                    'type': 'code',
                    'path': 'api.py',
                    'created_by': 'backend_agent',
                    'metadata': {'language': 'python'}
                }
            ]
        }
        
        # Save mock state
        import yaml
        state_file = self.coral_dir / 'project_state.yaml'
        with open(state_file, 'w') as f:
            yaml.dump(self.mock_state, f)
            
    def teardown_method(self):
        """Clean up test files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            
    async def test_migration_process(self):
        """Test complete migration process"""
        
        with patch('memory.migration_strategy.initialize_project_memory') as mock_init:
            # Mock memory integration
            mock_memory_integration = Mock()
            mock_memory_integration.project_id = "test_project"
            mock_memory_integration.memory_system = Mock()
            mock_memory_integration.memory_system.add_memory = AsyncMock(return_value="test_id")
            
            mock_init.return_value = mock_memory_integration
            
            # Run migration
            migration = MemoryMigrationStrategy(self.temp_dir)
            report = await migration.migrate_project()
            
            # Verify migration report
            assert "migrated_items" in report
            assert "errors" in report
            assert report["project_name"] == self.temp_dir.name
            
            # Verify memories were added
            call_count = mock_memory_integration.memory_system.add_memory.call_count
            assert call_count >= 4  # At least: agent start, completion, handoff, artifact
            
    async def test_migration_validation(self):
        """Test migration validation"""
        
        # Mock memory integration for validation
        mock_memory_integration = Mock()
        mock_memory_integration.project_id = "test_project"
        mock_memory_integration.memory_system = Mock()
        mock_memory_integration.memory_system.add_memory = AsyncMock(return_value="test_id")
        mock_memory_integration.search_project_knowledge = AsyncMock(return_value=[])
        mock_memory_integration.get_agent_context = AsyncMock(return_value={})
        mock_memory_integration.consolidate_session_memory = AsyncMock()
        
        validator = MemorySystemValidator(mock_memory_integration)
        validation_report = await validator.validate_migration()
        
        assert "tests" in validation_report
        assert "overall_status" in validation_report
        assert len(validation_report["tests"]) >= 4  # memory_storage, search, context, consolidation

class TestMemorySummarizer:
    """Test memory summarization functionality"""
    
    def setup_method(self):
        """Set up test summarizer"""
        self.config = {}
        self.summarizer = MemorySummarizer(self.config)
        
    async def test_fallback_summarization(self):
        """Test fallback summarization when LLM unavailable"""
        
        memories = [
            MemoryItem(
                id="mem1",
                content="Agent started backend development",
                memory_type=MemoryType.EPISODIC,
                timestamp=datetime.now() - timedelta(hours=2),
                agent_id="backend_agent",
                project_id="test_project",
                importance=ImportanceLevel.HIGH,
                context={},
                tags=[]
            ),
            MemoryItem(
                id="mem2", 
                content="API endpoints created successfully",
                memory_type=MemoryType.EPISODIC,
                timestamp=datetime.now() - timedelta(hours=1),
                agent_id="backend_agent",
                project_id="test_project",
                importance=ImportanceLevel.HIGH,
                context={},
                tags=[]
            )
        ]
        
        summary = await self.summarizer.summarize_memories(memories)
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "backend_agent" in summary
        assert "2 agent interactions" in summary

# Integration tests that require the full system
@pytest.mark.integration
@pytest.mark.asyncio
class TestFullMemorySystemIntegration:
    """Full system integration tests"""
    
    async def setup_method(self):
        """Set up full system test"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create memory config
        from memory.coral_memory_integration import create_memory_config
        self.config_path = create_memory_config(self.temp_dir)
        
    def teardown_method(self):
        """Clean up test files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            
    @pytest.mark.skipif(True, reason="Requires ChromaDB installation")
    async def test_full_memory_workflow(self):
        """Test complete memory workflow with real ChromaDB"""
        
        # This test would run with real ChromaDB
        # Skip by default to avoid dependency requirements
        pass

# Test fixtures and utilities
@pytest.fixture
def sample_memory_items():
    """Fixture providing sample memory items for testing"""
    
    return [
        MemoryItem(
            id="sample1",
            content="Backend API development started",
            memory_type=MemoryType.EPISODIC,
            timestamp=datetime.now() - timedelta(hours=1),
            agent_id="backend_agent",
            project_id="test_project",
            importance=ImportanceLevel.HIGH,
            context={"type": "agent_start"},
            tags=["backend", "api", "start"]
        ),
        MemoryItem(
            id="sample2",
            content="Database schema created with user and product tables",
            memory_type=MemoryType.SEMANTIC,
            timestamp=datetime.now() - timedelta(minutes=30),
            agent_id="backend_agent",
            project_id="test_project",
            importance=ImportanceLevel.MEDIUM,
            context={"type": "artifact_creation"},
            tags=["database", "schema", "artifact"]
        ),
        MemoryItem(
            id="sample3",
            content="Frontend components need API integration",
            memory_type=MemoryType.SHORT_TERM,
            timestamp=datetime.now() - timedelta(minutes=10),
            agent_id="frontend_agent",
            project_id="test_project",
            importance=ImportanceLevel.MEDIUM,
            context={"type": "requirement"},
            tags=["frontend", "integration", "requirement"]
        )
    ]

@pytest.fixture
def temp_project_dir():
    """Fixture providing temporary project directory"""
    
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

# Performance tests
@pytest.mark.performance
class TestMemoryPerformance:
    """Performance tests for memory system"""
    
    @pytest.mark.asyncio
    async def test_memory_addition_performance(self):
        """Test performance of adding many memories"""
        
        import time
        from memory.memory_system import MemorySystem
        
        # Create test memory system with mocked ChromaDB
        with patch('memory.memory_system.chromadb'):
            memory_system = MemorySystem()
            
            start_time = time.time()
            
            # Add 100 memories
            for i in range(100):
                await memory_system.add_memory(
                    content=f"Test memory {i}",
                    agent_id=f"agent_{i % 5}",
                    project_id="performance_test"
                )
                
            end_time = time.time()
            duration = end_time - start_time
            
            # Should complete within reasonable time (adjust threshold as needed)
            assert duration < 5.0  # 5 seconds for 100 memories
            assert len(memory_system.short_term.buffer) == 100

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])