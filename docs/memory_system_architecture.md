# CoralCollective Advanced Memory System

## Overview

The CoralCollective Advanced Memory System implements a dual-memory architecture based on the principles from "How to Build an Advanced AI Agent with Summarized Short-Term and Vector-Based Long-Term Memory". This system provides intelligent context management, semantic search, and automatic memory consolidation for CoralCollective agents.

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Memory System                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────┐  │
│  │ Short-Term      │    │ Long-Term Memory                │  │
│  │ Memory          │◄──►│ (Vector Database)               │  │
│  │ - Buffer        │    │ - ChromaDB                      │  │
│  │ - Summarization │    │ - Semantic Search               │  │
│  │ - Working Mem   │    │ - Embeddings                    │  │
│  └─────────────────┘    └─────────────────────────────────┘  │
│           ▲                            ▲                     │
│           │              ┌─────────────┴─────────────┐       │
│           └──────────────│ Memory Orchestrator       │       │
│                          │ - Importance Scoring      │       │
│                          │ - Consolidation Logic     │       │
│                          │ - Attention Mechanism     │       │
│                          └───────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Memory Types

1. **Short-Term Memory**: Recent agent interactions and working context
2. **Long-Term Memory**: Persistent knowledge stored as vector embeddings  
3. **Episodic Memory**: Specific events and milestones
4. **Procedural Memory**: Learned workflows and processes
5. **Semantic Memory**: Domain knowledge and facts

### Importance Levels

- **CRITICAL (5)**: Security issues, errors, deployments
- **HIGH (4)**: Major features, architecture decisions
- **MEDIUM (3)**: Regular development tasks
- **LOW (2)**: Minor updates, routine operations  
- **TRIVIAL (1)**: Temporary notes, debugging

## Key Features

### 1. Dual-Memory Architecture

**Short-Term Memory**:
- Fixed-size buffer (default: 20 items)
- Automatic summarization when buffer overflows
- Working memory for current task context
- Session memory for temporary state

**Long-Term Memory**:
- Vector database storage (ChromaDB)
- Semantic similarity search
- Persistent across sessions
- Automatic embedding generation

### 2. Memory Orchestration

**Intelligent Routing**:
- Automatic decision on short-term vs long-term storage
- Importance-based consolidation
- Time-decay algorithms
- Context-aware retrieval

**Attention Mechanism**:
- Relevance scoring for memory retrieval
- Importance weighting
- Recency biasing
- Query-context matching

### 3. Semantic Search

**Vector Similarity**:
- Embedding-based content matching
- Hybrid search (keyword + semantic)
- Filtering by agent, project, type
- Ranked results with attention weights

**Advanced Queries**:
- Natural language search
- Context-aware retrieval
- Cross-project knowledge sharing
- Temporal filtering

## Implementation

### Core Classes

#### MemoryItem
```python
@dataclass
class MemoryItem:
    id: str
    content: str
    memory_type: MemoryType
    timestamp: datetime
    agent_id: str
    project_id: str
    importance: ImportanceLevel
    context: Dict[str, Any]
    tags: List[str]
    embedding: Optional[List[float]]
```

#### MemorySystem
```python
class MemorySystem:
    def __init__(self, config_path: str = None)
    async def add_memory(self, content: str, agent_id: str, ...)
    async def search_memories(self, query: str, ...)
    async def get_agent_context(self, agent_id: str, ...)
    async def consolidate_memories(self)
```

#### CoralMemoryIntegration
```python
class CoralMemoryIntegration:
    async def record_agent_start(self, agent_id: str, ...)
    async def record_agent_completion(self, agent_id: str, ...)
    async def get_agent_context(self, agent_id: str, ...)
    async def search_project_knowledge(self, query: str, ...)
```

### Database Schema

#### ChromaDB Collections
```
coral_collective_memory/
├── documents/          # Memory content
├── embeddings/         # Vector representations  
├── metadata/          # Structured data
│   ├── agent_id       # Agent identifier
│   ├── project_id     # Project identifier
│   ├── memory_type    # Type classification
│   ├── importance     # Importance level
│   ├── timestamp      # Creation time
│   └── tags           # Classification tags
└── ids/               # Unique identifiers
```

#### Metadata Schema
```json
{
  "agent_id": "string",
  "project_id": "string", 
  "memory_type": "short_term|long_term|episodic|procedural|semantic",
  "importance": "1|2|3|4|5",
  "timestamp": "ISO-8601",
  "tags": "comma,separated,tags",
  "access_count": "integer",
  "context": "JSON serialized context data"
}
```

## Configuration

### Memory Configuration File
```json
{
  "short_term": {
    "buffer_size": 25,
    "max_tokens": 10000
  },
  "long_term": {
    "type": "chroma",
    "collection_name": "coral_memory_project",
    "persist_directory": "./memory/chroma_db"
  },
  "orchestrator": {
    "consolidation_threshold": 0.6,
    "importance_decay_hours": 48
  },
  "summarizer": {
    "max_summary_length": 500
  }
}
```

### Environment Variables
```bash
# Optional: Advanced embedding models
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Memory system settings
CORAL_MEMORY_LOG_LEVEL=INFO
CORAL_MEMORY_PERSIST_DIR=./memory/db
```

## Usage

