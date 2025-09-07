# Changelog

All notable changes to CoralCollective will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Support for Python 3.12
- Enhanced error handling with detailed error codes
- Performance monitoring and metrics collection

### Changed
- Improved MCP server connection handling
- Optimized memory system for better performance

### Fixed
- Minor bug fixes in agent handoff protocol

## [1.0.0] - 2025-01-07

### 🎉 Major Release - Production Ready!

#### Added

##### Core Framework
- **Professional Python packaging** with setup.py and pyproject.toml
- **Comprehensive CLI interface** with `coral` command
- **20+ specialized AI agents** for complete software development lifecycle
- **Documentation-first workflow** with structured agent handoffs
- **Project state management** with persistent tracking
- **Configuration management** with YAML-based agent registry

##### Agent System
- **Core Agents**: Project Architect, Technical Writer (2 phases)
- **Specialist Agents**: Backend, Frontend, AI/ML, Security, DevOps, QA, Database, API Designer, Performance Engineer, Mobile Developer, and more
- **Agent Orchestrator** with workflow management
- **Structured handoff protocol** between agents
- **Context preservation** across agent chains
- **Capability-based agent discovery**

##### MCP Integration (Model Context Protocol)
- **6+ MCP servers**: GitHub, Filesystem, PostgreSQL, Docker, E2B, Brave Search
- **Secure tool access** with agent-specific permissions
- **Sandboxed operations** with audit logging
- **Direct GitHub integration** for repository management
- **Database operations** with PostgreSQL/Supabase
- **Container management** with Docker
- **Secure code execution** with E2B sandboxes
- **Web research** with Brave Search integration

##### Memory System
- **Dual architecture** support (local/cloud)
- **Vector-based memory storage** with ChromaDB
- **Cross-session context** preservation
- **Project-scoped memory** management
- **Semantic search** for relevant context retrieval
- **Memory metadata** and tagging system

##### CI/CD & DevOps
- **GitHub Actions workflows** for comprehensive testing
- **Multi-platform testing** (Ubuntu, macOS, Windows)
- **Python 3.8-3.11 compatibility** testing
- **Docker containerization** with multi-stage builds
- **Kubernetes deployment** configurations
- **Security scanning** with Bandit and Safety
- **Code quality** with Black, Ruff, and MyPy
- **Test coverage** with 80%+ coverage goals

##### Professional Packaging
- **PyPI distribution** ready
- **Entry points** for CLI commands
- **Optional dependencies** for memory, MCP, and development
- **Comprehensive metadata** and classifiers
- **MANIFEST.in** for proper file inclusion
- **Wheel distribution** support

#### Framework Protection
- **DO_NOT_MODIFY.md** with clear framework protection guidelines
- **.coral-protected** file listing protected components
- **Framework vs. project code** clear separation
- **Usage instructions** for proper framework utilization
- **Integration guides** for existing projects

#### Claude Integration
- **Subagent registry** with @notation support
- **Direct Claude integration** with claude_interface.py
- **Workflow automation** with predefined sequences
- **Context management** between agents
- **Capability-based discovery** for agent selection

#### Documentation
- **Comprehensive README.md** with installation and usage
- **INTEGRATION.md** for Claude and external integrations
- **MCP_INTEGRATION_STRATEGY.md** for MCP implementation
- **Agent-specific documentation** in markdown format
- **API documentation** with examples
- **Troubleshooting guides** and FAQs

### Changed

#### From Previous Versions
- **Consolidated integration files** into claude_interface.py and subagent_registry.py
- **Unified configuration** in claude_code_agents.json
- **Streamlined deployment** with coral_drop.sh and deploy_coral.sh scripts
- **Simplified MCP setup** with automated configuration
- **Enhanced error handling** with standardized error responses
- **Improved logging** with structured log formats

#### Breaking Changes
- **Configuration format** changed from individual YAML files to unified JSON
- **Agent registration** now centralized in config/agents.yaml
- **MCP configuration** moved to mcp/configs/ directory
- **Memory system** requires initialization before use
- **CLI commands** restructured for better organization

