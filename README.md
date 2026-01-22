# CoralCollective 🪸

[![Python 3.8-3.12](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**The collective intelligence for evolutionary development** - 20+ specialized AI agents working as a unified team to build your software projects.

CoralCollective is an AI agent orchestration framework that can assist in how your software is built. Instead of working alone, you collaborate with a team of specialized AI agents, each expert in their domain, following a structured documentation-first workflow that ensures quality, security, and maintainability.

## ⚡ Quick Start

### Prerequisites
- Python 3.8 - 3.12 (3.10+ recommended for best performance)
- Virtual environment (recommended)
- API keys for AI models (OpenAI, Anthropic, etc.)

### Installation

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install CoralCollective
pip install -r requirements.txt

# Run the interactive interface
./start.sh
```

### Docker Installation
```bash
# Using Docker Compose
docker-compose up -d

# Or run directly
docker run -it coral-collective:latest
```

## 🎯 Key Features

### 20+ Specialized AI Agents
Each agent is an expert in their domain, working together seamlessly:

**Core Agents:**
- **Project Architect** - System design and architecture planning
- **Technical Writer** - Documentation specialist (requirements & user docs)

**Development Specialists:**
- **Backend Developer** - API and server-side development
- **Frontend Developer** - UI/UX implementation
- **Full Stack Engineer** - End-to-end development
- **Mobile Developer** - iOS/Android applications
- **Database Specialist** - Schema design and optimization
- **API Designer** - RESTful and GraphQL API design

**Quality & Operations:**
- **QA Testing** - Comprehensive testing strategies
- **Security Specialist** - Security analysis and implementation
- **DevOps Engineer** - CI/CD and deployment
- **Performance Engineer** - Optimization and scaling
- **Site Reliability Engineer** - Monitoring and reliability

**Specialized Experts:**
- **AI/ML Specialist** - Machine learning integration
- **Data Engineer** - Data pipelines and ETL
- **Analytics Engineer** - Analytics and reporting
- **Accessibility Specialist** - WCAG compliance
- **Compliance Specialist** - Regulatory compliance
- **UI Designer** - Design systems and mockups
- **Model Strategy Specialist** - AI model optimization

### Documentation-First Workflow
1. **Requirements Phase**: Technical Writer creates detailed specifications
2. **Architecture Phase**: Project Architect designs the system
3. **Implementation Phase**: Specialized developers build to specification
4. **Quality Phase**: QA and Security specialists validate
5. **Deployment Phase**: DevOps engineers deploy and monitor

### Smart Agent Handoffs
Each agent provides structured handoffs including:
- Completion summary
- Next agent recommendation
- Copy-paste ready prompts
- Context for the next agent

### 2026 Model Support
Optimized for the latest AI models:
- GPT-5.2 and GPT-5.2 Pro
- Claude 4.5 (Opus, Sonnet, Haiku)
- Gemini 3 Pro
- DeepSeek V3.2
- O3 and O3-mini

### MCP Integration
Direct integration with Model Context Protocol for:
- File system operations
- GitHub integration
- Database connections
- Docker management
- Web search capabilities

## 📁 Project Structure

```
coral-collective/
├── agents/                      # Agent prompt definitions
│   ├── core/                    # Core workflow agents
│   └── specialists/             # Specialized agents
├── config/                      # Configuration files
│   ├── agents.yaml              # Agent registry
│   └── model_assignments_2026.yaml  # Model configurations
├── mcp/                         # Model Context Protocol integration
│   ├── servers/                 # MCP server implementations
│   └── mcp_client.py           # Python MCP client
├── tools/                       # Utility modules
│   ├── project_state.py        # Project state management
│   └── feedback_collector.py   # Feedback system
├── docs/                        # Documentation
│   └── IDE_INTEGRATION.md      # VS Code & Claude integration
├── examples/                    # Usage examples
└── tests/                       # Test suite
```

## 🚀 Usage Examples

### Basic Agent Execution
```python
from agent_runner import AgentRunner

runner = AgentRunner()
result = runner.run_agent(
    agent_id="backend_developer",
    task="Create a REST API for user management",
    context={"framework": "FastAPI"}
)
```

### Full Project Workflow
```bash
# Start with architecture
python agent_runner.py run project_architect \
  --task "Design a scalable e-commerce platform"

# Generate requirements
python agent_runner.py run technical_writer \
  --task "Create detailed requirements" \
  --phase 1

# Implement backend
python agent_runner.py run backend_developer \
  --task "Implement REST API based on requirements"
```

### Interactive Mode
```bash
# Launch interactive interface
./start.sh

# Choose workflow type:
# 1. Full Stack Development
# 2. API Development  
# 3. Frontend Only
# 4. Custom Workflow
```

## 🔧 Configuration

### Model Configuration
Edit `config/model_assignments_2026.yaml` to configure model preferences:

```yaml
agent_assignments:
  backend_developer:
    primary: gpt-5.2
    fallback: claude-4.5-sonnet
    budget: deepseek-v3.2
    max_tokens: 25000
```

### Environment Variables
Create a `.env` file:

```bash
# Required API Keys
OPENAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key
GOOGLE_API_KEY=your-key  # For Gemini
DEEPSEEK_API_KEY=your-key  # Optional

# Optional Settings
CORAL_LOG_LEVEL=INFO
CORAL_CACHE_ENABLED=true
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest --cov=coral_collective tests/
```

## 🐳 Docker Deployment

```bash
# Build image
docker build -t coral-collective:latest .

# Run with docker-compose
docker-compose up -d

# Check logs
docker-compose logs -f
```

## 📊 Performance

- **60-80% cost reduction** through smart model routing
- **Parallel agent execution** for faster completion
- **Intelligent caching** to minimize API calls
- **Batch processing** for 50% cost savings

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
# Fork and clone
git clone https://github.com/YOUR-USERNAME/coral-collective.git
cd coral-collective

# Setup development environment
python3 -m venv venv
source venv/bin/activate
pip install -e .[dev]

# Run tests before submitting PR
pytest tests/
black .
```

## 🔧 IDE Integration

CoralCollective works seamlessly with popular IDEs and Claude's `/agent` command:

- **VS Code**: Full integration with tasks, debugging, and terminal
- **GitHub Desktop**: Visual git management for agent-generated code
- **Claude /agent**: Direct agent invocation in Claude conversations

See [IDE Integration Guide](docs/IDE_INTEGRATION.md) for detailed setup instructions.

## 📚 Documentation

- [User Guide](docs/USER_GUIDE.md) - Complete usage instructions
- [IDE Integration](docs/IDE_INTEGRATION.md) - VS Code, GitHub Desktop, and Claude setup
- [API Reference](docs/API_REFERENCE.md) - Detailed API documentation
- [Architecture](docs/ARCHITECTURE.md) - System design and patterns
- [Integration Guide](INTEGRATION.md) - Various integration methods
- [MCP Integration](docs/MCP_INTEGRATION_STRATEGY.md) - MCP setup guide
- [FAQ](docs/FAQ.md) - Common questions and solutions

### Version Information

```python
from coral_collective.utils import get_version_info

# Get detailed version information
info = get_version_info()
print(f"CoralCollective v{info['version']}")
```

## 🛟 Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/coral-collective/coral-collective/issues)
- **Discussions**: [Community forum](https://github.com/coral-collective/coral-collective/discussions)
- **Documentation**: [Full documentation](https://coral-collective.dev)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for the AI engineering community
- Inspired by collective intelligence in nature
- Powered by the latest AI models from OpenAI, Anthropic, Google, and DeepSeek

---

**Ready to evolve your development?** Start building with CoralCollective today! 🪸