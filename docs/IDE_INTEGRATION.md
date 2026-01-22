# CoralCollective IDE Integration Guide

This guide explains how to integrate CoralCollective with popular IDEs and development tools, particularly VS Code and GitHub Desktop, and how to use it with Claude's `/agent` command.

## Table of Contents
1. [VS Code Integration](#vs-code-integration)
2. [GitHub Desktop Setup](#github-desktop-setup)
3. [Claude /agent Command Integration](#claude-agent-command-integration)
4. [Workflow Examples](#workflow-examples)
5. [Best Practices](#best-practices)

## VS Code Integration

### Installation Methods

#### Method 1: Direct Clone with VS Code

1. **Open VS Code Command Palette** (`Cmd+Shift+P` on Mac, `Ctrl+Shift+P` on Windows/Linux)
2. **Clone from GitHub**:
   ```
   Git: Clone
   Enter URL: https://github.com/natesmalley/coral_collective.git
   ```
3. **Open in VS Code**:
   - VS Code will prompt to open the cloned repository
   - Trust the workspace when prompted

#### Method 2: VS Code Terminal Integration

1. **Open VS Code Terminal** (`View > Terminal`)
2. **Clone and setup**:
   ```bash
   # Clone the repository
   git clone https://github.com/natesmalley/coral_collective.git
   cd coral_collective
   
   # Run drop-in installer
   ./coral_drop.sh
   
   # The coral command is now available in terminal
   ./coral run project_architect
   ```

### VS Code Extensions for CoralCollective

Install these recommended extensions for the best experience:

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-vscode-remote.remote-containers",
    "github.copilot",
    "github.copilot-chat",
    "ms-azuretools.vscode-docker",
    "eamodio.gitlens",
    "usernamehw.errorlens"
  ]
}
```

### VS Code Settings Configuration

Add to `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "files.exclude": {
    "**/.coral": false,
    "**/__pycache__": true,
    "**/*.pyc": true
  },
  "terminal.integrated.env.osx": {
    "CORAL_HOME": "${workspaceFolder}/.coral"
  },
  "terminal.integrated.env.linux": {
    "CORAL_HOME": "${workspaceFolder}/.coral"
  },
  "terminal.integrated.env.windows": {
    "CORAL_HOME": "${workspaceFolder}\\.coral"
  }
}
```

### VS Code Tasks Configuration

Create `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Run Project Architect",
      "type": "shell",
      "command": "./coral run project_architect",
      "group": "build",
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "Run Backend Developer",
      "type": "shell",
      "command": "./coral run backend_developer",
      "group": "build"
    },
    {
      "label": "List Agents",
      "type": "shell",
      "command": "./coral list",
      "group": "test"
    },
    {
      "label": "Run Full Workflow",
      "type": "shell",
      "command": "./coral workflow full_stack",
      "group": "build"
    }
  ]
}
```

## GitHub Desktop Setup

### Initial Setup

1. **Clone via GitHub Desktop**:
   - Click "Clone a Repository from the Internet"
   - Search for: `natesmalley/coral_collective`
   - Choose local path
   - Click "Clone"

2. **Open in VS Code**:
   - In GitHub Desktop: `Repository > Open in Visual Studio Code`
   - Or use: `Cmd+Shift+A` (Mac) / `Ctrl+Shift+A` (Windows)

3. **Initialize CoralCollective**:
   - Open terminal in VS Code
   - Run: `./coral_drop.sh`

### GitHub Desktop Workflow

1. **Make Changes with Agents**:
   ```bash
   # In VS Code terminal
   ./coral run backend_developer --task "Create user API"
   ```

2. **Review in GitHub Desktop**:
   - See all changes made by agents
   - Review diffs line-by-line
   - Stage specific changes

3. **Commit with Context**:
   - GitHub Desktop shows all agent-generated files
   - Add descriptive commit message
   - Reference which agent was used

4. **Push to GitHub**:
   - Push changes to your fork
   - Create pull request if needed

## Claude /agent Command Integration

### Setting Up for Claude

When using Claude (via claude.ai or Claude Desktop), you can invoke CoralCollective agents directly using the `/agent` command.

#### Prerequisites

1. **Ensure CoralCollective is in your project**:
   ```bash
   # Option 1: Clone directly
   git clone https://github.com/natesmalley/coral_collective.git
   
   # Option 2: Add as submodule
   git submodule add https://github.com/natesmalley/coral_collective.git .coral_collective
   
   # Option 3: Drop-in installation
   curl -O https://raw.githubusercontent.com/natesmalley/coral_collective/main/coral_drop.sh
   bash coral_drop.sh
   ```

2. **Create CLAUDE.md in your project root**:
   ```markdown
   # CLAUDE.md
   
   This project uses CoralCollective agents. Available agents:
   
   ## Core Agents
   - project_architect: System design and architecture
   - technical_writer: Documentation and specifications
   
   ## Specialist Agents
   - backend_developer: API and server development
   - frontend_developer: UI and client development
   - database_specialist: Database design and optimization
   - security_specialist: Security review and implementation
   - qa_testing: Test creation and validation
   - devops_deployment: CI/CD and deployment
   
   Use: /agent [agent_name] to invoke an agent
   ```

### Using /agent Command

#### Basic Usage

In your Claude conversation:

```
/agent project_architect

