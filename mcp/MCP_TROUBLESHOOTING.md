# CoralCollective MCP Troubleshooting Guide

This guide provides comprehensive troubleshooting information for resolving common issues with the CoralCollective MCP infrastructure.

## Table of Contents

- [Quick Diagnostic Steps](#quick-diagnostic-steps)
- [Common Error Patterns](#common-error-patterns)
- [Server-Specific Issues](#server-specific-issues)
- [Environment and Configuration](#environment-and-configuration)
- [Performance Issues](#performance-issues)
- [Network and Connectivity](#network-and-connectivity)
- [Advanced Troubleshooting](#advanced-troubleshooting)
- [Recovery Procedures](#recovery-procedures)

## Quick Diagnostic Steps

When experiencing issues, start with these rapid diagnostic commands:

### 1. System Status Check

```bash
# Check overall system status
npm run mcp:status

# Run comprehensive health check
npm run mcp:health

# View recent logs
ls -la mcp/logs/ | tail -10
```

### 2. Process Verification

```bash
# Check for running MCP processes
ps aux | grep mcp | grep -v grep

# Check PID files
ls -la mcp/logs/*.pid

# Verify process ownership and permissions
ls -la mcp/servers/*.sh
```

### 3. Configuration Validation

```bash
# Test environment loading
node -e "require('dotenv').config({path: './mcp/.env'}); console.log('Loaded vars:', Object.keys(process.env).filter(k => k.includes('GITHUB') || k.includes('E2B')))"

# Validate YAML configuration
node -e "console.log(require('js-yaml').load(require('fs').readFileSync('mcp/configs/mcp_config.yaml')))"

# Check file permissions
find mcp/ -type f -name "*.sh" ! -perm -u+x
```

## Common Error Patterns

### Pattern 1: "Command not found"

**Error Messages**:
```
bash: npx: command not found
bash: node: command not found
/usr/bin/env: 'node': No such file or directory
```

**Cause**: Node.js/npm not installed or not in PATH

**Solutions**:
```bash
# Check if Node.js is installed
which node
echo $PATH

# Install Node.js using package manager (Ubuntu/Debian)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install using Homebrew (macOS)  
brew install node

# Install using Node Version Manager
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 18
nvm use 18
```

### Pattern 2: "Permission denied"

**Error Messages**:
```
bash: ./setup_mcp.sh: Permission denied
./mcp/servers/github_server.sh: Permission denied
EACCES: permission denied, open '/path/to/file'
```

**Cause**: Missing execute permissions or file access rights

**Solutions**:
```bash
# Fix script permissions
chmod +x mcp/setup_mcp.sh
chmod +x mcp/servers/*.sh  
chmod +x mcp/scripts/*.js

# Fix directory permissions
chmod 755 mcp/{servers,scripts,monitoring,tests}
chmod 700 mcp/{logs,memory}

# Check file ownership
ls -la mcp/
sudo chown -R $USER:$USER mcp/
```

### Pattern 3: "Environment variable not set"

**Error Messages**:
```
Missing required environment variable: GITHUB_TOKEN
Environment file not found: /path/to/.env
Invalid GitHub token format
```

**Cause**: Missing or incorrectly configured environment variables

**Solutions**:
```bash
# Verify .env file exists and is readable
ls -la mcp/.env
cat mcp/.env | grep -v "^#" | grep "="

# Check for placeholder values
grep "your_.*_here" mcp/.env

# Test environment loading
cd mcp && node -e "
require('dotenv').config();
console.log('GITHUB_TOKEN:', process.env.GITHUB_TOKEN ? 'SET' : 'NOT SET');
console.log('E2B_API_KEY:', process.env.E2B_API_KEY ? 'SET' : 'NOT SET');
"

# Copy from template if missing
cp mcp/.env.example mcp/.env
```

### Pattern 4: "Package not found" or "Module not found"

**Error Messages**:
```
npm ERR! 404 Not Found - GET https://registry.npmjs.org/@modelcontextprotocol%2fserver-github
Error: Cannot find module '@modelcontextprotocol/server-github'
```

**Cause**: MCP packages not installed or npm registry issues

**Solutions**:
```bash
# Clear npm cache
npm cache clean --force

# Check npm registry connectivity
npm ping
npm config get registry

# Install packages manually
npm install -g @modelcontextprotocol/server-github
npm install -g @modelcontextprotocol/server-filesystem
npm install -g @modelcontextprotocol/server-postgres

# Check global installations
npm list -g @modelcontextprotocol/server-github

# Use local installation if global fails
cd /path/to/coral_collective
npm install @modelcontextprotocol/server-github
```

### Pattern 5: "Server failed to start"

**Error Messages**:
```
Server exited with code 1
GitHub MCP server failed to start
Process error: spawn ENOENT
```

**Cause**: Server configuration issues or missing dependencies

**Diagnostic Steps**:
```bash
# Test server package directly
npx @modelcontextprotocol/server-github --help

# Check server logs
tail -50 mcp/logs/github_server.log

# Test with verbose logging
DEBUG=* npx @modelcontextprotocol/server-github

# Verify environment variables for specific server
./mcp/servers/github_server.sh status
```

## Server-Specific Issues

### GitHub Server Issues

**Common Problems**:

1. **Invalid Token Format**
   ```bash
   # Test token validity
   curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
   
   # Expected token format: ghp_*, ghs_*, or github_pat_*
   echo $GITHUB_TOKEN | grep -E '^gh[ps]_|^github_pat_'
   ```

2. **Rate Limiting**
   ```bash
   # Check current rate limit status
   curl -H "Authorization: token $GITHUB_TOKEN" -I https://api.github.com/rate_limit
   
   # Look for X-RateLimit-Remaining header
   ```

3. **Repository Access**
   ```bash
   # Test repository access
   curl -H "Authorization: token $GITHUB_TOKEN" \
        https://api.github.com/repos/owner/repo
   ```

### Filesystem Server Issues

**Common Problems**:

1. **Path Access Denied**
   ```bash
   # Check PROJECT_ROOT accessibility
   ls -la "$PROJECT_ROOT"
   cd "$PROJECT_ROOT" && pwd
   
   # Test write permissions
   touch "$PROJECT_ROOT/test_write" && rm "$PROJECT_ROOT/test_write"
   ```

2. **Sandboxing Issues**
   ```bash
   # Check excluded paths configuration
   grep -A 10 "excluded_paths" mcp/configs/mcp_config.yaml
   
   # Verify path restrictions
   find "$PROJECT_ROOT" -name ".env" -o -name ".git" -type d
   ```

### PostgreSQL Server Issues

**Common Problems**:

1. **Connection Refused**
   ```bash
   # Test database connectivity
   pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER
   
   # Test connection string
   psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME" -c "SELECT version();"
   ```

2. **Authentication Failed**
   ```bash
   # Check credentials
   echo "Host: $DB_HOST, Port: $DB_PORT, User: $DB_USER, DB: $DB_NAME"
   
   # Test with psql
   PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;"
   ```

### Docker Server Issues

**Common Problems**:

1. **Docker Daemon Not Running**
   ```bash
   # Check Docker daemon status
   docker version
   docker ps
   
   # Start Docker daemon (varies by system)
   sudo systemctl start docker  # Linux
   # or use Docker Desktop app on macOS/Windows
   ```

2. **Socket Permission Issues**
   ```bash
   # Check socket permissions
   ls -la /var/run/docker.sock
   
   # Add user to docker group (Linux)
   sudo usermod -aG docker $USER
   # Then logout and login again
   ```

### E2B Server Issues  

**Common Problems**:

1. **Invalid API Key**
   ```bash
   # Test E2B API key
   curl -H "Authorization: Bearer $E2B_API_KEY" \
        https://api.e2b.dev/health
   ```

2. **Quota Exceeded**
   ```bash
   # Check usage limits
   curl -H "Authorization: Bearer $E2B_API_KEY" \
        https://api.e2b.dev/usage
   ```

## Environment and Configuration

### Environment File Issues

**Problem**: Environment variables not loading correctly

**Diagnostic Steps**:
```bash
# Check file format (no BOM, Unix line endings)
file mcp/.env
hexdump -C mcp/.env | head -1

# Check for invisible characters
cat -v mcp/.env | head -5

# Test loading in isolation
node -e "
const dotenv = require('dotenv');
const result = dotenv.config({path: 'mcp/.env'});
console.log('Loaded:', result.parsed);
console.log('Errors:', result.error);
"
```

**Common Fixes**:
```bash
# Remove BOM if present
sed -i '1s/^\xEF\xBB\xBF//' mcp/.env

# Convert to Unix line endings
dos2unix mcp/.env

# Remove trailing spaces
sed -i 's/[[:space:]]*$//' mcp/.env
```

### YAML Configuration Issues

**Problem**: Invalid YAML syntax or configuration

**Diagnostic Steps**:
```bash
# Validate YAML syntax
python3 -c "import yaml; print(yaml.safe_load(open('mcp/configs/mcp_config.yaml')))"

# Check with Node.js
node -e "console.log(require('js-yaml').load(require('fs').readFileSync('mcp/configs/mcp_config.yaml')))"

# Identify line with issue
yaml-lint mcp/configs/mcp_config.yaml  # if available
```

**Common Issues**:
- Mixed tabs and spaces (use spaces only)
- Incorrect indentation (2 spaces per level)
- Special characters not quoted
- Missing quotes around values with colons

### Path Resolution Issues

**Problem**: Incorrect path references in configuration

**Diagnostic Steps**:
```bash
# Check PROJECT_ROOT resolution
echo "PROJECT_ROOT: $PROJECT_ROOT"
ls -la "$PROJECT_ROOT"

# Check relative paths from MCP directory
cd mcp && pwd
ls -la ../  # Should show coral_collective contents

# Test path expansion
node -e "console.log('Resolved:', path.resolve(process.env.PROJECT_ROOT || '.'))"
```

## Performance Issues

### High Memory Usage

**Symptoms**:
- Servers crashing with out-of-memory errors
- System becoming unresponsive
- High swap usage

**Diagnostic Commands**:
```bash
# Check memory usage of MCP processes
ps aux | grep mcp | awk '{print $4, $11}' | sort -nr

# Monitor memory over time
./mcp/scripts/server_monitor.py --once

# Check system memory
free -h
# or on macOS:
vm_stat
```

**Solutions**:
```bash
# Limit memory per server (in mcp_config.yaml)
global:
  memory_limit_mb: 256  # Adjust per server needs

# Enable memory monitoring alerts
# Add to mcp/monitoring/alert_rules.yaml:
- name: "High Memory Usage"
  metric: "memory_mb"
  operator: ">"
  threshold: 500.0
  duration_seconds: 60
  enabled: true
```

### High CPU Usage

**Symptoms**:
- System slow or unresponsive
- Servers consuming excessive CPU
- Thermal throttling

**Diagnostic Commands**:
```bash
# Check CPU usage by process
top -p $(pgrep -d, mcp)

# Monitor CPU over time  
./mcp/scripts/server_monitor.py

# Check for CPU-intensive operations
strace -c -p <MCP_PID>  # Linux only
```

**Solutions**:
```bash
# Set CPU limits (systemd)
systemd-run --scope -p CPUQuota=50% your-mcp-command

# Enable CPU monitoring
# Add alert rule for high CPU usage
- name: "High CPU Usage"
  metric: "cpu_percent" 
  operator: ">"
  threshold: 80.0
  duration_seconds: 30
  enabled: true
```

### Slow Response Times

**Symptoms**:
- Timeouts in client requests
- Delayed server responses
- Health checks failing

**Diagnostic Steps**:
```bash
# Test individual server response time
time npx @modelcontextprotocol/server-github --help

# Check network latency
ping api.github.com
curl -w "@/dev/stdin" -o /dev/null -s https://api.github.com <<< "
     time_namelookup:  %{time_namelookup}\n
      time_connect:  %{time_connect}\n
   time_appconnect:  %{time_appconnect}\n
  time_pretransfer:  %{time_pretransfer}\n
     time_redirect:  %{time_redirect}\n
time_starttransfer:  %{time_starttransfer}\n
                   ----------\n
         time_total:  %{time_total}\n
"

# Monitor response times
./mcp/scripts/server_monitor.py --once | grep -i response
```

## Network and Connectivity

### API Rate Limiting

**GitHub API**:
```bash
# Check rate limit status
curl -H "Authorization: token $GITHUB_TOKEN" \
     -s https://api.github.com/rate_limit | jq '.rate'

# Monitor rate limit in logs
grep -i "rate limit" mcp/logs/github_server.log
```

**Solutions**:
- Use personal access token instead of app token
- Implement request caching
- Add delays between requests
- Use GraphQL API for complex queries

### DNS Resolution Issues

**Symptoms**:
- Timeouts connecting to external APIs
- Name resolution failures
- Intermittent connectivity

**Diagnostic Steps**:
```bash
# Test DNS resolution
nslookup api.github.com
dig api.github.com

# Check DNS configuration
cat /etc/resolv.conf

# Test with different DNS servers
nslookup api.github.com 8.8.8.8
```

### Proxy and Firewall Issues

**Corporate Networks**:
```bash
# Check proxy configuration
echo $HTTP_PROXY $HTTPS_PROXY $NO_PROXY

# Configure npm proxy
npm config set proxy http://proxy.company.com:8080
npm config set https-proxy https://proxy.company.com:8080

# Test connectivity through proxy
curl -x http://proxy.company.com:8080 https://api.github.com
```

## Advanced Troubleshooting

### Debug Mode Operation

**Enable Detailed Logging**:
```bash
# Set debug environment
export DEBUG=*
export MCP_LOG_LEVEL=DEBUG

# Run with verbose output
./mcp/servers/github_server.sh start

# Or start individual server with debug
DEBUG=* npx @modelcontextprotocol/server-github
```

### Tracing System Calls

**Linux Systems**:
```bash
# Trace server startup
strace -f -o /tmp/mcp_trace.log npx @modelcontextprotocol/server-github --help

# Monitor file access
strace -e trace=file ./mcp/servers/github_server.sh start

# Monitor network calls  
strace -e trace=network -p <MCP_PID>
```

**macOS Systems**:
```bash
# Use dtruss (requires SIP disable or proper entitlements)
sudo dtruss -n npx @modelcontextprotocol/server-github --help

# Monitor file access
sudo fs_usage -w -f filesystem | grep mcp
```

### Memory Leak Detection

**Node.js Memory Profiling**:
```bash
# Generate heap snapshot
node --inspect --heap-prof --heap-prof-interval=5000 \
     node_modules/.bin/@modelcontextprotocol/server-github

# Analyze with Node.js built-in profiler
node --prof --heap-prof your-server-script.js

# Use clinic.js for advanced profiling
npm install -g clinic
clinic doctor -- node your-server-script.js
```

### Process Monitoring

**Continuous Monitoring**:
```bash
# Monitor with watch
watch -n 5 'ps aux | grep mcp'

# Log resource usage over time
while true; do
  date >> resource_usage.log
  ps aux | grep mcp >> resource_usage.log
  free -h >> resource_usage.log
  echo "---" >> resource_usage.log
  sleep 60
done
```

## Recovery Procedures

### Emergency Shutdown

**Graceful Shutdown**:
```bash
# Stop all servers gracefully
npm run mcp:stop

# Kill all MCP processes if needed
pkill -f "mcp"
pkill -f "@modelcontextprotocol"

# Clean up PID files
rm -f mcp/logs/*.pid
```

### Configuration Reset

**Complete Configuration Reset**:
```bash
# Backup current configuration
cp mcp/.env mcp/.env.backup
cp -r mcp/configs mcp/configs.backup

# Reset to defaults
cp mcp/.env.example mcp/.env
git checkout mcp/configs/mcp_config.yaml

# Re-run setup
./mcp/setup_mcp.sh
```

### Database Recovery

**PostgreSQL Connection Recovery**:
```bash
# Reset connection pool
systemctl restart postgresql  # Linux
brew services restart postgresql  # macOS

# Clear connection cache
# In application, reconnect to database
```

### File System Recovery

**Permission Recovery**:
```bash
# Fix all permissions
find mcp/ -type f -name "*.sh" -exec chmod +x {} \;
find mcp/ -type f -name "*.js" -exec chmod +x {} \;
chmod 755 mcp/{servers,scripts,monitoring,tests}
chmod 700 mcp/{logs,memory}
chown -R $USER:$USER mcp/
```

### Log Rotation and Cleanup

**Emergency Log Cleanup**:
```bash
# Compress large logs
find mcp/logs -name "*.log" -size +100M -exec gzip {} \;

# Remove old compressed logs
find mcp/logs -name "*.log.gz" -mtime +7 -delete

# Truncate current logs if needed
for log in mcp/logs/*.log; do
  tail -1000 "$log" > "$log.tmp" && mv "$log.tmp" "$log"
done
```

## Escalation Procedures

### Information Gathering

Before escalating issues, gather:

```bash
# System information
uname -a > debug_info.txt
node --version >> debug_info.txt
npm --version >> debug_info.txt

# Configuration (sanitized)
cat mcp/.env | sed 's/=.*/=***REDACTED***/' >> debug_info.txt
cat mcp/configs/mcp_config.yaml >> debug_info.txt

# Process information
ps aux | grep mcp >> debug_info.txt

# Recent logs
tail -100 mcp/logs/*.log >> debug_info.txt

# Health check results
npm run mcp:health --json >> debug_info.txt

# Test results
npm run mcp:test --json >> debug_info.txt 2>&1
```

### Diagnostic Package Creation

```bash
# Create comprehensive diagnostic package
tar -czf mcp_diagnostic_$(date +%Y%m%d_%H%M%S).tar.gz \
  --exclude="mcp/.env" \
  --exclude="mcp/logs/*.log" \
  mcp/configs/ \
  mcp/scripts/ \
  debug_info.txt \
  <(echo "Environment variables (sanitized):"; env | grep -E "NODE|NPM|PATH" | head -20) \
  <(npm run mcp:health --json 2>/dev/null) \
  <(tail -100 mcp/logs/*.log 2>/dev/null)
```

This troubleshooting guide covers the most common issues and provides systematic approaches to diagnosis and resolution. Always start with the quick diagnostic steps before proceeding to more complex troubleshooting procedures.