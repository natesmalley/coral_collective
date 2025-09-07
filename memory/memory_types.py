"""
Memory Type Definitions for CoralCollective

Comprehensive data structures for the advanced memory system including
memory types, queries, metadata, and interaction patterns.
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple
import json


class MemoryType(Enum):
    """Comprehensive memory type enumeration for different contexts"""
    
    # Core memory types
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    
    # Episodic memory types (events and interactions)
    AGENT_INTERACTION = "agent_interaction"
    AGENT_HANDOFF = "agent_handoff"
    AGENT_START = "agent_start"
    AGENT_COMPLETION = "agent_completion"
    USER_INTERACTION = "user_interaction"
    SYSTEM_EVENT = "system_event"
    
    # Semantic memory types (knowledge and facts)
    PROJECT_CONTEXT = "project_context"
    REQUIREMENT = "requirement"
    SPECIFICATION = "specification"
    ARCHITECTURE_DECISION = "architecture_decision"
    DESIGN_PATTERN = "design_pattern"
    
    # Procedural memory types (how-to knowledge)
    CODE_PATTERN = "code_pattern"
    SOLUTION_TEMPLATE = "solution_template"
    WORKFLOW_STEP = "workflow_step"
    BEST_PRACTICE = "best_practice"
    
    # Error and problem-solving memory
    ERROR_SOLUTION = "error_solution"
    BUG_FIX = "bug_fix"
    TROUBLESHOOTING = "troubleshooting"
    LESSONS_LEARNED = "lessons_learned"
    
    # Project artifacts and outputs
    CODE_ARTIFACT = "code_artifact"
    DOCUMENTATION = "documentation"
    TEST_CASE = "test_case"
    DEPLOYMENT_CONFIG = "deployment_config"
    
    # Meta-memory (memory about memory)
    SUMMARY = "summary"
    CONSOLIDATION = "consolidation"
    MEMORY_STATS = "memory_stats"


class ImportanceLevel(Enum):
    """Memory importance levels for prioritization"""
    CRITICAL = 5  # Must never be forgotten
    HIGH = 4      # Very important, keep long-term
    MEDIUM = 3    # Moderately important
    LOW = 2       # Keep short-term, may consolidate
    TRIVIAL = 1   # Can be discarded quickly


class AccessPattern(Enum):
    """Memory access patterns for optimization"""
    FREQUENT = "frequent"      # Accessed regularly
    OCCASIONAL = "occasional"  # Accessed sometimes
    RARE = "rare"             # Rarely accessed
    ARCHIVE = "archive"       # Historical, rarely needed


class MemoryStatus(Enum):
    """Memory lifecycle status"""
    ACTIVE = "active"         # Currently relevant
    CONSOLIDATED = "consolidated"  # Has been summarized
    ARCHIVED = "archived"     # Moved to long-term storage
    EXPIRED = "expired"       # Should be cleaned up
    DELETED = "deleted"       # Marked for deletion


@dataclass
class MemoryMetadata:
    """Comprehensive metadata for memory items"""
    
    # Core metadata
    source: str = "unknown"                    # Source of the memory
    confidence: float = 1.0                    # Confidence in accuracy (0-1)
    verified: bool = False                     # Has been verified/validated
    
    # Context metadata
    session_id: Optional[str] = None           # Session when created
    conversation_id: Optional[str] = None      # Conversation context
    workflow_stage: Optional[str] = None       # Stage in workflow
    project_phase: Optional[str] = None        # Project development phase
    
    # Relationship metadata
    parent_ids: List[str] = field(default_factory=list)      # Parent memories
    child_ids: List[str] = field(default_factory=list)       # Child memories
    related_ids: List[str] = field(default_factory=list)     # Related memories
    references: List[str] = field(default_factory=list)      # External references
    
    # Usage metadata
    access_pattern: AccessPattern = AccessPattern.OCCASIONAL
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    success_rate: Optional[float] = None       # For solution patterns
    
    # Technical metadata
    embedding_model: Optional[str] = None      # Model used for embeddings
    embedding_version: Optional[str] = None    # Version of embeddings
    token_count: Optional[int] = None          # Token count if relevant
    
    # Agent-specific metadata
    agent_success: Optional[bool] = None       # Did agent succeed with this?
    agent_feedback: Optional[str] = None       # Agent's feedback on memory
    human_feedback: Optional[str] = None       # Human feedback if any
    
    # Custom fields for extensions
    custom: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        if self.last_accessed:
            data['last_accessed'] = self.last_accessed.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryMetadata':
        """Create from dictionary"""
        # Handle datetime conversion
        if 'last_accessed' in data and data['last_accessed']:
            data['last_accessed'] = datetime.fromisoformat(data['last_accessed'])
        
        # Handle enum conversion
        if 'access_pattern' in data:
            data['access_pattern'] = AccessPattern(data['access_pattern'])
            
        return cls(**data)


@dataclass
class MemoryItem:
    """Core memory item with comprehensive metadata"""
    
    # Core fields
    id: str
    content: str
    memory_type: MemoryType
    timestamp: datetime
    
    # Identity fields
    agent_id: str
    project_id: str
    user_id: Optional[str] = None
    
    # Importance and classification
    importance: ImportanceLevel = ImportanceLevel.MEDIUM
    tags: List[str] = field(default_factory=list)
    status: MemoryStatus = MemoryStatus.ACTIVE
    
    # Vector storage
    embedding: Optional[List[float]] = None
    embedding_hash: Optional[str] = None
    
    # Content metadata
    summary: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)  # Named entities
    
    # Detailed metadata
    metadata: MemoryMetadata = field(default_factory=MemoryMetadata)
    
    # Computed fields (not stored)
    relevance_score: Optional[float] = field(default=None, init=False)
    attention_weight: Optional[float] = field(default=None, init=False)
    
    def __post_init__(self):
        """Post-initialization processing"""
        # Ensure timestamp has timezone
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)
        
        # Generate embedding hash if embedding exists
        if self.embedding and not self.embedding_hash:
            self.embedding_hash = self._compute_embedding_hash()
        
        # Initialize access tracking
        if not self.metadata.last_accessed:
            self.metadata.last_accessed = self.timestamp
    
    def _compute_embedding_hash(self) -> str:
        """Compute hash of embedding for deduplication"""
        import hashlib
        embedding_str = json.dumps(self.embedding, sort_keys=True)
        return hashlib.sha256(embedding_str.encode()).hexdigest()[:16]
    
    def access(self):
        """Record access to this memory"""
        self.metadata.access_count += 1
        self.metadata.last_accessed = datetime.now(timezone.utc)
        
        # Update access pattern based on frequency
        if self.metadata.access_count > 10:
            self.metadata.access_pattern = AccessPattern.FREQUENT
        elif self.metadata.access_count > 3:
            self.metadata.access_pattern = AccessPattern.OCCASIONAL
    
    def add_relationship(self, other_id: str, relationship_type: str = "related"):
        """Add relationship to another memory"""
        if relationship_type == "parent":
            if other_id not in self.metadata.parent_ids:
                self.metadata.parent_ids.append(other_id)
        elif relationship_type == "child":
            if other_id not in self.metadata.child_ids:
                self.metadata.child_ids.append(other_id)
        else:
            if other_id not in self.metadata.related_ids:
                self.metadata.related_ids.append(other_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        
        # Convert enums to strings
        data['memory_type'] = self.memory_type.value
        data['importance'] = self.importance.value
        data['status'] = self.status.value
        
        # Convert datetime
        data['timestamp'] = self.timestamp.isoformat()
        
        # Convert metadata
        data['metadata'] = self.metadata.to_dict()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        """Create from dictionary"""
        # Handle enum conversions
        data['memory_type'] = MemoryType(data['memory_type'])
        data['importance'] = ImportanceLevel(data['importance'])
        if 'status' in data:
            data['status'] = MemoryStatus(data['status'])
        
        # Handle datetime
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        # Handle metadata
        if 'metadata' in data and isinstance(data['metadata'], dict):
            data['metadata'] = MemoryMetadata.from_dict(data['metadata'])
        
        return cls(**data)
    
    def get_age_hours(self) -> float:
        """Get age of memory in hours"""
        return (datetime.now(timezone.utc) - self.timestamp).total_seconds() / 3600
    
    def is_expired(self, ttl_hours: int = 168) -> bool:  # Default 1 week
        """Check if memory has expired"""
        return self.get_age_hours() > ttl_hours
    
    def calculate_importance_score(self) -> float:
        """Calculate normalized importance score (0-1)"""
        base_score = self.importance.value / 5.0  # Normalize to 0-1
        
        # Boost for frequent access
        access_boost = min(0.2, self.metadata.access_count * 0.01)
        
        # Boost for successful patterns
        success_boost = 0.1 if self.metadata.success_rate and self.metadata.success_rate > 0.8 else 0
        
        # Penalty for age (exponential decay)
        age_penalty = max(0, min(0.3, self.get_age_hours() / 720))  # 30 days max penalty
        
        final_score = base_score + access_boost + success_boost - age_penalty
        return max(0.0, min(1.0, final_score))


@dataclass
class MemoryQuery:
    """Query object for memory retrieval"""
    
    # Core query
    query: str
    query_type: str = "semantic"  # semantic, keyword, hybrid, contextual
    
    # Filtering
    agent_id: Optional[str] = None
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    memory_types: Optional[List[MemoryType]] = None
    tags: Optional[List[str]] = None
    
    # Importance and quality filters
    min_importance: ImportanceLevel = ImportanceLevel.LOW
    max_importance: Optional[ImportanceLevel] = None
    min_confidence: float = 0.0
    verified_only: bool = False
    
    # Time-based filters
    time_range: Optional[Tuple[datetime, datetime]] = None
    max_age_hours: Optional[float] = None
    
    # Result configuration
    max_results: int = 10
    include_archived: bool = False
    exclude_expired: bool = True
    
    # Search configuration
    similarity_threshold: float = 0.7
    use_semantic_search: bool = True
    use_keyword_search: bool = True
    semantic_weight: float = 0.7
    keyword_weight: float = 0.3
    
    # Context for query expansion
    context: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """Validate query parameters"""
        if not self.query and not self.agent_id and not self.project_id:
            return False
        
        if self.semantic_weight + self.keyword_weight != 1.0:
            # Auto-normalize weights
            total = self.semantic_weight + self.keyword_weight
            if total > 0:
                self.semantic_weight /= total
                self.keyword_weight /= total
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        
        # Convert enums
        if self.memory_types:
            data['memory_types'] = [mt.value for mt in self.memory_types]
        data['min_importance'] = self.min_importance.value
        if self.max_importance:
            data['max_importance'] = self.max_importance.value
        
        # Convert time range
        if self.time_range:
            data['time_range'] = [dt.isoformat() for dt in self.time_range]
        
        return data


@dataclass
class WorkingMemory:
    """Working memory for current context and active tasks"""
    
    # Current context
    current_agent: Optional[str] = None
    current_task: Optional[str] = None
    current_phase: Optional[str] = None
    
    # Active state
    active_files: List[str] = field(default_factory=list)
    active_variables: Dict[str, Any] = field(default_factory=dict)
    pending_actions: List[str] = field(default_factory=list)
    
    # Context buffer
    recent_interactions: List[str] = field(default_factory=list)
    context_buffer: Dict[str, Any] = field(default_factory=dict)
    
    # Task context
    task_context: Dict[str, Any] = field(default_factory=dict)
    project_context: Dict[str, Any] = field(default_factory=dict)
    
    def update_context(self, key: str, value: Any):
        """Update working memory context"""
        self.context_buffer[key] = {
            'value': value,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'ttl': 3600  # 1 hour default TTL
        }
    
    def get_context(self, key: str) -> Optional[Any]:
        """Get context value if not expired"""
        if key not in self.context_buffer:
            return None
        
        entry = self.context_buffer[key]
        timestamp = datetime.fromisoformat(entry['timestamp'])
        ttl_seconds = entry.get('ttl', 3600)
        
        if (datetime.now(timezone.utc) - timestamp).total_seconds() > ttl_seconds:
            # Expired, remove it
            del self.context_buffer[key]
            return None
        
        return entry['value']
    
    def add_file(self, file_path: str):
        """Add file to active files, maintaining recency"""
        if file_path in self.active_files:
            self.active_files.remove(file_path)
        
        self.active_files.insert(0, file_path)
        
        # Keep only recent files
        if len(self.active_files) > 20:
            self.active_files = self.active_files[:20]
    
    def clear_expired_context(self):
        """Clear expired context entries"""
        expired_keys = []
        current_time = datetime.now(timezone.utc)
        
        for key, entry in self.context_buffer.items():
            timestamp = datetime.fromisoformat(entry['timestamp'])
            ttl_seconds = entry.get('ttl', 3600)
            
            if (current_time - timestamp).total_seconds() > ttl_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.context_buffer[key]


@dataclass
class MemoryOperationResult:
    """Result of memory operations"""
    
    success: bool
    message: str
    data: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: Optional[float] = None
    
    # For search operations
    total_results: Optional[int] = None
    filtered_results: Optional[int] = None
    search_strategies_used: List[str] = field(default_factory=list)
    
    # For storage operations
    memory_id: Optional[str] = None
    storage_location: Optional[str] = None
    
    @classmethod
    def success_result(cls, message: str, data: Any = None, **kwargs) -> 'MemoryOperationResult':
        """Create success result"""
        return cls(success=True, message=message, data=data, **kwargs)
    
    @classmethod
    def error_result(cls, message: str, **kwargs) -> 'MemoryOperationResult':
        """Create error result"""
        return cls(success=False, message=message, **kwargs)


# Memory storage interfaces

class MemoryStorage(ABC):
    """Abstract base class for memory storage backends"""
    
    @abstractmethod
    async def store(self, memory: MemoryItem) -> MemoryOperationResult:
        """Store a memory item"""
        pass
    
    @abstractmethod
    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve a memory by ID"""
        pass
    
    @abstractmethod
    async def search(self, query: MemoryQuery) -> List[MemoryItem]:
        """Search for memories"""
        pass
    
    @abstractmethod
    async def update(self, memory_id: str, updates: Dict[str, Any]) -> MemoryOperationResult:
        """Update a memory item"""
        pass
    
    @abstractmethod
    async def delete(self, memory_id: str) -> MemoryOperationResult:
        """Delete a memory item"""
        pass
    
    @abstractmethod
    async def list_by_criteria(self, **criteria) -> List[MemoryItem]:
        """List memories by criteria"""
        pass