Design a microservices architecture for an e-commerce platform with:
- User management
- Product catalog
- Order processing
- Payment integration
```

#### Chaining Agents

```
/agent project_architect
Create the system architecture for a task management app

/agent backend_developer
Implement the API based on the architecture above

/agent frontend_developer  
Build the React UI for the task management system

/agent qa_testing
Write comprehensive tests for the implementation
```

#### With Context Files

```
/agent backend_developer

Implement the user authentication system based on:
- Architecture: @architecture.md
- API Spec: @api_specification.yaml
- Database Schema: @schema.sql
```

### Claude Desktop Configuration

For Claude Desktop app, add to your configuration:

1. **Create claude_desktop_config.json**:
   ```json
   {
     "coral_collective": {
       "agents_path": "~/.coral_collective/agents",
       "default_model": "claude-3-opus",
       "enable_mcp": true,
       "workspace": "~/projects"
     }
   }
   ```

2. **Set Environment Variables**:
   ```bash
   export CORAL_COLLECTIVE_HOME="$HOME/.coral_collective"
   export CORAL_AGENT_PATH="$CORAL_COLLECTIVE_HOME/agents"
   ```

## Workflow Examples

### Example 1: Full Stack Development

```bash
# 1. Start with architecture
/agent project_architect
Design a real-time chat application with rooms and direct messages

# 2. Create specifications
/agent technical_writer phase:1
Write detailed technical specifications based on the architecture

# 3. Implement backend
/agent backend_developer
Create WebSocket server with room management

# 4. Build frontend
/agent frontend_developer
Build React chat interface with real-time updates

# 5. Add security
/agent security_specialist
Review and secure the WebSocket implementation

# 6. Test everything
/agent qa_testing
Create integration tests for real-time features

# 7. Deploy
/agent devops_deployment
Create Docker deployment configuration
```

### Example 2: API Development

```bash
# In VS Code terminal
./coral run api_designer --task "Design REST API for blog platform"

# Then in Claude
/agent backend_developer
Implement the blog API with the following endpoints:
- POST /posts
- GET /posts
- GET /posts/{id}
- PUT /posts/{id}
- DELETE /posts/{id}

# Back in VS Code terminal
./coral run qa_testing --task "Generate API tests"
```

### Example 3: Database Design

```bash
# Using Claude
/agent database_specialist
Design a scalable database schema for:
- Multi-tenant SaaS application
- User management with roles
- Subscription billing
- Activity logging

