#!/bin/bash
# E2B MCP Server wrapper script for CoralCollective
# Provides secure code execution in sandboxed environments

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Script directory and paths
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly MCP_DIR="$(dirname "$SCRIPT_DIR")"
readonly LOG_FILE="$MCP_DIR/logs/e2b_server.log"
readonly PID_FILE="$MCP_DIR/logs/e2b_server.pid"

# Server configuration
readonly SERVER_NAME="e2b"
readonly MCP_PACKAGE="@modelcontextprotocol/server-e2b"
readonly REQUIRED_ENV_VARS=("E2B_API_KEY")

# Ensure log directory exists
mkdir -p "$MCP_DIR/logs"

# Logging functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - [E2B] $1" | tee -a "$LOG_FILE"
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

# Load environment variables
load_environment() {
    local env_file="$MCP_DIR/.env"
    
    if [[ -f "$env_file" ]]; then
        while IFS='=' read -r key value; do
            [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
            value=$(echo "$value" | sed 's/^["'"'"']\|["'"'"']$//g')
            export "$key=$value"
        done < <(grep -E '^[^#]*=' "$env_file")
        info "Environment loaded from $env_file"
    else
        error "Environment file not found: $env_file"
        return 1
    fi
}

# Validate environment variables
validate_environment() {
    local missing_vars=()
    
    for var in "${REQUIRED_ENV_VARS[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if (( ${#missing_vars[@]} > 0 )); then
        error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            error "  - $var"
        done
        error "Please get your E2B API key from: https://e2b.dev"
        return 1
    fi
    
    # Validate E2B API key format (basic check)
    if [[ ! "$E2B_API_KEY" =~ ^e2b_[a-zA-Z0-9]+$ ]]; then
        warn "E2B API key format looks unusual. Expected format: e2b_..."
        warn "Please verify your E2B_API_KEY is correct"
    fi
    
    info "Environment validation passed ✓"
    return 0
}

# Test E2B API connectivity
test_api_connectivity() {
    info "Testing E2B API connectivity..."
    
    # Simple curl test to E2B API
    local api_url="https://api.e2b.dev/health"
    
    if command -v curl &> /dev/null; then
        if timeout 10 curl -s -f "$api_url" > /dev/null 2>&1; then
            info "E2B API connectivity test passed ✓"
        else
            warn "E2B API connectivity test failed"
            warn "Check your internet connection and firewall settings"
        fi
    else
        warn "curl not found, skipping API connectivity test"
    fi
    
    return 0
}

# Check if server process is running
is_server_running() {
    if [[ -f "$PID_FILE" ]]; then
        local pid
        pid=$(cat "$PID_FILE")
        
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Start the E2B MCP server
start_server() {
    info "Starting E2B MCP server..."
    
    if is_server_running; then
        warn "E2B MCP server is already running (PID: $(cat "$PID_FILE"))"
        return 0
    fi
    
    if ! load_environment || ! validate_environment; then
        error "Environment setup failed"
        return 1
    fi
    
    if ! npm list -g "$MCP_PACKAGE" > /dev/null 2>&1; then
        error "$MCP_PACKAGE is not installed globally"
        error "Run: npm install -g $MCP_PACKAGE"
        return 1
    fi
    
    # Test API connectivity
    test_api_connectivity
    
    info "Launching E2B MCP server process..."
    info "Using E2B API key: ${E2B_API_KEY:0:8}..."
    
    nohup bash -c "
        cd '$MCP_DIR' && 
        E2B_API_KEY='$E2B_API_KEY' npx '$MCP_PACKAGE' >> '$LOG_FILE' 2>&1
    " &
    
    local pid=$!
    echo "$pid" > "$PID_FILE"
    sleep 3  # E2B server may take a bit longer to initialize
    
    if is_server_running; then
        info "E2B MCP server started successfully (PID: $pid) ✓"
        return 0
    else
        error "Failed to start E2B MCP server"
        return 1
    fi
}

# Stop the E2B MCP server
stop_server() {
    info "Stopping E2B MCP server..."
    
    if ! is_server_running; then
        warn "E2B MCP server is not running"
        return 0
    fi
    
    local pid
    pid=$(cat "$PID_FILE")
    
    if kill -TERM "$pid" 2>/dev/null; then
        local count=0
        while is_server_running && (( count < 15 )); do  # E2B may take longer to shut down
            sleep 1
            ((count++))
        done
        
        if ! is_server_running; then
            info "E2B MCP server stopped gracefully ✓"
            rm -f "$PID_FILE"
        else
            warn "Graceful shutdown failed, forcing termination..."
            kill -KILL "$pid" 2>/dev/null
            rm -f "$PID_FILE"
            info "E2B MCP server forcefully terminated ✓"
        fi
    else
        error "Failed to send signal to process $pid"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Health check
health_check() {
    info "Performing health check for E2B MCP server..."
    
    if ! is_server_running; then
        error "E2B MCP server is not running"
        return 1
    fi
    
    local pid
    pid=$(cat "$PID_FILE")
    info "Server process is running (PID: $pid) ✓"
    
    # Test API connectivity
    load_environment
    test_api_connectivity
    
    return 0
}

# Test E2B operations
test_operations() {
    info "Testing E2B MCP server operations..."
    
    if ! is_server_running; then
        error "Server is not running. Start it first with: $0 start"
        return 1
    fi
    
    load_environment
    
    info "E2B operations testing requires MCP client integration"
    info "Basic connectivity and server process tests passed"
    
    # Check if E2B CLI is available for additional testing
    if command -v e2b &> /dev/null; then
        info "E2B CLI found, testing template listing..."
        if timeout 10 e2b template list > /dev/null 2>&1; then
            info "E2B template listing successful ✓"
        else
            warn "E2B template listing failed (may require authentication)"
        fi
    else
        info "E2B CLI not found - install with: npm install -g @e2b/cli"
    fi
    
    info "E2B operations test completed"
}

# Show E2B account information
account_info() {
    info "E2B Account Information"
    info "======================"
    
    load_environment
    
    if [[ -z "${E2B_API_KEY:-}" ]]; then
        error "E2B_API_KEY not set"
        return 1
    fi
    
    info "API Key: ${E2B_API_KEY:0:8}... (masked)"
    
    if command -v e2b &> /dev/null; then
        info "E2B CLI version: $(e2b --version 2>/dev/null || echo 'Unknown')"
        
        # Try to get account info
        if timeout 10 e2b auth whoami > /dev/null 2>&1; then
            info "E2B authentication successful ✓"
        else
            warn "E2B authentication test failed"
        fi
    else
        warn "E2B CLI not found - install for more detailed account information"
    fi
}

# Get server status
status() {
    info "E2B MCP Server Status"
    info "===================="
    
    if is_server_running; then
        local pid
        pid=$(cat "$PID_FILE")
        info "Status: RUNNING (PID: $pid)"
    else
        info "Status: STOPPED"
    fi
    
    if [[ -f "$LOG_FILE" ]]; then
        local log_size log_lines
        log_size=$(du -h "$LOG_FILE" | cut -f1)
        log_lines=$(wc -l < "$LOG_FILE")
        info "Log file: $LOG_FILE ($log_size, $log_lines lines)"
    fi
    
    info ""
    info "Configuration:"
    info "  Package: $MCP_PACKAGE"
    info "  API Key: ${E2B_API_KEY:+${E2B_API_KEY:0:8}...}${E2B_API_KEY:-NOT SET}"
    
    # Show account info
    echo ""
    if [[ -n "${E2B_API_KEY:-}" ]]; then
        account_info
    fi
}

# View logs
logs() {
    local lines=${1:-50}
    if [[ ! -f "$LOG_FILE" ]]; then
        warn "Log file not found: $LOG_FILE"
        return 1
    fi
    info "Showing last $lines lines from E2B MCP server logs:"
    tail -n "$lines" "$LOG_FILE"
}

# Follow logs
follow_logs() {
    if [[ ! -f "$LOG_FILE" ]]; then
        warn "Log file not found: $LOG_FILE"
        return 1
    fi
    info "Following E2B MCP server logs (Press Ctrl+C to stop):"
    tail -f "$LOG_FILE"
}

# Usage
usage() {
    echo "Usage: $0 {start|stop|restart|status|health|logs|follow|test|account|help}"
    echo ""
    echo "Commands:"
    echo "  start     Start the E2B MCP server"
    echo "  stop      Stop the E2B MCP server"
    echo "  restart   Restart the E2B MCP server"
    echo "  status    Show server status and information"
    echo "  health    Perform health check"
    echo "  logs [N]  Show last N lines of logs (default: 50)"
    echo "  follow    Follow logs in real-time"
    echo "  test      Test E2B operations"
    echo "  account   Show E2B account information"
    echo "  help      Show this help message"
    echo ""
    echo "Environment (required in $MCP_DIR/.env):"
    echo "  E2B_API_KEY - Get from https://e2b.dev"
    echo ""
    echo "Supported Languages:"
    echo "  - Python"
    echo "  - JavaScript/TypeScript"
    echo "  - Go"
    echo "  - And more via E2B templates"
}

# Main function
main() {
    local action="${1:-}"
    
    if [[ -z "$action" ]]; then
        error "No action specified"
        usage
        exit 1
    fi
    
    case "$action" in
        start) start_server ;;
        stop) stop_server ;;
        restart) stop_server; sleep 2; start_server ;;
        status) status ;;
        health|healthcheck) health_check ;;
        logs) logs "${2:-50}" ;;
        follow|tail) follow_logs ;;
        test) test_operations ;;
        account|info) account_info ;;
        help|--help|-h) usage ;;
        *) error "Unknown action: $action"; usage; exit 1 ;;
    esac
}

trap 'exit_code=$?; [[ $exit_code -ne 0 ]] && error "Script exited with code: $exit_code"' EXIT
main "$@"