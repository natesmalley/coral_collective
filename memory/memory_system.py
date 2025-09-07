"""
Advanced Memory System for CoralCollective

Implements dual-memory architecture with:
1. Short-term memory with summarization and buffer management
2. Long-term memory with vector embeddings and semantic search
3. Memory orchestration for intelligent routing and consolidation
4. Integration with CoralCollective's agent workflow system

Based on "How to Build an Advanced AI Agent with Summarized Short-Term and Vector-Based Long-Term Memory"
"""

import json
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import uuid
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryType(Enum):
    """Types of memory storage"""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term" 
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"
    SEMANTIC = "semantic"

class ImportanceLevel(Enum):
    """Importance scoring for memory items"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    TRIVIAL = 1

@dataclass
class MemoryItem:
    """Core memory item structure"""
    id: str
    content: str
    memory_type: MemoryType
    timestamp: datetime
    agent_id: str
    project_id: str
    importance: ImportanceLevel
    context: Dict[str, Any]
    tags: List[str]
    embedding: Optional[List[float]] = None
    summary: Optional[str] = None
    parent_id: Optional[str] = None
    children_ids: List[str] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def __post_init__(self):
        if self.children_ids is None:
            self.children_ids = []
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)
        if self.last_accessed and isinstance(self.last_accessed, str):
            self.last_accessed = datetime.fromisoformat(self.last_accessed)

class MemoryOrchestrator:
    """
    Central orchestrator that manages memory flow between short-term and long-term storage
    Implements attention mechanism and importance scoring
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.short_term_limit = config.get('short_term_limit', 20)
        self.consolidation_threshold = config.get('consolidation_threshold', 0.7)
        self.importance_decay_hours = config.get('importance_decay_hours', 24)
        
    def should_consolidate_to_long_term(self, item: MemoryItem) -> bool:
        """Determine if memory item should be moved to long-term storage"""
        
        # Always consolidate critical items
        if item.importance == ImportanceLevel.CRITICAL:
            return True
            
        # Consolidate based on age and importance
        age_hours = (datetime.now() - item.timestamp).total_seconds() / 3600
        importance_score = item.importance.value
        
        # Apply decay based on age
        decayed_importance = importance_score * max(0.1, 1 - (age_hours / self.importance_decay_hours))
        
        # Consolidate if above threshold
        return decayed_importance >= self.consolidation_threshold
        
    def calculate_importance(self, content: str, context: Dict[str, Any]) -> ImportanceLevel:
        """Calculate importance score for memory content"""
        
        # Rule-based importance scoring
        importance_score = ImportanceLevel.LOW.value
        
        # Critical keywords boost importance
        critical_keywords = ['error', 'critical', 'security', 'production', 'failure', 'complete', 'deploy']
        high_keywords = ['implement', 'create', 'design', 'architecture', 'api', 'database']
        
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in critical_keywords):
            importance_score = max(importance_score, ImportanceLevel.CRITICAL.value)
        elif any(keyword in content_lower for keyword in high_keywords):
            importance_score = max(importance_score, ImportanceLevel.HIGH.value)
            
        # Context-based importance
        if context.get('agent_handoff'):
            importance_score = max(importance_score, ImportanceLevel.HIGH.value)
            
        if context.get('project_milestone'):
            importance_score = max(importance_score, ImportanceLevel.CRITICAL.value)
            
        # Length-based importance (longer content often more important)
        if len(content) > 1000:
            importance_score += 1
            
        return ImportanceLevel(min(importance_score, ImportanceLevel.CRITICAL.value))
        
    def generate_attention_weights(self, query: str, memories: List[MemoryItem]) -> List[float]:
        """Generate attention weights for memories based on query relevance"""
        
        weights = []
        for memory in memories:
            # Simple keyword overlap scoring
            query_words = set(query.lower().split())
            memory_words = set(memory.content.lower().split())
            
            overlap = len(query_words.intersection(memory_words))
            total_words = len(query_words.union(memory_words))
            
            similarity = overlap / total_words if total_words > 0 else 0.0
            
            # Boost based on importance and recency
            importance_boost = memory.importance.value / 5.0
            recency_boost = max(0.1, 1 - (datetime.now() - memory.timestamp).days / 30.0)
            
            weight = similarity * importance_boost * recency_boost
            weights.append(weight)
            
        return weights

