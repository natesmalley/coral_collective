#!/bin/bash

# CoralCollective Project Initializer
# Automatically sets up CoralCollective in any new project
# Usage: curl -sSL https://coral-init.sh | bash

set -e

CORAL_VERSION="1.0.0"
PROJECT_NAME="${1:-$(basename $(pwd))}"
CORAL_REPO="https://github.com/coral-collective/coral"

echo "🪸 CoralCollective Project Initializer v${CORAL_VERSION}"
echo "================================================"
echo "Project: ${PROJECT_NAME}"
echo ""

# Function to check if CoralCollective is already installed
check_existing() {
    if [ -d ".coral" ]; then
        echo "⚠️  CoralCollective already installed in this project"
        read -p "Reinstall? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
        rm -rf .coral
    fi
}

# Function to create project structure
create_structure() {
    echo "📁 Creating project structure..."
    
    # Create directories
    mkdir -p src tests docs .coral/{agents,workflows,state,logs}
    
    # Create .gitignore if not exists
    if [ ! -f .gitignore ]; then
        cat > .gitignore << 'EOF'
# CoralCollective
.coral/cache/
.coral/logs/
.coral/tmp/
.coral/*.log

# Environment
.env
*.env.local
venv/
.venv/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store
EOF
    fi
}

# Function to install CoralCollective
install_coral() {
    echo "🚀 Installing CoralCollective..."
    
    # Download coral_drop.sh
    curl -sSL -o .coral/coral_drop.sh https://raw.githubusercontent.com/coral-collective/coral/main/coral_drop.sh
    chmod +x .coral/coral_drop.sh
    
    # Run coral_drop to get full installation
    cd .coral && ./coral_drop.sh --quiet && cd ..
    
    # Create coral command wrapper
    cat > coral << 'EOF'
#!/bin/bash
# CoralCollective CLI Wrapper
CORAL_DIR="$(dirname "$0")/.coral"
cd "$CORAL_DIR" && python agent_runner.py "$@"
EOF
    chmod +x coral
}

# Function to create CLAUDE.md
create_claude_md() {
    echo "📝 Creating CLAUDE.md instructions..."
    
    cat > CLAUDE.md << EOF
# CLAUDE.md - Project Instructions for Claude Code

## 🪸 This project uses CoralCollective

CoralCollective is integrated into this project to provide specialized AI agents for development.

### Project: ${PROJECT_NAME}
- **Status**: Initialized
- **Phase**: Planning
- **Next Agent**: project_architect

## ⛔ IMPORTANT: DO NOT MODIFY CORAL COLLECTIVE

**CoralCollective is a FRAMEWORK - Use it, don't edit it!**
- ❌ NEVER modify .coral/ directory contents
- ❌ NEVER edit coral framework files
- ✅ USE: \`./coral run [agent_name]\`
- ✅ IMPORT: \`from coral_collective import ...\`

Framework files are protected and should only be used through their interfaces.

## Workflow Instructions

### Starting Development
1. **ALWAYS** begin with: \`./coral run project_architect --task "Design ${PROJECT_NAME}"\`
2. Follow the agent's handoff recommendations
3. Track progress: \`./coral status\`

### Available Agents
- **Planning**: project_architect, technical_writer_phase1
- **Development**: backend_developer, frontend_developer, database_specialist
- **Quality**: qa_testing, security_specialist, performance_engineer
- **Deployment**: devops_deployment, site_reliability_engineer
- **Documentation**: technical_writer_phase2

### Commands
\`\`\`bash
# Run recommended workflow
./coral workflow

# Run specific agent
./coral run [agent_name] --task "[description]"

# Check status
./coral status

# View dashboard
./coral dashboard
\`\`\`

## Development Protocol

1. **New Feature**: Start with project_architect
2. **API Changes**: Use api_designer
3. **Database Changes**: Use database_specialist
4. **Security Concerns**: Use security_specialist
5. **Performance Issues**: Use performance_engineer
6. **Deployment**: Use devops_deployment

## Important Notes
- Agent recommendations are in handoff sections
- Each agent provides context for the next
- State is tracked in .coral/project_state.yaml
- Decisions are logged in .coral/decisions.md

## Auto-Integration
This project is configured to automatically suggest appropriate agents based on the task at hand.
EOF
}

# Function to create project configuration
create_project_config() {
    echo "⚙️  Creating project configuration..."
    
    cat > .coral/project.yaml << EOF
# CoralCollective Project Configuration
project:
  name: ${PROJECT_NAME}
  version: 1.0.0
  created: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
  framework: coral_collective
  
workflow:
  type: full_stack_development
  auto_suggest: true
  
phases:
  current: planning
  completed: []
  sequence:
    - planning
    - documentation
    - development
    - testing
    - deployment
    - maintenance
    
agents:
  enabled: true
  auto_handoff: true
  tracking: true
  
  preferred:
    architecture: project_architect
    backend: backend_developer
    frontend: frontend_developer
    database: database_specialist
    testing: qa_testing
    security: security_specialist
    deployment: devops_deployment
    
memory:
  enabled: true
  type: project_isolated
  
mcp:
  enabled: false
  servers: []
EOF
}

# Function to create initial workflow
create_workflow() {
    echo "🔄 Creating initial workflow..."
    
    cat > .coral/workflows/default.yaml << 'EOF'
name: Default Development Workflow
description: Standard workflow for full-stack development

triggers:
  - "new project"
  - "build app"
  - "create application"

phases:
  planning:
    agents:
      - project_architect
      - technical_writer_phase1
    duration: "1-2 hours"
    
  development:
    parallel: true
    agents:
      - backend_developer
      - frontend_developer
      - database_specialist
    duration: "2-5 days"
    
  testing:
    agents:
      - qa_testing
      - security_specialist
    duration: "1-2 days"
    
  deployment:
    agents:
      - devops_deployment
    duration: "2-4 hours"
    
  documentation:
    agents:
      - technical_writer_phase2
    duration: "2-4 hours"

handoff_rules:
  project_architect: technical_writer_phase1
  technical_writer_phase1: [backend_developer, frontend_developer]
  backend_developer: qa_testing
  frontend_developer: qa_testing
  qa_testing: devops_deployment
  devops_deployment: technical_writer_phase2
EOF
}

# Function to create quick start guide
create_quickstart() {
    echo "📚 Creating quick start guide..."
    
    cat > .coral/QUICKSTART.md << 'EOF'
# 🪸 CoralCollective Quick Start

## Your First Steps

1. **Start the Project Architect**
   ```bash
   ./coral run project_architect --task "Design this application"
   ```

2. **Follow Recommendations**
   The architect will recommend the next agent. Run it with:
   ```bash
   ./coral run [recommended_agent]
   ```

3. **Or Run Full Workflow**
   ```bash
   ./coral workflow
   ```

## Common Tasks

### Add a New Feature
```bash
./coral run project_architect --task "Add user authentication"
```

### Create API
```bash
./coral run api_designer --task "Design REST API"
```

### Set Up Database
```bash
./coral run database_specialist --task "Design database schema"
```

### Write Tests
```bash
./coral run qa_testing --task "Create test suite"
```

### Deploy Application
```bash
./coral run devops_deployment --task "Set up CI/CD"
```

## Tips
- Always start with project_architect for new features
- Check `./coral status` to see current phase
- View `./coral dashboard` for visual progress
- Agents pass context automatically via handoffs
EOF
}

# Function to initialize git with coral
init_git() {
    if [ ! -d .git ]; then
        echo "📦 Initializing git repository..."
        git init
        git add .
        git commit -m "🪸 Initialize project with CoralCollective

- Added CoralCollective agent framework
- Created project structure
- Set up development workflow
- Added CLAUDE.md for AI assistance"
    else
        echo "📦 Adding CoralCollective to git..."
        git add .coral CLAUDE.md coral
        git commit -m "🪸 Add CoralCollective to project" || true
    fi
}

# Function to show success message
show_success() {
    cat << 'EOF'

✅ CoralCollective Successfully Installed!
==========================================

🎯 Next Steps:
1. Start with: ./coral run project_architect
2. Follow agent recommendations
3. Track progress: ./coral status

📚 Resources:
- Quick Start: .coral/QUICKSTART.md
- Instructions: CLAUDE.md
- Workflows: .coral/workflows/

🪸 Happy Building with CoralCollective!

EOF
}

# Main installation flow
main() {
    echo "🔍 Checking environment..."
    check_existing
    
    echo "🏗️  Setting up project..."
    create_structure
    
    echo "📦 Installing components..."
    install_coral
    
    echo "📄 Creating documentation..."
    create_claude_md
    create_project_config
    create_workflow
    create_quickstart
    
    echo "🔧 Finalizing setup..."
    init_git
    
    show_success
}

# Run main installation
main "$@"