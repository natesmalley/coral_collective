#!/bin/bash

# CoralCollective Deployment Script
# This script packages and deploys CoralCollective to any directory

set -e

echo "🪸 CoralCollective Deployment Tool"
echo "==================================="
echo ""

# Function to show usage
usage() {
    echo "Usage: $0 [deploy|package|init] [target_directory]"
    echo ""
    echo "Commands:"
    echo "  deploy <dir>   - Deploy CoralCollective to specified directory"
    echo "  package        - Create portable coral_collective.tar.gz"
    echo "  init           - Initialize CoralCollective in current directory"
    echo ""
    echo "Examples:"
    echo "  $0 deploy ~/projects/my_new_project"
    echo "  $0 package"
    echo "  $0 init"
    exit 1
}

# Check arguments
if [ $# -lt 1 ]; then
    usage
fi

COMMAND=$1
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to create minimal package
create_minimal_package() {
    echo "Creating minimal CoralCollective package..."
    
    # Essential files only
    PACKAGE_FILES=(
        "agent_runner.py"
        "claude_code_agents.json"
        "claude_interface.py"
        "subagent_registry.py"
        "start.sh"
        "requirements.txt"
        "project_manager.py"
        "coral_drop.sh"
        "README.md"
        "agent_prompt_service.py"
        "codex_subagents.py"
        "coral_agents.yaml"
    )
    
    # Essential directories
    PACKAGE_DIRS=(
        "agents"
        "config"
        "tools"
        "mcp"
        "providers"
        "docs"
    )
    
    # Create temp directory
    TEMP_DIR=$(mktemp -d)
    PACKAGE_DIR="$TEMP_DIR/coral_collective"
    mkdir -p "$PACKAGE_DIR"
    
    # Copy files
    for file in "${PACKAGE_FILES[@]}"; do
        if [ -f "$SOURCE_DIR/$file" ]; then
            cp "$SOURCE_DIR/$file" "$PACKAGE_DIR/"
            echo "  ✓ Copied $file"
        fi
    done
    
    # Copy directories
    for dir in "${PACKAGE_DIRS[@]}"; do
        if [ -d "$SOURCE_DIR/$dir" ]; then
            cp -r "$SOURCE_DIR/$dir" "$PACKAGE_DIR/"
            echo "  ✓ Copied $dir/"
        fi
    done
    
    # Copy provider system
    if [ -d "$SOURCE_DIR/providers" ]; then
        cp -r "$SOURCE_DIR/providers" "$PACKAGE_DIR/"
        echo "  ✓ Copied providers/"
    fi
    
    # Copy documentation
    if [ -f "$SOURCE_DIR/CLAUDE.md" ]; then
        cp "$SOURCE_DIR/CLAUDE.md" "$PACKAGE_DIR/"
        echo "  ✓ Copied CLAUDE.md"
    fi
    if [ -f "$SOURCE_DIR/INTEGRATION_GUIDE.md" ]; then
        cp "$SOURCE_DIR/INTEGRATION_GUIDE.md" "$PACKAGE_DIR/"
        echo "  ✓ Copied INTEGRATION_GUIDE.md"
    fi
    
    # Create init script for the package
    cat > "$PACKAGE_DIR/init_coral.sh" << 'INIT_SCRIPT'
#!/bin/bash
# CoralCollective Initialization Script

echo "🪸 Initializing CoralCollective..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Please install it first."
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Make scripts executable
chmod +x start.sh
chmod +x agent_runner.py
chmod +x coral_drop.sh

# Create necessary directories
mkdir -p projects feedback metrics

# Set up Python path for imports
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo ""
echo "✅ CoralCollective initialized successfully!"
echo ""
echo "To get started:"
echo "  1. Run: ./start.sh"
echo "  2. Select 'Run Agent Workflow' to start a project"
echo ""
INIT_SCRIPT
    
    chmod +x "$PACKAGE_DIR/init_coral.sh"
    
    # Create tarball
    cd "$TEMP_DIR"
    tar -czf coral_collective.tar.gz coral_collective/
    mv coral_collective.tar.gz "$SOURCE_DIR/"
    
    # Cleanup
    rm -rf "$TEMP_DIR"
    
    echo ""
    echo "✅ Package created: coral_collective.tar.gz"
    echo ""
    echo "To deploy:"
    echo "  1. Copy coral_collective.tar.gz to target location"
    echo "  2. Run: tar -xzf coral_collective.tar.gz"
    echo "  3. Run: cd coral_collective && ./init_coral.sh"
}

# Function to deploy to directory
deploy_to_directory() {
    TARGET_DIR=$1
    
    if [ -z "$TARGET_DIR" ]; then
        echo "❌ Error: Target directory required"
        usage
    fi
    
    # Create target directory if it doesn't exist
    mkdir -p "$TARGET_DIR"
    
    echo "Deploying CoralCollective to: $TARGET_DIR"
    echo ""
    
    # Create coral_collective subdirectory
    CORAL_DIR="$TARGET_DIR/coral_collective"
    mkdir -p "$CORAL_DIR"
    
    # Copy essential files
    echo "Copying files..."
    cp "$SOURCE_DIR/agent_runner.py" "$CORAL_DIR/" 2>/dev/null || true
    cp "$SOURCE_DIR/claude_code_agents.json" "$CORAL_DIR/" 2>/dev/null || true
    cp "$SOURCE_DIR/claude_interface.py" "$CORAL_DIR/" 2>/dev/null || true
    cp "$SOURCE_DIR/subagent_registry.py" "$CORAL_DIR/" 2>/dev/null || true
    cp "$SOURCE_DIR/agent_prompt_service.py" "$CORAL_DIR/" 2>/dev/null || true
    cp "$SOURCE_DIR/codex_subagents.py" "$CORAL_DIR/" 2>/dev/null || true
    cp "$SOURCE_DIR/coral_agents.yaml" "$CORAL_DIR/" 2>/dev/null || true
    cp "$SOURCE_DIR/start.sh" "$CORAL_DIR/" 2>/dev/null || true
    cp "$SOURCE_DIR/requirements.txt" "$CORAL_DIR/" 2>/dev/null || true
    cp "$SOURCE_DIR/project_manager.py" "$CORAL_DIR/" 2>/dev/null || true
    
    # Copy directories
    echo "Copying agent definitions..."
    cp -r "$SOURCE_DIR/agents" "$CORAL_DIR/" 2>/dev/null || true
    cp -r "$SOURCE_DIR/config" "$CORAL_DIR/" 2>/dev/null || true
    cp -r "$SOURCE_DIR/tools" "$CORAL_DIR/" 2>/dev/null || true
    cp -r "$SOURCE_DIR/providers" "$CORAL_DIR/" 2>/dev/null || true
    cp -r "$SOURCE_DIR/mcp" "$CORAL_DIR/" 2>/dev/null || true
    
    # Make scripts executable
    chmod +x "$CORAL_DIR/start.sh" 2>/dev/null || true
    chmod +x "$CORAL_DIR/agent_runner.py" 2>/dev/null || true
    
    # Create initialization script
    cat > "$CORAL_DIR/init.sh" << 'EOF'
#!/bin/bash
echo "🪸 Initializing CoralCollective in this directory..."
pip3 install -r requirements.txt
mkdir -p projects feedback metrics
echo "✅ Ready to use! Run ./start.sh to begin"
EOF
    chmod +x "$CORAL_DIR/init.sh"
    
    echo ""
    echo "✅ CoralCollective deployed successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. cd $CORAL_DIR"
    echo "  2. ./init.sh  (first time only)"
    echo "  3. ./start.sh"
}

# Function to initialize in current directory
init_current_directory() {
    echo "Initializing CoralCollective in current directory..."
    echo ""
    
    # Check if we're in the source directory
    if [ "$PWD" == "$SOURCE_DIR" ]; then
        echo "✅ Already in CoralCollective directory"
        return
    fi
    
    # Check if JSON exists
    if [ ! -f "claude_code_agents.json" ]; then
        echo "Creating configuration file..."
        if [ -f "$SOURCE_DIR/claude_code_agents.json" ]; then
            cp "$SOURCE_DIR/claude_code_agents.json" .
            echo "  ✓ Copied configuration from source"
        else
            echo "  ⚠️  Configuration will be created on first run"
        fi
    fi
    
    # Check if agent_runner.py exists
    if [ ! -f "agent_runner.py" ]; then
        if [ -f "$SOURCE_DIR/agent_runner.py" ]; then
            cp "$SOURCE_DIR/agent_runner.py" .
            echo "  ✓ Copied agent_runner.py"
        fi
    fi
    
    # Create necessary directories
    mkdir -p projects feedback metrics
    
    echo ""
    echo "✅ CoralCollective initialized in current directory"
    echo "Run: python3 agent_runner.py workflow"
}

# Main command processing
case "$COMMAND" in
    deploy)
        deploy_to_directory "$2"
        ;;
    package)
        create_minimal_package
        ;;
    init)
        init_current_directory
        ;;
    *)
        echo "❌ Unknown command: $COMMAND"
        usage
        ;;
esac