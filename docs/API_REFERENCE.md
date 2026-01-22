# CoralCollective API Reference 🪸

## Table of Contents

1. [Overview](#overview)
2. [Core APIs](#core-apis)
3. [Agent Runner API](#agent-runner-api)
4. [Project State API](#project-state-api)
5. [MCP Client API](#mcp-client-api)
6. [Project Manager API](#project-manager-api)
7. [CLI Commands](#cli-commands)
8. [Python Examples](#python-examples)
9. [Error Handling](#error-handling)
10. [Configuration](#configuration)

## Overview

CoralCollective provides comprehensive APIs for agent orchestration, project state management, and project lifecycle control. This reference covers all public APIs with examples and usage patterns.

### Quick Start Example

```python
from coral_collective import AgentRunner, ProjectManager

# Initialize core components
runner = AgentRunner()
pm = ProjectManager()

# Run an agent
result = runner.run_agent('backend_developer', 'Create REST API')
print(f"Success: {result.success}")
print(f"Output: {result.output}")
```

## Core APIs

### ClaudeInterface

The main entry point for Claude integration.

```python
from coral_collective.claude_interface import ClaudeInterface

class ClaudeInterface:
    def __init__(self, config_path: Optional[str] = None):
        """Initialize Claude interface with optional config path."""
        
    def list_agents(self) -> Dict[str, Dict[str, Any]]:
        """List all available agents with metadata."""
        
    def get_agent_prompt(self, agent_id: str, task: str) -> Dict[str, Any]:
        """Get formatted prompt for specific agent and task."""
        
    def get_workflow(self, workflow_type: str) -> Dict[str, Any]:
        """Get workflow definition by type."""
        
    def get_agent_by_capability(self, capability: str) -> List[Dict[str, Any]]:
        """Find agents by capability."""
```

#### Usage Examples

```python
# Initialize interface
coral = ClaudeInterface()

# List available agents
agents = coral.list_agents()
for agent_id, info in agents.items():
    print(f"{agent_id}: {info['name']}")

# Get agent prompt
prompt_data = coral.get_agent_prompt('backend_developer', 'Create user authentication')
print(prompt_data['prompt'])

# Find agents by capability
api_agents = coral.get_agent_by_capability('api')
print(f"Found {len(api_agents)} agents with API capability")

# Get workflow
workflow = coral.get_workflow('full_stack_web')
for phase in workflow['phases']:
    print(f"Phase: {phase['name']}")
```

### SubagentRegistry

Registry for subagent invocation and management.

```python
from coral_collective.subagent_registry import SubagentRegistry, coral_subagents

class SubagentRegistry:
    def __init__(self):
        """Initialize subagent registry."""
        
    def invoke(self, agent_notation: str) -> Dict[str, Any]:
        """Invoke subagent using @notation."""
        
    def get_agent_help(self, agent_id: str) -> str:
        """Get help text for specific agent."""
        
    def list_agents(self) -> List[str]:
        """List all available subagent IDs."""
        
    def create_workflow(self, workflow_id: str, task: str) -> Dict[str, Any]:
        """Execute predefined workflow."""
```

#### Usage Examples

```python
# Direct subagent invocation
result = coral_subagents('@backend_developer "Create REST API with JWT auth"')

# Get agent help
help_text = coral_subagents.help('@qa_testing')
print(help_text)

# List all agents
registry = SubagentRegistry()
agents = registry.list_agents()

# Run workflow
workflow_result = registry.create_workflow('full_stack', 'Build todo app')
```

## Agent Runner API

Core agent execution and orchestration engine.

### AgentRunner Class

```python
from coral_collective.agent_runner import AgentRunner

class AgentRunner:
    def __init__(self, 
                 config_path: Optional[str] = None,
                 mcp_enabled: bool = False,
                 project_tracking: bool = True):
        """Initialize agent runner with optional MCP and project tracking support."""
        
    def run_agent(self, 
                  agent_id: str, 
                  task: str, 
                  context: Optional[Dict] = None) -> AgentResult:
        """Execute a single agent."""
        
    def run_workflow(self, 
                     workflow_name: str, 
                     task: str,
                     context: Optional[Dict] = None) -> WorkflowResult:
        """Execute a complete workflow."""
        
    def get_agent_config(self, agent_id: str) -> Dict[str, Any]:
        """Get configuration for specific agent."""
        
    def list_agents(self) -> List[str]:
        """List all available agent IDs."""
        
    def validate_agent(self, agent_id: str) -> bool:
        """Check if agent exists and is valid."""
```

### AgentResult Class

```python
@dataclass
class AgentResult:
    success: bool
    output: str
    agent_id: str
    task: str
    execution_time: float
    metadata: Dict[str, Any]
    next_agents: List[str]
    context: Dict[str, Any]
    errors: List[str]
```

### WorkflowResult Class

```python
@dataclass
class WorkflowResult:
    success: bool
    workflow_name: str
    task: str
    agent_results: List[AgentResult]
    total_execution_time: float
    final_output: str
    metadata: Dict[str, Any]
    errors: List[str]
```

### Usage Examples

```python
from coral_collective.agent_runner import AgentRunner

# Initialize runner
runner = AgentRunner(mcp_enabled=True, project_tracking=True)

# Run single agent
result = runner.run_agent('project_architect', 'Design e-commerce platform')

if result.success:
    print(f"Agent completed: {result.output}")
    print(f"Execution time: {result.execution_time:.2f}s")
    print(f"Next recommended agents: {result.next_agents}")
else:
    print(f"Agent failed: {result.errors}")

# Run workflow
workflow_result = runner.run_workflow('full_stack_web', 'Build task manager')

for i, agent_result in enumerate(workflow_result.agent_results):
    print(f"Step {i+1}: {agent_result.agent_id} - {agent_result.success}")

# Context passing between agents
context = {
    'project_name': 'TaskManager',
    'tech_stack': ['Node.js', 'React', 'PostgreSQL'],
    'features': ['auth', 'tasks', 'teams']
}

result1 = runner.run_agent('project_architect', 'Design system', context)
result2 = runner.run_agent('backend_developer', 'Implement API', result1.context)
```

## Project State API

Project state management and context tracking.

### ProjectStateManager Class

```python
from coral_collective.tools.project_state import ProjectStateManager

class ProjectStateManager:
    def __init__(self, 
                 state_dir: Optional[str] = None):
        """Initialize project state manager."""
        
    def save_state(self, 
                   project_id: str,
                   state_data: Dict[str, Any]) -> bool:
        """Save project state."""
        
    def load_state(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Load project state."""
        
    def update_state(self, 
                     project_id: str,
                     updates: Dict[str, Any]) -> bool:
        """Update existing project state."""
        
    def delete_state(self, project_id: str) -> bool:
        """Delete project state."""
        
    def get_project_context(self, project_id: str) -> Dict[str, Any]:
        """Get accumulated context for project."""
        
    def clear_project_context(self, project_id: str) -> bool:
        """Clear all state for project."""
        
    def list_states(self) -> List[str]:
        """List all saved project states."""
```

### State Structure

```python
@dataclass
class ProjectState:
    project_id: str
    name: str
    phase: str
    status: str
    agents_completed: List[str]
    current_agent: Optional[str]
    context: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
```

### Usage Examples

```python
from coral_collective.tools.project_state import ProjectStateManager

# Initialize state manager
state_manager = ProjectStateManager()

# Save project state
state_manager.save_state(
    project_id='ecommerce_app',
    state_data={
        'name': 'E-commerce Platform',
        'phase': 'development',
        'status': 'in_progress',
        'agents_completed': ['project_architect', 'technical_writer'],
        'current_agent': 'backend_developer',
        'context': {
            'tech_stack': ['Node.js', 'React', 'PostgreSQL'],
            'features': ['authentication', 'catalog', 'checkout']
        }
    }
)

# Load project state
state = state_manager.load_state('ecommerce_app')
if state:
    print(f"Project: {state['name']}")
    print(f"Current Phase: {state['phase']}")
    print(f"Completed Agents: {', '.join(state['agents_completed'])}")

# Update state
state_manager.update_state(
    project_id='ecommerce_app',
    updates={
        'agents_completed': state['agents_completed'] + ['backend_developer'],
        'current_agent': 'frontend_developer'
    }
)

# Get project context
context = state_manager.get_project_context('ecommerce_app')
print(f"Tech Stack: {context['tech_stack']}")
```

## MCP Client API

Model Context Protocol integration for direct tool access.

### MCPClient Class

```python
from coral_collective.mcp.mcp_client import MCPClient

class MCPClient:
    def __init__(self, config_path: Optional[str] = None):
        """Initialize MCP client with server configurations."""
        
    def list_tools(self, server_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available tools from MCP servers."""
        
    def call_tool(self, 
                  tool_name: str, 
                  arguments: Dict[str, Any],
                  server_name: Optional[str] = None) -> Dict[str, Any]:
        """Execute tool through MCP server."""
        
    def get_server_info(self, server_name: str) -> Dict[str, Any]:
        """Get information about specific MCP server."""
        
    def get_agent_permissions(self, agent_id: str) -> List[str]:
        """Get MCP tools allowed for specific agent."""
        
    def health_check(self) -> Dict[str, bool]:
        """Check health status of all MCP servers."""
```

### Usage Examples

```python
from coral_collective.mcp.mcp_client import MCPClient

# Initialize MCP client
mcp = MCPClient()

# List all available tools
tools = mcp.list_tools()
for tool in tools:
    print(f"Tool: {tool['name']} - {tool['description']}")

# Execute filesystem operation
result = mcp.call_tool(
    'filesystem_read',
    {'path': '/project/src/api.js'},
    server_name='filesystem'
)

if result['success']:
    print(f"File content: {result['content']}")

# GitHub operations
github_result = mcp.call_tool(
    'github_create_pr',
    {
        'title': 'Add authentication system',
        'branch': 'feature/auth',
        'description': 'Implements JWT-based authentication'
    },
    server_name='github'
)

# Check what tools an agent can use
agent_tools = mcp.get_agent_permissions('backend_developer')
print(f"Backend Developer can use: {agent_tools}")

# Health check
health = mcp.health_check()
for server, status in health.items():
    print(f"{server}: {'✅' if status else '❌'}")
```

## Project Manager API

Project lifecycle and state management.

### ProjectManager Class

```python
from coral_collective.project_manager import ProjectManager

class ProjectManager:
    def __init__(self, projects_dir: Optional[str] = None):
        """Initialize project manager."""
        
    def create_project(self, 
                       project_name: str, 
                       project_type: str,
                       description: Optional[str] = None) -> Project:
        """Create new project."""
        
    def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID."""
        
    def list_projects(self) -> List[Project]:
        """List all projects."""
        
    def update_project_status(self, 
                              project_id: str, 
                              status: str,
                              metadata: Optional[Dict] = None) -> bool:
        """Update project status."""
        
    def get_project_state(self, project_id: str) -> Dict[str, Any]:
        """Get current project state."""
        
    def export_project(self, 
                       project_id: str, 
                       format: str = 'json') -> str:
        """Export project data."""
```

### Project Class

```python
@dataclass
class Project:
    project_id: str
    name: str
    description: str
    project_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    agents_used: List[str]
    current_phase: str
    progress: float
```

### Usage Examples

```python
from coral_collective.project_manager import ProjectManager

# Initialize project manager
pm = ProjectManager()

# Create new project
project = pm.create_project(
    project_name="E-commerce Platform",
    project_type="full_stack_web",
    description="Multi-vendor e-commerce platform with real-time features"
)

# Update project status
pm.update_project_status(
    project.project_id,
    "development",
    metadata={
        'current_agent': 'backend_developer',
        'completed_agents': ['project_architect', 'technical_writer_phase1'],
        'progress': 0.3
    }
)

# Get project state
state = pm.get_project_state(project.project_id)
print(f"Project: {state['name']}")
print(f"Status: {state['status']}")
print(f"Progress: {state['progress']:.1%}")

# List all projects
projects = pm.list_projects()
for proj in projects:
    print(f"{proj.name}: {proj.status} ({proj.progress:.1%})")

# Export project data
export_data = pm.export_project(project.project_id, format='json')
```

## CLI Commands

Command-line interface for CoralCollective operations.

### Basic Commands

```bash
# Check version and system health
coral --version
coral check
coral check --all --verbose

# List agents
coral list
coral list --category specialists
coral list --capability api

# Run single agent
coral run project_architect --task "Design microservices architecture"
coral run backend_developer --task "Create user API" --context project_context.json

# Run workflows
coral workflow full_stack --task "Build todo application"
coral workflow api_first --task "Create microservice"

# Project management
coral init --name "MyProject" --type web_app
coral status
coral save-state project_state.json
coral load-state project_state.json
```

### Advanced Commands

```bash
# MCP operations
coral setup mcp
coral mcp list-tools
coral mcp health-check
coral mcp call-tool --tool filesystem_read --args '{"path": "src/api.js"}'

# Project state operations
coral state save --project myproject
coral state load --project myproject
coral state update --project myproject --phase development
coral state clear --project myproject

# Agent development
coral agent create --name "custom_agent" --category specialists
coral agent validate --agent backend_developer
coral agent test --agent qa_testing --task "test sample"

# System operations
coral deploy --environment production
coral monitor --metrics
coral logs --level debug --last 100
```

### CLI Examples

```bash
# Complete project workflow
coral init --name "TaskManager" --type web_app
coral run project_architect --task "Design task management app with teams"
coral workflow full_stack --project TaskManager
coral deploy --environment staging

# Agent chaining
coral run project_architect --task "Design API" --save-context
coral run backend_developer --load-context --task "Implement based on architecture"
coral run qa_testing --load-context --task "Test the implementation"

# MCP-enabled development
coral setup mcp --servers github,filesystem,postgresql
coral run backend_developer --mcp --task "Create API with database"
# Agent automatically uses GitHub, filesystem, and database tools

# State-enabled context
coral state init --project myproject
coral run project_architect --state --task "Design system"
coral run backend_developer --state --task "Continue from architecture"
# Context automatically preserved across agents
```

## Python Examples

### Complete Project Example

```python
from coral_collective import AgentRunner, ProjectManager, ProjectManager

# Initialize components
runner = AgentRunner(mcp_enabled=True, project_tracking=True)
pm = ProjectManager()
pm = ProjectManager()

# Create project
project = pm.create_project("TaskManager", "full_stack_web")

# Define task
task = "Build a team-based task management application with real-time updates"

# Context for all agents
context = {
    'project_id': project.project_id,
    'requirements': [
        'User authentication and authorization',
        'Team creation and management',
        'Task CRUD operations',
        'Real-time updates via WebSocket',
        'File attachments for tasks',
        'Email notifications'
    ],
    'tech_preferences': {
        'backend': 'Node.js + Express',
        'frontend': 'React + TypeScript',
        'database': 'PostgreSQL',
        'real_time': 'Socket.io',
        'auth': 'JWT',
        'deployment': 'Docker Compose'
    }
}

# Execute workflow
agents_sequence = [
    'project_architect',
    'technical_writer_phase1',
    'backend_developer',
    'database_specialist',
    'frontend_developer',
    'security_specialist',
    'qa_testing',
    'devops_deployment',
    'technical_writer_phase2'
]

results = []
current_context = context.copy()

for agent_id in agents_sequence:
    print(f"🤖 Running {agent_id}...")
    
    # Execute agent
    result = runner.run_agent(agent_id, task, current_context)
    results.append(result)
    
    if result.success:
        print(f"✅ {agent_id} completed successfully")
        
        # Store result in memory
        memory.store_memory(
            content=result.output,
            metadata={
                'project_id': project.project_id,
                'agent_id': agent_id,
                'execution_time': result.execution_time
            }
        )
        
        # Update context for next agent
        current_context.update(result.context)
        
        # Update project status
        progress = (len([r for r in results if r.success]) / len(agents_sequence))
        pm.update_project_status(
            project.project_id,
            "in_progress",
            metadata={
                'current_agent': agent_id,
                'progress': progress,
                'last_success': True
            }
        )
        
        print(f"📊 Project progress: {progress:.1%}")
        
    else:
        print(f"❌ {agent_id} failed: {result.errors}")
        break

# Final project status
if all(r.success for r in results):
    pm.update_project_status(project.project_id, "completed")
    print("🎉 Project completed successfully!")
else:
    print("⚠️ Project completed with errors")

# Export results
export_data = pm.export_project(project.project_id)
print(f"📄 Project data exported: {len(export_data)} characters")
```

### MCP Integration Example

```python
from coral_collective import AgentRunner, MCPClient

# Initialize with MCP
runner = AgentRunner(mcp_enabled=True)
mcp = MCPClient()

# Check available tools
tools = mcp.list_tools()
github_tools = [t for t in tools if 'github' in t['name']]
print(f"Available GitHub tools: {len(github_tools)}")

# Run agent with MCP access
result = runner.run_agent(
    'backend_developer',
    'Create a REST API for user management with authentication',
    {
        'mcp_tools': ['filesystem', 'github'],
        'repository': 'myorg/myproject',
        'branch': 'feature/user-api'
    }
)

if result.success:
    # Agent automatically:
    # 1. Created files using filesystem MCP
    # 2. Committed changes using GitHub MCP
    # 3. Created pull request using GitHub MCP
    print("✅ API created and PR submitted automatically")
    print(f"MCP tools used: {result.metadata.get('mcp_tools_used', [])}")
```

### Project State Example

```python
from coral_collective import AgentRunner, ProjectManager
from coral_collective.tools.project_state import ProjectStateManager

# Initialize with state tracking
runner = AgentRunner(project_tracking=True)
pm = ProjectManager()
state_manager = ProjectStateManager()

# Save initial project state
state_manager.save_state(
    project_id='ecommerce',
    state_data={
        'name': 'E-commerce Platform',
        'architecture': 'Microservices with API Gateway',
        'phase': 'design',
        'agents_completed': ['project_architect']
    }
)

# Run development agents with state context
backend_result = runner.run_agent(
    'backend_developer',
    'Implement user service based on architectural decisions',
    {'project_id': 'ecommerce'}
)

# Update state after backend completion
state_manager.update_state(
    project_id='ecommerce',
    updates={
        'agents_completed': ['project_architect', 'backend_developer'],
        'current_agent': 'frontend_developer'
    }
)

frontend_result = runner.run_agent(
    'frontend_developer', 
    'Create user interface for the user service',
    {'project_id': 'ecommerce'}
)

# State system provides context about:
# - Project architecture
# - Completed components
# - Current progress
```

## Error Handling

### Exception Types

```python
from coral_collective.exceptions import (
    AgentNotFoundError,
    WorkflowExecutionError,
    MCPConnectionError,
    StateManagementError,
    ConfigurationError
)

try:
    result = runner.run_agent('nonexistent_agent', 'task')
except AgentNotFoundError as e:
    print(f"Agent not found: {e}")
    # Show available agents
    available = runner.list_agents()
    print(f"Available agents: {available}")
    
except WorkflowExecutionError as e:
    print(f"Workflow failed: {e}")
    # Check which step failed
    print(f"Failed at step: {e.failed_step}")
    print(f"Error details: {e.details}")
    
except MCPConnectionError as e:
    print(f"MCP server unavailable: {e}")
    # Check server status
    health = mcp.health_check()
    print(f"Server status: {health}")
    
except StateManagementError as e:
    print(f"State operation failed: {e}")
    # Fallback to non-memory operation
    
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    print("Check your configuration files and environment variables")
```

### Error Response Format

```python
# Standardized error response
{
    "success": false,
    "error_type": "AgentNotFoundError",
    "error_message": "Agent 'invalid_agent' not found",
    "error_code": "AGENT_404",
    "details": {
        "agent_id": "invalid_agent",
        "available_agents": ["project_architect", "backend_developer", ...]
    },
    "timestamp": "2025-01-07T10:30:00Z",
    "request_id": "req_123456"
}
```

## Configuration

### Environment Variables

```bash
# Core Configuration
CORAL_CONFIG_PATH=/path/to/config
CORAL_AGENTS_PATH=/path/to/agents
CORAL_LOG_LEVEL=INFO

# MCP Configuration
CORAL_MCP_ENABLED=true
CORAL_MCP_CONFIG_PATH=/path/to/mcp/config

# Memory System
CORAL_MEMORY_ENABLED=true
CORAL_MEMORY_TYPE=local  # or 'cloud'
CORAL_MEMORY_PERSIST_PATH=/path/to/memory

# API Keys (for MCP servers)
GITHUB_TOKEN=ghp_xxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx
```

### Configuration Files

#### `coral_config.yaml`

```yaml
# Core settings
core:
  agents_path: "./agents"
  config_path: "./config"
  log_level: "INFO"
  default_timeout: 300

# Agent settings
agents:
  default_context_size: 100000
  max_execution_time: 600
  enable_handoffs: true

# MCP settings
mcp:
  enabled: true
  config_path: "./mcp/configs"
  default_timeout: 30
  retry_attempts: 3

# Memory settings
memory:
  enabled: true
  type: "local"
  persist_path: "./memory_data"
  max_memories: 10000
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
```

### Loading Configuration

```python
from coral_collective.config import load_config

# Load default configuration
config = load_config()

# Load custom configuration
config = load_config("/path/to/custom/config.yaml")

# Access configuration values
agents_path = config['core']['agents_path']
mcp_enabled = config['mcp']['enabled']
memory_type = config['memory']['type']
```

---

## API Versioning

CoralCollective follows semantic versioning (SemVer) for its APIs:

- **Major version** changes indicate breaking API changes
- **Minor version** changes add new features without breaking existing functionality
- **Patch version** changes include bug fixes and minor improvements

### Version Compatibility

```python
import coral_collective

# Check version
print(coral_collective.__version__)  # e.g., "1.2.3"

# Check API compatibility
if coral_collective.api_version >= "1.2":
    # Use new features
    result = runner.run_agent_with_streaming(agent_id, task)
else:
    # Fallback to older API
    result = runner.run_agent(agent_id, task)
```

### Migration Guide

When upgrading between major versions, check the [CHANGELOG.md](CHANGELOG.md) for breaking changes and migration instructions.

---

**This API reference is continuously updated. For the latest information, check the source code documentation and inline docstrings.**