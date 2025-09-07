# Frequently Asked Questions (FAQ) 🪸

## Table of Contents

1. [Getting Started](#getting-started)
2. [Installation & Setup](#installation--setup)
3. [Using Agents](#using-agents)
4. [Memory System](#memory-system)
5. [MCP Integration](#mcp-integration)
6. [Development & Contributing](#development--contributing)
7. [Troubleshooting](#troubleshooting)
8. [Performance & Optimization](#performance--optimization)
9. [Security](#security)
10. [License & Legal](#license--legal)

---

## Getting Started

### What is CoralCollective?

**Q: What exactly is CoralCollective?**

A: CoralCollective is an AI agent orchestration framework that provides 20+ specialized AI agents working together to build software projects. Think of it as having an entire development team of AI specialists, each expert in their domain (architecture, backend, frontend, security, testing, etc.), following a structured documentation-first workflow.

**Q: How is CoralCollective different from other AI development tools?**

A: Key differences:
- **Specialized agents** vs. single generalist AI
- **Documentation-first workflow** ensuring quality
- **Structured handoffs** between agents with context preservation
- **MCP integration** for direct tool access (GitHub, databases, Docker, etc.)
- **Memory system** for cross-session context
- **Production-ready** with comprehensive testing and deployment

**Q: Who should use CoralCollective?**

A: Perfect for:
- **Solo developers** who want a full development team
- **Development teams** looking to accelerate workflows
- **Startups** needing rapid prototyping and MVP development
- **Enterprises** requiring structured, documented development processes
- **Anyone** building complex software projects with AI assistance

### How does the documentation-first approach work?

**Q: What does "documentation-first" mean?**

A: Instead of jumping into code, CoralCollective follows this workflow:
1. **Project Architect** designs the system and creates technical specifications
2. **Technical Writer (Phase 1)** creates detailed requirements and API documentation
3. **Specialist agents** build to the documented specifications
4. **QA Testing** validates against documented acceptance criteria
5. **Technical Writer (Phase 2)** creates user documentation and guides

This ensures everyone (human and AI) understands what's being built before building it.

**Q: Doesn't this slow down development?**

A: Initially it might seem slower, but it actually accelerates development because:
- **Fewer misunderstandings** and rework cycles
- **Clear requirements** prevent scope creep
- **Structured handoffs** maintain context
- **Quality assurance** catches issues early
- **Complete documentation** makes maintenance easier

---

## Installation & Setup

### Virtual Environment Requirements

**Q: Why is a virtual environment required?**

A: Virtual environments are **mandatory** for several critical reasons:

1. **Dependency isolation**: CoralCollective has many dependencies (AI libraries, MCP servers, etc.)
2. **System protection**: Prevents conflicts with system Python packages
3. **Reproducible environments**: Ensures consistent behavior across machines
4. **Security**: Isolates potentially risky operations
5. **Framework protection**: Prevents accidental system-wide modifications

**Never install CoralCollective system-wide.**

**Q: I'm getting permission errors during installation. What should I do?**

A: This usually means you're not in a virtual environment:

```bash
# Create virtual environment (REQUIRED)
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Verify you're in the virtual environment
which python  # Should show venv/bin/python

# Now install
pip install coral-collective[all]
```

### Installation Methods

**Q: What's the difference between installation methods?**

A: Multiple options for different use cases:

1. **PyPI Install (Recommended)**: `pip install coral-collective[all]`
   - Easiest setup
   - Automatic dependency management
   - Latest stable version

2. **Development Install**: `pip install -e .[dev,all]`
   - For contributing to CoralCollective
   - Includes development tools
   - Live code changes

3. **Docker Install**: `docker run coralcollective/coral-collective`
   - Containerized environment
   - Consistent across systems
   - Good for production

4. **Source Install**: Clone from GitHub
   - Latest development features
   - Can be unstable
   - For advanced users

**Q: Which optional dependencies should I install?**

A: Depends on your needs:

- `coral-collective[memory]`: Advanced memory system with ChromaDB
- `coral-collective[mcp]`: MCP integration for direct tool access
- `coral-collective[dev]`: Development tools (testing, linting)
- `coral-collective[all]`: Everything (recommended)

**Q: The installation is taking forever. Is this normal?**

A: Yes, first installation can be slow because:
- **Many dependencies**: AI libraries like transformers are large
- **Compilation**: Some packages need to be compiled (PyTorch, etc.)
- **Downloads**: ML models are downloaded on first use

Subsequent installs are much faster due to pip caching.

---

## Using Agents

### Agent Basics

**Q: How do I know which agent to use?**

A: Start with these guidelines:

- **Always start** with `project_architect` for new projects
- **For APIs**: Use `api_designer` → `backend_developer`
- **For UIs**: Use `frontend_developer` → `ui_ux_designer`
- **For databases**: Use `database_specialist`
- **For security**: Use `security_specialist`
- **For testing**: Use `qa_testing`
- **For deployment**: Use `devops_deployment`

Or use capability search:
```bash
coral list --capability api
coral list --category security
```

**Q: Can I skip agents or change the order?**

A: While possible, it's not recommended because:
- **Agent handoffs** are designed for specific sequences
- **Context accumulation** builds through the workflow
- **Quality depends** on following the documentation-first approach

However, for small tasks or specific fixes, you can use individual agents directly.

**Q: How do agents pass information between each other?**

A: Through structured handoff protocols:

1. **Completion Summary**: What was accomplished
2. **Context Data**: Technical details, decisions, file locations
3. **Next Agent Recommendation**: Who should work next and why
4. **Copy-paste Prompts**: Ready-to-use prompts for the next agent

Plus automatic context preservation with the memory system.

### Agent Customization

**Q: Can I modify agent prompts?**

A: **No, don't modify agent prompts** - they're part of the framework. Instead:

1. **Use context** to provide specific requirements
2. **Create custom agents** following the agent development guide
3. **Contribute improvements** via pull requests
4. **Use configuration** to customize behavior

**Q: How do I provide specific requirements to agents?**

A: Use context and detailed task descriptions:

```bash
# Detailed task with context
coral run backend_developer --task "Create REST API with JWT authentication using Node.js and Express, following OpenAPI 3.0 spec"

# Context file with requirements
coral run frontend_developer --context requirements.json --task "Build dashboard"
```

**Q: Can agents use different programming languages?**

A: Yes! Specify in your task or context:

```python
context = {
    'tech_stack': {
        'backend': 'Python + FastAPI',
        'frontend': 'Vue.js + TypeScript', 
        'database': 'PostgreSQL',
        'deployment': 'Docker + Kubernetes'
    }
}

result = runner.run_agent('backend_developer', 'Create API', context)
```

### Working with Claude

**Q: How do I use CoralCollective agents in Claude?**

A: Multiple ways:

1. **Subagent notation**:
   ```python
   @backend_developer "Create user authentication system"
   @frontend_developer "Build login UI for the authentication system"
   ```

2. **Workflow execution**:
   ```python
   @workflow full_stack "Build e-commerce platform"
   ```

3. **Python interface**:
   ```python
   from coral_collective import AgentRunner
   runner = AgentRunner()
   result = runner.run_agent('project_architect', 'Design system')
   ```

**Q: Do I need to install CoralCollective to use agents in Claude?**

A: For basic agent prompts: **No** - Claude can directly read agent markdown files

For full functionality (MCP, memory, context): **Yes** - install CoralCollective

---

## Memory System

### Memory Basics

**Q: What is the memory system and why do I need it?**

A: The memory system provides:

- **Cross-session context**: Agents remember previous work
- **Project knowledge**: Accumulated understanding over time
- **Design decisions**: Why choices were made
- **Code patterns**: Reusable solutions and preferences
- **Team standards**: Consistent coding styles and practices

Without memory, each agent starts from scratch every time.

**Q: How does memory work technically?**

A: CoralCollective uses vector-based memory storage:

1. **Content storage**: Text content is stored with metadata
2. **Vector embeddings**: Content is converted to numerical vectors
3. **Semantic search**: Queries find relevant memories by meaning
4. **Context injection**: Relevant memories are added to agent prompts
5. **Memory updates**: New information is continuously stored

**Q: Local vs. Cloud memory - which should I choose?**

A: Depends on your needs:

**Local Memory** (default):
- ✅ Complete privacy
- ✅ Fast access
- ✅ No external dependencies
- ❌ Limited to single machine
- ❌ No team sharing

**Cloud Memory**:
- ✅ Access from anywhere
- ✅ Team collaboration
- ✅ Better scalability
- ❌ Privacy considerations
- ❌ Network dependency

### Memory Management

**Q: How much disk space does memory use?**

A: Varies by usage:
- **Small project** (< 10 agents): ~50-100 MB
- **Medium project** (full workflow): ~200-500 MB  
- **Large project** (multiple iterations): ~1-2 GB
- **Vector models**: ~500 MB (one-time download)

**Q: Can I clear or reset memory?**

A: Yes, several options:

```bash
# Clear specific project
coral memory clear --project myproject

# Clear all memory
coral memory clear --all

# Clear by type
coral memory clear --type context

# Clear old memories
coral memory clear --older-than 30days
```

**Q: How do I back up memory data?**

A: Memory is stored in files you can back up:

```bash
# Default location
~/.coral/memory/

# Copy to backup
cp -r ~/.coral/memory/ ~/backups/coral-memory-$(date +%Y%m%d)/

# Or use built-in export
coral memory export --project myproject --format json > backup.json
```

---

## MCP Integration

### MCP Basics

**Q: What is MCP and why should I use it?**

A: MCP (Model Context Protocol) allows agents to directly use tools:

**Without MCP**: Agent writes code → You copy/paste → You run commands → You report back
**With MCP**: Agent directly executes GitHub operations, file changes, database queries, etc.

This eliminates manual steps and makes agents truly autonomous.

**Q: Which MCP servers should I install?**

A: Start with essential ones:

1. **GitHub**: Repository management, PRs, issues
2. **Filesystem**: File operations with sandboxing
3. **PostgreSQL**: Database operations
4. **E2B**: Secure code execution
5. **Docker**: Container management

Add others based on your needs (Slack, Linear, AWS, etc.)

**Q: Is MCP secure?**

A: Yes, with proper configuration:

- **Agent-specific permissions**: Each agent only gets needed tools
- **Sandboxed operations**: File access is limited and controlled
- **Audit logging**: All operations are logged
- **API key management**: Secure credential handling
- **Network controls**: Limited external access

Always review MCP permissions before enabling.

### MCP Troubleshooting

**Q: MCP servers won't connect. What should I check?**

A: Common issues and solutions:

1. **API keys**: Check environment variables
   ```bash
   echo $GITHUB_TOKEN
   echo $ANTHROPIC_API_KEY
   ```

2. **Server status**: Check if servers are running
   ```bash
   coral mcp health-check
   ```

3. **Configuration**: Validate MCP config
   ```bash
   coral mcp validate-config
   ```

4. **Network**: Check firewall and proxy settings

5. **Dependencies**: Ensure MCP packages are installed
   ```bash
   pip install coral-collective[mcp]
   ```

**Q: Can I use MCP without internet?**

A: Partially:
- **Filesystem server**: Yes, works offline
- **E2B server**: No, requires internet
- **GitHub server**: No, requires internet
- **Database servers**: Yes, if database is local

For offline development, disable cloud MCP servers and use local ones only.

---

## Development & Contributing

### Framework vs. Project Code

**Q: I want to modify how an agent works. How do I do this?**

A: **Don't modify the framework files!** Instead:

1. **Create custom agents** in your project
2. **Use context** to customize behavior
3. **Configure preferences** in agent configs
4. **Contribute improvements** back to the framework

Remember: CoralCollective is a **tool to USE**, not code to MODIFY.

**Q: What files can I safely modify?**

A: **Safe to modify**:
- Your project files
- Custom agent files you create
- Project-specific configurations
- Test files in your project

**Never modify**:
- `agents/**/*.md` (agent prompts)
- `agent_runner.py` (core orchestration)
- `mcp/` (MCP integration)
- `memory/` (memory system)
- Files listed in `.coral-protected`

**Q: How do I create a custom agent?**

A: Follow the agent development guide:

1. **Create agent file**: `agents/custom/my_agent.md`
2. **Register agent**: Add to `config/agents.yaml`
3. **Test agent**: `coral agent test --agent my_agent`
4. **Use agent**: `coral run my_agent --task "test"`

See `CONTRIBUTING.md` for detailed instructions.

### Testing and Quality

**Q: How do I test my changes?**

A: Comprehensive testing strategy:

```bash
# Run all tests
pytest

# Test specific areas  
pytest tests/unit/          # Fast unit tests
pytest tests/integration/   # Integration tests
pytest tests/e2e/          # End-to-end tests

# Test coverage
pytest --cov=coral_collective --cov-report=html

# Code quality
pre-commit run --all-files
```

**Q: Why are there so many code quality tools?**

A: Quality is critical for a framework used by many projects:

- **Black**: Consistent code formatting
- **Ruff**: Fast linting and error detection  
- **MyPy**: Type checking for better reliability
- **Bandit**: Security vulnerability scanning
- **Pre-commit**: Automated quality checks

These run automatically to catch issues early.

**Q: My contribution was rejected. What should I do?**

A: Common reasons and solutions:

1. **Code quality issues**: Run pre-commit hooks and fix issues
2. **Missing tests**: Add tests for new functionality  
3. **Breaking changes**: Consider backwards compatibility
4. **Documentation**: Update relevant docs
5. **Framework modifications**: Don't modify protected files

Check the PR feedback and contributing guidelines.

---

## Troubleshooting

### Common Issues

**Q: "Agent not found" error. What does this mean?**

A: The agent ID doesn't exist or isn't registered:

```bash
# Check available agents
coral list

# Check specific agent
coral agent validate --agent backend_developer

# Common typos:
# ❌ "backend_dev" → ✅ "backend_developer"
# ❌ "architect" → ✅ "project_architect"
# ❌ "frontend" → ✅ "frontend_developer"
```

**Q: Agents aren't producing good results. What should I do?**

A: Troubleshooting steps:

1. **Be more specific** in task descriptions
2. **Provide context** with requirements and preferences
3. **Check agent capabilities** - use the right agent for the task
4. **Follow the workflow** - don't skip recommended previous agents
5. **Use memory system** for better context
6. **Try MCP integration** for direct tool access

**Q: Installation fails with "permission denied" errors?**

A: You're likely not using a virtual environment:

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Verify you're in venv
which python  # Should show venv path

# Try installation again
pip install coral-collective[all]
```

**Q: Commands are slow or hanging. What's wrong?**

A: Common causes:

1. **Network issues**: MCP servers or downloads timing out
2. **Large memory database**: Clear old memories
3. **Resource constraints**: Need more RAM/CPU
4. **Model downloads**: First-time AI model downloads are slow
5. **Debug mode**: Remove --verbose flag

Try:
```bash
# Check system resources
coral monitor --system

# Clear memory cache
coral memory clear --cache

# Disable MCP temporarily
coral run agent --no-mcp --task "test"
```

### Error Messages

**Q: What do the different error codes mean?**

A: Common error codes:

- **AGENT_404**: Agent not found - check agent ID spelling
- **CONFIG_ERROR**: Configuration problem - check YAML syntax
- **MCP_CONNECTION**: MCP server unreachable - check network/API keys
- **MEMORY_ERROR**: Memory system issue - check disk space/permissions
- **WORKFLOW_ERROR**: Workflow execution failed - check agent sequence
- **PERMISSION_ERROR**: File/directory permissions - check access rights

**Q: How do I get more detailed error information?**

A: Use debugging flags:

```bash
# Verbose output
coral run agent --verbose --task "test"

# Debug logging
CORAL_LOG_LEVEL=DEBUG coral run agent --task "test"

# Check logs
coral logs --level debug --last 50

# System health check
coral check --all --verbose
```

---

## Performance & Optimization

### Speed Optimization

**Q: How can I make CoralCollective faster?**

A: Several optimization strategies:

1. **Use SSD storage** for memory system
2. **Increase RAM** for better caching
3. **Use local MCP servers** when possible
4. **Clear old memories** periodically
5. **Disable unused features** (memory, MCP if not needed)
6. **Use parallel execution** for independent tasks

```bash
# Performance tuning
coral config set memory.cache_size 1000
coral config set mcp.connection_pool 10
coral memory clear --older-than 7days
```

**Q: Why is the first run so slow?**

A: First-time setup includes:

- **Model downloads**: AI models (500MB-2GB)
- **Dependency compilation**: Native libraries
- **Configuration initialization**: Setting up directories
- **Memory system setup**: Creating databases

Subsequent runs are much faster.

**Q: Can I run agents in parallel?**

A: Currently limited parallel support:

```bash
# Run independent tasks in parallel
coral run backend_developer --task "API" &
coral run frontend_developer --task "UI" &
wait

# Future versions will have better parallel execution
```

### Resource Usage

**Q: How much memory and disk space does CoralCollective use?**

A: Resource requirements:

**RAM**:
- Minimum: 4GB
- Recommended: 8GB+
- With memory system: +2GB
- With MCP: +1GB

**Disk Space**:
- Installation: ~2-3GB
- Memory data: 100MB-2GB per project
- Model cache: ~1-2GB (shared)
- Logs: 10-100MB

**Q: Can I run CoralCollective on a low-spec machine?**

A: Yes, with optimizations:

```bash
# Lightweight installation
pip install coral-collective  # No [all] extras

# Disable memory system
coral config set memory.enabled false

# Use fewer MCP servers
coral setup mcp --servers filesystem

# Reduce logging
coral config set log_level ERROR
```

---

## Security

### Data Privacy

**Q: What data does CoralCollective store?**

A: CoralCollective stores:

**Locally**:
- Agent configurations and prompts
- Memory data (if memory system enabled)  
- Project state and metadata
- Log files with usage data

**Never stored**:
- Your source code (unless you explicitly store it in memory)
- API keys (only used in memory, not persisted)
- Personal information

**Q: Is my code secure when using MCP?**

A: MCP operations are designed for security:

- **Sandboxed file access** prevents unauthorized access
- **Agent-specific permissions** limit what each agent can do
- **Audit logging** tracks all operations
- **No data persistence** in MCP servers
- **Local execution** when possible

**Q: Can I use CoralCollective in enterprise environments?**

A: Yes, with proper configuration:

1. **Air-gapped deployment** using local-only features
2. **Custom MCP servers** for internal tools
3. **Network security** with firewall rules
4. **Audit logging** for compliance
5. **Access controls** for multi-user environments

See enterprise deployment documentation.

### API Keys and Secrets

**Q: How should I manage API keys?**

A: Best practices:

1. **Environment variables** (recommended):
   ```bash
   export GITHUB_TOKEN=ghp_xxx
   export ANTHROPIC_API_KEY=sk-ant-xxx
   ```

2. **.env files** (for development):
   ```bash
   # .env
   GITHUB_TOKEN=ghp_xxx
   ANTHROPIC_API_KEY=sk-ant-xxx
   ```

3. **Secret management** (for production):
   - Use proper secret management systems
   - Never commit secrets to version control
   - Rotate keys regularly

**Q: What happens if API keys leak?**

A: If keys are compromised:

1. **Immediately revoke** the compromised keys
2. **Generate new keys** from the service provider
3. **Update environment variables** with new keys
4. **Check logs** for unauthorized usage
5. **Review access permissions** for the compromised keys

---

## License & Legal

### AGPL License

**Q: What does the AGPL license mean for users?**

A: The AGPL-3.0 license means:

**You CAN**:
- ✅ Use CoralCollective for personal projects
- ✅ Use CoralCollective for commercial projects
- ✅ Modify CoralCollective for your needs
- ✅ Distribute CoralCollective

**You MUST**:
- ⚠️ Share modifications under the same license
- ⚠️ Provide source code if you distribute
- ⚠️ Include license notices
- ⚠️ Share network-accessible modifications (key difference from GPL)

**Q: Does using CoralCollective make my project AGPL?**

A: **No**, your project code remains yours. The AGPL applies to:
- CoralCollective framework code
- Modifications you make to CoralCollective
- Not your application code built with CoralCollective

**Q: Can I sell software built with CoralCollective?**

A: **Yes**, you can sell your software. You only need to share:
- CoralCollective source code (already public)
- Any modifications you made to CoralCollective
- Not your application source code

**Q: What if I modify CoralCollective agents?**

A: If you modify the framework:
- ✅ For internal use: No obligations
- ⚠️ If you distribute: Must share modifications
- ⚠️ If you provide as network service: Must share modifications

This is why we recommend NOT modifying framework files.

### Commercial Use

**Q: Do I need a commercial license?**

A: **No commercial license needed**. The AGPL allows commercial use. You only need to comply with the license terms (sharing modifications).

**Q: Can I offer CoralCollective as a service?**

A: **Yes**, but you must:
- Provide CoralCollective source code to users
- Share any modifications you made
- Include proper license notices

Many SaaS companies successfully use AGPL software this way.

**Q: I'm nervous about AGPL. What are my options?**

A: Several approaches:

1. **Use as-is**: Don't modify framework files (recommended)
2. **Commercial support**: Contact us for enterprise support
3. **Fork and comply**: Fork the project and follow license terms
4. **Alternative tools**: Use different frameworks (but you'll miss CoralCollective's unique features)

---

## Getting Help

### Support Channels

**Q: Where can I get help?**

A: Multiple support options:

1. **Documentation**: Check README, guides, and this FAQ first
2. **GitHub Issues**: Bug reports and feature requests
3. **GitHub Discussions**: Questions and community help
4. **Discord**: Real-time chat (coming soon)
5. **Email**: security@coral-collective.dev (security issues only)

**Q: How do I report bugs?**

A: Create a GitHub issue with:

1. **Clear description** of the problem
2. **Steps to reproduce** the issue
3. **Expected vs. actual behavior**
4. **System information** (OS, Python version, CoralCollective version)
5. **Error messages** or logs
6. **Minimal example** if possible

**Q: How do I suggest new features?**

A: Use GitHub Discussions for:
- **Feature ideas** and requirements
- **Use case descriptions** 
- **Community feedback** and discussion
- **Implementation ideas**

Popular features may become GitHub issues for implementation.

### Community

**Q: How can I contribute to CoralCollective?**

A: Many ways to contribute:

1. **Report bugs** and issues
2. **Suggest features** and improvements
3. **Improve documentation** 
4. **Write tests** and examples
5. **Create agents** for specific domains
6. **Answer questions** in discussions
7. **Share projects** built with CoralCollective

See `CONTRIBUTING.md` for detailed guidelines.

**Q: Is there a community forum?**

A: Currently using GitHub Discussions. Discord server coming soon.

Active community helps with:
- Questions and troubleshooting
- Best practices sharing
- Project showcases
- Feature discussions
- Agent development

---

**Still have questions? Check our [documentation](https://github.com/coral-collective/coral-collective) or ask in [GitHub Discussions](https://github.com/coral-collective/coral-collective/discussions)!**