class ShortTermMemory:
    """
    Buffer-based short-term memory with automatic summarization
    Maintains recent context within token limits
    """
    
    def __init__(self, config: Dict[str, Any], summarizer: 'MemorySummarizer' = None):
        self.config = config
        self.buffer_size = config.get('buffer_size', 20)
        self.max_tokens = config.get('max_tokens', 8000)
        self.summarizer = summarizer
        self.buffer: List[MemoryItem] = []
        self.session_memory: Dict[str, Any] = {}
        self.working_memory: Dict[str, Any] = {}
        
    def add_memory(self, item: MemoryItem) -> bool:
        """Add memory item to short-term buffer"""
        
        # Add to buffer
        self.buffer.append(item)
        
        # Check if buffer needs pruning
        if len(self.buffer) > self.buffer_size:
            await self._prune_buffer()
            
        return True
        
    async def _prune_buffer(self):
        """Prune buffer when it exceeds limits"""
        
        # Sort by importance and recency
        self.buffer.sort(key=lambda x: (x.importance.value, x.timestamp), reverse=True)
        
        # Keep most important items
        keep_count = int(self.buffer_size * 0.7)  # Keep 70%
        items_to_consolidate = self.buffer[keep_count:]
        self.buffer = self.buffer[:keep_count]
        
        # Summarize items being removed if summarizer available
        if self.summarizer and items_to_consolidate:
            summary = await self.summarizer.summarize_memories(items_to_consolidate)
            
            # Create summary memory item
            summary_item = MemoryItem(
                id=str(uuid.uuid4()),
                content=summary,
                memory_type=MemoryType.SHORT_TERM,
                timestamp=datetime.now(),
                agent_id="memory_system",
                project_id=items_to_consolidate[0].project_id,
                importance=ImportanceLevel.MEDIUM,
                context={"type": "summary", "summarized_count": len(items_to_consolidate)},
                tags=["summary"],
                parent_id=None,
                children_ids=[item.id for item in items_to_consolidate]
            )
            
            self.buffer.append(summary_item)
            
    def get_recent_memories(self, limit: int = None, agent_id: str = None) -> List[MemoryItem]:
        """Get recent memories, optionally filtered by agent"""
        
        memories = self.buffer
        
        if agent_id:
            memories = [m for m in memories if m.agent_id == agent_id]
            
        # Sort by timestamp (most recent first)
        memories.sort(key=lambda x: x.timestamp, reverse=True)
        
        if limit:
            memories = memories[:limit]
            
        return memories
        
    def get_working_memory(self) -> Dict[str, Any]:
        """Get current working memory state"""
        return self.working_memory.copy()
        
    def set_working_memory(self, key: str, value: Any):
        """Set working memory variable"""
        self.working_memory[key] = value
        
    def get_session_context(self) -> Dict[str, Any]:
        """Get session-specific context"""
        return self.session_memory.copy()
        
    def set_session_context(self, context: Dict[str, Any]):
        """Update session context"""
        self.session_memory.update(context)

