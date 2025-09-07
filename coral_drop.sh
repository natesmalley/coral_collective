#!/bin/bash

# CoralCollective Drop-In Script for Existing Projects
# This script safely adds CoralCollective to existing projects without disruption

set -e

echo "🪸 CoralCollective Drop-In Installer"
echo "===================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the source directory (where this script lives)
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to check if we're in a git repo
check_git_repo() {
    if git rev-parse --git-dir > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to check for existing project files
check_existing_project() {
    local has_project=false
    
    # Check for common project indicators
    if [ -f "package.json" ] || [ -f "requirements.txt" ] || [ -f "Gemfile" ] || [ -f "pom.xml" ] || [ -f "Cargo.toml" ]; then
        has_project=true
    fi
    
    if [ -d ".git" ] || [ -d "src" ] || [ -d "app" ] || [ -d "lib" ]; then
        has_project=true
    fi
    
    if [ "$has_project" = true ]; then
        echo -e "${GREEN}✓${NC} Detected existing project"
        return 0
    else
        echo -e "${YELLOW}⚠${NC}  No existing project detected"
        return 1
    fi
}

# Function to create .coral directory structure
setup_coral_directory() {
    echo "Setting up CoralCollective in .coral/ directory..."
    
    # Create hidden .coral directory
    mkdir -p .coral
    
    # Copy essential files
    cp "$SOURCE_DIR/agent_runner.py" .coral/ 2>/dev/null || echo "Warning: agent_runner.py not found"
    cp "$SOURCE_DIR/claude_code_agents.json" .coral/ 2>/dev/null || echo "Warning: claude_code_agents.json not found"
    cp "$SOURCE_DIR/claude_interface.py" .coral/ 2>/dev/null || echo "Warning: claude_interface.py not found"
    cp "$SOURCE_DIR/subagent_registry.py" .coral/ 2>/dev/null || echo "Warning: subagent_registry.py not found"
    cp "$SOURCE_DIR/agent_prompt_service.py" .coral/ 2>/dev/null || echo "Warning: agent_prompt_service.py not found"
    cp "$SOURCE_DIR/codex_subagents.py" .coral/ 2>/dev/null || echo "Warning: codex_subagents.py not found"
    cp "$SOURCE_DIR/coral_agents.yaml" .coral/ 2>/dev/null || echo "Warning: coral_agents.yaml not found"
    cp "$SOURCE_DIR/project_manager.py" .coral/ 2>/dev/null || echo "Warning: project_manager.py not found"
    cp "$SOURCE_DIR/requirements.txt" .coral/requirements.txt 2>/dev/null || echo "Warning: requirements.txt not found"
    
    # Copy agent definitions and configurations
    cp -r "$SOURCE_DIR/agents" .coral/ 2>/dev/null || echo "Warning: agents directory not found"
    cp -r "$SOURCE_DIR/config" .coral/ 2>/dev/null || echo "Warning: config directory not found"
    cp -r "$SOURCE_DIR/providers" .coral/ 2>/dev/null || echo "Warning: providers directory not found"
    
    # Copy tools and MCP integration
    if [ -d "$SOURCE_DIR/tools" ]; then
        cp -r "$SOURCE_DIR/tools" .coral/ 2>/dev/null || echo "Warning: tools directory not found"
    fi
    
    # Copy MCP integration if available
    if [ -d "$SOURCE_DIR/mcp" ]; then
        cp -r "$SOURCE_DIR/mcp" .coral/ 2>/dev/null || echo "Warning: mcp directory not found"
    fi
    
    echo -e "${GREEN}✓${NC} Created .coral/ directory with CoralCollective files"
}

# Function to create coral wrapper script
create_coral_wrapper() {
    cat > coral << 'WRAPPER_SCRIPT'
#!/bin/bash
# CoralCollective Wrapper Script
# This script runs CoralCollective from the .coral directory

# Check if .coral exists
if [ ! -d ".coral" ]; then
    echo "❌ CoralCollective not found in this project"
    echo "Run 'coral-drop.sh' first to install"
    exit 1
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Setup virtual environment if needed
if [ ! -d ".coral/venv" ]; then
    echo "🔧 Setting up Python virtual environment..."
    python3 -m venv .coral/venv
    source .coral/venv/bin/activate
    pip install --upgrade pip --quiet
    if [ -f ".coral/requirements.txt" ]; then
        pip install -r .coral/requirements.txt --quiet
    else
        pip install rich pyyaml pyperclip --quiet
    fi
    echo "✅ Virtual environment created"
else
    source .coral/venv/bin/activate 2>/dev/null || true
fi

# Parse command
COMMAND=${1:-help}

case "$COMMAND" in
    help|--help|-h)
        echo "🪸 CoralCollective Commands"
        echo "=========================="
        echo ""
        echo "Usage: ./coral [command] [options]"
        echo ""
        echo "Commands:"
        echo "  workflow    - Start workflow wizard for this project"
        echo "  agent       - Run a specific agent"
        echo "  list        - List available agents"
        echo "  init        - Initialize/reinitialize CoralCollective"
        echo "  update      - Update CoralCollective configuration"
        echo ""
        echo "Examples:"
        echo "  ./coral workflow"
        echo "  ./coral agent backend_developer 'Create user authentication'"
        echo "  ./coral list"
        ;;
        
    workflow)
        cd .coral && python3 agent_runner.py workflow
        ;;
        
    agent)
        shift
        AGENT_ID=$1
        shift
        TASK="$@"
        if [ -z "$AGENT_ID" ] || [ -z "$TASK" ]; then
            echo "Usage: ./coral agent <agent_id> <task>"
            exit 1
        fi
        cd .coral && python3 agent_runner.py run --agent "$AGENT_ID" --task "$TASK"
        ;;
        
    list)
        cd .coral && python3 agent_runner.py list
        ;;
        
    init)
        cd .coral && python3 agent_runner.py init
        ;;
        
    update)
        echo "Updating CoralCollective configuration..."
        # Re-run the drop-in script to update
        if [ -f "../coral_drop.sh" ]; then
            ../coral_drop.sh
        else
            echo "Update script not found. Please re-download coral_drop.sh"
        fi
        ;;
        
    *)
        echo "Unknown command: $COMMAND"
        echo "Run './coral help' for usage information"
        exit 1
        ;;
