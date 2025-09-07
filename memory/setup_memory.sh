#!/bin/bash
# CoralCollective Memory System Setup Script
# 
# This script sets up the advanced memory system for CoralCollective
# including dependencies, vector database initialization, and configuration.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MEMORY_DIR="$SCRIPT_DIR"

# Configuration
PYTHON_MIN_VERSION="3.8"
VENV_NAME="coral_memory_venv"
MEMORY_DB_DIR="$MEMORY_DIR/chroma_db"
CONFIG_FILE="$MEMORY_DIR/config.yaml"

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python version
check_python_version() {
    log "Checking Python version..."
    
    if ! command_exists python3; then
        error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    REQUIRED_VERSION=$(echo -e "$PYTHON_VERSION\n$PYTHON_MIN_VERSION" | sort -V | head -n1)
    
    if [ "$REQUIRED_VERSION" != "$PYTHON_MIN_VERSION" ]; then
        error "Python $PYTHON_MIN_VERSION or higher is required. Found: $PYTHON_VERSION"
        exit 1
    fi
    
    success "Python $PYTHON_VERSION found"
}

# Setup virtual environment
setup_venv() {
    log "Setting up Python virtual environment..."
    
    cd "$PROJECT_ROOT"
    
    if [ -d "$VENV_NAME" ]; then
        warning "Virtual environment already exists. Removing old one..."
        rm -rf "$VENV_NAME"
    fi
    
    python3 -m venv "$VENV_NAME"
    source "$VENV_NAME/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    success "Virtual environment created and activated"
}

# Install Python dependencies
install_dependencies() {
    log "Installing Python dependencies..."
    
    # Ensure we're in the virtual environment
    if [ -z "$VIRTUAL_ENV" ]; then
        source "$PROJECT_ROOT/$VENV_NAME/bin/activate"
    fi
    
    # Install core memory system requirements
    pip install -r "$MEMORY_DIR/requirements.txt"
    
    # Install additional dependencies if main requirements.txt exists
    if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
        pip install -r "$PROJECT_ROOT/requirements.txt"
    fi
    
    success "Dependencies installed"
}

