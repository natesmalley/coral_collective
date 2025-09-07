# CoralCollective MCP Infrastructure 🪸

## Overview

Complete production-ready Model Context Protocol (MCP) server infrastructure for CoralCollective AI development framework. This comprehensive system provides secure, sandboxed access to external services, complete with health monitoring, orchestration, and management tools.

## Key Features

- **🚀 Complete MCP Server Infrastructure**: 6 core MCP servers with production-ready configuration
- **⚙️ Automated Setup & Management**: Comprehensive setup script and orchestration tools
- **🔍 Health Monitoring & Diagnostics**: Real-time monitoring, health checks, and integration testing
- **🔐 Security-First Design**: Agent-specific permissions, audit logging, sandboxed operations
- **📊 Observability**: Comprehensive logging, metrics, alerting, and status reporting
- **🛠️ Production Operations**: Server management, log rotation, emergency procedures

## Quick Start

### 1. Basic Usage

```python
import asyncio
from mcp.mcp_client import MCPClient, AgentMCPInterface

async def main():
    # Create client with configuration
    async with MCPClient('mcp/configs/mcp_config.yaml') as client:
        
        # List available servers
        servers = client.get_available_servers()
        print(f"Available servers: {servers}")
        
        # Check agent permissions
        can_access = client.check_agent_permissions('backend_developer', 'filesystem')
        print(f"Backend dev can access filesystem: {can_access}")
        
        # List tools from a server
        tools = await client.list_tools('filesystem')
        print(f"Filesystem tools: {[tool['name'] for tool in tools]}")
        
        # Call a tool
        result = await client.call_tool('filesystem', 'read_file', {'path': 'README.md'})
        print(f"File content: {result.get('content', '')[:100]}...")

asyncio.run(main())
```

### 2. Agent Interface

```python
import asyncio
from mcp.mcp_client import AgentMCPInterface

async def agent_workflow():
    # Create agent-specific interface
    interface = AgentMCPInterface('backend_developer')
    
    try:
        # Filesystem operations
        content = await interface.filesystem_read('package.json')
        success = await interface.filesystem_write('output.txt', 'Hello MCP!')
        files = await interface.filesystem_list('src/')
        
        # GitHub operations
        issue = await interface.github_create_issue(
            title="Bug Report",
            body="Description of the issue",
            labels=["bug", "high-priority"]
        )
        
        # Database operations
        users = await interface.database_query("SELECT * FROM users LIMIT 10")
        
        # Web search
        results = await interface.search_web("React best practices", max_results=5)
        
        # Docker operations
        output = await interface.docker_run('python:3.11', 'python --version')
        
        # Code execution in sandbox
        result = await interface.e2b_execute('print("Hello from E2B!")', 'python')
        
    finally:
        await interface.close()

asyncio.run(agent_workflow())
```

### 3. Installation & Configuration

```bash
# Run the setup script
cd coral_collective
chmod +x mcp/setup_mcp.sh
./mcp/setup_mcp.sh

# Copy and edit the environment file
cp mcp/.env.example mcp/.env
# Edit mcp/.env with your API keys and tokens

# Test the client
python3 mcp/test_mcp_client.py
```

## Available MCP Servers

### Core Stack (Tier 1)

| Server | Purpose | Status | Agents |
|--------|---------|--------|--------|
| **GitHub** | Repository management, PRs, issues | ✅ Ready | All |
| **Filesystem** | Secure file operations | ✅ Ready | All |
| **PostgreSQL** | Database operations | ✅ Ready | Backend, Database |
| **Docker** | Container management | ✅ Ready | DevOps, Backend |
| **E2B** | Secure code execution | ✅ Ready | QA, Testing |

### Productivity (Tier 2)

| Server | Purpose | Status | Agents |
|--------|---------|--------|--------|
| **Brave Search** | Web research | ✅ Ready | All |
| **Slack** | Team communication | 🔧 Config needed | Project, DevOps |
| **Linear/Jira** | Project management | 🔧 Config needed | Project Architect |
| **Notion** | Documentation | 🔧 Config needed | Technical Writer |

## Agent-Specific Capabilities

### Backend Developer
```python
# Available MCP servers
- GitHub: Full repository access
- PostgreSQL: Database operations
- Docker: Container management
- Filesystem: Code file operations
- E2B: Test execution
```

