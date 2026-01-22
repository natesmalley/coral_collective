# CoralCollective Deployment Guide

Simple deployment instructions for CoralCollective using Docker and pip.

## Table of Contents

- [Quick Start](#quick-start)
- [Docker Deployment](#docker-deployment)
- [Python Package Installation](#python-package-installation)
- [Environment Configuration](#environment-configuration)
- [Basic Security](#basic-security)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

- Python 3.8+
- Docker and Docker Compose (for containerized deployment)
- Git
- 4GB RAM minimum, 8GB recommended
- API keys for AI models (OpenAI, Anthropic, etc.)

### One-Line Installation

```bash
# Clone and setup
git clone https://github.com/coral-collective/coral-collective.git
cd coral-collective
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
./start.sh
```

## Docker Deployment

### Basic Docker Setup

1. **Clone the repository:**
```bash
git clone https://github.com/coral-collective/coral-collective.git
cd coral-collective
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Run with Docker Compose:**
```bash
docker-compose up -d
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  coral-collective:
    build: .
    container_name: coral-collective
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./projects:/app/projects
      - ./feedback:/app/feedback
    ports:
      - "8000:8000"
    restart: unless-stopped
```

### Building Docker Image

```bash
# Build the image
docker build -t coral-collective:latest .

# Run the container
docker run -d \
  --name coral-collective \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -v $(pwd)/projects:/app/projects \
  -p 8000:8000 \
  coral-collective:latest
```

## Python Package Installation

### Install from PyPI (Coming Soon)

```bash
pip install coral-collective
```

### Install from Source

```bash
# Clone the repository
git clone https://github.com/coral-collective/coral-collective.git
cd coral-collective

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install as package
pip install -e .
```

### Using CoralCollective

```python
from coral_collective import AgentRunner

# Initialize runner
runner = AgentRunner()

# Run an agent
result = runner.run_agent(
    agent_id="backend_developer",
    task="Create a REST API with authentication",
    context={"project": "my-api"}
)

print(result)
```

## Environment Configuration

### Required Environment Variables

Create a `.env` file with:

```bash
# AI Model API Keys (at least one required)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key  # For Gemini
DEEPSEEK_API_KEY=your-deepseek-key  # Optional

# Optional Configuration
CORAL_PROJECT_PATH=./projects
CORAL_LOG_LEVEL=INFO
CORAL_MAX_WORKERS=4
CORAL_CACHE_ENABLED=true
```

### Model Configuration

Edit `config/model_assignments_2026.yaml` to configure model preferences:

```yaml
# Example: Use cheaper models
agent_assignments:
  backend_developer:
    primary: deepseek-v3.2  # Cost-effective option
    fallback: gpt-5.2
    max_tokens: 25000
```

## Basic Security

### API Key Management

1. **Never commit `.env` files:**
```bash
# .gitignore should include
.env
*.env
```

2. **Use environment variables in production:**
```bash
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
```

3. **Rotate keys regularly**

### File System Permissions

```bash
# Secure project files
chmod 700 projects/
chmod 600 .env
```

### Docker Security

```dockerfile
# Run as non-root user
RUN useradd -m -u 1000 coral
USER coral
```

## Troubleshooting

### Common Issues

**1. Module not found errors:**
```bash
pip install -r requirements.txt --upgrade
```

**2. Permission errors:**
```bash
# Fix permissions
chmod +x start.sh
chmod +x coral
```

**3. API key errors:**
```bash
# Verify environment variables
python -c "import os; print('Keys set:', bool(os.getenv('OPENAI_API_KEY')))"
```

**4. Resource issues:**
```bash
# Increase Docker resources
docker update --memory=4g --cpus=2 coral-collective
```

### Debug Mode

```bash
# Enable debug logging
export CORAL_LOG_LEVEL=DEBUG
python agent_runner.py run --debug
```

### Getting Help

- GitHub Issues: https://github.com/coral-collective/coral-collective/issues
- Documentation: https://coral-collective.dev/docs
- Community Discord: https://discord.gg/coral-collective

## Next Steps

- Read the [User Guide](USER_GUIDE.md) for detailed usage instructions
- Check [API Reference](API_REFERENCE.md) for programmatic access
- See [Architecture](ARCHITECTURE.md) for system design details
- Review [FAQ](FAQ.md) for common questions