# Initialize ChromaDB
init_chromadb() {
    log "Initializing ChromaDB vector database..."
    
    # Create database directory
    mkdir -p "$MEMORY_DB_DIR"
    
    # Create initialization script
    cat > "$MEMORY_DIR/init_chroma.py" << EOF
#!/usr/bin/env python3
"""
ChromaDB Initialization Script for CoralCollective Memory System
"""

import chromadb
from chromadb.config import Settings
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_chromadb():
    """Initialize ChromaDB with default collections"""
    
    db_path = Path("$MEMORY_DB_DIR")
    db_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Initialize client
        client = chromadb.PersistentClient(
            path=str(db_path),
            settings=Settings(
                allow_reset=True,
                anonymized_telemetry=False
            )
        )
        
        # Create default collection
        collection = client.get_or_create_collection(
            name="coral_collective_memory",
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info(f"ChromaDB initialized at: {db_path}")
        logger.info(f"Default collection created: {collection.name}")
        logger.info(f"Collection count: {collection.count()}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {e}")
        return False

if __name__ == "__main__":
    success = initialize_chromadb()
    if success:
        print("✓ ChromaDB initialization completed successfully")
        exit(0)
    else:
        print("✗ ChromaDB initialization failed")
        exit(1)
EOF

    # Run initialization
    python3 "$MEMORY_DIR/init_chroma.py"
    
    # Cleanup initialization script
    rm "$MEMORY_DIR/init_chroma.py"
    
    success "ChromaDB initialized at $MEMORY_DB_DIR"
}

# Create configuration file
create_config() {
    log "Creating memory system configuration..."
    
    # Get project name
    PROJECT_NAME=$(basename "$PROJECT_ROOT")
    
    cat > "$CONFIG_FILE" << EOF
# CoralCollective Memory System Configuration
# Generated on $(date)

memory_system:
  # Short-term memory configuration
  short_term:
    buffer_size: 25                    # Number of recent interactions to keep
    max_tokens: 10000                  # Maximum tokens in short-term memory
    summarization_threshold: 4000      # Token threshold for summarization
    pruning_strategy: "importance"     # importance, recency, hybrid
    
  # Long-term memory configuration  
  long_term:
    type: "chroma"                     # Vector database type
    collection_name: "coral_memory_${PROJECT_NAME}"
    persist_directory: "$MEMORY_DB_DIR"
    embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
    similarity_threshold: 0.7          # Minimum similarity for retrieval
    max_results_per_query: 50          # Maximum results from vector search
    
  # Memory orchestration
  orchestrator:
    short_term_limit: 25               # Items before consolidation
    consolidation_threshold: 0.6       # Importance threshold for long-term
    importance_decay_hours: 48         # Hours for importance decay
    cleanup_interval_hours: 24         # Background cleanup frequency
    
  # Memory summarization
  summarizer:
    max_summary_length: 500            # Maximum summary length
    preserve_critical_info: true       # Always preserve critical information
    summarization_model: "local"       # local, openai, anthropic
    batch_size: 10                     # Items to summarize together

# Project-specific settings
project:
  name: "$PROJECT_NAME"
  memory_retention_days: 90           # Days to keep memories
  auto_consolidation: true            # Automatic memory consolidation
  context_window_size: 2000          # Context size for agent prompts
  
# Integration settings
integration:
  agent_runner: true                  # Integrate with agent runner
  project_state: true                # Integrate with project state manager
  mcp_enabled: false                  # MCP server integration
  
# Performance settings
performance:
  async_operations: true              # Use async operations
  batch_processing: true              # Batch memory operations
  cache_embeddings: true              # Cache computed embeddings
  parallel_search: true               # Parallel search strategies

# Logging and monitoring
logging:
  level: "INFO"                       # DEBUG, INFO, WARNING, ERROR
  file: "$MEMORY_DIR/logs/memory.log"
  max_file_size: "10MB"              # Log rotation size
  backup_count: 5                     # Number of backup log files
  
monitoring:
  collect_metrics: true               # Collect performance metrics
  metrics_file: "$MEMORY_DIR/metrics/memory_metrics.json"
  health_check_interval: 300         # Health check interval in seconds
EOF

    success "Configuration file created at $CONFIG_FILE"
}

# Create directory structure
create_directories() {
    log "Creating directory structure..."
    
    # Create necessary directories
    mkdir -p "$MEMORY_DIR/logs"
    mkdir -p "$MEMORY_DIR/metrics"
    mkdir -p "$MEMORY_DIR/backups"
    mkdir -p "$MEMORY_DIR/exports"
    mkdir -p "$MEMORY_DB_DIR"
    
    success "Directory structure created"
}

# Create environment file
create_env_file() {
    log "Creating environment configuration..."
    
    ENV_FILE="$MEMORY_DIR/.env"
    
    cat > "$ENV_FILE" << EOF
# CoralCollective Memory System Environment Variables
# Generated on $(date)

# Memory System Configuration
CORAL_MEMORY_CONFIG="$CONFIG_FILE"
CORAL_MEMORY_DB_PATH="$MEMORY_DB_DIR"
CORAL_PROJECT_ROOT="$PROJECT_ROOT"

# Vector Database Settings
CHROMA_DB_PATH="$MEMORY_DB_DIR"
CHROMA_COLLECTION_NAME="coral_memory_$(basename "$PROJECT_ROOT")"

# Embedding Model Settings
EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_CACHE_DIR="$MEMORY_DIR/.cache/embeddings"

# Optional: External API Keys (uncomment and set if using external services)
# OPENAI_API_KEY=your_openai_key_here
# ANTHROPIC_API_KEY=your_anthropic_key_here

# Logging
CORAL_LOG_LEVEL=INFO
CORAL_LOG_FILE="$MEMORY_DIR/logs/memory.log"

# Performance
CORAL_ASYNC_OPERATIONS=true
CORAL_BATCH_SIZE=10
CORAL_CACHE_EMBEDDINGS=true
EOF

    success "Environment file created at $ENV_FILE"
}

# Test installation
test_installation() {
    log "Testing memory system installation..."
    
    # Create test script
    cat > "$MEMORY_DIR/test_installation.py" << 'EOF'
#!/usr/bin/env python3
"""Test script for CoralCollective memory system installation"""

import sys
import asyncio
from pathlib import Path

# Add memory system to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_memory_system():
    """Test memory system components"""
    
    print("Testing memory system installation...")
    
    try:
        # Test imports
        from memory_system import MemorySystem
        from memory_types import MemoryItem, MemoryType, ImportanceLevel
        from coral_memory_integration import CoralMemoryIntegration
        print("✓ Memory system imports successful")
        
        # Test ChromaDB
        import chromadb
        client = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_or_create_collection("test_collection")
        print("✓ ChromaDB connection successful")
        
        # Test memory system initialization
        memory_system = MemorySystem()
        print("✓ Memory system initialization successful")
        
        # Test basic memory operations
        memory_id = await memory_system.add_memory(
            content="Test memory for installation verification",
            agent_id="test_agent",
            project_id="test_project",
            tags=["test", "installation"]
        )
        print(f"✓ Memory storage successful: {memory_id}")
        
        # Test memory retrieval
        memories = await memory_system.search_memories(
            query="test memory",
            limit=5
        )
        print(f"✓ Memory retrieval successful: {len(memories)} results")
        
        print("\n" + "="*50)
        print("✅ All tests passed! Memory system is ready to use.")
        print("="*50)
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_memory_system())
    sys.exit(0 if success else 1)
EOF

    # Run test
    if python3 "$MEMORY_DIR/test_installation.py"; then
        success "Installation test completed successfully"
        rm "$MEMORY_DIR/test_installation.py"
        return 0
    else
        error "Installation test failed"
        rm "$MEMORY_DIR/test_installation.py"
        return 1
    fi
}