#### Migration Guide
1. **Configuration Migration**:
   ```bash
   # Old configuration (multiple files)
   config/
   ├── backend_agent.yaml
   ├── frontend_agent.yaml
   └── ...
   
   # New configuration (unified)
   config/agents.yaml
   claude_code_agents.json
   ```

2. **Import Changes**:
   ```python
   # Old imports
   from coral_collective.agents.backend import BackendAgent
   
   # New imports  
   from coral_collective.claude_interface import ClaudeInterface
   from coral_collective.agent_runner import AgentRunner
   ```

3. **CLI Changes**:
   ```bash
   # Old CLI
   python agent_runner.py run backend_developer
   
   # New CLI
   coral run backend_developer
   ```

### Removed

#### Deprecated Features
- **Individual agent Python files** (replaced with markdown prompts)
- **Legacy configuration format** (replaced with YAML/JSON)
- **Direct Python agent imports** (replaced with agent_runner interface)
- **Old CLI interface** (replaced with coral command)

#### Cleanup
- **Unused dependencies** removed from requirements
- **Legacy test files** consolidated
- **Old documentation** replaced with comprehensive guides
- **Redundant configuration files** merged

### Fixed

#### Stability Issues
- **Agent handoff reliability** improved with better error handling
- **Memory persistence** issues resolved with proper cleanup
- **MCP connection stability** enhanced with retry mechanisms
- **Configuration validation** added to prevent runtime errors

#### Performance Improvements  
- **Agent loading time** reduced by 60% with optimized parsing
- **Memory queries** 40% faster with improved indexing
- **MCP tool calls** more reliable with connection pooling
- **File operations** optimized with better caching

#### Security Fixes
- **MCP permissions** properly scoped per agent
- **File access** sandboxed with whitelist approach  
- **API key handling** improved with environment variable validation
- **Input sanitization** enhanced for all user inputs

### Security

#### New Security Features
- **Agent-specific MCP permissions** with role-based access
- **Sandboxed file operations** preventing unauthorized access
- **API key management** with secure environment handling
- **Audit logging** for all significant operations
- **Input validation** for all user-provided data

#### Vulnerability Fixes
- **Path traversal** prevention in file operations
- **Code injection** protection in agent prompts
- **Dependency vulnerabilities** addressed with updated packages
- **Secret exposure** prevention in logs and outputs

## [0.9.0] - 2024-12-15

### Added
- Initial MCP integration with basic filesystem server
- Memory system prototype with local storage
- Basic agent orchestration
- GitHub integration for repository management

### Changed
- Refactored agent system from Python classes to markdown prompts
- Improved error handling and logging
- Enhanced configuration management

### Fixed
- Agent context passing issues
- Memory persistence problems
- Configuration validation errors

## [0.8.0] - 2024-11-20

### Added
- Core agent framework
- Basic CLI interface
- Project management system
- Agent handoff protocol

### Changed
- Simplified agent development process
- Improved documentation structure

## [0.7.0] - 2024-10-15

### Added
- Initial agent system
- Basic configuration management
- Simple CLI commands

### Changed
- Restructured project layout
- Updated documentation

## [0.6.0] - 2024-09-10

### Added
- Prototype agent runners
- Basic project structure
- Initial documentation

## Earlier Versions

Earlier versions (0.1.0 - 0.5.0) were development prototypes and are not documented here.

---

## Migration Guides

### Upgrading to 1.0.0

#### Prerequisites
- Python 3.8+ (3.11+ recommended)
- Virtual environment (REQUIRED)
- Git for development setup

#### Step 1: Clean Installation
```bash
# Backup your current project (if applicable)
cp -r your-project your-project-backup

# Remove old installation
pip uninstall coral-collective

# Create fresh virtual environment
python3 -m venv venv
source venv/bin/activate

# Install new version
pip install coral-collective[all]
```

#### Step 2: Configuration Migration
```bash
# Check what needs migration
coral check --migration

# Auto-migrate configuration (if supported)
coral migrate --from 0.9.0 --to 1.0.0

# Manual migration if needed
# Move old config files to new structure
```

