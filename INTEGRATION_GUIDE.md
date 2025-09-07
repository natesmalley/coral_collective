# 🔄 CoralCollective Integration Guide

## How to Use Agents in Other Projects

### Method 1: Direct Copy Integration (Simplest)

#### Step 1: Copy the Agent Prompt
```bash
# From your coral_collective directory, copy any agent prompt
cat agents/specialists/backend_developer.md

# Or copy the prompt content directly from the file
```

#### Step 2: Use in Any Project
Simply paste the agent prompt into Claude Code when working on any project. The agent will adapt to your current context.

---

### Method 2: Git Submodule (Recommended for Teams)

#### Step 1: Add Agent Force as a Submodule
```bash
# In your new project directory
git submodule add https://github.com/natesmalley/coral_collective.git coral_collective
git submodule init
git submodule update
```

#### Step 2: Use the Agents
```bash
# Run agents from the submodule
cd coral_collective
./start.sh

# Or reference agent prompts directly
cat coral_collective/agents/specialists/full_stack_engineer.md
```

---

### Method 3: Standalone Agent Package

#### Step 1: Clone Agent Force Separately
```bash
# Keep agent_force in a central location
cd ~/tools  # or wherever you keep tools
git clone https://github.com/natesmalley/coral_collective.git
```

#### Step 2: Create Alias for Easy Access
```bash
# Add to ~/.bashrc or ~/.zshrc
alias coral='cd ~/tools/coral_collective && ./start.sh'
alias coral-agent='python ~/tools/coral_collective/agent_runner.py'

# Now from any project:
coral  # Opens CoralCollective command center
coral-agent --agent backend-developer --task "Build API for user auth"
```

---

### Method 4: Project Template Integration

#### Step 1: Create a Project with Agent Force
```bash
# Use coral_collective to bootstrap new projects
cd ~/tools/coral_collective
./start.sh
# Select "1. Run Agent Workflow"
# Choose project type
# Let agents create the project structure
```

#### Step 2: Move Generated Code
```bash
# After agents create your project structure
cp -r ~/tools/coral_collective/projects/your_project ~/your-actual-project
cd ~/your-actual-project
```

---

### Method 5: Import as Python Module

#### Step 1: Install Agent Force
```bash
# In your project's virtual environment
pip install -e /path/to/coral_collective
```

#### Step 2: Use in Python Scripts
```python
from agent_runner import AgentRunner
from project_manager import ProjectManager

# Initialize runner
runner = AgentRunner()

# Run an agent programmatically
result = runner.run_agent(
    'backend-developer',
    'Create REST API for user management',
    project_context={'name': 'MyApp', 'tech_stack': 'Node.js'}
)
```

---

## 📋 Quick Reference Commands

### Running Agents from Anywhere

```bash
# Set up a global command (add to ~/.bashrc or ~/.zshrc)
function agent() {
    local AGENT_FORCE_DIR="$HOME/tools/agent_force"
    local CURRENT_DIR=$(pwd)
    
    cd "$AGENT_FORCE_DIR"
    python agent_runner.py run --agent "$1" --task "$2"
    cd "$CURRENT_DIR"
}

# Usage from any project:
agent backend-developer "Create user authentication system"
agent full-stack-engineer "Debug production issue with login"
```

### Project-Specific Agent Configuration

Create `.agent_force` in your project root:

```yaml
# .agent_force/config.yaml
project_name: "My Awesome App"
preferred_agents:
  - full-stack-engineer  # For quick fixes
  - backend-developer    # For API work
  - frontend-developer   # For UI work
  
tech_stack:
  backend: "Node.js"
  frontend: "React"
  database: "PostgreSQL"
  
agent_preferences:
  backend-developer:
    additional_context: "Use Express.js with TypeScript"
  frontend-developer:
    additional_context: "Use Tailwind CSS for styling"
```

---

## 🚀 Workflow Integration Examples

### Example 1: New Feature Development

```bash
# From your project directory
cd my-app

# 1. Plan the feature
agent project-architect "Plan implementation for real-time chat feature"

# 2. Create API
agent backend-developer "Build WebSocket API for real-time chat"

# 3. Build UI
agent frontend-developer "Create chat interface component"

# 4. Test
agent qa-testing "Write tests for chat feature"
```

