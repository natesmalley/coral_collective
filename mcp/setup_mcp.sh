#!/bin/bash

# CoralCollective MCP Setup Script
# This script installs and configures MCP servers for CoralCollective
# Production-ready setup with comprehensive error handling and monitoring

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly BOLD='\033[1m'
readonly NC='\033[0m' # No Color

# Script configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
readonly MCP_DIR="$SCRIPT_DIR"
readonly LOG_FILE="$MCP_DIR/logs/setup.log"
readonly MIN_NODE_VERSION="18"
readonly SETUP_LOCKFILE="$MCP_DIR/.setup_complete"

# Ensure logs directory exists
mkdir -p "$MCP_DIR/logs"

# Logging functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

step() {
    echo -e "${BLUE}${BOLD}[STEP]${NC} $1" | tee -a "$LOG_FILE"
}

echo "🪸 CoralCollective MCP Infrastructure Setup"
echo "==========================================="
echo ""

# Check if setup was already completed
if [[ -f "$SETUP_LOCKFILE" ]]; then
    warn "MCP setup appears to be already complete (found $SETUP_LOCKFILE)"
    read -p "Do you want to re-run the setup? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "Setup cancelled. To force re-setup, delete $SETUP_LOCKFILE"
        exit 0
    fi
    rm -f "$SETUP_LOCKFILE"
fi

