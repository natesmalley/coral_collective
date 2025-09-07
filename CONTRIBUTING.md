# Contributing to CoralCollective 🪸

Thank you for your interest in contributing to CoralCollective! This guide will help you set up your development environment and understand our contribution process.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Code Quality Standards](#code-quality-standards)
4. [Testing Requirements](#testing-requirements)
5. [Agent Development Guidelines](#agent-development-guidelines)
6. [Pull Request Process](#pull-request-process)
7. [Security Considerations](#security-considerations)
8. [Documentation](#documentation)
9. [Community](#community)

## Getting Started

### Prerequisites

- Python 3.8+ (3.11+ recommended)
- Git
- Virtual environment (REQUIRED - never install system-wide)
- Docker (optional, for MCP integration testing)

### First Contribution Checklist

- [ ] Read this entire contributing guide
- [ ] Set up development environment
- [ ] Run the test suite successfully
- [ ] Make a small test change
- [ ] Submit your first pull request

## Development Setup

### ⚠️ IMPORTANT: Virtual Environment Required

**NEVER install CoralCollective system-wide.** Always use a virtual environment:

```bash
# Create virtual environment (REQUIRED)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Verify you're in virtual environment
which python  # Should show venv/bin/python
```

### 1. Clone and Setup

```bash
# Fork the repository on GitHub first, then:
git clone https://github.com/YOUR_USERNAME/coral-collective.git
cd coral-collective

# Create and activate virtual environment (REQUIRED)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip and install build tools
pip install --upgrade pip setuptools wheel

# Install development dependencies
pip install -e .[dev,all]

# Install pre-commit hooks for code quality
pre-commit install
```

### 2. Verify Installation

```bash
# Check system health
python -c "import coral_collective; print('✅ Core package installed')"

# Verify CLI works
coral --version
coral list

# Run quick tests
pytest tests/unit/ -v

# Verify pre-commit hooks
pre-commit run --all-files
```

### 3. Development Environment

```bash
# Set up MCP servers for testing (optional)
cd mcp && ./setup_mcp.sh

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys for testing

# Test MCP integration
python -c "from coral_collective.mcp.mcp_client import MCPClient; print('✅ MCP integration working')"
```

## Code Quality Standards

We maintain high code quality standards using automated tools:

### Code Formatting

- **Black**: Code formatting (line length: 88)
- **Ruff**: Fast Python linter
- **MyPy**: Type checking

### Pre-Commit Hooks

Pre-commit hooks run automatically on every commit:

```bash
# Install hooks (already done in setup)
pre-commit install

# Run manually
pre-commit run --all-files

# Skip hooks temporarily (not recommended)
git commit -m "message" --no-verify
```

### Style Guidelines

1. **Python Version**: Target Python 3.8+ compatibility
2. **Line Length**: 88 characters (Black default)
3. **Type Hints**: Required for all public functions
4. **Docstrings**: Required for all public classes and functions
5. **Variable Names**: Descriptive, snake_case
6. **Function Names**: Verb-based, snake_case

### Example Code Style

```python
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class AgentManager:
    """Manages CoralCollective agents and their lifecycle.
    
    This class provides methods for loading, executing, and managing
    the lifecycle of CoralCollective agents.
    
    Attributes:
        agents_config: Dictionary containing agent configurations
        active_agents: List of currently active agent instances
    """
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize the AgentManager.
        
        Args:
            config_path: Optional path to agent configuration file
            
        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        self.agents_config: Dict[str, Any] = {}
        self.active_agents: List[Agent] = []
        
    def load_agent(self, agent_id: str, task: str) -> Optional[Agent]:
        """Load and return an agent instance.
        
        Args:
            agent_id: Unique identifier for the agent
            task: Task description for the agent
            
        Returns:
            Agent instance if successful, None otherwise
            
        Raises:
            AgentNotFoundError: If agent_id is not registered
        """
        logger.info(f"Loading agent: {agent_id}")
        # Implementation here
        return None
```

### Running Code Quality Checks

```bash
# Format code
black coral_collective/ tests/
ruff format coral_collective/ tests/

# Lint code
ruff check coral_collective/ tests/

# Type check
mypy coral_collective/

# Security scan
bandit -r coral_collective/

# All quality checks
make lint  # If Makefile exists
# Or run individually as above
```

## Testing Requirements

We maintain **80%+ test coverage** with comprehensive testing:

### Test Structure

```
tests/
├── unit/                 # Unit tests (fast, isolated)
├── integration/         # Integration tests (slower, with dependencies)
├── e2e/                # End-to-end tests (full workflows)
├── fixtures/           # Test data and mocks
├── conftest.py        # Pytest configuration
└── requirements.txt   # Test-specific dependencies
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=coral_collective --cov-report=html --cov-report=term-missing

# Run specific test types
pytest tests/unit/          # Fast unit tests
pytest tests/integration/   # Integration tests
pytest tests/e2e/          # End-to-end tests

# Run specific test file
pytest tests/unit/test_agent_runner.py -v

# Run tests matching pattern
pytest -k "test_agent" -v

# Run tests with debugging
pytest --pdb  # Drop into debugger on failure
pytest -s     # Show print statements
```

### Coverage Requirements

- **Minimum**: 80% overall coverage
- **New code**: Must have 90%+ coverage
- **Critical paths**: 100% coverage required

```bash
# Generate coverage report
pytest --cov=coral_collective --cov-report=html

# View detailed coverage
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Writing Tests

#### Unit Test Example

```python
import pytest
from unittest.mock import Mock, patch
from coral_collective.core.agent_runner import AgentRunner

class TestAgentRunner:
    """Test cases for AgentRunner class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.agent_runner = AgentRunner()
    
    def test_load_agent_success(self):
        """Test successful agent loading."""
        # Arrange
        agent_id = "backend_developer"
        task = "Create REST API"
        
        # Act
        result = self.agent_runner.load_agent(agent_id, task)
        
        # Assert
        assert result is not None
        assert result.agent_id == agent_id
        
    def test_load_agent_not_found(self):
        """Test agent loading with invalid ID."""
        with pytest.raises(AgentNotFoundError):
            self.agent_runner.load_agent("nonexistent_agent", "task")
    
    @patch('coral_collective.core.agent_runner.load_config')
    def test_load_agent_with_mock(self, mock_load_config):
        """Test agent loading with mocked dependencies."""
        # Arrange
        mock_load_config.return_value = {"test": "config"}
        
        # Act & Assert
        result = self.agent_runner.load_agent("test_agent", "task")
        mock_load_config.assert_called_once()
```

#### Integration Test Example

```python
import pytest
from coral_collective.mcp.mcp_client import MCPClient
from coral_collective.core.agent_runner import AgentRunner

@pytest.mark.integration
class TestMCPIntegration:
    """Integration tests for MCP functionality."""
    
    def test_mcp_agent_workflow(self):
        """Test complete MCP-enabled agent workflow."""
        # Requires actual MCP server running
        mcp_client = MCPClient()
        agent_runner = AgentRunner(mcp_enabled=True)
        
        # Test agent can access MCP tools
        result = agent_runner.run_agent(
            "backend_developer", 
            "Create a simple API endpoint"
        )
        
        assert result.success
        assert "mcp_tools_used" in result.metadata
```

### Test Configuration

Add to `tests/conftest.py`:

```python
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_mcp_client():
    """Mock MCP client for testing."""
    mock = Mock()
    mock.get_tools.return_value = ["filesystem", "github"]
    return mock

@pytest.fixture
def sample_agent_config():
    """Sample agent configuration for testing."""
    return {
        "backend_developer": {
            "name": "Backend Developer",
            "prompt_path": "agents/specialists/backend_developer.md",
            "capabilities": ["api", "database", "server"]
        }
    }
```

## Agent Development Guidelines

### Creating New Agents

1. **Agent Structure**: All agents are markdown files with structured prompts
2. **Naming Convention**: Use snake_case for agent IDs
3. **File Location**: Core agents in `agents/core/`, specialists in `agents/specialists/`
4. **Configuration**: Add to `config/agents.yaml`

### Agent Template

Create new agent file: `agents/specialists/your_agent.md`

```markdown
# Your Agent Name

## Role & Purpose

Brief description of what this agent does and when to use it.

## Core Responsibilities

- Primary responsibility 1
- Primary responsibility 2
- Primary responsibility 3

## Context Requirements

What information this agent needs to work effectively:

- Required context item 1
- Required context item 2
- Optional context item 3

## Workflow Integration

### Recommended Previous Agents
- agent_id_1 (reason why)
- agent_id_2 (reason why)

### Recommended Next Agents
- agent_id_1 (reason why)
- agent_id_2 (reason why)

## Deliverables

What this agent produces:

1. **Primary Deliverable**: Description
2. **Secondary Deliverable**: Description
3. **Documentation**: Description

## Agent Prompt

[The actual prompt that Claude receives when this agent is invoked]

You are the [Agent Name] for CoralCollective...

### Task Context
[Task-specific information will be inserted here]

### Your Expertise
- Expertise area 1
- Expertise area 2
- Expertise area 3

### Deliverables Required
1. Specific deliverable 1
2. Specific deliverable 2
3. Specific deliverable 3

### Handoff Protocol
Upon completion, provide:
1. **Summary**: What was accomplished
2. **Next Agent**: Recommended next agent with reason
3. **Context**: Key information for next agent
4. **Files**: List of files created/modified

## Usage Examples

### Example 1: Common Use Case
```
Task: "Build a REST API for user management"
Context: Project architecture already defined
Output: API endpoints, database models, authentication
```

### Example 2: Complex Scenario
```
Task: "Implement microservices architecture"
Context: System requirements and scaling needs
Output: Service definitions, inter-service communication, deployment configs
```
```

### Register Your Agent

Add to `config/agents.yaml`:

```yaml
your_agent:
  name: "Your Agent Name"
  description: "Brief description of what this agent does"
  category: "specialists"  # or "core"
  prompt_path: "agents/specialists/your_agent.md"
  capabilities:
    - "capability1"
    - "capability2"
  dependencies:
    - "previous_agent_id"
  next_agents:
    - "next_agent_id"
```

### Testing Your Agent

```python
# Test agent loading
from coral_collective.core.agent_runner import AgentRunner

runner = AgentRunner()
prompt = runner.get_agent_prompt("your_agent", "Test task")
assert prompt is not None
```

## Pull Request Process

### Before Submitting

1. **Run all tests**: `pytest --cov=coral_collective`
2. **Check code quality**: `pre-commit run --all-files`
3. **Update documentation**: If you changed APIs or behavior
4. **Test locally**: Make sure everything works in your environment

### PR Requirements

- [ ] **Descriptive title**: Clear, concise description of changes
- [ ] **Detailed description**: What, why, and how of your changes
- [ ] **Tests added**: New code has appropriate test coverage
- [ ] **Documentation updated**: README, docstrings, comments
- [ ] **No breaking changes**: Or clearly documented if unavoidable
- [ ] **Follows style guide**: Black, Ruff, MyPy all pass

### PR Template

```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that causes existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed
- [ ] All tests pass locally

## Checklist
- [ ] Code follows the project's style guidelines
- [ ] Self-review of code completed
- [ ] Documentation updated (if applicable)
- [ ] No new warnings introduced
- [ ] Changes generate no breaking changes (or documented)
```

### Review Process

1. **Automated checks**: All CI checks must pass
2. **Code review**: At least one maintainer review
3. **Testing**: Comprehensive test coverage
4. **Documentation**: Updates to relevant docs
5. **Backwards compatibility**: Maintain API stability

## Security Considerations

### Security First Principles

1. **Least Privilege**: MCP tools have minimal required permissions
2. **Input Validation**: All user inputs are validated and sanitized
3. **Secure Defaults**: Secure configurations by default
4. **Audit Logging**: All significant actions are logged
5. **Secret Management**: No secrets in code or logs

### Security Checklist

- [ ] No hardcoded secrets or API keys
- [ ] Input validation for all user-provided data
- [ ] Proper error handling (no information leaks)
- [ ] MCP permissions are minimal and scoped
- [ ] File operations are sandboxed
- [ ] Network operations are controlled
- [ ] Dependencies are regularly updated

### Reporting Security Issues

**DO NOT open public issues for security vulnerabilities.**

Instead:
1. Email: security@coral-collective.dev
2. Include: Detailed description, reproduction steps, impact assessment
3. Response: We'll acknowledge within 48 hours
4. Timeline: Fix and disclosure within 90 days

### Protected Framework Files

**NEVER modify protected framework files** (see `DO_NOT_MODIFY.md`):

```
❌ DON'T EDIT:
- agent_runner.py (core orchestration)
- agents/**/*.md (agent prompts)
- mcp/ (MCP integration)
- memory/ (memory system)
- .coral-protected (protection list)

✅ OK TO EDIT:
- tests/ (test files)
- docs/ (documentation)
- examples/ (example code)
- New feature files
```

## Documentation

### Documentation Standards

1. **API Documentation**: All public APIs must be documented
2. **Code Comments**: Complex logic needs inline comments
3. **Docstrings**: All public classes and functions
4. **README Updates**: Keep README.md current
5. **Changelog**: Add entries for user-facing changes

### Documentation Types

- **API Reference**: Generated from docstrings
- **User Guides**: Step-by-step instructions
- **Developer Docs**: Architecture and contribution guides
- **Examples**: Working code examples

### Writing Documentation

```python
def process_agent_workflow(
    agent_sequence: List[str], 
    task: str,
    context: Optional[Dict[str, Any]] = None
) -> WorkflowResult:
    """Process a sequence of agents for a given task.
    
    This function executes agents in sequence, passing context
    between them to complete a complex task.
    
    Args:
        agent_sequence: Ordered list of agent IDs to execute
        task: Description of the task to accomplish
        context: Optional context data to pass between agents
        
    Returns:
        WorkflowResult containing success status, outputs, and metadata
        
    Raises:
        AgentNotFoundError: If any agent in sequence doesn't exist
        WorkflowExecutionError: If workflow execution fails
        
    Example:
        >>> sequence = ["project_architect", "backend_developer"]
        >>> result = process_agent_workflow(sequence, "Build API")
        >>> print(result.success)
        True
    """
```

## Community

### Communication Channels

- **GitHub Discussions**: General questions and ideas
- **GitHub Issues**: Bug reports and feature requests
- **Discord**: Real-time chat (coming soon)
- **Email**: security@coral-collective.dev (security issues only)

### Code of Conduct

We follow the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). Be respectful, inclusive, and constructive.

### Getting Help

1. **Documentation**: Check README, API docs, and guides first
2. **Search Issues**: Look for existing discussions
3. **Ask Questions**: Use GitHub Discussions for questions
4. **Report Bugs**: Use GitHub Issues with detailed reproduction steps

### Recognition

Contributors are recognized in:
- CHANGELOG.md for their contributions
- GitHub contributor list
- Special thanks in releases

## Development Workflow

### Daily Development

```bash
# Start your day
source venv/bin/activate
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and test
# ... code changes ...
pytest tests/
pre-commit run --all-files

# Commit and push
git add .
git commit -m "feat: add your feature description"
git push origin feature/your-feature-name

# Create pull request
# ... use GitHub web interface ...
```

### Release Process

1. **Version Bump**: Update version in `__init__.py`
2. **Changelog**: Update CHANGELOG.md
3. **Documentation**: Update any version-specific docs
4. **Tag Release**: Create annotated git tag
5. **CI/CD**: Automated testing and PyPI publishing

## FAQ

### Common Questions

**Q: Can I modify agent prompts?**
A: No, agent prompts are part of the framework. Create new agents instead or contribute improvements.

**Q: How do I add a new MCP server?**
A: Add configuration to `mcp/configs/` and update relevant agent permissions.

**Q: Can I use different Python versions?**
A: Yes, we support Python 3.8+, but 3.11+ is recommended for best performance.

**Q: How do I test MCP integration?**
A: Use the test MCP servers in `mcp/servers/test/` or mock MCP clients.

**Q: What if my tests are slow?**
A: Use `pytest -m "not slow"` to skip slow tests during development.

## License

By contributing to CoralCollective, you agree that your contributions will be licensed under the AGPL-3.0 license. This means:

- ✅ Your code can be used commercially
- ✅ Others can modify and distribute your code
- ⚠️ Any modifications must be shared under the same license
- ⚠️ Network use counts as distribution

## Final Checklist

Before your first contribution:

- [ ] Read this entire guide
- [ ] Set up development environment with virtual environment
- [ ] Run test suite successfully
- [ ] Install pre-commit hooks
- [ ] Make a small test change
- [ ] Understand the security requirements
- [ ] Know which files you can/cannot modify

---

**Welcome to the CoralCollective community! 🪸**

We're excited to have you contribute to the future of AI-powered development tools. Together, we're building something amazing!

For questions about contributing, open a GitHub Discussion or check our documentation.