esac
WRAPPER_SCRIPT
    
    chmod +x coral
    echo -e "${GREEN}✓${NC} Created 'coral' command wrapper"
}

# Function to create .coralrc configuration
create_coralrc() {
    # Check if .coralrc already exists
    if [ -f ".coralrc" ]; then
        echo -e "${YELLOW}⚠${NC}  .coralrc already exists, skipping"
        return
    fi
    
    # Detect project type and set defaults
    local project_type="unknown"
    local project_name=$(basename "$PWD")
    
    if [ -f "package.json" ]; then
        project_type="javascript"
        # Try to get project name from package.json
        if command -v jq &> /dev/null; then
            project_name=$(jq -r '.name // empty' package.json 2>/dev/null || echo "$project_name")
        fi
    elif [ -f "requirements.txt" ] || [ -f "setup.py" ]; then
        project_type="python"
    elif [ -f "Gemfile" ]; then
        project_type="ruby"
    elif [ -f "pom.xml" ]; then
        project_type="java"
    elif [ -f "Cargo.toml" ]; then
        project_type="rust"
    fi
    
    cat > .coralrc << EOF
# CoralCollective Configuration for This Project
# Generated: $(date)

# Project Information
PROJECT_NAME="$project_name"
PROJECT_TYPE="$project_type"
PROJECT_ROOT="$PWD"

# CoralCollective Settings
CORAL_DIR=".coral"
CORAL_ISOLATED=true  # Run in isolated mode, don't affect project files

# Agent Preferences (customize based on your project)
DEFAULT_AGENTS="backend_developer,frontend_developer,qa_testing"
SKIP_AGENTS=""  # Comma-separated list of agents to skip

# Model Preferences (for cost optimization)
PREFER_FAST_MODELS=false  # Use faster/cheaper models when possible
MAX_TOKEN_BUDGET=50000    # Maximum tokens per session

# Integration Settings
USE_EXISTING_TESTS=true   # Try to use existing test framework
USE_EXISTING_DOCS=true    # Try to use existing documentation structure
RESPECT_GITIGNORE=true    # Don't modify files in .gitignore

# Custom Settings for Your Project
# Add any project-specific settings here
EOF
    
    echo -e "${GREEN}✓${NC} Created .coralrc configuration file"
}