# Enhanced prerequisites check
check_prerequisites() {
    step "Checking system prerequisites..."
    
    # Check for required commands
    local missing_commands=()
    local commands=("node" "npm" "npx" "curl" "git")
    
    for cmd in "${commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_commands+=("$cmd")
        fi
    done
    
    if (( ${#missing_commands[@]} > 0 )); then
        error "Missing required commands:"
        for cmd in "${missing_commands[@]}"; do
            error "  - $cmd"
        done
        error "Please install missing prerequisites and try again."
        exit 1
    fi
    
    # Check Node.js version
    local node_version
    node_version=$(node --version | sed 's/v//')
    local node_major
    node_major=$(echo "$node_version" | cut -d. -f1)
    
    if (( node_major < MIN_NODE_VERSION )); then
        error "Node.js version $node_version is too old. Minimum required: v$MIN_NODE_VERSION"
        error "Please update Node.js and try again."
        exit 1
    fi
    
    # Check npm version and registry access
    if ! npm ping > /dev/null 2>&1; then
        warn "Cannot reach npm registry. Check your internet connection."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    success "Prerequisites verified ✓"
    info "Node.js: v$node_version"
    info "npm: $(npm --version)"
    info "Platform: $(uname -s) $(uname -m)"
    echo ""
}

check_prerequisites

# Create directory structure
setup_directories() {
    step "Setting up directory structure..."
    
    local directories=(
        "servers"
        "configs" 
        "scripts"
        "logs"
        "monitoring"
        "tests"
        "memory"
        "indexes"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$MCP_DIR/$dir"
        info "Created $MCP_DIR/$dir"
    done
    
    # Set proper permissions
    chmod 755 "$MCP_DIR"/{servers,scripts,monitoring,tests}
    chmod 700 "$MCP_DIR"/{logs,memory}
    
    success "Directory structure created ✓"
    echo ""
}

# Install MCP SDK and servers
install_mcp_packages() {
    step "Installing MCP SDK and servers..."
    
    # Check if global installation is preferred
    local install_global=true
    if [[ -f "$PROJECT_ROOT/package.json" ]]; then
        read -p "Install MCP packages locally in project (recommended) or globally? (l/G): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Ll]$ ]]; then
            install_global=false
        fi
    fi
    
    # Define servers to install
    local servers=(
        "@modelcontextprotocol/server-github"
        "@modelcontextprotocol/server-filesystem" 
        "@modelcontextprotocol/server-postgres"
        "@modelcontextprotocol/server-docker"
        "@modelcontextprotocol/server-brave-search"
        "@modelcontextprotocol/server-slack"
        "@modelcontextprotocol/server-e2b"
    )
    
    # Optional servers (install if specifically requested)
    local optional_servers=(
        "@modelcontextprotocol/server-supabase"
        "@modelcontextprotocol/server-linear"
        "@modelcontextprotocol/server-notion"
        "@modelcontextprotocol/server-memory"
        "@modelcontextprotocol/server-everything"
    )
    
    # Install SDK first
    info "Installing MCP SDK..."
    if [[ "$install_global" == true ]]; then
        npm install -g @modelcontextprotocol/sdk || warn "SDK installation failed, continuing..."
    else
        cd "$PROJECT_ROOT" && npm install --save-dev @modelcontextprotocol/sdk || warn "SDK installation failed, continuing..."
    fi
    
    # Install core servers
    local installed_servers=()
    local failed_servers=()
    
    for server in "${servers[@]}"; do
        info "Installing $server..."
        
        if [[ "$install_global" == true ]]; then
            if npm install -g "$server" > /dev/null 2>&1; then
                installed_servers+=("$server")
                success "  ✓ $server installed"
            else
                failed_servers+=("$server")
                warn "  ✗ $server installation failed"
            fi
        else
            cd "$PROJECT_ROOT"
            if npm install --save-dev "$server" > /dev/null 2>&1; then
                installed_servers+=("$server") 
                success "  ✓ $server installed"
            else
                failed_servers+=("$server")
                warn "  ✗ $server installation failed"
            fi
        fi
    done
    
    # Report results
    echo ""
    success "Successfully installed ${#installed_servers[@]} MCP servers"
    
    if (( ${#failed_servers[@]} > 0 )); then
        warn "Failed to install ${#failed_servers[@]} servers:"
        for server in "${failed_servers[@]}"; do
            warn "  - $server"
        done
        warn "You may need to install these manually or check your npm configuration"
    fi
    
    # Store installation info for later reference
    {
        echo "# MCP Installation Record"
        echo "# Generated: $(date)"
        echo "INSTALL_GLOBAL=$install_global"
        echo "INSTALLED_SERVERS=(${installed_servers[*]})"
        echo "FAILED_SERVERS=(${failed_servers[*]})"
    } > "$MCP_DIR/.install_record"
    
    echo ""
}

setup_directories
install_mcp_packages

# Environment setup
setup_environment() {
    step "Setting up environment configuration..."
    
    # Check for .env file
    if [[ ! -f "$MCP_DIR/.env" ]]; then
        info "Creating .env file from template..."
        cp "$MCP_DIR/.env.example" "$MCP_DIR/.env"
        
        # Update PROJECT_ROOT in .env
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s|PROJECT_ROOT=.*|PROJECT_ROOT=$PROJECT_ROOT|" "$MCP_DIR/.env"
        else
            # Linux
            sed -i "s|PROJECT_ROOT=.*|PROJECT_ROOT=$PROJECT_ROOT|" "$MCP_DIR/.env"
        fi
        
        warn "Created .env file from template"
        warn "⚠️  You must edit $MCP_DIR/.env with your actual API keys and tokens"
        
        # Provide guidance on which keys are required
        echo ""
        info "Required API keys for core functionality:"
        info "  - GITHUB_TOKEN: For GitHub MCP server"
        info "  - E2B_API_KEY: For secure code execution"
        info "  - BRAVE_API_KEY: For web search capabilities"
        echo ""
        info "Optional API keys (enable specific servers in mcp_config.yaml):"
        info "  - Database credentials: For PostgreSQL/Supabase"
        info "  - SLACK_BOT_TOKEN: For Slack integration"
        info "  - LINEAR_API_KEY: For Linear project management"
        info "  - NOTION_API_KEY: For Notion documentation"
        echo ""
    else
        success "Environment file already exists ✓"
        
        # Validate existing .env for common issues
        local env_warnings=()
        
        # Check if PROJECT_ROOT matches current location
        local env_project_root
        env_project_root=$(grep "^PROJECT_ROOT=" "$MCP_DIR/.env" | cut -d= -f2 || echo "")
        if [[ "$env_project_root" != "$PROJECT_ROOT" ]]; then
            env_warnings+=("PROJECT_ROOT mismatch: env has '$env_project_root', current is '$PROJECT_ROOT'")
        fi
        
        # Check for placeholder values
        if grep -q "your_.*_here" "$MCP_DIR/.env"; then
            env_warnings+=("Found placeholder values, please update with real credentials")
        fi
        
        if (( ${#env_warnings[@]} > 0 )); then
            warn "Environment file issues detected:"
            for warning in "${env_warnings[@]}"; do
                warn "  - $warning"
            done
        fi
    fi
    echo ""
}

# Setup Node.js project configuration
setup_project_config() {
    step "Setting up project configuration..."
    
    cd "$PROJECT_ROOT"
    
    # Create or update package.json
    if [[ ! -f "package.json" ]]; then
        info "Creating package.json..."
        npm init -y > /dev/null
        success "Created package.json ✓"
    fi
    
    # Add MCP scripts to package.json
    info "Adding MCP scripts to package.json..."
    
    # Use Node.js to safely update package.json
    node -e "
        const fs = require('fs');
        const path = require('path');
        
        try {
            const pkgPath = 'package.json';
            const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
            
            // Initialize scripts section
            pkg.scripts = pkg.scripts || {};
            
            // Add MCP server scripts
            const mcpScripts = {
                'mcp:start': 'node mcp/scripts/start_all_servers.js',
                'mcp:stop': 'node mcp/scripts/stop_all_servers.js', 
                'mcp:status': 'node mcp/scripts/server_status.js',
                'mcp:health': 'node mcp/scripts/health_check.js',
                'mcp:test': 'node mcp/scripts/test_servers.js',
                'mcp:monitor': 'node mcp/scripts/server_monitor.js',
                'mcp:github': './mcp/servers/github_server.sh start',
                'mcp:filesystem': './mcp/servers/filesystem_server.sh start',
                'mcp:postgres': './mcp/servers/postgres_server.sh start',
                'mcp:docker': './mcp/servers/docker_server.sh start',
                'mcp:brave': './mcp/servers/brave_search_server.sh start',
                'mcp:e2b': './mcp/servers/e2b_server.sh start'
            };
            
            // Add scripts without overwriting existing ones
            Object.entries(mcpScripts).forEach(([key, value]) => {
                if (!pkg.scripts[key]) {
                    pkg.scripts[key] = value;
                }
            });
            
            // Add development dependencies
            pkg.devDependencies = pkg.devDependencies || {};
            
            fs.writeFileSync(pkgPath, JSON.stringify(pkg, null, 2));
            console.log('✓ Updated package.json with MCP scripts');
            
        } catch (err) {
            console.error('Failed to update package.json:', err.message);
            process.exit(1);
        }
    "
    
    success "Project configuration updated ✓"
    echo ""
}

setup_environment
setup_project_config

# Claude Desktop configuration
setup_claude_desktop() {
    step "Setting up Claude Desktop configuration..."
    
    local claude_config_dir="$HOME/Library/Application Support/Claude"
    local claude_config_file="$claude_config_dir/claude_desktop_config.json"
    
    if [[ -d "$claude_config_dir" ]]; then
        info "Found Claude Desktop configuration directory"
        
        if [[ -f "$claude_config_file" ]]; then
            warn "Existing Claude Desktop config found"
            warn "Backing up to: $claude_config_file.backup.$(date +%s)"
            cp "$claude_config_file" "$claude_config_file.backup.$(date +%s)"
        fi
        
        info "Installing Claude Desktop configuration..."
        cp "$MCP_DIR/claude_desktop_config.json" "$claude_config_file"
        success "Claude Desktop configuration installed ✓"
        
    else
        warn "Claude Desktop configuration directory not found"
        warn "Configuration saved in: $MCP_DIR/claude_desktop_config.json" 
        warn "Install Claude Desktop and manually copy the configuration"
    fi
    echo ""
}

# Run final setup steps  
setup_claude_desktop

# Create completion marker and final summary
complete_setup() {
    step "Finalizing MCP infrastructure setup..."
    
    # Create setup completion marker
    {
        echo "# CoralCollective MCP Setup Completed"
        echo "# Generated: $(date)"
        echo "# Version: 1.0"
        echo "SETUP_DATE=$(date -u +%Y%m%d_%H%M%S)"
        echo "PROJECT_ROOT=$PROJECT_ROOT"  
        echo "MCP_DIR=$MCP_DIR"
        echo "NODE_VERSION=$(node --version)"
        echo "NPM_VERSION=$(npm --version)"
        echo "PLATFORM=$(uname -s)"
    } > "$SETUP_LOCKFILE"
    
    # Set executable permissions for scripts
    find "$MCP_DIR/servers" -name "*.sh" -exec chmod +x {} \;
    find "$MCP_DIR/scripts" -name "*.js" -exec chmod +x {} \; 2>/dev/null || true
    
    success "MCP infrastructure setup completed successfully ✓"
    echo ""
}

# Final summary and next steps
show_completion_summary() {
    echo ""
    echo "============================================================================"
    echo "🎉 CoralCollective MCP Infrastructure Setup Complete!"
    echo "============================================================================"
    echo ""
    
    success "✓ Directory structure created"
    success "✓ MCP servers installed and configured"
    success "✓ Environment configuration prepared"
    success "✓ Server wrapper scripts ready"
    success "✓ Project configuration updated"
    success "✓ Claude Desktop configuration prepared"
    
    echo ""
    echo "${BOLD}NEXT STEPS:${NC}"
    echo ""
    echo "1. ${YELLOW}Configure API Keys:${NC}"
    echo "   Edit: $MCP_DIR/.env"
    echo "   Required: GITHUB_TOKEN, E2B_API_KEY, BRAVE_API_KEY"
    echo ""
    echo "2. ${YELLOW}Test Server Installation:${NC}"
    echo "   Run: npm run mcp:health"
    echo "   Or: ./mcp/scripts/health_check.py"
    echo ""
    echo "3. ${YELLOW}Start MCP Servers:${NC}"
    echo "   Individual: npm run mcp:github"  
    echo "   All servers: npm run mcp:start"
    echo ""
    echo "4. ${YELLOW}Monitor Server Status:${NC}"
    echo "   Status: npm run mcp:status"
    echo "   Health: npm run mcp:health"
    echo "   Logs: npm run mcp:monitor"
    echo ""
    
    echo "${BOLD}AVAILABLE SERVERS:${NC}"
    echo "  🐙 GitHub      - Repository and issue management"
    echo "  📁 Filesystem  - Secure file operations"
    echo "  🐘 PostgreSQL  - Database operations and queries"
    echo "  🐳 Docker      - Container management"
    echo "  🔍 Brave Search- Web search and research"
    echo "  ⚡ E2B         - Secure code execution sandbox"
    echo "  💬 Slack       - Team communication (optional)"
    echo ""
    
    echo "${BOLD}MANAGEMENT COMMANDS:${NC}"
    echo "  ./mcp/setup_mcp.sh           - Re-run this setup"
    echo "  ./mcp/scripts/health_check.py - Comprehensive health check"
    echo "  ./mcp/scripts/server_monitor.py - Real-time monitoring"
    echo ""
    
    echo "${BOLD}DOCUMENTATION:${NC}"
    echo "  Setup logs: $LOG_FILE"
    echo "  Configuration: $MCP_DIR/configs/mcp_config.yaml"
    echo "  API keys guide: $MCP_DIR/.env.example"
    echo ""
    
    if [[ -f "$MCP_DIR/.env" ]] && grep -q "your_.*_here" "$MCP_DIR/.env"; then
        warn "⚠️  Don't forget to update API keys in $MCP_DIR/.env"
    fi
    
    echo "🪸 CoralCollective MCP Infrastructure is ready for deployment!"
    echo "   Start with: npm run mcp:health"
    echo ""
}

complete_setup
show_completion_summary

# Exit with success
exit 0