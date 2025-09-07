#!/usr/bin/env python3
"""
CoralCollective Memory System - Three-Tier Architecture

Implements working memory, short-term memory, and long-term memory systems
for persistent knowledge retention across agent interactions.
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import logging
from abc import ABC, abstractmethod

# Memory-specific logging
logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memory content"""
    INTERACTION = "interaction"
    CODE_PATTERN = "code_pattern"
    REQUIREMENT = "requirement"
    DECISION = "decision"
    ERROR_SOLUTION = "error_solution"
    AGENT_HANDOFF = "agent_handoff"
    PROJECT_CONTEXT = "project_context"
    TECHNICAL_DOC = "technical_doc"


@dataclass
class MemoryItem:
    """Basic memory item structure"""
    id: str
    content: str
    memory_type: MemoryType
    agent_id: str
    project_id: Optional[str]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance_score: float = 0.5
    access_count: int = 0
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'content': self.content,
            'memory_type': self.memory_type.value,
            'agent_id': self.agent_id,
            'project_id': self.project_id,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            'importance_score': self.importance_score,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat(),
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            content=data['content'],
            memory_type=MemoryType(data['memory_type']),
            agent_id=data['agent_id'],
            project_id=data.get('project_id'),
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata', {}),
            importance_score=data.get('importance_score', 0.5),
            access_count=data.get('access_count', 0),
            last_accessed=datetime.fromisoformat(data.get('last_accessed', datetime.now(timezone.utc).isoformat())),
            tags=data.get('tags', [])
        )


@dataclass
class MemoryQuery:
    """Memory retrieval query structure"""
    query: str
    agent_id: Optional[str] = None
    project_id: Optional[str] = None
    memory_types: List[MemoryType] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    max_results: int = 10
    importance_threshold: float = 0.3
    recency_weight: float = 0.3
    similarity_threshold: float = 0.7
    time_range: Optional[Tuple[datetime, datetime]] = None