### Basic Setup
```python
from memory import setup_memory_for_project

# Initialize memory for project
memory_integration = await setup_memory_for_project(
    project_path="/path/to/project",
    auto_migrate=True
)
```

### Agent Integration
```python
from memory import MemoryEnhancedAgentRunner

# Create memory-enhanced runner
runner = MemoryEnhancedAgentRunner(enable_memory=True)

# Run agent with memory context
result = await runner.run_agent_with_memory(
    agent_id="backend_developer",
    task="Create API endpoints"
)
```

### Memory Operations
```python
# Add memory
memory_id = await memory_system.add_memory(
    content="API endpoints created successfully",
    agent_id="backend_developer",
    project_id="ecommerce_app",
    context={"endpoints": ["users", "products"]},
    tags=["api", "backend"]
)

# Search memories
results = await memory_system.search_memories(
    query="API endpoints",
    agent_id="backend_developer",
    limit=10
)

# Get agent context
context = await memory_system.get_agent_context("frontend_developer")
```

### MCP Integration
```python
# Memory MCP server provides external access
from mcp.servers.memory_server import create_memory_server

server = create_memory_server("/path/to/project")
await server.initialize()
```

## Migration Strategy

### Automatic Migration

The system automatically migrates existing CoralCollective project state:

1. **Backup Creation**: Preserves original project state
2. **Agent Activities**: Converts completed agents to episodic memories
3. **Handoffs**: Records agent transitions as memories
4. **Artifacts**: Stores created files as semantic memories
5. **Context**: Preserves shared project context

### Migration Process
```python
from memory.migration_strategy import run_migration

# Run migration
report = await run_migration(
    project_path="/path/to/project",
    preserve_existing=True
)

# Validate migration
from memory.migration_strategy import MemorySystemValidator
validator = MemorySystemValidator(memory_integration)
validation = await validator.validate_migration()
```

## Performance Considerations

### Memory Optimization

1. **Buffer Management**: Automatic pruning when limits exceeded
2. **Vector Storage**: Efficient ChromaDB persistence
3. **Query Optimization**: Attention-weighted search results
4. **Background Tasks**: Async consolidation and cleanup

### Scalability

- **Project Isolation**: Separate memory spaces per project
- **Incremental Loading**: On-demand memory retrieval
- **Configurable Limits**: Adjustable buffer sizes and thresholds
- **Cleanup Policies**: Automatic removal of old, low-importance memories

### Monitoring

```python
# Memory statistics
stats = memory_system.get_memory_stats()
print(f"Short-term: {stats['short_term_memories']}")
print(f"Long-term: {stats['long_term_memories']}")

# Export for analysis
export_path = await memory_integration.export_project_memory()
```

## Advanced Features

### 1. Episodic Memory

Tracks project milestones and significant events:
- Agent handoffs
- Phase transitions  
- Error occurrences
- Deployment events

### 2. Procedural Memory

Learns from agent workflows:
- Successful agent sequences
- Common task patterns
- Error recovery procedures
- Optimization strategies

### 3. Cross-Project Learning

Shares knowledge across projects:
- Architecture patterns
- Common solutions
- Best practices
- Reusable components

### 4. Memory Decay

Implements forgetting mechanisms:
- Time-based importance decay
- Access frequency weighting
- Relevance scoring
- Automatic cleanup

## Integration Points

### 1. Agent Runner Integration
- Enhanced prompts with memory context
- Automatic memory recording
- Context-aware agent selection
- Performance tracking

### 2. MCP Server Integration
- External tool access to memory
- Real-time memory operations  
- Cross-system memory sharing
- API-based memory management

### 3. Project State Integration
- Seamless migration from existing state
- Backward compatibility
- Dual-tracking during transition
- Validation and rollback capabilities

## Best Practices

### 1. Memory Hygiene
- Regular consolidation runs
- Periodic cleanup of old memories
- Importance level calibration
- Tag standardization

### 2. Query Optimization
- Specific rather than broad queries
- Use filters to narrow results
- Leverage tag-based organization
- Monitor query performance

### 3. Context Management
- Maintain session boundaries
- Clear working memory between tasks  
- Use appropriate memory types
- Document context structure

### 4. Performance Monitoring
- Track memory growth rates
- Monitor search performance
- Analyze consolidation efficiency
- Optimize configuration parameters

## Troubleshooting

### Common Issues

1. **Memory Growth**: Adjust buffer sizes and cleanup policies
2. **Search Performance**: Optimize embeddings and indexing
3. **Migration Errors**: Check backup integrity and validation
4. **Context Overflow**: Implement better summarization

### Debug Commands
```bash
# Check memory status
python -m memory.memory_enhanced_runner status

# Search memory
python -m memory.memory_enhanced_runner search --query "API endpoints"

# Export memory
python -m memory.memory_enhanced_runner export --output memory_dump.json

# Validate migration
python -m memory.migration_strategy /path/to/project --validate-only
```

## Future Enhancements

1. **Multi-Modal Memory**: Support for images, diagrams, code
2. **Federated Learning**: Cross-team knowledge sharing
3. **Active Learning**: Memory-guided agent improvement
4. **Real-Time Collaboration**: Shared memory spaces
5. **Advanced Analytics**: Memory usage insights and optimization

---

This advanced memory system transforms CoralCollective into a truly intelligent, context-aware agent orchestration platform that learns and improves over time.