# Function to update .gitignore
update_gitignore() {
    if [ ! -f ".gitignore" ]; then
        echo -e "${YELLOW}⚠${NC}  No .gitignore found, creating one"
        touch .gitignore
    fi
    
    # Check if .coral is already in gitignore
    if grep -q "^\.coral" .gitignore; then
        echo -e "${GREEN}✓${NC} .coral already in .gitignore"
    else
        echo "" >> .gitignore
        echo "# CoralCollective" >> .gitignore
        echo ".coral/projects/" >> .gitignore
        echo ".coral/feedback/" >> .gitignore
        echo ".coral/metrics/" >> .gitignore
        echo ".coral/__pycache__/" >> .gitignore
        echo ".coral/*.pyc" >> .gitignore
        echo -e "${GREEN}✓${NC} Added .coral to .gitignore"
    fi
}

# Function to create standalone mode
create_standalone_files() {
    # Create a minimal, non-invasive setup
    cat > .coral/standalone_config.json << 'CONFIG'
{
  "mode": "standalone",
  "respect_existing": true,
  "create_directories": false,
  "use_hidden_directories": true,
  "directories": {
    "projects": ".coral/projects",
    "feedback": ".coral/feedback",
    "metrics": ".coral/metrics"
  },
  "integration": {
    "detect_framework": true,
    "use_existing_tests": true,
    "use_existing_docs": true
  }
}
CONFIG
    
    echo -e "${GREEN}✓${NC} Created standalone configuration"
}

# Function to check for conflicts
check_conflicts() {
    local has_conflicts=false
    
    # Check for conflicting files
    if [ -f "coral" ]; then
        echo -e "${YELLOW}⚠${NC}  Warning: 'coral' file already exists"
        has_conflicts=true
    fi
    
    if [ -d ".coral" ]; then
        echo -e "${YELLOW}⚠${NC}  Warning: '.coral' directory already exists"
        read -p "Overwrite existing .coral directory? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Installation cancelled"
            exit 1
        fi
    fi
    
    if [ "$has_conflicts" = true ]; then
        read -p "Continue with installation? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Installation cancelled"
            exit 1
        fi
    fi
}

# Function to show next steps
show_next_steps() {
    echo ""
    echo "=====================================</=="
    echo -e "${GREEN}✅ CoralCollective successfully installed!${NC}"
    echo "=====================================</=="
    echo ""
    echo "📁 Installation Summary:"
    echo "  • Created .coral/ directory (hidden)"
    echo "  • Added 'coral' command wrapper"
    echo "  • Created .coralrc configuration"
    echo "  • Updated .gitignore"
    echo ""
    echo "🚀 Quick Start:"
    echo "  1. Install Python dependencies (if needed):"
    echo "     pip install rich pyyaml pyperclip"
    echo ""
    echo "  2. Run CoralCollective:"
    echo "     ./coral workflow    # Start workflow wizard"
    echo "     ./coral list        # List available agents"
    echo "     ./coral help        # Show all commands"
    echo ""
    echo "📝 Configuration:"
    echo "  • Edit .coralrc to customize settings"
    echo "  • CoralCollective runs isolated in .coral/"
    echo "  • Your project files remain untouched"
    echo ""
    echo "🔄 To update or remove:"
    echo "  • Update: ./coral update"
    echo "  • Remove: rm -rf .coral coral .coralrc"
}

# Main installation flow
main() {
    echo "Checking project environment..."
    echo ""
    
    # Check if we're in a project directory
    check_existing_project || true
    
    # Check for git repo
    if check_git_repo; then
        echo -e "${GREEN}✓${NC} Git repository detected"
    else
        echo -e "${YELLOW}⚠${NC}  Not a git repository"
    fi
    
    echo ""
    
    # Check for conflicts
    check_conflicts
    
    echo ""
    echo "Installing CoralCollective..."
    echo ""
    
    # Setup .coral directory
    setup_coral_directory
    
    # Create wrapper script
    create_coral_wrapper
    
    # Create configuration
    create_coralrc
    
    # Create standalone configuration
    create_standalone_files
    
    # Update .gitignore if in git repo
    if check_git_repo; then
        update_gitignore
    fi
    
    # Show next steps
    show_next_steps
}

# Run main function
main "$@"