### Frontend Developer
```python
# Available MCP servers
- GitHub: Repository management
- Filesystem: Component files
- E2B: Component testing
- Brave Search: Documentation lookup
```

### DevOps & Deployment
```python
# Available MCP servers
- Docker: Container orchestration
- GitHub: CI/CD management
- Filesystem: Config files
- Slack: Deployment notifications
```

## Client Architecture

### Core Components

- **MCPClient**: Main client class for MCP server communication
- **MCPConnection**: Manages individual server connections with retry logic
- **MCPTransport**: Handles stdio communication and message framing
- **MCPMessage**: JSON-RPC 2.0 message serialization/deserialization
- **AgentMCPInterface**: High-level interface for CoralCollective agents

### Production Features

- **Connection Pooling**: Efficient server connection management
- **Circuit Breaker**: Fault tolerance for failing servers
- **Health Monitoring**: Background health checks and metrics
- **Caching**: Tool list caching with TTL expiration
- **Security**: Agent-specific permissions and audit logging
- **Error Handling**: Comprehensive retry logic and graceful degradation

## API Reference

### MCPClient Class

Main client class for MCP server communication.

```python
class MCPClient:
    def __init__(self, config_path: str = "mcp/configs/mcp_config.yaml")
    
    # Lifecycle management
    async def initialize(self) -> None
    async def connect_server(self, server_name: str) -> bool
    async def shutdown(self) -> None
    
    # Tool operations
    async def list_tools(self, server_name: str) -> List[Dict[str, Any]]
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any
    async def send_request(self, server_name: str, method: str, params: Dict[str, Any]) -> Any
    
    # Permission management
    def check_agent_permissions(self, agent_id: str, server_name: str) -> bool
    def get_tools_for_agent(self, agent_id: str) -> Dict[str, List[str]]
    
    # Information and monitoring
    def get_available_servers(self) -> List[str]
    def get_server_info(self, server_name: str) -> Optional[Dict[str, Any]]
    def get_metrics(self) -> Dict[str, Any]
```

### AgentMCPInterface Class

High-level interface for CoralCollective agents with built-in security.

```python
class AgentMCPInterface:
    def __init__(self, agent_type: str, client: Optional[MCPClient] = None)
    
    # GitHub operations
    async def github_create_issue(self, title: str, body: str, labels: List[str] = None) -> Optional[Dict]
    async def github_create_pr(self, title: str, body: str, head: str, base: str = 'main') -> Optional[Dict]
    
    # Filesystem operations
    async def filesystem_read(self, path: str) -> Optional[str]
    async def filesystem_write(self, path: str, content: str) -> bool
    async def filesystem_list(self, path: str) -> List[str]
    
    # Database operations
    async def database_query(self, query: str, params: List[Any] = None) -> List[Dict]
    
    # Web search and external APIs
    async def search_web(self, query: str, max_results: int = 10) -> List[Dict]
    
    # Container operations
    async def docker_run(self, image: str, command: str = None, env: Dict[str, str] = None) -> Optional[str]
    
    # Secure code execution
    async def e2b_execute(self, code: str, language: str = 'python') -> Optional[Dict]
    
    # Tool discovery and management
    async def get_available_tools(self) -> Dict[str, List[Dict]]
    async def close(self) -> None
```

### Direct CLI Usage

```bash
# GitHub operations
npx @modelcontextprotocol/server-github create-issue --title "New feature" --body "Description"

# File operations
npx @modelcontextprotocol/server-filesystem read --path "./src/index.js"

# Database queries
npx @modelcontextprotocol/server-postgres query --sql "SELECT * FROM users"
```

## Claude Desktop Integration

### Setup

1. Locate Claude Desktop config:
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

2. Add MCP servers configuration:
```json
{
  "mcpServers": {
    "coral-github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your_token_here"
      }
    },
    "coral-filesystem": {
      "command": "npx",
      "args": [
        "-y", 
        "@modelcontextprotocol/server-filesystem",
        "/path/to/coral_collective"
      ]
    }
  }
}
```

3. Restart Claude Desktop

### Using MCP in Claude

Once configured, you can use MCP tools directly in Claude:

```
"Use the GitHub MCP server to create a new issue for the bug we discussed"

"Read the backend configuration file using the filesystem MCP server"

"Query the users table to find active accounts using the PostgreSQL server"
```

## Security Configuration

### Sandboxing

All file operations are sandboxed to the project directory:

```yaml
filesystem:
  sandboxed: true
  excluded_paths:
    - .env
    - .git
    - secrets/
    - node_modules/
```

### Read-Only Mode

For production databases:

```yaml
postgres:
  mode: read_only  # Prevents write operations
  branch: production
```

### Agent Permissions

Each agent has specific MCP server access:

```yaml
security_specialist:
  servers:
    - github
    - filesystem
  read_only: true  # All operations are read-only
```

## Environment Variables

Required environment variables in `mcp/.env`:

```bash
# GitHub
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# Database
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=coral_collective_dev

# Brave Search
BRAVE_API_KEY=BSA_xxxxxxxxxxxxxxxxxxxx

# E2B (Code Execution)
E2B_API_KEY=e2b_xxxxxxxxxxxxxxxxxxxx

# Docker
DOCKER_HOST=unix:///var/run/docker.sock

# Project
PROJECT_ROOT=/path/to/coral_collective
```

## Troubleshooting

### Common Issues

#### MCP Server Not Found
```bash
# Reinstall the server
npm install -g @modelcontextprotocol/server-github
```

#### Permission Denied
```bash
# Check agent permissions in mcp_config.yaml
# Ensure the agent has access to the required server
```

#### Connection Failed
```bash
# Check environment variables
cat mcp/.env | grep GITHUB_TOKEN

# Test server directly
npx @modelcontextprotocol/server-github --help
```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Advanced Configuration

### Custom MCP Server

Create a custom MCP server for specific needs:

```javascript
// mcp/servers/custom-server.js
const { Server } = require('@modelcontextprotocol/sdk');

const server = new Server({
  name: 'custom-coral-server',
  version: '1.0.0',
  tools: [
    {
      name: 'custom_tool',
      description: 'Custom tool for CoralCollective',
      inputSchema: {
        type: 'object',
        properties: {
          param: { type: 'string' }
        }
      },
      handler: async ({ param }) => {
        // Tool implementation
        return { result: 'success' };
      }
    }
  ]
});

server.start();
```

### Monitoring

Track MCP usage:

```python
# mcp/monitor.py
import json
from datetime import datetime

def log_mcp_operation(agent, server, operation, result):
    with open('mcp/logs/operations.json', 'a') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'agent': agent,
            'server': server,
            'operation': operation,
            'success': result
        }, f)
        f.write('\n')
```

## Best Practices

1. **Start Small**: Begin with GitHub and Filesystem servers
2. **Test Thoroughly**: Validate each integration before production
3. **Monitor Usage**: Track which tools provide most value
4. **Security First**: Always use least privilege principle
5. **Document Everything**: Keep detailed logs of MCP operations
6. **Version Control**: Track MCP configurations in Git

## Performance Optimization

### Caching

Enable caching for frequently accessed data:

```yaml
features:
  enable_caching: true
  cache_ttl: 300  # 5 minutes
```

### Connection Pooling

Reuse MCP connections:

```python
class MCPConnectionPool:
    def __init__(self, max_connections=10):
        self.pool = {}
        self.max_connections = max_connections
    
    async def get_connection(self, server_name):
        if server_name not in self.pool:
            self.pool[server_name] = await self.connect(server_name)
        return self.pool[server_name]
```

## Roadmap

### Phase 1 (Current)
- ✅ GitHub MCP Server
- ✅ Filesystem MCP Server
- ✅ PostgreSQL MCP Server
- ✅ Docker MCP Server
- ✅ E2B Code Execution

### Phase 2 (Next Month)
- 🔄 Slack Integration
- 🔄 Linear/Jira Integration
- 🔄 Notion Documentation
- 🔄 MongoDB Support
- 🔄 Redis Caching

### Phase 3 (Q2 2025)
- 📋 AWS/Azure Integration
- 📋 Stripe Payments
- 📋 Sentry Monitoring
- 📋 Figma Design System
- 📋 Custom MCP Servers

## Contributing

To add a new MCP server:

1. Install the server package
2. Add configuration to `mcp_config.yaml`
3. Update agent permissions
4. Add Python interface methods
5. Test with relevant agents
6. Document usage

## Support

- **Documentation**: See `MCP_INTEGRATION_STRATEGY.md`
- **Issues**: Create GitHub issue with `mcp` label
- **Updates**: Check official MCP repository

---

*Last Updated: January 2025*
*Maintained by: CoralCollective Team*