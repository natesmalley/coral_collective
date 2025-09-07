# CoralCollective MCP Infrastructure Setup Guide

This guide provides comprehensive instructions for setting up and configuring the CoralCollective MCP (Model Context Protocol) server infrastructure.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Setup](#quick-setup)
- [Detailed Configuration](#detailed-configuration)
- [Server Management](#server-management)
- [Troubleshooting](#troubleshooting)
- [API Key Configuration](#api-key-configuration)
- [Advanced Configuration](#advanced-configuration)

## Prerequisites

Before starting the MCP setup, ensure you have the following installed:

### Required Software

- **Node.js**: Version 18 or higher
- **npm**: Version 8 or higher (comes with Node.js)
- **Python**: Version 3.8 or higher (for health checks and monitoring)
- **Git**: For repository management

### System Requirements

- **Operating System**: macOS, Linux, or Windows with WSL
- **Memory**: At least 4GB RAM available
- **Disk Space**: 2GB free space for MCP servers and logs
- **Network**: Internet connection for package installation

### Verification Commands

```bash
# Check Node.js version
node --version  # Should be v18.0.0 or higher

# Check npm version
npm --version   # Should be 8.0.0 or higher

# Check Python version
python3 --version  # Should be 3.8 or higher

# Check Git
git --version
```

## Quick Setup

The fastest way to get MCP infrastructure up and running:

### 1. Run the Setup Script

```bash
# Navigate to the MCP directory
cd mcp/

# Make setup script executable
chmod +x setup_mcp.sh

# Run the comprehensive setup
./setup_mcp.sh
```

### 2. Configure API Keys

Edit the environment file with your actual credentials:

```bash
# Copy and edit the environment file
cp .env.example .env
nano .env  # or your preferred editor
```

**Required API Keys:**
- `GITHUB_TOKEN`: GitHub Personal Access Token
- `E2B_API_KEY`: E2B Code Execution API key
- `BRAVE_API_KEY`: Brave Search API key

### 3. Start MCP Servers

```bash
# Start all enabled servers
npm run mcp:start

# Check status
npm run mcp:status

# Run health check
npm run mcp:health
```

## Detailed Configuration

### Environment Configuration

The `.env` file contains all configuration for MCP servers:

```bash
# GitHub MCP Server (Required)
GITHUB_TOKEN=ghp_your_github_token_here
GITHUB_OWNER=your_github_username
GITHUB_REPO=your_default_repo

# E2B Code Execution (Required for secure sandboxing)
E2B_API_KEY=your_e2b_api_key_here

# Brave Search (Required for web search capabilities)
BRAVE_API_KEY=your_brave_search_api_key_here

# Project Configuration
PROJECT_ROOT=/path/to/your/coral_collective
MCP_LOG_LEVEL=INFO
MCP_ENABLE_AUDIT=true

# Database (Optional - configure if using database features)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password

# Docker (Optional - uses default socket)
DOCKER_HOST=unix:///var/run/docker.sock

# Additional Services (Optional)
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
LINEAR_API_KEY=your_linear_api_key
NOTION_API_KEY=your_notion_api_key
```

### Server Configuration

MCP servers are configured in `configs/mcp_config.yaml`. Each server can be enabled/disabled and customized:

```yaml
mcp_servers:
  github:
    enabled: true
    command: npx
    args:
      - "@modelcontextprotocol/server-github"
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "${GITHUB_TOKEN}"
    permissions:
      - repo_read
      - repo_write
      - issue_manage
    agents:
      - all

  filesystem:
    enabled: true
    command: npx
    args:
      - "@modelcontextprotocol/server-filesystem"
      - "${PROJECT_ROOT}"
    permissions:
      - read
      - write
      - create
    sandboxed: true
    excluded_paths:
      - .env
      - .git
      - secrets/
```

### Agent Permissions

Configure which agents can access which servers:

```yaml
agent_permissions:
  backend_developer:
    servers:
      - github
      - filesystem
      - postgres
      - docker
    max_tokens_per_operation: 25000
    
  frontend_developer:
    servers:
      - github
      - filesystem
      - e2b
    max_tokens_per_operation: 20000
```

## Server Management

### Starting and Stopping Servers

```bash
# Start all enabled servers
npm run mcp:start

# Stop all running servers
npm run mcp:stop

# Restart all servers
npm run mcp:stop && npm run mcp:start

# Start individual server
npm run mcp:github
./mcp/servers/github_server.sh start

# Stop individual server
./mcp/servers/github_server.sh stop
```

### Monitoring and Health Checks

```bash
# Check status of all servers
npm run mcp:status

# Run comprehensive health check
npm run mcp:health

# Start real-time monitoring dashboard
npm run mcp:monitor

# Run integration tests
npm run mcp:test
```

### Log Management

```bash
# View logs for a specific server
./mcp/servers/github_server.sh logs

# Follow logs in real-time
./mcp/servers/github_server.sh follow

# View all server logs
ls -la mcp/logs/

# Check log file sizes
du -h mcp/logs/*.log
```

## Troubleshooting

### Common Issues and Solutions

#### 1. "Node.js version too old"

**Problem**: Setup script reports Node.js version is insufficient.

**Solution**:
```bash
# Install Node.js 18+ using Node Version Manager
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 18
nvm use 18
```

#### 2. "npm install failed" or "Package not found"

**Problem**: MCP server packages can't be installed.

**Solutions**:
```bash
# Clear npm cache
npm cache clean --force

# Update npm
npm install -g npm@latest

# Check npm registry access
npm ping

# Try manual installation
npm install -g @modelcontextprotocol/server-github
```

#### 3. "Environment variable missing"

**Problem**: Server fails to start due to missing API keys.

**Solution**:
```bash
# Check current environment
cat mcp/.env

# Verify environment loading
node -e "require('dotenv').config({path: './mcp/.env'}); console.log('GITHUB_TOKEN:', !!process.env.GITHUB_TOKEN);"

# Test individual server configuration
./mcp/servers/github_server.sh help
```

#### 4. "Permission denied" errors

**Problem**: Scripts can't execute or access files.

**Solutions**:
```bash
# Fix script permissions
chmod +x mcp/setup_mcp.sh
chmod +x mcp/servers/*.sh
chmod +x mcp/scripts/*.js

# Fix directory permissions
chmod 755 mcp/{servers,scripts,monitoring,tests}
chmod 700 mcp/{logs,memory}
```

#### 5. "Server not responding" or "Health check failed"

**Problem**: Server starts but doesn't respond to requests.

**Diagnostic Steps**:
```bash
# Check if process is actually running
ps aux | grep mcp

# Check server logs for errors
tail -f mcp/logs/github_server.log

# Test server manually
npx @modelcontextprotocol/server-github --help

# Check network connectivity
curl -I https://api.github.com
```

#### 6. "Port already in use" or "Address in use"

**Problem**: Server can't bind to required port.

**Solutions**:
```bash
# Find processes using ports
lsof -i :8080  # Replace with actual port

# Kill conflicting processes
pkill -f "mcp-server"

# Check for stale PID files
ls -la mcp/logs/*.pid
rm mcp/logs/*.pid  # If servers are not actually running
```

### Diagnostic Commands

```bash
# Comprehensive system check
./mcp/scripts/health_check.py

# Test individual server connectivity  
./mcp/scripts/health_check.py --server=github

# Run full integration test suite
./mcp/scripts/test_servers.js

# Check configuration validity
node -e "const yaml=require('js-yaml'); const fs=require('fs'); console.log(yaml.load(fs.readFileSync('mcp/configs/mcp_config.yaml')))"

# Test environment variable resolution
./mcp/servers/github_server.sh status

# Monitor server resource usage
./mcp/scripts/server_monitor.py --once
```

### Log Analysis

#### Common Log Patterns

**Successful startup**:
```
2024-01-31 10:30:45 - [GitHub] Starting GitHub MCP server...
2024-01-31 10:30:47 - [GitHub] Server started successfully (PID: 12345) ✓
```

**API Authentication issues**:
```
2024-01-31 10:30:50 - [ERROR] GitHub API authentication failed
2024-01-31 10:30:50 - [ERROR] Please check GITHUB_TOKEN in .env file
```

**Memory/Resource issues**:
```
2024-01-31 10:35:22 - [WARN] High memory usage detected: 85%
2024-01-31 10:35:25 - [ERROR] Out of memory, server crashed
```

#### Log File Locations

```
mcp/logs/
├── setup.log              # Setup script output
├── startup_report.json     # Server startup results
├── shutdown_report.json    # Server shutdown results
├── status_report.json      # Latest status report
├── github_server.log       # GitHub server logs
├── filesystem_server.log   # Filesystem server logs
├── postgres_server.log     # PostgreSQL server logs
├── docker_server.log       # Docker server logs
├── e2b_server.log         # E2B server logs
├── brave_search_server.log # Brave Search server logs
└── *.pid                  # Process ID files
```

## API Key Configuration

### GitHub Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Select scopes:
   - `repo` (for repository access)
   - `read:org` (for organization info)
   - `workflow` (for GitHub Actions)
4. Copy token to `GITHUB_TOKEN` in `.env`

### E2B API Key

1. Visit [E2B.dev](https://e2b.dev)
2. Sign up/log in
3. Go to API Keys section
4. Generate new API key
5. Copy to `E2B_API_KEY` in `.env`

### Brave Search API Key

1. Visit [Brave Search API](https://brave.com/search/api/)
2. Sign up for developer account
3. Create new application
4. Generate API key
5. Copy to `BRAVE_API_KEY` in `.env`

### Database Configuration (Optional)

For PostgreSQL integration:

```bash
# Local PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=coral_collective
DB_USER=your_username
DB_PASSWORD=your_password

# Or Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key
```

## Advanced Configuration

### Custom Server Configuration

Create custom server configurations by modifying `configs/mcp_config.yaml`:

```yaml
mcp_servers:
  custom_server:
    enabled: true
    command: node
    args:
      - "custom/server.js"
    env:
      CUSTOM_API_KEY: "${CUSTOM_API_KEY}"
    permissions:
      - custom_permission
    agents:
      - specific_agent_only
    features:
      - custom_feature
```

### Security Configuration

```yaml
security:
  require_authentication: true
  encrypt_communications: true
  log_all_operations: true
  rate_limiting:
    requests_per_minute: 100
    requests_per_hour: 5000
  forbidden_operations:
    - delete_production_data
    - modify_security_settings
  allowed_file_extensions:
    - .py
    - .js
    - .ts
    - .md
```

### Monitoring Configuration

Create `mcp/monitoring/alert_rules.yaml`:

```yaml
alert_rules:
  - name: "High CPU Usage"
    metric: "cpu_percent"
    operator: ">"
    threshold: 80.0
    duration_seconds: 30
    enabled: true
    
  - name: "Server Down"
    metric: "status"
    operator: "=="
    threshold: "stopped"
    duration_seconds: 10
    enabled: true
```

### Performance Tuning

```yaml
# In mcp_config.yaml
global:
  max_concurrent_servers: 10
  request_timeout_seconds: 30
  memory_limit_mb: 512
  enable_caching: true
  enable_retry_logic: true
  enable_circuit_breaker: true
```

## Maintenance and Operations

### Regular Maintenance Tasks

```bash
# Weekly health check
npm run mcp:health --save weekly_report.json

# Log rotation (if not handled by system)
find mcp/logs -name "*.log" -size +100M -exec gzip {} \;

# Clean old reports
find mcp/logs -name "*_report.json" -mtime +30 -delete

# Update MCP servers
npm update -g @modelcontextprotocol/server-*

# Backup configuration
tar -czf mcp_config_backup_$(date +%Y%m%d).tar.gz mcp/configs/ mcp/.env
```

### Monitoring Best Practices

1. **Regular Health Checks**: Run `npm run mcp:health` daily
2. **Log Monitoring**: Check logs weekly for error patterns
3. **Resource Monitoring**: Monitor CPU/memory usage trends
4. **Performance Testing**: Run integration tests after changes
5. **Backup**: Keep configuration and environment file backups

### Scaling Considerations

- **Server Limits**: Each server has memory and CPU requirements
- **Concurrent Connections**: Limit based on available resources  
- **Log Management**: Implement log rotation for long-running systems
- **API Rate Limits**: Monitor API usage to avoid hitting limits
- **Database Connections**: Pool database connections appropriately

## Getting Help

### Support Channels

- **Documentation**: Review this guide and inline code comments
- **Health Check**: Run `npm run mcp:health` for diagnostic information  
- **Integration Tests**: Use `npm run mcp:test` to validate setup
- **Logs**: Check server logs in `mcp/logs/` for error details

### Reporting Issues

When reporting issues, include:

1. **System Information**: OS, Node.js version, npm version
2. **Configuration**: Sanitized `.env` and `mcp_config.yaml` contents
3. **Error Messages**: Complete error output from logs
4. **Steps to Reproduce**: Exact commands and sequence
5. **Health Check Output**: Results from `npm run mcp:health --json`

### Emergency Procedures

**Complete Reset**:
```bash
# Stop all servers
npm run mcp:stop

# Clean all runtime data
rm -rf mcp/logs/*.log mcp/logs/*.pid

# Reset to clean state
./mcp/setup_mcp.sh

# Reconfigure and restart
# Edit .env file
npm run mcp:start
```

---

## Summary

This MCP infrastructure provides a robust, scalable foundation for CoralCollective's AI agent operations. The setup script automates most configuration, while the management tools provide comprehensive monitoring and control capabilities.

Key commands to remember:
- `./mcp/setup_mcp.sh` - Initial setup
- `npm run mcp:start` - Start all servers  
- `npm run mcp:status` - Check server status
- `npm run mcp:health` - Run health checks
- `npm run mcp:monitor` - Real-time monitoring

For ongoing operations, establish regular monitoring routines and keep API keys current to ensure reliable service.