# Utility functions for memory management

def generate_memory_id(content: str, agent_id: str, timestamp: datetime = None) -> str:
    """Generate a unique memory ID based on content and context"""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    
    # Create deterministic ID based on content hash and context
    import hashlib
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    timestamp_str = timestamp.strftime('%Y%m%d%H%M%S')
    
    return f"mem_{agent_id}_{timestamp_str}_{content_hash}"


def create_memory_from_interaction(
    agent_id: str,
    content: str,
    project_id: str,
    interaction_type: str = "general",
    importance: ImportanceLevel = ImportanceLevel.MEDIUM,
    tags: List[str] = None,
    context: Dict[str, Any] = None
) -> MemoryItem:
    """Create a memory item from an agent interaction"""
    
    # Determine memory type based on interaction type
    memory_type_mapping = {
        'start': MemoryType.AGENT_START,
        'completion': MemoryType.AGENT_COMPLETION,
        'handoff': MemoryType.AGENT_HANDOFF,
        'error': MemoryType.ERROR_SOLUTION,
        'code': MemoryType.CODE_ARTIFACT,
        'general': MemoryType.AGENT_INTERACTION
    }
    
    memory_type = memory_type_mapping.get(interaction_type, MemoryType.AGENT_INTERACTION)
    timestamp = datetime.now(timezone.utc)
    
    # Create metadata
    metadata = MemoryMetadata(
        source=f"agent_{agent_id}",
        session_id=context.get('session_id') if context else None,
        workflow_stage=context.get('workflow_stage') if context else None,
        project_phase=context.get('project_phase') if context else None,
        custom=context or {}
    )
    
    # Generate memory
    memory = MemoryItem(
        id=generate_memory_id(content, agent_id, timestamp),
        content=content,
        memory_type=memory_type,
        timestamp=timestamp,
        agent_id=agent_id,
        project_id=project_id,
        importance=importance,
        tags=tags or [],
        metadata=metadata
    )
    
    return memory


