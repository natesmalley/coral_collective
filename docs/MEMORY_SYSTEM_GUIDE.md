# CoralCollective Advanced Memory System Guide

## Overview

The CoralCollective Advanced Memory System implements a sophisticated dual-memory architecture that enhances agent workflows with persistent context, semantic search, and intelligent memory consolidation. This system is designed to work seamlessly with Claude Code and provides comprehensive memory capabilities for multi-agent software development projects.

## Architecture

### Dual-Memory Design

1. **Short-Term Memory**
   - Buffer-based storage for recent interactions
   - Automatic summarization when buffer limits are reached
   - Session and working memory management
   - Token-aware content management

2. **Long-Term Memory**
   - Vector embeddings with ChromaDB storage
   - Semantic search capabilities
   - Persistent storage across sessions
   - Automatic consolidation from short-term memory

3. **Memory Orchestrator**
   - Intelligent routing between memory types
   - Importance scoring and attention mechanisms
   - Consolidation logic based on age and importance
   - Context-aware memory management

## Key Features

### 🧠 Intelligent Memory Management
- **Automatic Importance Scoring**: Content is automatically scored for importance based on keywords, context, and agent activities
- **Attention Mechanism**: Relevant memories are weighted and prioritized based on query similarity and context
- **Memory Consolidation**: Important memories are automatically moved to long-term storage

### 🔍 Semantic Search
- **Vector Embeddings**: Content is converted to embeddings for semantic similarity search
- **Multi-Modal Search**: Search across different memory types and agent activities
- **Context-Aware Results**: Search results are ranked by relevance and importance

### 🔄 Agent Integration
- **Seamless Workflow Integration**: Memory-enhanced agent runner provides transparent memory operations
- **Agent Context**: Each agent receives relevant historical context before execution
- **Handoff Tracking**: Agent handoffs are automatically recorded and tracked

### 📊 Project Timeline
- **Activity Tracking**: Complete timeline of project activities and agent interactions
- **Memory Export**: Export project memory for analysis and archival
- **Migration Support**: Automatic migration from existing CoralCollective project states

## Installation and Setup

### Prerequisites

- Python 3.8+
- CoralCollective installed and configured
- ChromaDB and related dependencies

### Quick Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Setup Script**
   ```bash
   python setup_memory_system.py
   ```

3. **Verify Installation**
   ```bash
   python setup_memory_system.py --validate-only
   ```

### Manual Setup

1. **Install Memory Dependencies**
   ```bash
   pip install chromadb>=0.4.15 sentence-transformers>=2.2.0 numpy>=1.24.0
   ```

2. **Create Memory Configuration**
   ```python
   from memory.coral_memory_integration import create_memory_config
   from pathlib import Path
   
   project_path = Path(".")
   config_path = create_memory_config(project_path)
   print(f"Memory configuration created at: {config_path}")
   ```

3. **Initialize Memory System**
   ```python
   from memory.coral_memory_integration import initialize_project_memory
   
   memory_integration = await initialize_project_memory(project_path)
   print("Memory system initialized successfully")
   ```

## Usage Examples

### Basic Memory Operations

```python
import asyncio
from memory.memory_system import MemorySystem, MemoryType, ImportanceLevel

# Initialize memory system
memory_system = MemorySystem("path/to/memory_config.json")

# Add memory
memory_id = await memory_system.add_memory(
    content="Implemented user authentication API endpoint",
    agent_id="backend_developer",
    project_id="my_project",
    context={"type": "implementation", "module": "auth"},
    tags=["api", "authentication", "backend"],
    memory_type=MemoryType.SEMANTIC
)

# Search memories
results = await memory_system.search_memories(
    query="authentication API",
    limit=10
)

for memory in results:
    print(f"[{memory.timestamp}] {memory.agent_id}: {memory.content}")
```

### Agent Integration

```python
from memory.memory_enhanced_runner import MemoryEnhancedAgentRunner

# Create memory-enhanced runner
runner = MemoryEnhancedAgentRunner(enable_memory=True)

# Run agent with memory context
result = await runner.run_agent_with_memory(
    agent_id="backend_developer",
    task="Create REST API with authentication",
    context={"priority": "high", "deadline": "2024-01-15"}
)

print(f"Agent execution result: {result}")
print(f"Memory IDs: {result.get('memory_ids', {})}")
```

### Memory Search and Context

```python
from memory.coral_memory_integration import CoralMemoryIntegration

# Initialize integration
integration = CoralMemoryIntegration(project_path=Path("."))

# Search project knowledge
knowledge = await integration.search_project_knowledge(
    query="API authentication implementation",
    limit=5
)

# Get agent context
context = await integration.get_agent_context(
    agent_id="backend_developer",
    include_history=True
)

print("Recent memories:")
for memory in context["memory_context"]["recent_memories"]:
    print(f"  - {memory['content'][:100]}...")
    
print(f"Working memory: {context['memory_context']['working_memory']}")
```

### Project Timeline

