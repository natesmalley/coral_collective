# CoralCollective Integration Guide

This guide explains how to integrate CoralCollective into your projects and workflows.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Integration Methods](#integration-methods)
3. [Python Package Integration](#python-package-integration)
4. [Docker Integration](#docker-integration)
5. [Drop-In Integration](#drop-in-integration)
6. [API Integration](#api-integration)

## Quick Start

The fastest way to add CoralCollective to an existing project:

```bash
# Download and run the drop-in installer
curl -O https://raw.githubusercontent.com/coral-collective/coral-collective/main/coral_drop.sh
bash coral_drop.sh

# Use the coral command
./coral run project_architect
```

## Integration Methods

### 1. Python Package (Recommended)

Install CoralCollective as a Python package:

```bash
pip install coral-collective

# With optional features
pip install coral-collective[mcp,dev]
```

Use in your Python code:

```python
from coral_collective import AgentRunner, ProjectManager

# Initialize runner
runner = AgentRunner()

# Run an agent
result = runner.run_agent(
    'backend_developer',
    'Create user authentication API',
    context={'tech_stack': ['Python', 'FastAPI']}
)

# Manage project state
pm = ProjectManager()
project = pm.create_project(
    'my_app',
    'web_application',
    'E-commerce platform'
)
```

### 2. Docker Integration

Run CoralCollective in a container:

```bash
# Pull the image
docker pull coralcollective/coral:latest

# Run interactively
docker run -it --rm \
  -v $(pwd):/workspace \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  coralcollective/coral

# Using docker-compose
docker-compose up
```

Docker Compose configuration:

```yaml
version: '3.8'
services:
  coral:
    image: coralcollective/coral:latest
    volumes:
      - .:/workspace
      - ./config:/app/config
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    stdin_open: true
    tty: true
```

### 3. Drop-In Integration

Add CoralCollective to an existing project without modifying its structure:

```bash
# Run the drop-in script
./coral_drop.sh

# This creates:
# - .coral/ directory for state and cache
# - coral wrapper command
# - .coralrc configuration file
```

The drop-in method is ideal for:
- Existing projects that need AI assistance
- Teams wanting to try CoralCollective without commitment
- Projects with strict file structure requirements

### 4. Git Submodule

Add as a git submodule:

```bash
git submodule add https://github.com/coral-collective/coral-collective.git
git submodule update --init --recursive

# Use from submodule
python coral-collective/agent_runner.py
```

## API Integration

### REST API (Coming Soon)

Future versions will include a REST API server:

```python
# Start API server
coral serve --port 8080

# Make requests
POST /api/agents/run
{
  "agent": "backend_developer",
  "task": "Create REST API",
  "context": {...}
}
```

### Python API

Direct Python integration:

```python
from coral_collective import AgentRunner
from coral_collective.tools.project_state import ProjectStateManager

class MyApplication:
    def __init__(self):
        self.coral = AgentRunner()
        self.state = ProjectStateManager()
    
    def generate_code(self, requirements):
        # Run architect first
        arch_result = self.coral.run_agent(
            'project_architect',
            requirements
        )
        
        # Save state
        self.state.save_state(
            'my_project',
            {'architecture': arch_result.output}
        )
        
        # Run implementation agents
        backend = self.coral.run_agent(
            'backend_developer',
            'Implement based on architecture',
            context=arch_result.context
        )
        
        return backend.output
```

## Environment Configuration

### Required Environment Variables

```bash
# AI Model API Keys (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# Optional Configuration
CORAL_MODEL_PROVIDER=openai  # or anthropic, google
CORAL_MODEL_DEFAULT=gpt-4
CORAL_MCP_ENABLED=false
```

### Configuration Files

`.coralrc` - Project-specific settings:
```bash
CORAL_HOME=.coral
CORAL_PYTHON=python3
CORAL_MODEL_PROVIDER=openai
```

`config/agents.yaml` - Agent definitions
`config/model_assignments_2026.yaml` - Model routing

## MCP Integration

Enable Model Context Protocol for tool access:

```python
from coral_collective import AgentRunner

# Enable MCP
runner = AgentRunner(mcp_enabled=True)

# Agents can now use:
# - GitHub operations
# - Docker management  
# - Database queries
# - File system access (sandboxed)
```

## Workflow Integration

### Sequential Workflow

```python
from coral_collective import AgentRunner

runner = AgentRunner()

# Define workflow
workflow = [
    ('project_architect', 'Design e-commerce platform'),
    ('backend_developer', 'Implement API'),
    ('frontend_developer', 'Create UI'),
    ('qa_testing', 'Write tests'),
    ('devops_deployment', 'Deploy to cloud')
]

# Execute workflow
results = []
context = {}
for agent, task in workflow:
    result = runner.run_agent(agent, task, context)
    results.append(result)
    context = result.context
```

### Parallel Execution

```python
import asyncio
from coral_collective import AgentRunner

async def parallel_development():
    runner = AgentRunner()
    
    # Run backend and frontend in parallel
    tasks = [
        runner.run_agent_async('backend_developer', 'Create API'),
        runner.run_agent_async('frontend_developer', 'Build UI'),
        runner.run_agent_async('database_specialist', 'Design schema')
    ]
    
    results = await asyncio.gather(*tasks)
    return results
```

## CI/CD Integration

### GitHub Actions

```yaml
name: AI-Assisted Development
on: [push, pull_request]

jobs:
  coral-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup CoralCollective
        run: |
          pip install coral-collective
          
      - name: Run Architecture Review
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          coral run architecture_compliance_auditor \
            --task "Review architecture changes"
            
      - name: Generate Tests
        run: |
          coral run qa_testing \
            --task "Generate unit tests for changed files"
```

### GitLab CI

```yaml
coral-assist:
  image: coralcollective/coral:latest
  script:
    - coral run security_specialist --task "Security audit"
    - coral run performance_engineer --task "Performance review"
  variables:
    OPENAI_API_KEY: $OPENAI_API_KEY
```

## Best Practices

1. **State Management**: Always save project state between agent runs
2. **Context Passing**: Pass context between agents for continuity
3. **Model Selection**: Use appropriate models for each agent (see model_assignments_2026.yaml)
4. **Error Handling**: Wrap agent calls in try-catch blocks
5. **Rate Limiting**: Implement rate limiting for API calls
6. **Caching**: Cache agent outputs when possible
7. **Security**: Never commit API keys; use environment variables

## Troubleshooting

### Common Issues

**Import Errors**
```python
# If imports fail, add to Python path
import sys
sys.path.append('/path/to/coral_collective')
```

**API Key Issues**
```bash
# Check if keys are set
python -c "import os; print('Key set:', bool(os.getenv('OPENAI_API_KEY')))"
```

**Permission Errors**
```bash
# Make scripts executable
chmod +x coral coral_drop.sh start.sh
```

## Support

- GitHub Issues: https://github.com/coral-collective/coral-collective/issues
- Documentation: https://coral-collective.dev/docs
- Discord: https://discord.gg/coral-collective

## License

MIT License - See LICENSE file for details