class MemoryStore(ABC):
    """Abstract base class for memory storage implementations"""
    
    @abstractmethod
    async def store(self, item: MemoryItem) -> bool:
        """Store a memory item"""
        pass
    
    @abstractmethod
    async def retrieve(self, query: MemoryQuery) -> List[MemoryItem]:
        """Retrieve memory items based on query"""
        pass
    
    @abstractmethod
    async def update(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """Update a memory item"""
        pass
    
    @abstractmethod
    async def delete(self, item_id: str) -> bool:
        """Delete a memory item"""
        pass
    
    @abstractmethod
    async def get_by_id(self, item_id: str) -> Optional[MemoryItem]:
        """Get memory item by ID"""
        pass


class WorkingMemory:
    """
    Working Memory - Active agent context during task execution
    Holds immediate context, current task state, and active variables
    """
    
    def __init__(self, max_items: int = 20):
        self.max_items = max_items
        self.items: Dict[str, Any] = {}
        self.task_context: Dict[str, Any] = {}
        self.agent_state: Dict[str, Any] = {}
        self.active_files: List[str] = []
        self.current_phase: str = ""
        self.created_at = datetime.now(timezone.utc)
    
    def set_context(self, key: str, value: Any):
        """Set working memory context"""
        self.items[key] = {
            'value': value,
            'timestamp': datetime.now(timezone.utc),
            'type': type(value).__name__
        }
        
        # Keep only most recent items
        if len(self.items) > self.max_items:
            oldest_key = min(self.items.keys(), key=lambda k: self.items[k]['timestamp'])
            del self.items[oldest_key]
    
    def get_context(self, key: str) -> Any:
        """Get working memory context"""
        item = self.items.get(key)
        return item['value'] if item else None
    
    def update_task_state(self, agent_id: str, task: str, status: str):
        """Update current task state"""
        self.task_context = {
            'agent_id': agent_id,
            'task': task,
            'status': status,
            'updated_at': datetime.now(timezone.utc)
        }
    
    def add_active_file(self, file_path: str):
        """Add file to active files list"""
        if file_path not in self.active_files:
            self.active_files.append(file_path)
        
        # Keep reasonable limit
        if len(self.active_files) > 50:
            self.active_files = self.active_files[-50:]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get working memory summary for handoff"""
        return {
            'context_items': len(self.items),
            'task_context': self.task_context,
            'agent_state': self.agent_state,
            'active_files': self.active_files[-10:],  # Recent files
            'current_phase': self.current_phase,
            'session_duration': (datetime.now(timezone.utc) - self.created_at).total_seconds()
        }
    
    def clear(self):
        """Clear working memory (end of session)"""
        self.items.clear()
        self.task_context.clear()
        self.agent_state.clear()
        self.active_files.clear()


class ShortTermMemory:
    """
    Short-Term Memory - Recent interactions and summaries
    Compresses and summarizes recent agent interactions
    """
    
    def __init__(self, max_items: int = 100, max_age_hours: int = 24):
        self.max_items = max_items
        self.max_age_hours = max_age_hours
        self.interactions: List[MemoryItem] = []
        self.summaries: Dict[str, str] = {}
        
    async def add_interaction(self, item: MemoryItem):
        """Add new interaction to short-term memory"""
        self.interactions.append(item)
        
        # Remove old items
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.max_age_hours)
        self.interactions = [
            interaction for interaction in self.interactions
            if interaction.timestamp > cutoff_time
        ]
        
        # Keep only most recent items
        if len(self.interactions) > self.max_items:
            self.interactions = self.interactions[-self.max_items:]
        
        # Generate periodic summaries
        if len(self.interactions) % 10 == 0:
            await self._generate_summary()
    
    async def _generate_summary(self):
        """Generate summary of recent interactions using LLM"""
        if not self.interactions:
            return
        
        # Group interactions by agent
        by_agent = {}
        for interaction in self.interactions[-20:]:  # Last 20 interactions
            agent_id = interaction.agent_id
            if agent_id not in by_agent:
                by_agent[agent_id] = []
            by_agent[agent_id].append(interaction)
        
        # Create summaries for each agent
        for agent_id, interactions in by_agent.items():
            recent_content = [item.content for item in interactions]
            summary = await self._summarize_content(recent_content, agent_id)
            self.summaries[f"{agent_id}_{datetime.now(timezone.utc).date()}"] = summary
    
    async def _summarize_content(self, content_list: List[str], agent_id: str) -> str:
        """Summarize content using LLM (placeholder for actual implementation)"""
        # This would integrate with an LLM service
        # For now, create a basic summary
        total_chars = sum(len(content) for content in content_list)
        unique_topics = set()
        
        for content in content_list:
            # Extract key topics (simple keyword extraction)
            words = content.lower().split()
            keywords = [word for word in words if len(word) > 4 and word.isalpha()]
            unique_topics.update(keywords[:5])  # Top 5 keywords per content
        
        return f"Agent {agent_id} - {len(content_list)} interactions, {total_chars} chars. Key topics: {', '.join(list(unique_topics)[:10])}"
    
    def get_recent_interactions(self, agent_id: Optional[str] = None, limit: int = 20) -> List[MemoryItem]:
        """Get recent interactions, optionally filtered by agent"""
        interactions = self.interactions
        
        if agent_id:
            interactions = [item for item in interactions if item.agent_id == agent_id]
        
        return interactions[-limit:]
    
    def get_summary(self, agent_id: Optional[str] = None) -> str:
        """Get summary of short-term memory"""
        if agent_id:
            # Find most recent summary for agent
            agent_summaries = [
                (key, summary) for key, summary in self.summaries.items()
                if key.startswith(agent_id)
            ]
            if agent_summaries:
                return agent_summaries[-1][1]
        
        # General summary
        total_interactions = len(self.interactions)
        unique_agents = len(set(item.agent_id for item in self.interactions))
        recent_summary = list(self.summaries.values())[-1] if self.summaries else "No summaries available"
        
        return f"Short-term memory: {total_interactions} interactions from {unique_agents} agents. Latest: {recent_summary}"
    
    async def prepare_for_long_term(self) -> List[MemoryItem]:
        """Prepare items for transfer to long-term memory"""
        # Select important items for long-term storage
        important_items = [
            item for item in self.interactions
            if item.importance_score > 0.6 or item.access_count > 2
        ]
        
        return important_items


class MemoryManager:
    """
    Central Memory Manager - Coordinates all memory tiers
    Handles memory transfer, retrieval, and lifecycle management
    """
    
    def __init__(self, 
                 long_term_store: MemoryStore,
                 project_path: Optional[Path] = None):
        self.working_memory = WorkingMemory()
        self.short_term_memory = ShortTermMemory()
        self.long_term_store = long_term_store
        self.project_path = project_path or Path.cwd()
        
        # Memory transfer settings
        self.auto_transfer_enabled = True
        self.transfer_interval_minutes = 60
        self.last_transfer = datetime.now(timezone.utc)
        
        # Importance scoring weights
        self.importance_weights = {
            'agent_handoff': 0.9,
            'error_solution': 0.8,
            'requirement': 0.7,
            'decision': 0.7,
            'code_pattern': 0.6,
            'interaction': 0.4,
            'technical_doc': 0.8
        }
    
    async def store_interaction(self, 
                              agent_id: str,
                              content: str,
                              memory_type: MemoryType,
                              project_id: Optional[str] = None,
                              metadata: Dict[str, Any] = None,
                              tags: List[str] = None) -> str:
        """Store a new interaction in memory"""
        # Generate unique ID
        item_id = str(uuid.uuid4())
        
        # Calculate importance score
        importance_score = self._calculate_importance(content, memory_type, metadata or {})
        
        # Create memory item
        item = MemoryItem(
            id=item_id,
            content=content,
            memory_type=memory_type,
            agent_id=agent_id,
            project_id=project_id,
            metadata=metadata or {},
            importance_score=importance_score,
            tags=tags or []
        )
        
        # Add to short-term memory
        await self.short_term_memory.add_interaction(item)
        
        # Check if immediate long-term storage is needed
        if importance_score > 0.8:
            await self.long_term_store.store(item)
        
        # Trigger periodic transfer if needed
        await self._maybe_transfer_memories()
        
        return item_id
    
    def _calculate_importance(self, 
                            content: str, 
                            memory_type: MemoryType, 
                            metadata: Dict[str, Any]) -> float:
        """Calculate importance score for memory item"""
        base_score = self.importance_weights.get(memory_type.value, 0.5)
        
        # Adjust based on content characteristics
        content_length_factor = min(1.0, len(content) / 1000)  # Longer content slightly more important
        
        # Boost for certain keywords
        important_keywords = ['error', 'fix', 'solution', 'requirement', 'decision', 'api', 'database']
        keyword_boost = sum(0.05 for keyword in important_keywords if keyword in content.lower())
        
        # Metadata boosts
        metadata_boost = 0
        if metadata.get('success') is False:  # Failed operations are important
            metadata_boost += 0.2
        if metadata.get('handoff_data'):  # Handoffs are important
            metadata_boost += 0.3
        
        final_score = min(1.0, base_score + content_length_factor * 0.1 + keyword_boost + metadata_boost)
        return final_score
    
    async def retrieve_memories(self, query: MemoryQuery) -> List[MemoryItem]:
        """Retrieve memories from all tiers"""
        results = []
        
        # Search short-term memory first
        short_term_results = self._search_short_term(query)
        results.extend(short_term_results)
        
        # Search long-term memory
        long_term_results = await self.long_term_store.retrieve(query)
        results.extend(long_term_results)
        
        # Remove duplicates and sort by relevance
        unique_results = {item.id: item for item in results}
        sorted_results = sorted(
            unique_results.values(),
            key=lambda x: self._calculate_relevance_score(x, query),
            reverse=True
        )
        
        # Update access counts
        for item in sorted_results[:query.max_results]:
            item.access_count += 1
            item.last_accessed = datetime.now(timezone.utc)
            await self.long_term_store.update(item.id, {
                'access_count': item.access_count,
                'last_accessed': item.last_accessed.isoformat()
            })
        
        return sorted_results[:query.max_results]
    
    def _search_short_term(self, query: MemoryQuery) -> List[MemoryItem]:
        """Search short-term memory"""
        interactions = self.short_term_memory.get_recent_interactions(
            agent_id=query.agent_id,
            limit=100
        )
        
        # Simple text-based filtering
        filtered = []
        query_lower = query.query.lower()
        
        for item in interactions:
            # Check memory type filter
            if query.memory_types and item.memory_type not in query.memory_types:
                continue
            
            # Check tag filter
            if query.tags and not any(tag in item.tags for tag in query.tags):
                continue
            
            # Check content relevance
            if query_lower in item.content.lower():
                filtered.append(item)
            
            # Check time range
            if query.time_range:
                start, end = query.time_range
                if not (start <= item.timestamp <= end):
                    continue
        
        return filtered
    
    def _calculate_relevance_score(self, item: MemoryItem, query: MemoryQuery) -> float:
        """Calculate relevance score for retrieved memory item"""
        # Base importance score
        relevance = item.importance_score
        
        # Recency boost
        age_hours = (datetime.now(timezone.utc) - item.timestamp).total_seconds() / 3600
        recency_score = max(0, 1 - (age_hours / 168))  # Decay over a week
        relevance += recency_score * query.recency_weight
        
        # Access frequency boost
        access_boost = min(0.3, item.access_count * 0.05)
        relevance += access_boost
        
        # Agent match boost
        if query.agent_id == item.agent_id:
            relevance += 0.2
        
        # Project match boost
        if query.project_id == item.project_id:
            relevance += 0.2
        
        return min(1.0, relevance)
    
    async def _maybe_transfer_memories(self):
        """Transfer memories from short-term to long-term if needed"""
        if not self.auto_transfer_enabled:
            return
        
        time_since_transfer = datetime.now(timezone.utc) - self.last_transfer
        if time_since_transfer.total_seconds() < (self.transfer_interval_minutes * 60):
            return
        
        # Prepare items for transfer
        important_items = await self.short_term_memory.prepare_for_long_term()
        
        # Transfer to long-term storage
        transferred_count = 0
        for item in important_items:
            try:
                success = await self.long_term_store.store(item)
                if success:
                    transferred_count += 1
            except Exception as e:
                logger.error(f"Failed to transfer memory item {item.id}: {e}")
        
        logger.info(f"Transferred {transferred_count} items to long-term memory")
        self.last_transfer = datetime.now(timezone.utc)
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        return {
            'working_memory': {
                'items': len(self.working_memory.items),
                'task_context': bool(self.working_memory.task_context),
                'active_files': len(self.working_memory.active_files)
            },
            'short_term_memory': {
                'interactions': len(self.short_term_memory.interactions),
                'summaries': len(self.short_term_memory.summaries)
            },
            'long_term_memory': {
                # These would be implemented by the specific store
                'total_items': 'N/A',
                'storage_size': 'N/A'
            },
            'last_transfer': self.last_transfer.isoformat(),
            'transfer_enabled': self.auto_transfer_enabled
        }
    
    def get_working_memory(self) -> WorkingMemory:
        """Get working memory instance"""
        return self.working_memory
    
    def get_short_term_memory(self) -> ShortTermMemory:
        """Get short-term memory instance"""
        return self.short_term_memory
    
    async def clear_working_memory(self):
        """Clear working memory (end of session)"""
        # Store working memory summary before clearing
        summary = self.working_memory.get_summary()
        await self.store_interaction(
            agent_id="system",
            content=f"Session summary: {json.dumps(summary)}",
            memory_type=MemoryType.PROJECT_CONTEXT,
            metadata={'session_summary': True, 'summary_data': summary}
        )
        
        self.working_memory.clear()
    
    async def shutdown(self):
        """Shutdown memory manager and perform final transfer"""
        await self._maybe_transfer_memories()
        await self.clear_working_memory()