### Example 2: Debugging Production Issue

```bash
# Quick debugging with full-stack engineer
agent full-stack-engineer "Debug: Users can't login, getting 500 error"

# Follow up with specialist if needed
agent security-specialist "Review authentication implementation for vulnerabilities"
```

### Example 3: Starting New Project

```bash
# Let Agent Force create everything
cd ~/projects
mkdir new-saas-app && cd new-saas-app

# Initialize with Agent Force
~/tools/agent_force/start.sh
# Choose "Workflow Wizard"
# Select "Full-Stack Web App"
# Follow the guided process
```

---

## 🔧 Advanced Integration

### CI/CD Pipeline Integration

```yaml
# .github/workflows/agent-assist.yml
name: Agent Force Assistance

on:
  issues:
    types: [opened, labeled]

jobs:
  suggest-agent:
    if: contains(github.event.label.name, 'needs-agent')
    runs-on: ubuntu-latest
    steps:
      - name: Suggest Agent
        run: |
          echo "Suggested agents for this issue:"
          echo "- backend-developer: For API issues"
          echo "- frontend-developer: For UI issues"
          echo "- full-stack-engineer: For general fixes"
```

### VS Code Integration

Create `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Run Agent",
      "type": "shell",
      "command": "python",
      "args": [
        "${env:HOME}/tools/coral_collective/claude_interface.py",
        "get-prompt",
        "--agent",
        "${input:agentName}",
        "--task",
        "${input:taskDescription}"
      ]
    }
  ],
  "inputs": [
    {
      "id": "agentName",
      "type": "pickString",
      "description": "Select an agent",
      "options": [
        "full-stack-engineer",
        "backend-developer",
        "frontend-developer",
        "qa-testing"
      ]
    },
    {
      "id": "taskDescription",
      "type": "promptString",
      "description": "Describe the task"
    }
  ]
}
```

---

## 📦 Creating Portable Agent Bundle

```bash
# Create a portable version
cd ~/tools/agent_force
tar -czf agent_force_portable.tar.gz \
  agents/ \
  config/ \
  agent_runner.py \
  requirements.txt \
  start.sh

# Share with team or move to new machine
# Extract and use anywhere
tar -xzf agent_force_portable.tar.gz
./start.sh
```

---

## 🎯 Best Practices

1. **Keep Agent Force Updated**
   ```bash
   cd ~/tools/agent_force
   git pull origin main
   ```

2. **Track Agent Usage Per Project**
   - Each project can have its own feedback/metrics
   - Copy `feedback/` and `metrics/` directories to project

3. **Project-Specific Agents**
   - Customize agent prompts for specific needs
   - Store in `.agent_force/custom_agents/`

4. **Team Collaboration**
   - Share agent feedback across team
   - Maintain team-specific agent improvements

---

## 🔗 Quick Setup Script

Save this as `setup_agents.sh` in any project:

```bash
#!/bin/bash
# Quick Agent Force Setup for New Project

AGENT_FORCE_REPO="https://github.com/natesmalley/agent_force.git"
AGENT_FORCE_DIR="$HOME/.agent_force"

# Install Agent Force if not present
if [ ! -d "$AGENT_FORCE_DIR" ]; then
    echo "Installing Agent Force..."
    git clone $AGENT_FORCE_REPO $AGENT_FORCE_DIR
    cd $AGENT_FORCE_DIR
    pip install -r requirements.txt
fi

# Create project link
ln -sf $AGENT_FORCE_DIR/agent_runner.py ./run_agent
ln -sf $AGENT_FORCE_DIR/start.sh ./agents

echo "✅ Agent Force ready! Use './agents' to start"
```

---

## Summary

The key is that Agent Force is designed to be **portable and flexible**:

- **Standalone Tool**: Run from anywhere
- **Git Submodule**: Include in projects
- **Python Module**: Import and use programmatically
- **Copy & Paste**: Just grab agent prompts as needed

Choose the method that fits your workflow best!