#!/bin/bash
# MCP Server Installation Script for CoralCollective
# Installs all required npm packages for MCP servers

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Script directory
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly MCP_DIR="$(dirname "$SCRIPT_DIR")"
readonly PROJECT_ROOT="$(dirname "$MCP_DIR")"

# Logging
readonly LOG_FILE="$MCP_DIR/logs/install.log"

# Ensure log directory exists
mkdir -p "$MCP_DIR/logs"

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

# Check prerequisites
check_prerequisites() {
    info "Checking prerequisites..."
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        error "Node.js is not installed. Please install Node.js 18+ first."
        error "Visit: https://nodejs.org/en/download/"
        exit 1
    fi
    
    local node_version
    node_version=$(node --version | sed 's/v//')
    local node_major
    node_major=$(echo "$node_version" | cut -d. -f1)
    
    if (( node_major < 18 )); then
        error "Node.js version $node_version found. Minimum required: 18.x"
        error "Please upgrade Node.js: https://nodejs.org/en/download/"
        exit 1
    fi
    
    info "Node.js version: $node_version ✓"
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        error "npm is not installed. Please install npm first."
        exit 1
    fi
    
    local npm_version
    npm_version=$(npm --version)
    info "npm version: $npm_version ✓"
    
    # Check npx
    if ! command -v npx &> /dev/null; then
        error "npx is not installed. Please install npx first."
        exit 1
    fi
    
    info "npx available ✓"
    
    # Check disk space (minimum 1GB)
    local available_space
    available_space=$(df "$MCP_DIR" | awk 'NR==2 {print $4}')
    if (( available_space < 1048576 )); then  # 1GB in KB
        warn "Low disk space detected. At least 1GB recommended for MCP servers."
    fi
    
    info "Prerequisites check completed ✓"
}