# Create usage guide
create_usage_guide() {
    log "Creating usage guide..."
    
    cat > "$MEMORY_DIR/USAGE.md" << EOF
# CoralCollective Memory System Usage Guide

## Quick Start

### 1. Activate Environment
\`\`\`bash
cd $PROJECT_ROOT
source $VENV_NAME/bin/activate
\`\`\`

### 2. Basic Usage in Python
\`\`\`python
import asyncio
from memory.memory_system import MemorySystem

async def main():
    # Initialize memory system
    memory = MemorySystem()
    
    # Add a memory
    memory_id = await memory.add_memory(
        content="This is a test memory",
        agent_id="my_agent",
        project_id="my_project"
    )
    
    # Search memories
    results = await memory.search_memories("test memory")
    print(f"Found {len(results)} memories")

asyncio.run(main())
\`\`\`

### 3. Integration with CoralCollective
\`\`\`python
from memory.coral_memory_integration import CoralMemoryIntegration

# Initialize integration
integration = CoralMemoryIntegration()

# Record agent activities
await integration.record_agent_start("backend_developer", "Create API")
await integration.record_agent_output("backend_developer", "API created successfully")
await integration.record_agent_completion("backend_developer", success=True)
\`\`\`

### 4. Migration from Existing State
\`\`\`bash
cd $MEMORY_DIR
python migration.py --project $PROJECT_ROOT --verbose
\`\`\`

## Configuration

Edit \`$CONFIG_FILE\` to customize:
- Memory buffer sizes
- Consolidation thresholds  
- Vector database settings
- Performance options

## Monitoring

- Logs: \`$MEMORY_DIR/logs/memory.log\`
- Metrics: \`$MEMORY_DIR/metrics/\`
- Database: \`$MEMORY_DB_DIR\`

## Troubleshooting

1. **Import Errors**: Ensure virtual environment is activated
2. **ChromaDB Issues**: Check database directory permissions
3. **Memory Errors**: Adjust buffer sizes in config
4. **Performance Issues**: Enable batch processing and caching

For more details, see the full documentation in the project repository.
EOF

    success "Usage guide created at $MEMORY_DIR/USAGE.md"
}

# Print summary
print_summary() {
    echo
    echo "=========================================="
    echo "  CoralCollective Memory System Setup"
    echo "=========================================="
    echo
    echo "Setup completed successfully! 🎉"
    echo
    echo "Components installed:"
    echo "  ✓ Python virtual environment"
    echo "  ✓ Required dependencies"
    echo "  ✓ ChromaDB vector database"
    echo "  ✓ Memory system configuration"
    echo "  ✓ Directory structure"
    echo
    echo "Key files created:"
    echo "  📁 Virtual environment: $PROJECT_ROOT/$VENV_NAME"
    echo "  📁 Vector database: $MEMORY_DB_DIR"
    echo "  ⚙️  Configuration: $CONFIG_FILE"
    echo "  🔧 Environment: $MEMORY_DIR/.env"
    echo "  📖 Usage guide: $MEMORY_DIR/USAGE.md"
    echo
    echo "Next steps:"
    echo "  1. Activate environment: source $PROJECT_ROOT/$VENV_NAME/bin/activate"
    echo "  2. Review configuration: $CONFIG_FILE"
    echo "  3. Read usage guide: $MEMORY_DIR/USAGE.md"
    echo "  4. Start using the memory system in your agents!"
    echo
    echo "For migration from existing project state:"
    echo "  cd $MEMORY_DIR && python migration.py --project $PROJECT_ROOT"
    echo
}

# Main execution
main() {
    echo "Setting up CoralCollective Memory System..."
    echo "Project: $PROJECT_ROOT"
    echo "Memory directory: $MEMORY_DIR"
    echo
    
    check_python_version
    setup_venv
    install_dependencies
    create_directories
    init_chromadb
    create_config
    create_env_file
    create_usage_guide
    
    if test_installation; then
        print_summary
        exit 0
    else
        error "Setup completed but tests failed. Please check the installation."
        exit 1
    fi
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "CoralCollective Memory System Setup"
        echo "Usage: $0 [options]"
        echo
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --test         Run installation test only"
        echo "  --clean        Clean existing installation"
        echo
        exit 0
        ;;
    --test)
        if [ -d "$PROJECT_ROOT/$VENV_NAME" ]; then
            source "$PROJECT_ROOT/$VENV_NAME/bin/activate"
            test_installation
        else
            error "Virtual environment not found. Run setup first."
            exit 1
        fi
        ;;
    --clean)
        log "Cleaning existing installation..."
        rm -rf "$PROJECT_ROOT/$VENV_NAME"
        rm -rf "$MEMORY_DB_DIR"
        rm -f "$CONFIG_FILE"
        rm -f "$MEMORY_DIR/.env"
        success "Cleanup completed"
        exit 0
        ;;
    *)
        main
        ;;
esac