```python
# Get project timeline
timeline = await integration.get_project_timeline(limit=20)

print("Project Timeline:")
for event in timeline:
    print(f"[{event['timestamp'][:19]}] {event['agent_id']}: {event['content'][:80]}...")
```

### Memory Export

```python
# Export project memory
export_path = await integration.export_project_memory()
print(f"Project memory exported to: {export_path}")

# Export with custom path
custom_path = await integration.export_project_memory(
    output_path=Path("./exports/project_memory_backup.json")
)
```

## Memory-Enhanced Agent Runner

The memory-enhanced agent runner provides a drop-in replacement for the standard CoralCollective agent runner with full memory integration.

### CLI Usage

```bash
# Run single agent with memory
python -m memory.memory_enhanced_runner run --agent-id backend_developer --task "Create API"

# Run workflow with memory tracking
python -m memory.memory_enhanced_runner workflow --workflow full_stack

# Search project memory
python -m memory.memory_enhanced_runner search --query "API authentication"

# View memory statistics
python -m memory.memory_enhanced_runner status

# Export project memory
python -m memory.memory_enhanced_runner export --output ./memory_export.json
```

### Python API

```python
from memory.memory_enhanced_runner import create_memory_enhanced_runner

# Create runner
runner = create_memory_enhanced_runner(enable_memory=True, auto_migrate=True)

# Run workflow with memory
result = await runner.run_workflow_with_memory(
    workflow_name="full_stack_development",
    context={"project_type": "web_app", "framework": "react"}
)

# Check memory statistics
stats = runner.get_memory_stats()
print(f"Short-term memories: {stats['short_term_memories']}")
print(f"Long-term memories: {stats['long_term_memories']}")
```

## MCP (Model Context Protocol) Integration

The memory system provides MCP server integration for external tool access.

### Available MCP Tools

1. **add_memory** - Add new memory to the system
2. **search_memories** - Search memories using semantic search
3. **get_agent_context** - Get comprehensive context for an agent
4. **record_agent_start** - Record agent start with memory tracking
5. **record_agent_completion** - Record agent completion
6. **get_project_timeline** - Get chronological project timeline
7. **search_project_knowledge** - Search project knowledge base
8. **get_memory_stats** - Get memory system statistics
9. **consolidate_memory** - Perform memory consolidation
10. **export_project_memory** - Export project memory

### MCP Server Setup

```python
from mcp.servers.memory_server import create_memory_server

# Create MCP server
server = create_memory_server(project_path="./my_project")
await server.initialize()

# Server will be available for MCP client connections
```

### MCP Client Usage

```python
from mcp.client import MCPClient

client = MCPClient()

# Add memory via MCP
result = await client.call_tool("add_memory", {
    "content": "User authentication implemented",
    "agent_id": "backend_developer",
    "context": {"type": "implementation"},
    "tags": ["auth", "backend"]
})

# Search memories via MCP
search_result = await client.call_tool("search_memories", {
    "query": "authentication",
    "limit": 10
})
```

## Configuration

### Memory Configuration File

The memory system uses a JSON configuration file (`.coral/memory_config.json`) with the following structure:

```json
{
  "short_term": {
    "buffer_size": 25,
    "max_tokens": 10000
  },
  "long_term": {
    "type": "chroma",
    "collection_name": "coral_memory_project_name",
    "persist_directory": "./.coral/memory/chroma_db"
  },
  "orchestrator": {
    "short_term_limit": 25,
    "consolidation_threshold": 0.6,
    "importance_decay_hours": 48
  },
  "summarizer": {
    "max_summary_length": 500,
    "preserve_critical_info": true
  }
}
```

### Configuration Parameters

#### Short-Term Memory
- **buffer_size**: Maximum number of memories in short-term buffer
- **max_tokens**: Maximum token limit for short-term content

#### Long-Term Memory
- **type**: Vector storage type (currently supports "chroma")
- **collection_name**: ChromaDB collection name
- **persist_directory**: Directory for persistent storage

#### Orchestrator
- **short_term_limit**: Buffer size before consolidation triggers
- **consolidation_threshold**: Importance threshold for long-term storage
- **importance_decay_hours**: Hours after which importance decays

#### Summarizer
- **max_summary_length**: Maximum length for memory summaries
- **preserve_critical_info**: Whether to preserve critical information during summarization

## Migration from Existing Projects

The memory system includes automatic migration from existing CoralCollective project states.

### Automatic Migration

```python
from memory.migration_strategy import MemoryMigrationStrategy

# Create migration instance
migration = MemoryMigrationStrategy(project_path=Path("."))

# Run migration
report = await migration.migrate_project(preserve_existing=True)

print(f"Migration completed: {report['success']}")
print(f"Migrated items: {report['migrated_items']}")
if report['errors']:
    print(f"Errors: {report['errors']}")
```

### Migration Report

The migration process generates a comprehensive report:

