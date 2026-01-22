#!/bin/bash
# coral_drop.sh - Drop CoralCollective into an existing project

set -e

echo "🪸 CoralCollective Drop-In Installer"
echo "===================================="
echo ""

# Check if we're in a git repository
if [ -d .git ]; then
    echo "✓ Git repository detected"
else
    echo "⚠️  Warning: Not in a git repository"
fi

# Create .coral directory structure
echo "Creating .coral directory structure..."
mkdir -p .coral/{states,feedback,config,cache}

# Create .coralrc configuration
echo "Creating .coralrc configuration..."
cat > .coralrc << 'EOF'
# CoralCollective Configuration
CORAL_HOME="$(dirname "$(readlink -f "$0")")/.coral"
CORAL_PYTHON="${CORAL_PYTHON:-python3}"
CORAL_VENV="${CORAL_VENV:-$CORAL_HOME/venv}"

# Model configuration
CORAL_MODEL_PROVIDER="${CORAL_MODEL_PROVIDER:-openai}"
CORAL_MODEL_DEFAULT="${CORAL_MODEL_DEFAULT:-gpt-4}"

# MCP configuration
CORAL_MCP_ENABLED="${CORAL_MCP_ENABLED:-false}"

# Export for child processes
export CORAL_HOME CORAL_PYTHON CORAL_VENV
EOF

# Create coral wrapper script
echo "Creating coral command wrapper..."
cat > coral << 'EOF'
#!/bin/bash
# CoralCollective CLI Wrapper

# Source configuration
[ -f .coralrc ] && source .coralrc

# Set PYTHONPATH to include CoralCollective
CORAL_PATH="${CORAL_PATH:-$(dirname "$(readlink -f "$0")")}"
export PYTHONPATH="${CORAL_PATH}:${PYTHONPATH}"

# Check for virtual environment
if [ -d "$CORAL_VENV" ] && [ -f "$CORAL_VENV/bin/activate" ]; then
    source "$CORAL_VENV/bin/activate"
fi

# Run CoralCollective
if [ -f "$CORAL_PATH/agent_runner.py" ]; then
    exec "$CORAL_PYTHON" "$CORAL_PATH/agent_runner.py" "$@"
elif command -v coral-collective >/dev/null 2>&1; then
    exec coral-collective "$@"
else
    exec "$CORAL_PYTHON" -m coral_collective.cli.main "$@"
fi
EOF

chmod +x coral

# Add to .gitignore if it exists
if [ -f .gitignore ]; then
    if ! grep -q "^.coral/" .gitignore; then
        echo "" >> .gitignore
        echo "# CoralCollective" >> .gitignore
        echo ".coral/" >> .gitignore
        echo ".coralrc" >> .gitignore
        echo "coral" >> .gitignore
        echo "✓ Added CoralCollective entries to .gitignore"
    fi
fi

echo ""
echo "✅ CoralCollective has been dropped into your project!"
echo ""
echo "Next steps:"
echo "1. Set your API keys in environment or .env file"
echo "2. Run: ./coral --help"
echo "3. Start with: ./coral run project_architect"
echo ""
echo "For more information: https://github.com/coral-collective/coral-collective"