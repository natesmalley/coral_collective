# CoralCollective User Guide

Welcome to CoralCollective! This comprehensive guide will take you from first installation to deploying your first production application using our AI agent orchestration framework.

## Table of Contents

- [Getting Started](#getting-started)
- [First Project Walkthrough](#first-project-walkthrough)
- [Understanding Agents](#understanding-agents)
- [Workflow Management](#workflow-management)
- [Memory System Usage](#memory-system-usage)
- [MCP Integration](#mcp-integration)
- [Advanced Features](#advanced-features)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

Before you begin, ensure you have:
- **Python 3.8 or higher**
- **Virtual environment capability** (required)
- **Git** (for development)
- **Internet connection** (for AI model access)

### Installation

> ⚠️ **Critical**: Never install CoralCollective system-wide. Always use a virtual environment.

#### Quick Installation (Recommended)

```bash
# Create and activate virtual environment (REQUIRED)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install CoralCollective with all features
pip install coral-collective[all]

# Verify installation
coral --version
coral check
```

#### Feature-Specific Installation

```bash
# Core features only
pip install coral-collective

# With memory system support
pip install coral-collective[memory]

# With MCP integration
pip install coral-collective[mcp]

# Development installation
pip install coral-collective[dev]
```

### Initial Setup

After installation, set up your environment:

```bash
# Initialize CoralCollective in your project
coral init --name "MyFirstProject" --type web_app

# Check system status
coral check --all

# List available agents
coral list
```

## First Project Walkthrough

Let's build a complete task management web application from scratch using CoralCollective's documentation-first workflow.

### Step 1: Project Architecture

Start with the Project Architect to design your system:

```bash
# Run the project architect
coral run project_architect --task "Design a task management web application with user authentication, project organization, and team collaboration features"
```

The Project Architect will provide:
- Technical specifications
- Architecture diagrams
- Technology recommendations
- Database schema
- API design
- Security considerations

**Example output structure:**
```
project_architecture/
├── technical_specification.md
├── architecture_diagrams.md
├── technology_stack.md
├── database_schema.sql
├── api_specification.yaml
└── security_requirements.md
```

### Step 2: Documentation Foundation

Next, run the Technical Writer (Phase 1) to create comprehensive documentation:

```bash
# Create documentation foundation
coral run technical_writer --task "Create comprehensive documentation foundation based on the project architecture for the task management application"
```

This creates:
- Requirements documentation
- API specifications
- Database documentation
- User stories
- Acceptance criteria

### Step 3: Backend Development

Build the server-side components:

```bash
# Build the backend
coral run backend_developer --task "Implement the task management API according to the technical specifications, including user authentication, project management, task CRUD operations, and team collaboration features"
```

The backend developer will deliver:
- REST API implementation
- Database models and migrations
- Authentication system
- Authorization logic
- Unit tests
- API documentation

### Step 4: Frontend Development

Create the user interface:

```bash
# Build the frontend
coral run frontend_developer --task "Create a responsive React-based frontend for the task management application that implements all the features specified in the technical documentation"
```

Frontend deliverables include:
- React components
- State management setup
- API integration
- Responsive design
- User authentication flow
- Component tests

### Step 5: Security Implementation

Secure your application:

```bash
# Implement security measures
coral run security_specialist --task "Review and enhance the security of the task management application, focusing on authentication, authorization, data protection, and vulnerability prevention"
```

Security enhancements:
- Security audit report
- HTTPS configuration
- Input validation
- SQL injection prevention
- XSS protection
- Authentication improvements

### Step 6: Quality Assurance

Test your application thoroughly:

```bash
# Comprehensive testing
coral run qa_testing --task "Create and execute comprehensive tests for the task management application, including unit tests, integration tests, and end-to-end tests"
```

QA deliverables:
- Test suite implementation
- Test execution results
- Bug reports
- Performance testing
- Load testing results
- Test documentation

### Step 7: Deployment

Deploy to production:

```bash
# Deploy the application
coral run devops_deployment --task "Set up production deployment for the task management application with Docker, CI/CD pipeline, monitoring, and scaling capabilities"
```

Deployment includes:
- Docker containerization
- CI/CD pipeline
- Production environment setup
- Monitoring and logging
- Backup strategies
- Scaling configuration

### Step 8: Final Documentation

Complete the documentation:

```bash
# Finalize user documentation
coral run technical_writer --task "Create comprehensive user documentation, installation guides, and API reference for the completed task management application"
```

Final documentation:
- User manual
- Installation guide
- API reference
- Administrator guide
- Troubleshooting guide

## Understanding Agents

CoralCollective includes 20+ specialized agents, each with specific expertise.

### Core Agents

#### Project Architect
- **Purpose**: System design and architecture planning
- **Input**: Project requirements and goals
- **Output**: Technical specifications, architecture diagrams
- **When to use**: Start of every project

#### Technical Writer (2 Phases)
- **Phase 1**: Creates requirements and technical documentation
- **Phase 2**: Finalizes user documentation and guides
- **Purpose**: Ensures comprehensive documentation throughout the project

### Specialist Agents

#### Backend Developer
- **Expertise**: Server-side development, APIs, databases
- **Technologies**: Python, Node.js, Java, Go, databases
- **Deliverables**: API implementations, database models, backend tests

#### Frontend Developer
- **Expertise**: User interfaces, web applications
- **Technologies**: React, Vue, Angular, HTML/CSS/JavaScript
- **Deliverables**: UI components, responsive design, frontend tests

#### AI/ML Specialist
- **Expertise**: Machine learning, AI integration, data processing
- **Technologies**: TensorFlow, PyTorch, scikit-learn, LLM APIs
- **Deliverables**: ML models, AI integrations, data pipelines

#### Security Specialist
- **Expertise**: Application security, vulnerability assessment
- **Focus**: Authentication, authorization, data protection
- **Deliverables**: Security audits, vulnerability fixes, compliance reports

#### DevOps Deployment
- **Expertise**: Infrastructure, deployment, monitoring
- **Technologies**: Docker, Kubernetes, AWS, CI/CD
- **Deliverables**: Deployment configurations, monitoring setup

#### QA Testing
- **Expertise**: Test automation, quality assurance
- **Types**: Unit, integration, end-to-end, performance testing
- **Deliverables**: Test suites, test results, quality reports

### Choosing the Right Agent

Use this decision matrix:

| Project Type | Agent Sequence |
|-------------|----------------|
| **Full-Stack Web App** | Architect → Writer → Backend → Frontend → Security → QA → DevOps → Writer |
| **API Service** | Architect → Writer → Backend → Security → QA → DevOps |
| **Frontend Only** | Architect → Writer → Frontend → QA → DevOps |
| **AI Application** | Architect → Writer → AI/ML → Backend → Frontend → Security → QA → DevOps |
| **Mobile App** | Architect → Writer → Mobile → Backend → Security → QA → DevOps |

## Workflow Management

CoralCollective supports both individual agent execution and complete workflows.

### Pre-defined Workflows

#### Full Stack Workflow
```bash
# Complete web application development
coral workflow full_stack \
  --project "TaskManager" \
  --description "Task management with team collaboration" \
  --tech-stack "React, FastAPI, PostgreSQL"
```

#### API-Only Workflow
```bash
# Backend service development
coral workflow api_only \
  --project "UserAPI" \
  --description "User management API service" \
  --tech-stack "FastAPI, PostgreSQL, Redis"
```

#### Frontend-Only Workflow
```bash
# Frontend application development
coral workflow frontend_only \
  --project "Dashboard" \
  --description "Analytics dashboard" \
  --tech-stack "React, TypeScript, D3.js"
```

### Custom Workflows

Create custom workflows for specific needs:

```bash
# AI-focused workflow
coral run project_architect --task "Design AI-powered recommendation system"
coral run technical_writer --task "Document AI system requirements"
coral run ai_ml_specialist --task "Implement recommendation algorithms"
coral run backend_developer --task "Create API for recommendations"
coral run qa_testing --task "Test AI system performance"
coral run devops_deployment --task "Deploy with ML pipeline"
```

### Workflow State Management

Track and manage workflow progress:

```bash
# Save current workflow state
coral save-state project_state.json

# Load previous workflow state
coral load-state project_state.json

# Check workflow status
coral workflow status

# Resume interrupted workflow
coral workflow resume --from backend_developer
```

### Parallel Execution

Enable parallel processing for independent tasks:

```bash
# Run agents in parallel where possible
coral workflow full_stack --parallel \
  --project "ECommerce" \
  --description "Online store platform"
```

## Memory System Usage

The advanced memory system maintains context across sessions and agents.

### Setting Up Memory System

```bash
# Initialize memory system
coral setup memory

# Check memory system status
coral check --memory

# Configure memory settings
coral config memory --type local --embedding-model sentence-transformers
```

### Storing Project Knowledge

```python
from coral_collective.memory import MemorySystem

# Initialize memory system
memory = MemorySystem()

# Store project information
await memory.store_memory(
    key="project_requirements",
    content="Task management app with user auth and team features",
    metadata={"project": "TaskManager", "phase": "planning"},
    tags=["requirements", "planning", "web-app"]
)

# Store technical decisions
await memory.store_memory(
    key="tech_stack_decision",
    content="Using React frontend, FastAPI backend, PostgreSQL database",
    metadata={"project": "TaskManager", "phase": "architecture"},
    tags=["architecture", "technology", "decisions"]
)
```

### Retrieving Context

```python
# Search for relevant context
results = await memory.retrieve_memory(
    query="authentication requirements",
    limit=5,
    similarity_threshold=0.7
)

for result in results:
    print(f"Content: {result.content}")
    print(f"Similarity: {result.similarity_score}")
    print(f"Tags: {result.tags}")
```

### Memory System Best Practices

1. **Consistent Tagging**: Use consistent tags across projects
2. **Descriptive Keys**: Use meaningful memory keys
3. **Regular Cleanup**: Remove outdated information
4. **Metadata Usage**: Include project and phase information
5. **Similarity Tuning**: Adjust threshold based on needs

## MCP Integration

Model Context Protocol (MCP) enables agents to directly interact with development tools.

### Setting Up MCP

```bash
# Set up MCP integration
coral setup mcp

# Check MCP status
coral check --mcp

# List available MCP servers
coral mcp list-servers
```

### Available MCP Servers

#### GitHub Integration
```bash
# Configure GitHub access
export GITHUB_TOKEN="your_github_token"

# Use GitHub operations in agent tasks
coral run backend_developer \
  --task "Create repository and push initial backend code" \
  --mcp-enabled
```

#### Database Integration
```bash
# Configure database access
export DATABASE_URL="postgresql://user:pass@localhost/db"

# Direct database operations
coral run backend_developer \
  --task "Create database schema and run migrations" \
  --mcp-enabled
```

#### Docker Integration
```bash
# Docker operations
coral run devops_deployment \
  --task "Build and deploy Docker containers" \
  --mcp-enabled
```

#### File System Operations
```bash
# Direct file operations with safety
coral run frontend_developer \
  --task "Create React components with proper file structure" \
  --mcp-enabled
```

### MCP Security

MCP operations are sandboxed with configurable permissions:

```yaml
# mcp/configs/mcp_config.yaml
servers:
  github:
    permissions: ["read", "write"]
    allowed_repos: ["username/*"]
  
  filesystem:
    permissions: ["read", "write"]
    allowed_paths: ["/project/src", "/project/docs"]
    blocked_paths: ["/system", "/etc"]
  
  database:
    permissions: ["read", "write"]
    read_only_mode: false
    allowed_schemas: ["public"]
```

## Advanced Features

### Model Optimization

CoralCollective automatically selects optimal AI models for cost and performance:

```bash
# Check current model assignments
coral config models --show

# Override model for specific agent
coral run backend_developer \
  --model claude-3-5-sonnet \
  --task "Complex API implementation"

# Use cost-optimized models
coral run qa_testing \
  --model gpt-4o-mini \
  --task "Generate unit tests"
```

### Token Management

Monitor and optimize token usage:

```bash
# Validate token usage before execution
coral run project_architect \
  --validate-tokens \
  --task "Large system architecture"

# Check token usage history
coral tokens history

# Set token limits
coral config tokens --max-per-agent 50000
```

### Parallel Agent Execution

Run multiple agents concurrently:

```python
from coral_collective import ParallelAgentRunner

runner = ParallelAgentRunner()

# Run agents in parallel
tasks = [
    {"agent": "backend_developer", "task": "Create API endpoints"},
    {"agent": "frontend_developer", "task": "Create UI components"},
    {"agent": "qa_testing", "task": "Write unit tests"}
]

results = await runner.run_parallel(tasks)
```

### Custom Agent Development

Create specialized agents for your domain:

```markdown
# agents/specialists/my_custom_agent.md

# Custom Domain Agent

## Role Overview
Specialized agent for custom domain-specific tasks.

## Core Capabilities
- Domain-specific expertise
- Custom tool integration
- Specialized workflows

## Prompt Template
[Your custom agent prompt here]
```

Register your custom agent:

```yaml
# config/agents.yaml
my_custom_agent:
  name: "Custom Domain Agent"
  category: "specialist"
  description: "Domain-specific specialist"
  prompt_path: "agents/specialists/my_custom_agent.md"
```

## Best Practices

### Project Organization

1. **Follow Documentation-First Approach**
   - Always start with Project Architect
   - Create complete requirements before coding
   - Maintain documentation throughout development

2. **Use Consistent Naming**
   - Project names: PascalCase (e.g., "TaskManager")
   - File names: snake_case (e.g., "user_controller.py")
   - Database names: lowercase (e.g., "task_manager_db")

3. **Maintain Clean Structure**
   ```
   project_name/
   ├── docs/                 # All documentation
   ├── src/                  # Source code
   ├── tests/               # Test files
   ├── deployment/          # Deployment configs
   └── .coral/             # CoralCollective state
   ```

### Agent Usage Patterns

1. **Sequential Execution**
   - Follow recommended agent sequences
   - Complete each phase before moving forward
   - Use agent handoff instructions

2. **Context Preservation**
   - Save important context in memory system
   - Use consistent terminology across agents
   - Reference previous deliverables

3. **Quality Assurance**
   - Always include QA Testing in workflow
   - Run security reviews for production applications
   - Perform performance testing

### Development Workflow

1. **Version Control Integration**
   ```bash
   # Initialize git repository
   git init
   git add .
   git commit -m "Initial project setup with CoralCollective"
   
   # Create feature branches for each agent's work
   git checkout -b feature/backend-implementation
   # Run backend developer
   git add . && git commit -m "Backend implementation complete"
   ```

2. **Environment Management**
   ```bash
   # Development environment
   coral workflow full_stack --environment development
   
   # Staging environment
   coral workflow deployment --environment staging
   
   # Production deployment
   coral workflow deployment --environment production
   ```

3. **Testing Integration**
   ```bash
   # Run tests after each agent
   coral run qa_testing --task "Test recent changes"
   
   # Continuous testing
   coral config testing --auto-test true
   ```

### Performance Optimization

1. **Memory Usage**
   - Clear memory system periodically
   - Use appropriate similarity thresholds
   - Optimize embedding models for your use case

2. **Token Optimization**
   - Use appropriate models for task complexity
   - Enable caching for repeated operations
   - Monitor token usage patterns

3. **Parallel Processing**
   - Identify independent tasks for parallel execution
   - Use async operations where possible
   - Monitor system resources

## Troubleshooting

### Common Issues

#### Installation Problems

**Issue**: "coral: command not found"
```bash
# Solution: Ensure virtual environment is activated
source venv/bin/activate
pip show coral-collective
```

**Issue**: "Permission denied" errors
```bash
# Solution: Never install system-wide
pip uninstall coral-collective  # if installed system-wide
python -m venv fresh_venv
source fresh_venv/bin/activate
pip install coral-collective[all]
```

#### Agent Execution Issues

**Issue**: Agent not found
```bash
# Solution: Check available agents
coral list
coral check --agents

# Verify agent name spelling
coral run project_architect --help
```

**Issue**: Out of context/tokens
```bash
# Solution: Use model optimization
coral run agent_name --model gpt-4-turbo --task "your task"

# Or split complex tasks
coral run agent_name --task "Part 1 of complex task"
coral run agent_name --task "Part 2 of complex task"
```

#### MCP Integration Problems

**Issue**: MCP servers not connecting
```bash
# Solution: Check configuration
coral check --mcp
coral mcp test-connection github

# Verify environment variables
echo $GITHUB_TOKEN
echo $DATABASE_URL
```

**Issue**: Permission denied for MCP operations
```bash
# Solution: Check MCP configuration
cat mcp/configs/mcp_config.yaml

# Update permissions as needed
coral config mcp --server github --permissions read,write
```

#### Memory System Issues

**Issue**: Memory system not initialized
```bash
# Solution: Set up memory system
coral setup memory --type local

# Check memory system status
coral check --memory
```

**Issue**: Poor memory retrieval results
```bash
# Solution: Adjust similarity threshold
coral config memory --similarity-threshold 0.6

# Or use different embedding model
coral config memory --embedding-model all-MiniLM-L6-v2
```

### Getting Help

1. **Check System Status**
   ```bash
   coral check --all
   coral --version
   ```

2. **View Logs**
   ```bash
   coral logs --level debug
   coral logs --agent backend_developer --last 10
   ```

3. **Community Support**
   - GitHub Issues: Bug reports and feature requests
   - GitHub Discussions: Questions and community help
   - Documentation: Comprehensive guides and examples

4. **Debug Mode**
   ```bash
   coral run agent_name --debug --task "your task"
   coral workflow full_stack --verbose --debug
   ```

### Performance Monitoring

Monitor system performance:

```bash
# Check resource usage
coral monitor --system

# View token usage statistics
coral tokens stats

# Memory system statistics
coral memory stats

# Agent performance metrics
coral agents performance
```

---

## Next Steps

Now that you've completed the user guide:

1. **Try the Tutorial**: Build your first project following the walkthrough
2. **Read Architecture Docs**: Understand system design in [ARCHITECTURE.md](ARCHITECTURE.md)
3. **Explore API Reference**: Detailed API documentation in [API_REFERENCE.md](../API_REFERENCE.md)
4. **Join Community**: Participate in GitHub Discussions
5. **Contribute**: See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines

Happy building with CoralCollective! 🪸