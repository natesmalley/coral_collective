#!/bin/bash
# Brave Search MCP Server wrapper script for CoralCollective
# Provides web search capabilities and documentation lookup

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Script directory and paths
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly MCP_DIR="$(dirname "$SCRIPT_DIR")"
readonly LOG_FILE="$MCP_DIR/logs/brave_search_server.log"
readonly PID_FILE="$MCP_DIR/logs/brave_search_server.pid"

# Server configuration
readonly SERVER_NAME="brave-search"
readonly MCP_PACKAGE="@modelcontextprotocol/server-brave-search"
readonly REQUIRED_ENV_VARS=("BRAVE_API_KEY")

# Ensure log directory exists
mkdir -p "$MCP_DIR/logs"

# Logging functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - [BraveSearch] $1" | tee -a "$LOG_FILE"
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
        error "Please get your Brave Search API key from: https://brave.com/search/api/"
        return 1
    fi
    
    # Validate Brave API key format (basic check)
    if [[ ! "$BRAVE_API_KEY" =~ ^BSA[a-zA-Z0-9_-]+$ ]]; then
        warn "Brave API key format looks unusual. Expected format: BSA..."
        warn "Please verify your BRAVE_API_KEY is correct"
    fi
    
    info "Environment validation passed ✓"
    return 0
}

