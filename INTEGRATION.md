# CoralCollective Integration Guide

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Integration Methods](#integration-methods)
   - [Python Interface](#python-interface)
   - [Command-Line Interface](#command-line-interface)
   - [Direct File Access](#direct-file-access)
   - [Subagent Invocation](#subagent-invocation)
4. [Usage Patterns](#usage-patterns)
5. [Workflows](#workflows)
6. [Shortcuts & Aliases](#shortcuts--aliases)
7. [Context Management](#context-management)
8. [MCP Integration](#mcp-integration)
9. [Configuration](#configuration)
10. [Advanced Usage](#advanced-usage)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)

## Overview

This guide explains how Claude (both Claude.ai and Claude Code) can directly interact with CoralCollective to access agent prompts, workflows, and orchestration capabilities. CoralCollective provides multiple integration methods from simple subagent invocation to full programmatic control.

## Quick Start

### Basic Subagent Invocation

The simplest way to use CoralCollective is through Claude's subagent notation:

```python
# Simple task delegation
@backend_developer "Create a REST API for user management"
@frontend_developer "Build a React dashboard with charts"
@qa_testing "Write comprehensive test suite"
```

### Chaining Multiple Agents

```python
# Sequential execution
@chain [@architect, @backend, @frontend, @qa] "Build a todo application"

# Workflow execution  
@workflow full_stack "Create an e-commerce platform"
```

## Integration Methods

### Python Interface

The primary entry point for programmatic interaction with CoralCollective.

#### Core Interface (`claude_interface.py`)

```python
from claude_interface import ClaudeInterface

# Initialize the interface
coral = ClaudeInterface()

# List all available agents
agents = coral.list_agents()

# Get a specific agent's prompt
prompt = coral.get_agent_prompt('backend_developer', 'Create a REST API')

# Get a complete workflow
workflow = coral.get_workflow('full_stack_web')

# Find agents by capability
api_agents = coral.get_agent_by_capability('api')
```

#### Subagent Registry

```python
from subagent_registry import coral_subagents
from subagent_registry import SubagentRegistry

# Invoke a subagent
result = coral_subagents('@backend_developer "Create REST API"')

# Get help
help_text = coral_subagents.help('@backend_developer')

# Run a workflow
results = coral_subagents.workflow('full_stack', 'Build todo app')

# Access the registry directly
registry = SubagentRegistry()

# Find agents by capability
api_agents = registry.get_agent_by_capability('api')

# Create custom chain
chain = registry.create_subagent_chain(['architect', 'backend', 'frontend'])
results = chain("Build dashboard")
```

### Command-Line Interface

Claude can execute shell commands to interact with CoralCollective:

```bash
# List all agents
python claude_interface.py list --json

# Get a specific agent prompt
python claude_interface.py get-prompt --agent backend_developer --task "Create user authentication"

# Get workflow information
python claude_interface.py workflow --workflow full_stack_web --json

# Find agents with specific capabilities
python claude_interface.py capability --capability api --json

# Get agents by category
python claude_interface.py category --category development --json

# Subagent registry commands
python subagent_registry.py list
python subagent_registry.py invoke --agent backend_developer --task "Create API"
python subagent_registry.py help --agent backend_developer
python subagent_registry.py workflow --workflow full_stack --task "Build app"
```

### Direct File Access

Claude can directly read agent prompts from the filesystem:

```python
# Agent prompts are organized as:
# - agents/core/project_architect.md
# - agents/core/technical_writer.md
# - agents/specialists/*.md

# Example: Read backend developer prompt
with open('agents/specialists/backend_developer.md', 'r') as f:
    prompt = f.read()
```

### Subagent Invocation

CoralCollective agents are available as Claude subagents using @ notation:

#### Direct Invocation
```python
@{agent_id} "{task}"

# Examples:
@backend_developer "Implement JWT authentication"
@database_specialist "Design normalized schema for blog"
@security_specialist "Audit authentication implementation"
```

#### Capability-Based
```python
@do/{capability} "{task}"

# Examples:
@do/api "Design RESTful endpoints"
@do/auth "Implement OAuth 2.0"
@do/testing "Create integration tests"
```

#### Role-Based
```python
@role/{role_name} "{task}"

# Examples:
@role/architect "Design microservices architecture"
@role/qa_testing "Validate user flows"
```

#### Category-Based
```python
@category/{category}/{agent} "{task}"

# Examples:
@category/development/backend "Create API"
@category/security/specialist "Security audit"
```

## Usage Patterns

### Pattern 1: Sequential Agent Execution

Claude can orchestrate multiple agents in sequence:

```python
from claude_interface import ClaudeInterface

coral = ClaudeInterface()

# Define the task
task = "Build a task management application"

# Get project template
template = coral.get_project_template('full_stack_web')

# Execute each agent in sequence
for agent in template['sequence']:
    agent_id = agent['id']
    prompt_result = coral.get_agent_prompt(agent_id, task)
    
    # Claude processes the prompt and generates output
    # Then passes context to next agent
    task = f"Continue building based on previous work: {task}"
```

### Pattern 2: Capability-Based Selection

Claude can select agents based on required capabilities:

```python
# Find all agents that can work with APIs
api_agents = coral.get_agent_by_capability('api')

# Find all security-related agents
security_agents = coral.get_category_agents('security')

# Select the most appropriate agent
for agent in api_agents:
    if 'design' in agent['all_capabilities']:
        # Use API Designer for API specification
        prompt = coral.get_agent_prompt(agent['id'], task)
```

### Pattern 3: Workflow Automation

Claude can follow predefined workflows:

```python
# Get a workflow definition
workflow = coral.get_workflow('ai_application')

# Process each phase
for phase in workflow['phases']:
    print(f"Phase: {phase['name']}")
    for agent_id in phase['agents']:
        prompt_result = coral.get_agent_prompt(agent_id, task)
        # Process with Claude's capabilities
```

## Workflows

### Full Stack Web Application
```python
@workflow full_stack "Build a task management app"
# Automatically runs:
# 1. @architect - System design
# 2. @requirements - Documentation
# 3. @backend - API implementation
# 4. @frontend - UI development
# 5. @db - Database setup
# 6. @qa - Testing
# 7. @security - Security audit
# 8. @devops - Deployment
# 9. @docs - User documentation
```

### API Service
```python
@workflow api_first "Create microservice API"
# Runs: @architect → @api → @backend → @db → @qa → @devops
```

### AI-Powered Application
```python
@workflow ai_powered "Build ML-powered app"
# Runs: @architect → @requirements → @ai → @backend → @frontend → @devops → @sre
```

## Shortcuts & Aliases

Quick aliases for common agents:

| Shortcut | Full Agent ID | Purpose |
|----------|---------------|---------|
| `@architect` | project_architect | System design & planning |
| `@backend` | backend_developer | Server-side development |
| `@frontend` | frontend_developer | UI/UX implementation |
| `@fullstack` | full_stack_engineer | End-to-end development |
| `@qa` | qa_testing | Testing & quality |
| `@api` | api_designer | API specification |
| `@db` | database_specialist | Database design |
| `@ai` | ai_ml_specialist | AI/ML integration |
| `@security` | security_specialist | Security implementation |
| `@devops` | devops_deployment | Deployment & CI/CD |

## Context Management

### Context Passing Between Agents

```python
# Initial context
context = {
    "project": "E-commerce platform",
    "tech_stack": ["Node.js", "React", "PostgreSQL"],
    "requirements": ["User auth", "Product catalog", "Shopping cart"]
}

# First agent
result1 = @architect "Design the system" with context

# Pass results to next agent
context["architecture"] = result1["output"]
result2 = @backend "Implement based on architecture" with context
```

### Context Preservation

Pass context between agents programmatically:

```python
context = {"task": initial_task, "completed": [], "outputs": {}}

for agent_id in agent_sequence:
    prompt = coral.get_agent_prompt(agent_id, json.dumps(context))
    # Process and update context
    context["completed"].append(agent_id)
```

### Auto-Chaining

Certain agents automatically suggest next agents:

```python
# After @project_architect
Suggested: [@technical_writer_phase1, @api_designer, @database_specialist]

# After @backend_developer  
Suggested: [@frontend_developer, @database_specialist, @qa_testing]

# After @qa_testing
Suggested: [@devops_deployment, @performance_engineer]
```

## MCP Integration

When MCP (Model Context Protocol) is enabled, Claude can directly execute actions through the agents:

```python
from mcp.mcp_client import MCPClient
from claude_interface import ClaudeInterface

# Initialize both interfaces
coral = ClaudeInterface()
mcp = MCPClient()

# Get agent and its MCP permissions
agent_id = 'backend_developer'
agent_prompt = coral.get_agent_prompt(agent_id, task)
agent_tools = mcp.get_tools_for_agent(agent_id)

# Claude can now use both the prompt and tools
# to directly implement the solution
```

## Configuration

The integration uses `claude_code_agents.json` for configuration:

```json
{
  "agents": {
    "agent_id": {
      "name": "Agent Name",
      "category": "category",
      "description": "What the agent does",
      "prompt_path": "path/to/prompt.md",
      "capabilities": ["cap1", "cap2"]
    }
  },
  "workflows": {
    "workflow_id": {
      "name": "Workflow Name",
      "phases": [...]
    }
  }
}
```

## Advanced Usage

### Custom Chains
```python
# Define custom sequence
my_chain = [@architect, @api, @backend, @qa]
@chain my_chain "Build REST service"
```

### Conditional Agents
```python
# Use different agents based on requirements
if "mobile" in requirements:
    @mobile_developer "Build mobile app"
else:
    @frontend_developer "Build web app"
```

### Parallel Execution
```python
# Run multiple agents for different components
@parallel [
    @backend "Create API",
    @frontend "Build UI",
    @mobile "Create mobile app"
] "Multi-platform application"
```

## Best Practices

### 1. Start with Architecture
Always begin complex projects with:
```python
@architect "Design the system"
```

### 2. Use Appropriate Specialists
Match the agent to the task:
- `@backend` for APIs and server logic
- `@frontend` for UI/UX
- `@db` for database design
- `@security` for security concerns
- `@qa` for testing

### 3. Follow the Workflow
For complete projects, use workflows:
```python
@workflow full_stack "Your project description"
```

### 4. Error Handling
Always check for agent availability:

```python
result = coral.get_agent_prompt(agent_id, task)
if result['status'] == 'error':
    # Handle missing agent
    print(f"Agent not found: {result['message']}")
    # Use alternative agent
```

### 5. Capability Matching
Match agents to requirements:

```python
required_capabilities = ['api', 'auth', 'database']
suitable_agents = []

for capability in required_capabilities:
    agents = coral.get_agent_by_capability(capability)
    suitable_agents.extend(agents)

# Select best agent based on multiple capabilities
```

### 6. Validate with QA
Always include testing:
```python
@qa "Test the implementation"
```

## Troubleshooting

### Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Agent not found | Check agent_id matches JSON config |
| Prompt file missing | Verify prompt_path in configuration |
| No suitable agent | Use capability search to find alternatives |
| Workflow fails | Check all agents in sequence exist |

### Error Handling for Subagents

If a subagent is not found:
```python
result = @unknown_agent "Task"
# Returns: {
#   "status": "error",
#   "message": "Subagent unknown_agent not found",
#   "available_subagents": [...]
# }
```

## Available Methods

### Core Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `list_agents()` | Get all available agents | Dict of agents with metadata |
| `get_agent_prompt(agent_id, task)` | Get prompt for specific agent | Prompt text and metadata |
| `get_workflow(workflow_type)` | Get workflow definition | Phases and agent sequences |
| `get_project_template(template_name)` | Get project template | Ordered agent sequence |

### Discovery Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `get_agent_by_capability(capability)` | Find agents with capability | List of matching agents |
| `get_category_agents(category)` | Get agents in category | List of category agents |
| `get_recommended_next_agents(agent)` | Get next agent suggestions | List of agent IDs |

### Execution Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `execute_agent_sequence(agents, task)` | Run multiple agents | List of results |

## Usage Examples by Task Type

### Building a New Application
```python
# Start with architecture
@architect "Design a social media platform with real-time features"

# Then implementation
@backend "Implement the API based on the architecture"
@frontend "Build the UI components"
@db "Create the database schema"

# Quality and deployment
@qa "Write tests for all features"
@security "Audit the implementation"
@devops "Deploy to production"
```

### Adding Features
```python
# For a new feature
@architect "Design notification system"
@backend "Add notification endpoints"
@frontend "Create notification UI"
@qa "Test notification flow"
```

### Fixing Issues
```python
# Performance issues
@performance_engineer "Identify bottlenecks in API"
@backend "Optimize based on performance analysis"

# Security issues
@security "Audit authentication system"
@backend "Fix security vulnerabilities"
```

### Documentation
```python
# Technical documentation
@technical_writer_phase1 "Create API documentation"

# User documentation
@technical_writer_phase2 "Write user guides"
```

## Extending the Integration

To add new capabilities:

1. **Add new methods** to `ClaudeInterface` class
2. **Create new workflows** in `claude_code_agents.json`
3. **Add MCP tools** for direct execution
4. **Create custom agents** in `agents/` directory

## Summary

CoralCollective integration provides Claude with:

- **21+ specialized agents** for different development tasks
- **Multiple integration methods** (subagents, Python API, CLI)
- **Simple @ notation** for invocation
- **Workflow templates** for complete projects
- **Context passing** between agents
- **Auto-chaining** for sequential tasks
- **Capability-based** agent discovery
- **MCP tool integration** for actions
- **Flexible discovery** of agents by capability

This enables Claude to leverage specialized expertise for any software development task, from architecture to deployment, through both simple invocation and complex orchestration patterns.