def extract_keywords_from_content(content: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from content using simple NLP techniques"""
    import re
    from collections import Counter
    
    # Simple keyword extraction
    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'this', 'that', 'these', 'those', 'is', 'are',
        'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
        'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
        'i', 'you', 'he', 'she', 'it', 'we', 'they'
    }
    
    # Extract words (alphanumeric + common programming terms)
    words = re.findall(r'\b(?:[a-zA-Z]+(?:[_-][a-zA-Z]+)*|[A-Z]{2,})\b', content.lower())
    
    # Filter meaningful words
    filtered_words = [
        word for word in words 
        if len(word) > 2 and word not in stop_words
    ]
    
    # Get most common
    word_counts = Counter(filtered_words)
    return [word for word, count in word_counts.most_common(max_keywords)]


def classify_memory_importance(
    content: str,
    context: Dict[str, Any] = None,
    agent_id: str = None
) -> ImportanceLevel:
    """Classify memory importance based on content and context"""
    
    context = context or {}
    content_lower = content.lower()
    
    # Critical indicators
    critical_indicators = [
        'error', 'critical', 'security', 'production', 'failure',
        'urgent', 'emergency', 'broken', 'down', 'outage'
    ]
    
    # High importance indicators
    high_indicators = [
        'complete', 'deploy', 'release', 'launch', 'implement',
        'architecture', 'design', 'requirement', 'specification',
        'milestone', 'deadline', 'handoff'
    ]
    
    # Check for critical patterns
    if any(indicator in content_lower for indicator in critical_indicators):
        return ImportanceLevel.CRITICAL
    
    # Check context for importance signals
    if context.get('project_milestone'):
        return ImportanceLevel.CRITICAL
    
    if context.get('agent_handoff'):
        return ImportanceLevel.HIGH
    
    # Check for high importance patterns
    if any(indicator in content_lower for indicator in high_indicators):
        return ImportanceLevel.HIGH
    
    # Length-based importance (longer content often more important)
    if len(content) > 1000:
        return ImportanceLevel.MEDIUM
    elif len(content) > 200:
        return ImportanceLevel.LOW
    else:
        return ImportanceLevel.TRIVIAL