# Test Brave Search API connectivity
test_api_connectivity() {
    info "Testing Brave Search API connectivity..."
    
    local api_url="https://api.search.brave.com/res/v1/web/search"
    local test_query="test"
    
    if command -v curl &> /dev/null; then
        if timeout 10 curl -s -H "X-Subscription-Token: $BRAVE_API_KEY" \
           "$api_url?q=$test_query&count=1" > /dev/null 2>&1; then
            info "Brave Search API connectivity test passed ✓"
        else
            warn "Brave Search API connectivity test failed"
            warn "Check your API key and internet connection"
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

# Start the Brave Search MCP server
start_server() {
    info "Starting Brave Search MCP server..."
    
    if is_server_running; then
        warn "Brave Search MCP server is already running (PID: $(cat "$PID_FILE"))"
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
    
    info "Launching Brave Search MCP server process..."
    info "Using Brave API key: ${BRAVE_API_KEY:0:8}..."
    
    nohup bash -c "
        cd '$MCP_DIR' && 
        BRAVE_API_KEY='$BRAVE_API_KEY' npx '$MCP_PACKAGE' >> '$LOG_FILE' 2>&1
    " &
    
    local pid=$!
    echo "$pid" > "$PID_FILE"
    sleep 2
    
    if is_server_running; then
        info "Brave Search MCP server started successfully (PID: $pid) ✓"
        return 0
    else
        error "Failed to start Brave Search MCP server"
        return 1
    fi
}

# Stop the Brave Search MCP server
stop_server() {
    info "Stopping Brave Search MCP server..."
    
    if ! is_server_running; then
        warn "Brave Search MCP server is not running"
        return 0
    fi
    
    local pid
    pid=$(cat "$PID_FILE")
    
    if kill -TERM "$pid" 2>/dev/null; then
        local count=0
        while is_server_running && (( count < 10 )); do
            sleep 1
            ((count++))
        done
        
        if ! is_server_running; then
            info "Brave Search MCP server stopped gracefully ✓"
            rm -f "$PID_FILE"
        else
            warn "Graceful shutdown failed, forcing termination..."
            kill -KILL "$pid" 2>/dev/null
            rm -f "$PID_FILE"
            info "Brave Search MCP server forcefully terminated ✓"
        fi
    else
        error "Failed to send signal to process $pid"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Health check
health_check() {
    info "Performing health check for Brave Search MCP server..."
    
    if ! is_server_running; then
        error "Brave Search MCP server is not running"
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

# Test search operations
test_operations() {
    info "Testing Brave Search MCP server operations..."
    
    if ! is_server_running; then
        error "Server is not running. Start it first with: $0 start"
        return 1
    fi
    
    load_environment
    
    info "Testing Brave Search API directly..."
    
    if command -v curl &> /dev/null; then
        local api_url="https://api.search.brave.com/res/v1/web/search"
        local test_queries=("test search" "programming tutorial" "weather today")
        
        for query in "${test_queries[@]}"; do
            info "Testing search for: '$query'"
            
            local encoded_query
            encoded_query=$(printf '%s' "$query" | od -An -tx1 | tr ' ' '%')
            encoded_query=${encoded_query//%/%25}
            
            if timeout 15 curl -s -H "X-Subscription-Token: $BRAVE_API_KEY" \
               "$api_url?q=$query&count=3" | jq -e '.web.results | length > 0' > /dev/null 2>&1; then
                info "Search test passed: '$query' ✓"
            else
                warn "Search test failed: '$query'"
            fi
        done
    else
        warn "curl not found, cannot test API directly"
    fi
    
    info "Brave Search operations test completed"
}

# Show API quota information
quota_info() {
    info "Brave Search API Quota Information"
    info "=================================="
    
    load_environment
    
    if [[ -z "${BRAVE_API_KEY:-}" ]]; then
        error "BRAVE_API_KEY not set"
        return 1
    fi
    
    info "API Key: ${BRAVE_API_KEY:0:8}... (masked)"
    
    if command -v curl &> /dev/null && command -v jq &> /dev/null; then
        info "Checking API quota status..."
        
        # Make a simple request to check quota headers
        local api_url="https://api.search.brave.com/res/v1/web/search"
        local quota_response
        
        quota_response=$(timeout 10 curl -s -I -H "X-Subscription-Token: $BRAVE_API_KEY" \
            "$api_url?q=test&count=1" 2>/dev/null || echo "")
        
        if [[ -n "$quota_response" ]]; then
            local rate_limit_remaining
            rate_limit_remaining=$(echo "$quota_response" | grep -i "x-ratelimit-remaining:" | cut -d: -f2 | tr -d ' \r')
            
            local rate_limit_reset
            rate_limit_reset=$(echo "$quota_response" | grep -i "x-ratelimit-reset:" | cut -d: -f2 | tr -d ' \r')
            
            if [[ -n "$rate_limit_remaining" ]]; then
                info "Remaining requests: $rate_limit_remaining"
            fi
            
            if [[ -n "$rate_limit_reset" ]]; then
                local reset_time
                reset_time=$(date -d "@$rate_limit_reset" 2>/dev/null || echo "Unknown")
                info "Rate limit resets: $reset_time"
            fi
        else
            warn "Could not retrieve quota information"
        fi
    else
        warn "curl and jq required for quota information"
    fi
}

# Get server status
status() {
    info "Brave Search MCP Server Status"
    info "=============================="
    
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
    info "  API Key: ${BRAVE_API_KEY:+${BRAVE_API_KEY:0:8}...}${BRAVE_API_KEY:-NOT SET}"
    
    # Show quota info
    echo ""
    if [[ -n "${BRAVE_API_KEY:-}" ]]; then
        quota_info
    fi
}

# View logs
logs() {
    local lines=${1:-50}
    if [[ ! -f "$LOG_FILE" ]]; then
        warn "Log file not found: $LOG_FILE"
        return 1
    fi
    info "Showing last $lines lines from Brave Search MCP server logs:"
    tail -n "$lines" "$LOG_FILE"
}

# Follow logs
follow_logs() {
    if [[ ! -f "$LOG_FILE" ]]; then
        warn "Log file not found: $LOG_FILE"
        return 1
    fi
    info "Following Brave Search MCP server logs (Press Ctrl+C to stop):"
    tail -f "$LOG_FILE"
}

# Usage
usage() {
    echo "Usage: $0 {start|stop|restart|status|health|logs|follow|test|quota|help}"
    echo ""
    echo "Commands:"
    echo "  start     Start the Brave Search MCP server"
    echo "  stop      Stop the Brave Search MCP server"
    echo "  restart   Restart the Brave Search MCP server"
    echo "  status    Show server status and information"
    echo "  health    Perform health check"
    echo "  logs [N]  Show last N lines of logs (default: 50)"
    echo "  follow    Follow logs in real-time"
    echo "  test      Test search operations"
    echo "  quota     Show API quota information"
    echo "  help      Show this help message"
    echo ""
    echo "Environment (required in $MCP_DIR/.env):"
    echo "  BRAVE_API_KEY - Get from https://brave.com/search/api/"
    echo ""
    echo "Features:"
    echo "  - Web search with rich results"
    echo "  - Image search"
    echo "  - News search"
    echo "  - Local search"
    echo "  - Rate limiting and quota management"
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
        quota|info) quota_info ;;
        help|--help|-h) usage ;;
        *) error "Unknown action: $action"; usage; exit 1 ;;
    esac
}

trap 'exit_code=$?; [[ $exit_code -ne 0 ]] && error "Script exited with code: $exit_code"' EXIT
main "$@"