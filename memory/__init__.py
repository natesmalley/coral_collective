"""
CoralCollective Advanced Memory System

Implements dual-memory architecture with short-term buffer and long-term vector storage.
Provides semantic search, memory consolidation, and intelligent context management.
"""

from .memory_system import (
    MemorySystem,
    MemoryItem,
    MemoryType,
    ImportanceLevel,
    MemoryOrchestrator,
    ShortTermMemory,
    LongTermMemory,
    ChromaLongTermMemory,
    MemorySummarizer
)

from .coral_memory_integration import (
    CoralMemoryIntegration,
    MemoryEnhancedProjectState,
    initialize_project_memory,
    create_memory_config
)

from .migration_strategy import (
    MemoryMigrationStrategy,
    MemorySystemValidator,
    run_migration
)

from .memory_enhanced_runner import (
    MemoryEnhancedAgentRunner,
    create_memory_enhanced_runner
)

__version__ = "1.0.0"
__author__ = "CoralCollective AI/ML Specialist"

# Public API
__all__ = [
    # Core memory system
    "MemorySystem",
    "MemoryItem", 
    "MemoryType",
    "ImportanceLevel",
    
    # Memory components
    "MemoryOrchestrator",
    "ShortTermMemory",
    "LongTermMemory",
    "ChromaLongTermMemory",
    "MemorySummarizer",
    
    # Integration layer
    "CoralMemoryIntegration",
    "MemoryEnhancedProjectState",
    "initialize_project_memory",
    "create_memory_config",
    
    # Migration utilities
    "MemoryMigrationStrategy", 
    "MemorySystemValidator",
    "run_migration",
    
    # Enhanced runner
    "MemoryEnhancedAgentRunner",
    "create_memory_enhanced_runner"
]

# Quick setup function
async def setup_memory_for_project(project_path: str, auto_migrate: bool = True) -> CoralMemoryIntegration:
    """
    Quick setup function for enabling memory in a CoralCollective project
    
    Args:
        project_path: Path to the project directory
        auto_migrate: Whether to automatically migrate existing project state
        
    Returns:
        Initialized CoralMemoryIntegration instance
    """
    from pathlib import Path
    
    path = Path(project_path)
    
    # Create memory configuration
    config_path = create_memory_config(path)
    
    # Run migration if requested and existing state exists
    if auto_migrate and (path / '.coral' / 'project_state.yaml').exists():
        from .migration_strategy import MemoryMigrationStrategy
        migration = MemoryMigrationStrategy(path)
        await migration.migrate_project()
        
    # Initialize memory integration
    memory_integration = await initialize_project_memory(path, str(config_path))
    
    return memory_integration