# Install Tier 1 MCP Servers
install_tier1_servers() {
    info "Installing Tier 1 MCP servers..."
    
    local servers=(
        "@modelcontextprotocol/server-github"
        "@modelcontextprotocol/server-filesystem" 
        "@modelcontextprotocol/server-postgres"
        "@modelcontextprotocol/server-docker"
        "@modelcontextprotocol/server-e2b"
        "@modelcontextprotocol/server-brave-search"
    )
    
    local failed_installs=()
    
    for server in "${servers[@]}"; do
        info "Installing $server..."
        
        if npm install -g "$server" >> "$LOG_FILE" 2>&1; then
            info "$server installed successfully ✓"
        else
            error "Failed to install $server"
            failed_installs+=("$server")
        fi
    done
    
    if (( ${#failed_installs[@]} > 0 )); then
        error "Failed to install the following servers:"
        for server in "${failed_installs[@]}"; do
            error "  - $server"
        done
        warn "Some MCP servers may not be available"
        return 1
    fi
    
    info "All Tier 1 MCP servers installed successfully ✓"
    return 0
}

# Install optional/enhanced servers
install_optional_servers() {
    info "Installing optional MCP servers..."
    
    local optional_servers=(
        "@modelcontextprotocol/server-slack"
        "@modelcontextprotocol/server-linear"
        "@modelcontextprotocol/server-notion"
        "@modelcontextprotocol/server-supabase"
    )
    
    for server in "${optional_servers[@]}"; do
        info "Installing optional server: $server..."
        
        if npm install -g "$server" >> "$LOG_FILE" 2>&1; then
            info "$server installed successfully ✓"
        else
            warn "Optional server $server failed to install (this is not critical)"
        fi
    done
    
    info "Optional server installation completed"
}

# Verify installations
verify_installations() {
    info "Verifying MCP server installations..."
    
    local servers_to_verify=(
        "@modelcontextprotocol/server-github"
        "@modelcontextprotocol/server-filesystem"
        "@modelcontextprotocol/server-postgres"
        "@modelcontextprotocol/server-docker"
        "@modelcontextprotocol/server-e2b"
        "@modelcontextprotocol/server-brave-search"
    )
    
    local verification_failures=()
    
    for server in "${servers_to_verify[@]}"; do
        info "Verifying $server..."
        
        # Try to run the server with --help flag
        if timeout 10s npx "$server" --help > /dev/null 2>&1; then
            info "$server verification passed ✓"
        else
            error "$server verification failed"
            verification_failures+=("$server")
        fi
    done
    
    if (( ${#verification_failures[@]} > 0 )); then
        error "The following servers failed verification:"
        for server in "${verification_failures[@]}"; do
            error "  - $server"
        done
        return 1
    fi
    
    info "All MCP servers verified successfully ✓"
    return 0
}

# Create necessary directories
setup_directories() {
    info "Setting up MCP directory structure..."
    
    local dirs=(
        "$MCP_DIR/logs"
        "$MCP_DIR/memory"
        "$MCP_DIR/indexes"
        "$MCP_DIR/temp"
        "$MCP_DIR/backups"
    )
    
    for dir in "${dirs[@]}"; do
        if mkdir -p "$dir"; then
            info "Created directory: $dir ✓"
        else
            error "Failed to create directory: $dir"
            exit 1
        fi
    done
    
    # Set appropriate permissions
    chmod 755 "$MCP_DIR/logs"
    chmod 755 "$MCP_DIR/memory"
    chmod 755 "$MCP_DIR/indexes"
    chmod 755 "$MCP_DIR/temp"
    chmod 755 "$MCP_DIR/backups"
    
    info "Directory setup completed ✓"
}

# Create .env file if it doesn't exist
setup_environment() {
    info "Setting up environment configuration..."
    
    local env_file="$MCP_DIR/.env"
    local env_example="$MCP_DIR/.env.example"
    
    if [[ ! -f "$env_example" ]]; then
        info "Creating .env.example template..."
        cat > "$env_example" << 'EOF'
# CoralCollective MCP Server Environment Configuration
# Copy this file to .env and fill in your actual values

# Project Configuration
PROJECT_ROOT=/path/to/your/project

# GitHub Configuration (Required for GitHub MCP Server)
GITHUB_TOKEN=your_github_personal_access_token_here

# Database Configuration (Required for PostgreSQL MCP Server)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password

# E2B Configuration (Required for E2B MCP Server)
E2B_API_KEY=your_e2b_api_key_here

# Brave Search Configuration (Required for Brave Search MCP Server)
BRAVE_API_KEY=your_brave_api_key_here

# Docker Configuration (Optional)
DOCKER_HOST=unix:///var/run/docker.sock

# Supabase Configuration (Optional - only if using Supabase instead of PostgreSQL)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here

# Slack Configuration (Optional - only if enabling Slack integration)
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_TEAM_ID=your_slack_team_id

# Linear Configuration (Optional - only if enabling Linear integration)
LINEAR_API_KEY=your_linear_api_key_here

# Notion Configuration (Optional - only if enabling Notion integration)
NOTION_API_KEY=your_notion_api_key_here
EOF
        info ".env.example template created ✓"
    fi
    
    if [[ ! -f "$env_file" ]]; then
        info "Creating default .env file..."
        cp "$env_example" "$env_file"
        info ".env file created from template"
        warn "Please edit $env_file with your actual configuration values"
    else
        info ".env file already exists ✓"
    fi
}

# Display installation summary
display_summary() {
    info "==============================================="
    info "        MCP Server Installation Summary"
    info "==============================================="
    
    # Check which servers are available
    local available_servers=()
    local unavailable_servers=()
    
    local servers_to_check=(
        "@modelcontextprotocol/server-github"
        "@modelcontextprotocol/server-filesystem"
        "@modelcontextprotocol/server-postgres"
        "@modelcontextprotocol/server-docker"
        "@modelcontextprotocol/server-e2b"
        "@modelcontextprotocol/server-brave-search"
    )
    
    for server in "${servers_to_check[@]}"; do
        if npm list -g "$server" > /dev/null 2>&1; then
            available_servers+=("$server")
        else
            unavailable_servers+=("$server")
        fi
    done
    
    info "Available MCP Servers (${#available_servers[@]}):"
    for server in "${available_servers[@]}"; do
        info "  ✓ $server"
    done
    
    if (( ${#unavailable_servers[@]} > 0 )); then
        warn "Unavailable MCP Servers (${#unavailable_servers[@]}):"
        for server in "${unavailable_servers[@]}"; do
            warn "  ✗ $server"
        done
    fi
    
    info ""
    info "Next Steps:"
    info "1. Edit $MCP_DIR/.env with your API keys and configuration"
    info "2. Run '$MCP_DIR/scripts/start_mcp_servers.sh' to start the servers"
    info "3. Run '$MCP_DIR/scripts/health_check.sh' to verify everything is working"
    info ""
    info "For more information, see: $MCP_DIR/README.md"
    info "==============================================="
}

# Main installation function
main() {
    info "Starting MCP server installation for CoralCollective..."
    
    # Change to MCP directory
    cd "$MCP_DIR"
    
    check_prerequisites
    setup_directories
    setup_environment
    
    if install_tier1_servers; then
        install_optional_servers
        
        if verify_installations; then
            info "MCP server installation completed successfully! ✓"
            display_summary
            exit 0
        else
            error "Installation verification failed"
            exit 1
        fi
    else
        error "Critical server installation failed"
        exit 1
    fi
}

# Handle cleanup on script exit
cleanup() {
    local exit_code=$?
    if (( exit_code != 0 )); then
        error "Installation failed with exit code: $exit_code"
        error "Check the log file for details: $LOG_FILE"
    fi
}

trap cleanup EXIT

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --optional-only)
            # Only install optional servers
            info "Installing optional servers only..."
            check_prerequisites
            setup_directories
            install_optional_servers
            exit 0
            ;;
        --verify-only)
            # Only verify existing installations
            info "Verifying existing installations..."
            verify_installations
            exit $?
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "OPTIONS:"
            echo "  --optional-only    Install only optional MCP servers"
            echo "  --verify-only      Verify existing installations without installing"
            echo "  --help, -h         Show this help message"
            echo ""
            echo "Default behavior: Install all Tier 1 and optional MCP servers"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            error "Use --help for usage information"
            exit 1
            ;;
    esac
    shift
done

# Run main installation
main "$@"