# In VS Code
./coral run backend_developer --task "Generate Prisma/TypeORM models from schema"
```

## Best Practices

### 1. Project Structure

Organize your project for agent collaboration:

```
project/
├── .coral/                 # CoralCollective state
├── .vscode/               # VS Code settings
├── architecture/          # Architecture docs
├── specifications/        # Technical specs
├── src/                   # Source code
│   ├── backend/
│   ├── frontend/
│   └── shared/
├── tests/                 # Test files
├── docs/                  # Documentation
├── CLAUDE.md             # Agent instructions
└── README.md
```

### 2. Agent Instructions in CLAUDE.md

Provide clear context for agents:

```markdown
# CLAUDE.md

## Project Context
- Tech Stack: Node.js, React, PostgreSQL
- Architecture: Microservices
- Testing: Jest, Cypress
- Deployment: Docker, Kubernetes

## Agent Guidelines
- Follow existing code style
- Write comprehensive tests
- Update documentation
- Use TypeScript for all code
```

### 3. Git Workflow with Agents

1. **Create feature branch**:
   ```bash
   git checkout -b feature/agent-implementation
   ```

2. **Run agents**:
   ```bash
   ./coral run backend_developer --task "Implement feature"
   ```

3. **Review changes**:
   - Use VS Code Source Control
   - Or GitHub Desktop for visual review

4. **Commit with context**:
   ```bash
   git commit -m "feat: Add user authentication
   
   Implemented by: backend_developer agent
   CoralCollective session: $(date +%Y%m%d-%H%M%S)"
   ```

### 4. VS Code Snippets for Agents

Create `.vscode/coral.code-snippets`:

```json
{
  "Run Agent": {
    "prefix": "coral-agent",
    "body": [
      "/agent ${1|project_architect,backend_developer,frontend_developer,database_specialist,security_specialist,qa_testing|}",
      "",
      "${2:Task description}"
    ],
    "description": "Run CoralCollective agent"
  },
  "Agent Chain": {
    "prefix": "coral-chain",
    "body": [
      "/agent project_architect",
      "${1:Architecture task}",
      "",
      "/agent backend_developer", 
      "${2:Backend implementation}",
      "",
      "/agent frontend_developer",
      "${3:Frontend implementation}",
      "",
      "/agent qa_testing",
      "${4:Test creation}"
    ],
    "description": "Chain multiple agents"
  }
}
```

### 5. Debugging Agent Output

In VS Code, use the Output panel:

1. Open Output panel: `View > Output`
2. Select "CoralCollective" from dropdown
3. Monitor agent execution in real-time

### 6. Environment Setup

Create `.env` for API keys:

```bash
# AI Model Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# CoralCollective Settings
CORAL_MODEL_PROVIDER=openai
CORAL_DEFAULT_MODEL=gpt-4
CORAL_MCP_ENABLED=true
CORAL_LOG_LEVEL=INFO
```

## Troubleshooting

### Common Issues

1. **Agent not found**:
   ```bash
   # Ensure CoralCollective is initialized
   ./coral_drop.sh
   
   # List available agents
   ./coral list
   ```

2. **VS Code can't find coral command**:
   ```bash
   # Add to PATH in VS Code terminal
   export PATH=$PATH:$(pwd)
   
   # Or use full path
   ./coral run project_architect
   ```

3. **Claude doesn't recognize /agent**:
   - Ensure CLAUDE.md exists in project root
   - Include agent list in CLAUDE.md
   - Specify full agent names

4. **GitHub Desktop not showing changes**:
   - Refresh view: `Cmd+R` (Mac) / `Ctrl+R` (Windows)
   - Check .gitignore isn't excluding files
   - Ensure changes are saved in VS Code

## Additional Resources

- [CoralCollective Documentation](https://github.com/natesmalley/coral_collective/docs)
- [VS Code Python Guide](https://code.visualstudio.com/docs/python/python-tutorial)
- [GitHub Desktop Documentation](https://docs.github.com/desktop)
- [Claude Documentation](https://claude.ai/docs)

## Support

- GitHub Issues: https://github.com/natesmalley/coral_collective/issues
- Discord: [Join CoralCollective Discord]
- Email: support@coralcollective.dev