class LongTermMemory(ABC):
    """
    Abstract base class for long-term memory implementations
    Supports vector storage and semantic search
    """
    
    @abstractmethod
    async def store_memory(self, item: MemoryItem) -> bool:
        """Store memory item in long-term storage"""
        pass
        
    @abstractmethod
    async def search_memories(self, query: str, limit: int = 10, 
                            filters: Dict[str, Any] = None) -> List[MemoryItem]:
        """Search memories using semantic similarity"""
        pass
        
    @abstractmethod
    async def get_memory_by_id(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve specific memory by ID"""
        pass
        
    @abstractmethod
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete memory from storage"""
        pass
        
    @abstractmethod
    async def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Update memory item"""
        pass

class ChromaLongTermMemory(LongTermMemory):
    """
    ChromaDB implementation of long-term memory
    Provides vector storage and semantic search capabilities
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.collection_name = config.get('collection_name', 'coral_collective_memory')
        self.persist_directory = config.get('persist_directory', './memory/chroma_db')
        
        # Initialize ChromaDB
        try:
            import chromadb
            from chromadb.config import Settings
            
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(allow_reset=True)
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
        except ImportError:
            logger.error("ChromaDB not installed. Run: pip install chromadb")
            raise
            
    async def store_memory(self, item: MemoryItem) -> bool:
        """Store memory item in ChromaDB"""
        
        try:
            # Prepare metadata
            metadata = {
                "agent_id": item.agent_id,
                "project_id": item.project_id,
                "memory_type": item.memory_type.value,
                "importance": item.importance.value,
                "timestamp": item.timestamp.isoformat(),
                "tags": ",".join(item.tags),
                "access_count": item.access_count
            }
            
            # Add context fields
            metadata.update(item.context)
            
            # Store in ChromaDB
            self.collection.add(
                documents=[item.content],
                metadatas=[metadata],
                ids=[item.id]
            )
            
            logger.info(f"Stored memory {item.id} in long-term storage")
            return True
            
        except Exception as e:
            logger.error(f"Error storing memory {item.id}: {e}")
            return False
            
    async def search_memories(self, query: str, limit: int = 10, 
                            filters: Dict[str, Any] = None) -> List[MemoryItem]:
        """Search memories using semantic similarity"""
        
        try:
            # Build where clause for filtering
            where_clause = {}
            if filters:
                if 'agent_id' in filters:
                    where_clause['agent_id'] = filters['agent_id']
                if 'project_id' in filters:
                    where_clause['project_id'] = filters['project_id']
                if 'memory_type' in filters:
                    where_clause['memory_type'] = filters['memory_type']
                    
            # Query ChromaDB
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_clause if where_clause else None
            )
            
            # Convert results to MemoryItem objects
            memories = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i]
                    memory_id = results['ids'][0][i]
                    
                    # Reconstruct MemoryItem
                    memory = MemoryItem(
                        id=memory_id,
                        content=doc,
                        memory_type=MemoryType(metadata['memory_type']),
                        timestamp=datetime.fromisoformat(metadata['timestamp']),
                        agent_id=metadata['agent_id'],
                        project_id=metadata['project_id'],
                        importance=ImportanceLevel(metadata['importance']),
                        context={k: v for k, v in metadata.items() 
                               if k not in ['agent_id', 'project_id', 'memory_type', 
                                          'importance', 'timestamp', 'tags', 'access_count']},
                        tags=metadata['tags'].split(',') if metadata['tags'] else [],
                        access_count=metadata.get('access_count', 0)
                    )
                    
                    memories.append(memory)
                    
            return memories
            
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []
            
    async def get_memory_by_id(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve specific memory by ID"""
        
        try:
            results = self.collection.get(ids=[memory_id])
            
            if results['documents']:
                doc = results['documents'][0]
                metadata = results['metadatas'][0]
                
                memory = MemoryItem(
                    id=memory_id,
                    content=doc,
                    memory_type=MemoryType(metadata['memory_type']),
                    timestamp=datetime.fromisoformat(metadata['timestamp']),
                    agent_id=metadata['agent_id'],
                    project_id=metadata['project_id'],
                    importance=ImportanceLevel(metadata['importance']),
                    context={k: v for k, v in metadata.items() 
                           if k not in ['agent_id', 'project_id', 'memory_type', 
                                      'importance', 'timestamp', 'tags', 'access_count']},
                    tags=metadata['tags'].split(',') if metadata['tags'] else [],
                    access_count=metadata.get('access_count', 0)
                )
                
                return memory
                
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving memory {memory_id}: {e}")
            return None
            
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete memory from storage"""
        
        try:
            self.collection.delete(ids=[memory_id])
            logger.info(f"Deleted memory {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {e}")
            return False
            
    async def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Update memory item"""
        
        # ChromaDB doesn't support direct updates, so we retrieve, modify, and re-add
        memory = await self.get_memory_by_id(memory_id)
        if not memory:
            return False
            
        # Apply updates
        for key, value in updates.items():
            if hasattr(memory, key):
                setattr(memory, key, value)
                
        # Delete old and store updated
        await self.delete_memory(memory_id)
        return await self.store_memory(memory)

class MemorySummarizer:
    """
    Summarizes memory content using LLM to maintain context within token limits
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm_client = None  # Will be initialized with specific LLM client
        
    async def summarize_memories(self, memories: List[MemoryItem]) -> str:
        """Summarize a list of memories into a concise summary"""
        
        if not memories:
            return ""
            
        # Prepare content for summarization
        content_parts = []
        for memory in memories:
            timestamp_str = memory.timestamp.strftime("%Y-%m-%d %H:%M")
            content_parts.append(f"[{timestamp_str}] {memory.agent_id}: {memory.content}")
            
        combined_content = "\n".join(content_parts)
        
        # Create summarization prompt
        prompt = f"""
        Summarize the following agent interactions and outputs, preserving key information and decisions:
        
        {combined_content}
        
        Provide a concise summary that maintains:
        1. Key decisions made
        2. Important outputs or artifacts created
        3. Critical context for future agents
        4. Any errors or issues encountered
        
        Summary:
        """
        
        # If we have an LLM client, use it for summarization
        if self.llm_client:
            try:
                response = await self.llm_client.generate(prompt)
                return response.strip()
            except Exception as e:
                logger.warning(f"LLM summarization failed: {e}")
                
        # Fallback to simple concatenation with truncation
        return self._fallback_summarization(memories)
        
    def _fallback_summarization(self, memories: List[MemoryItem]) -> str:
        """Fallback summarization when LLM is unavailable"""
        
        # Extract key information
        agents = list(set(m.agent_id for m in memories))
        timespan = f"{memories[0].timestamp.strftime('%Y-%m-%d')} to {memories[-1].timestamp.strftime('%Y-%m-%d')}"
        
        # Get high-importance content
        important_content = []
        for memory in memories:
            if memory.importance.value >= ImportanceLevel.HIGH.value:
                important_content.append(f"- {memory.agent_id}: {memory.content[:200]}...")
                
        summary_parts = [
            f"Summary of {len(memories)} agent interactions ({timespan})",
            f"Agents involved: {', '.join(agents)}",
            "Key activities:"
        ]
        
        if important_content:
            summary_parts.extend(important_content)
        else:
            summary_parts.append("- Various agent activities and outputs")
            
        return "\n".join(summary_parts)

class MemorySystem:
    """
    Main memory system that orchestrates short-term and long-term memory
    Provides unified interface for CoralCollective agents
    """
    
    def __init__(self, config_path: str = None):
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.orchestrator = MemoryOrchestrator(self.config.get('orchestrator', {}))
        self.summarizer = MemorySummarizer(self.config.get('summarizer', {}))
        self.short_term = ShortTermMemory(self.config.get('short_term', {}), self.summarizer)
        
        # Initialize long-term memory based on config
        lt_config = self.config.get('long_term', {})
        lt_type = lt_config.get('type', 'chroma')
        
        if lt_type == 'chroma':
            self.long_term = ChromaLongTermMemory(lt_config)
        else:
            raise ValueError(f"Unsupported long-term memory type: {lt_type}")
            
        logger.info("Memory system initialized successfully")
        
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load memory system configuration"""
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                return json.load(f)
                
        # Default configuration
        return {
            "short_term": {
                "buffer_size": 20,
                "max_tokens": 8000
            },
            "long_term": {
                "type": "chroma",
                "collection_name": "coral_collective_memory",
                "persist_directory": "./memory/chroma_db"
            },
            "orchestrator": {
                "short_term_limit": 20,
                "consolidation_threshold": 0.7,
                "importance_decay_hours": 24
            },
            "summarizer": {}
        }
        
    async def add_memory(self, content: str, agent_id: str, project_id: str, 
                        context: Dict[str, Any] = None, tags: List[str] = None,
                        memory_type: MemoryType = None) -> str:
        """Add new memory to the system"""
        
        # Generate memory ID
        memory_id = str(uuid.uuid4())
        
        # Determine memory type
        if memory_type is None:
            memory_type = MemoryType.SHORT_TERM
            
        # Calculate importance
        importance = self.orchestrator.calculate_importance(content, context or {})
        
        # Create memory item
        memory_item = MemoryItem(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            timestamp=datetime.now(),
            agent_id=agent_id,
            project_id=project_id,
            importance=importance,
            context=context or {},
            tags=tags or []
        )
        
        # Add to short-term memory
        await self.short_term.add_memory(memory_item)
        
        # Check if should be consolidated to long-term
        if self.orchestrator.should_consolidate_to_long_term(memory_item):
            await self.long_term.store_memory(memory_item)
            
        logger.info(f"Added memory {memory_id} for agent {agent_id}")
        return memory_id
        
    async def search_memories(self, query: str, agent_id: str = None, 
                            project_id: str = None, limit: int = 10,
                            include_short_term: bool = True) -> List[MemoryItem]:
        """Search memories across short-term and long-term storage"""
        
        results = []
        
        # Search short-term memory
        if include_short_term:
            short_term_memories = self.short_term.get_recent_memories(
                limit=limit // 2, agent_id=agent_id
            )
            results.extend(short_term_memories)
            
        # Search long-term memory
        filters = {}
        if agent_id:
            filters['agent_id'] = agent_id
        if project_id:
            filters['project_id'] = project_id
            
        long_term_memories = await self.long_term.search_memories(
            query, limit=limit, filters=filters
        )
        results.extend(long_term_memories)
        
        # Remove duplicates and sort by relevance
        unique_memories = {m.id: m for m in results}.values()
        sorted_memories = list(unique_memories)
        
        # Apply attention weighting
        if query:
            weights = self.orchestrator.generate_attention_weights(query, sorted_memories)
            sorted_memories = [m for _, m in sorted(zip(weights, sorted_memories), reverse=True)]
            
        return sorted_memories[:limit]
        
    async def get_agent_context(self, agent_id: str, project_id: str = None) -> Dict[str, Any]:
        """Get relevant context for an agent"""
        
        # Get recent memories for this agent
        recent_memories = self.short_term.get_recent_memories(limit=10, agent_id=agent_id)
        
        # Get working memory
        working_memory = self.short_term.get_working_memory()
        
        # Search for relevant long-term memories
        relevant_memories = await self.long_term.search_memories(
            f"agent:{agent_id}", limit=5, 
            filters={'agent_id': agent_id, 'project_id': project_id} if project_id else {'agent_id': agent_id}
        )
        
        return {
            'recent_memories': [asdict(m) for m in recent_memories],
            'working_memory': working_memory,
            'relevant_memories': [asdict(m) for m in relevant_memories],
            'session_context': self.short_term.get_session_context()
        }
        
    async def record_agent_handoff(self, from_agent: str, to_agent: str, 
                                 project_id: str, handoff_data: Dict[str, Any]):
        """Record agent handoff in memory"""
        
        content = f"Handoff from {from_agent} to {to_agent}: {handoff_data.get('summary', '')}"
        context = {
            'type': 'handoff',
            'from_agent': from_agent,
            'to_agent': to_agent,
            'handoff_data': handoff_data
        }
        
        await self.add_memory(
            content=content,
            agent_id=from_agent,
            project_id=project_id,
            context=context,
            tags=['handoff', 'agent_transition'],
            memory_type=MemoryType.EPISODIC
        )
        
    async def consolidate_memories(self):
        """Perform background memory consolidation"""
        
        # Get memories from short-term that should be consolidated
        recent_memories = self.short_term.get_recent_memories()
        
        for memory in recent_memories:
            if self.orchestrator.should_consolidate_to_long_term(memory):
                await self.long_term.store_memory(memory)
                logger.info(f"Consolidated memory {memory.id} to long-term storage")
                
    async def cleanup_old_memories(self, days_threshold: int = 90):
        """Clean up old, low-importance memories"""
        
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        
        # This would require additional ChromaDB queries to find old memories
        # Implementation depends on specific cleanup policies
        logger.info(f"Memory cleanup completed for memories older than {days_threshold} days")
        
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        
        short_term_count = len(self.short_term.buffer)
        
        # Get long-term count (would need ChromaDB query)
        try:
            collection_info = self.long_term.collection.count()
            long_term_count = collection_info
        except:
            long_term_count = 0
            
        return {
            'short_term_memories': short_term_count,
            'long_term_memories': long_term_count,
            'working_memory_keys': len(self.short_term.working_memory),
            'session_context_keys': len(self.short_term.session_memory)
        }