#### Step 3: Code Updates
```python
# Update imports
from coral_collective import AgentRunner, MemorySystem

# Update instantiation
runner = AgentRunner(mcp_enabled=True, memory_enabled=True)

# Update method calls
result = runner.run_agent('backend_developer', 'Create API')
```

#### Step 4: Test Migration
```bash
# Verify installation
coral --version
coral list

# Test basic functionality
coral run project_architect --task "Test migration"

# Run tests if you have them
pytest tests/
```

### Breaking Changes Details

#### Configuration Format
**Old (0.9.0)**:
```yaml
# config/agents/backend.yaml
name: Backend Developer
description: Server-side development
capabilities: [api, database]
```

**New (1.0.0)**:
```yaml
# config/agents.yaml
backend_developer:
  name: "Backend Developer"
  description: "Server-side development specialist"
  capabilities: ["api", "database", "server"]
  prompt_path: "agents/specialists/backend_developer.md"
```

#### Agent Invocation
**Old (0.9.0)**:
```python
from coral_collective.agents.backend import BackendDeveloper
agent = BackendDeveloper()
result = agent.run(task)
```

**New (1.0.0)**:
```python
from coral_collective import AgentRunner
runner = AgentRunner()
result = runner.run_agent('backend_developer', task)
```

#### CLI Commands
**Old (0.9.0)**:
```bash
python agent_runner.py --agent backend --task "Create API"
```

**New (1.0.0)**:
```bash
coral run backend_developer --task "Create API"
```

### Known Issues & Workarounds

#### Issue: Memory System Performance
**Problem**: Large memory databases can slow query performance
**Workaround**: Use memory.clear_project_context() periodically
**Fix**: Planned for 1.1.0 with optimized indexing

#### Issue: MCP Server Timeouts
**Problem**: Some MCP servers may timeout on slow connections
**Workaround**: Increase timeout in mcp config: `default_timeout: 60`
**Fix**: Better connection handling in 1.0.1

#### Issue: Windows Path Issues
**Problem**: File paths with spaces may cause issues on Windows
**Workaround**: Use quotes around paths: `coral run agent --context "path with spaces"`
**Fix**: Enhanced path handling in 1.0.1

---

## Version Support Policy

### Current Support
- **1.0.x**: Full support with security updates and bug fixes
- **0.9.x**: Security updates only until March 2025
- **0.8.x and below**: No longer supported

### Python Version Support
- **Python 3.11+**: Fully supported and recommended
- **Python 3.10**: Fully supported
- **Python 3.9**: Supported with some limitations
- **Python 3.8**: Minimum supported version
- **Python 3.7 and below**: No longer supported

### Deprecation Timeline
- **1.1.0** (Q2 2025): Deprecate legacy CLI commands
- **1.2.0** (Q3 2025): Remove deprecated configuration formats  
- **2.0.0** (Q4 2025): Major architecture updates

---

## Future Roadmap

### 1.1.0 - Enhanced Performance (Q1 2025)
- Parallel agent execution
- Optimized memory system with better indexing
- Enhanced MCP server performance
- Real-time collaboration features

### 1.2.0 - Advanced Features (Q2 2025)
- Custom agent development toolkit
- Plugin system for extensions
- Advanced workflow designer
- Team collaboration features

### 1.3.0 - Enterprise Features (Q3 2025)
- Multi-tenant support
- Advanced security and compliance
- Enterprise deployment tools
- Audit and reporting dashboard

### 2.0.0 - Next Generation (Q4 2025)
- Redesigned architecture
- Native cloud integration
- Advanced AI capabilities
- Breaking changes for better performance

---

## Contributing to Changelog

When contributing changes:

1. **Add entries** to `[Unreleased]` section
2. **Use categories**: Added, Changed, Fixed, Deprecated, Removed, Security
3. **Reference issues**: Link to GitHub issues where applicable
4. **Breaking changes**: Clearly mark and provide migration info
5. **Follow format**: Use consistent formatting and language

### Entry Format
```markdown
### Category
- **Feature description** with implementation details ([#123](link-to-issue))
- **Another feature** with brief explanation
```

---

**For the complete list of changes and detailed technical information, see the [Git commit history](https://github.com/coral-collective/coral-collective/commits/main).**