```json
{
  "project_name": "my_project",
  "migration_timestamp": "2024-01-01T10:00:00",
  "migrated_items": {
    "agent_activities": 12,
    "handoffs": 3,
    "artifacts": 8,
    "shared_context": 1
  },
  "errors": [],
  "statistics": {
    "original_project_stats": {...},
    "new_memory_stats": {...},
    "migration_efficiency": {...}
  }
}
```

### Rollback Support

```python
# Rollback migration if needed
success = await migration.rollback_migration()
if success:
    print("Migration rolled back successfully")
else:
    print("Rollback failed")
```

## Performance Considerations

### Memory Management
- Short-term buffer automatically prunes old memories
- Long-term storage uses efficient vector indexing
- Memory consolidation runs in background
- Configurable importance thresholds

### Search Performance
- Vector embeddings enable fast semantic search
- Results are cached for repeated queries
- Attention weights improve relevance ranking
- Configurable result limits

### Storage Efficiency
- ChromaDB provides compressed vector storage
- Automatic cleanup of low-importance memories
- Configurable retention policies
- Export capabilities for archival

## Troubleshooting

### Common Issues

1. **ChromaDB Installation Issues**
   ```bash
   # Install with specific version
   pip install chromadb==0.4.15
   
   # For M1 Macs, use conda
   conda install -c conda-forge chromadb
   ```

2. **Memory Configuration Not Found**
   ```python
   # Recreate configuration
   from memory.coral_memory_integration import create_memory_config
   config_path = create_memory_config(Path("."))
   ```

3. **Migration Errors**
   ```python
   # Check project state file
   state_file = Path("./.coral/project_state.yaml")
   if not state_file.exists():
       print("No project state to migrate")
   
   # Run validation
   from memory.migration_strategy import MemorySystemValidator
   validator = MemorySystemValidator(memory_integration)
   report = await validator.validate_migration()
   ```

4. **Memory Search Not Working**
   ```python
   # Check if memories exist
   stats = memory_system.get_memory_stats()
   print(f"Total memories: {stats}")
   
   # Test with simple query
   results = await memory_system.search_memories("", limit=5)
   print(f"Found {len(results)} memories")
   ```

### Debug Mode

Enable debug logging for detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Memory operations will now log detailed information
```

### Performance Monitoring

```python
# Get memory statistics
stats = memory_system.get_memory_stats()
print(f"Memory usage: {stats}")

# Monitor search performance
import time
start_time = time.time()
results = await memory_system.search_memories("query")
search_time = time.time() - start_time
print(f"Search took {search_time:.2f} seconds")
```

## Best Practices

### Memory Content Guidelines
1. **Use Descriptive Content**: Write clear, searchable memory content
2. **Include Context**: Provide relevant context for better understanding
3. **Use Appropriate Tags**: Tag memories for easier filtering and search
4. **Set Proper Importance**: Use importance levels to guide consolidation

### Agent Integration
1. **Regular Context Updates**: Update agent context before major decisions
2. **Record Handoffs**: Always record agent handoffs with relevant data
3. **Use Memory Search**: Search existing memories before starting new work
4. **Export Regularly**: Export memory for backup and analysis

### Performance Optimization
1. **Configure Buffer Sizes**: Adjust buffer sizes based on project needs
2. **Set Consolidation Thresholds**: Balance memory size with retention needs
3. **Use Appropriate Search Limits**: Limit search results for better performance
4. **Clean Up Periodically**: Remove old, irrelevant memories

### Security Considerations
1. **Sensitive Information**: Avoid storing sensitive data in memory
2. **Access Controls**: Implement proper access controls for memory operations
3. **Data Retention**: Follow data retention policies for your organization
4. **Export Security**: Secure exported memory files appropriately

## API Reference

For complete API documentation, see the individual module documentation:

- [`memory.memory_system`](./memory/memory_system.py) - Core memory system classes
- [`memory.coral_memory_integration`](./memory/coral_memory_integration.py) - CoralCollective integration
- [`memory.memory_enhanced_runner`](./memory/memory_enhanced_runner.py) - Memory-enhanced agent runner
- [`memory.migration_strategy`](./memory/migration_strategy.py) - Migration and validation
- [`mcp.servers.memory_server`](./mcp/servers/memory_server.py) - MCP server implementation

## Support and Contributing

For issues, feature requests, and contributions, please see the main CoralCollective repository.

### Testing

Run the memory system tests:

```bash
# Run all memory tests
pytest tests/test_memory_system.py -v

# Run integration tests (requires ChromaDB)
pytest tests/test_memory_system.py::TestFullMemorySystemIntegration -v

# Run performance tests
pytest tests/test_memory_system.py -m performance
```

### Contributing

When contributing to the memory system:

1. Add unit tests for new functionality
2. Update documentation for API changes
3. Follow the existing code style and patterns
4. Test with real CoralCollective projects
5. Consider performance implications

---

The CoralCollective Advanced Memory System provides powerful memory capabilities for multi-agent software development, enabling more intelligent and context-aware agent workflows while maintaining compatibility with existing CoralCollective projects.