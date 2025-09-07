#!/bin/bash
# Filesystem MCP Server wrapper script for CoralCollective
# Provides secure file system operations with sandboxing

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Script directory and paths
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly MCP_DIR="$(dirname "$SCRIPT_DIR")"
readonly LOG_FILE="$MCP_DIR/logs/filesystem_server.log"
readonly PID_FILE="$MCP_DIR/logs/filesystem_server.pid"

# Server configuration
readonly SERVER_NAME="filesystem"
readonly MCP_PACKAGE="@modelcontextprotocol/server-filesystem"
readonly REQUIRED_ENV_VARS=("PROJECT_ROOT")
readonly HEALTH_CHECK_TIMEOUT=10

# Default project root if not set
readonly DEFAULT_PROJECT_ROOT="$(dirname "$MCP_DIR")"

# Ensure log directory exists
mkdir -p "$MCP_DIR/logs"

# Logging functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - [Filesystem] $1" | tee -a "$LOG_FILE"
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
        # Source .env file, but only export the variables we need
        while IFS='=' read -r key value; do
            # Skip empty lines and comments
            [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
            
            # Remove quotes from value
            value=$(echo "$value" | sed 's/^["'"'"']\|["'"'"']$//g')
            
            # Export the variable
            export "$key=$value"
        done < <(grep -E '^[^#]*=' "$env_file")
        
        info "Environment loaded from $env_file"
    else
        warn "Environment file not found: $env_file"
        warn "Using default PROJECT_ROOT: $DEFAULT_PROJECT_ROOT"
        export PROJECT_ROOT="$DEFAULT_PROJECT_ROOT"
    fi
    
    # Set PROJECT_ROOT to default if not provided
    if [[ -z "${PROJECT_ROOT:-}" ]]; then
        export PROJECT_ROOT="$DEFAULT_PROJECT_ROOT"
        info "Using default PROJECT_ROOT: $PROJECT_ROOT"
    fi
}

# Validate required environment variables and paths
validate_environment() {
    # Expand PROJECT_ROOT path
    PROJECT_ROOT=$(realpath "$PROJECT_ROOT" 2>/dev/null || echo "$PROJECT_ROOT")
    export PROJECT_ROOT
    
    # Validate PROJECT_ROOT exists
    if [[ ! -d "$PROJECT_ROOT" ]]; then
        error "PROJECT_ROOT directory does not exist: $PROJECT_ROOT"
        return 1
    fi
    
    # Check if PROJECT_ROOT is readable
    if [[ ! -r "$PROJECT_ROOT" ]]; then
        error "PROJECT_ROOT is not readable: $PROJECT_ROOT"
        return 1
    fi
    
    # Security check: ensure PROJECT_ROOT is not a system directory
    local system_paths=("/bin" "/sbin" "/usr/bin" "/usr/sbin" "/etc" "/root" "/boot" "/sys" "/proc" "/dev")
    for sys_path in "${system_paths[@]}"; do
        if [[ "$PROJECT_ROOT" == "$sys_path"* ]]; then
            error "PROJECT_ROOT cannot be a system directory: $PROJECT_ROOT"
            error "This is a security risk. Please use a user directory."
            return 1
        fi
    done
    
    info "PROJECT_ROOT validated: $PROJECT_ROOT ✓"
    return 0
}

# Check if server process is running
is_server_running() {
    if [[ -f "$PID_FILE" ]]; then
        local pid
        pid=$(cat "$PID_FILE")
        
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # Process is running
        else
            # PID file exists but process is not running
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    
    return 1  # PID file doesn't exist
}

# Start the Filesystem MCP server
start_server() {
    info "Starting Filesystem MCP server..."
    
    # Check if already running
    if is_server_running; then
        warn "Filesystem MCP server is already running (PID: $(cat "$PID_FILE"))"
        return 0
    fi
    
    # Load and validate environment
    if ! load_environment || ! validate_environment; then
        error "Environment setup failed"
        return 1
    fi
    
    # Check if the MCP package is installed
    if ! npm list -g "$MCP_PACKAGE" > /dev/null 2>&1; then
        error "$MCP_PACKAGE is not installed globally"
        error "Run: npm install -g $MCP_PACKAGE"
        return 1
    fi
    
    # Start the server in background
    info "Launching Filesystem MCP server process..."
    info "Serving directory: $PROJECT_ROOT"
    
    # Create the startup command with PROJECT_ROOT as argument
    local cmd="npx $MCP_PACKAGE '$PROJECT_ROOT'"
    
    # Start server with nohup to keep it running after script exits
    nohup bash -c "
        cd '$MCP_DIR' && 
        $cmd >> '$LOG_FILE' 2>&1
    " &
    
    local pid=$!
    echo "$pid" > "$PID_FILE"
    
    # Wait a moment and verify the process started
    sleep 2
    
    if is_server_running; then
        info "Filesystem MCP server started successfully (PID: $pid) ✓"
        info "Server logs: $LOG_FILE"
        info "Serving: $PROJECT_ROOT"
        return 0
    else
        error "Failed to start Filesystem MCP server"
        return 1
    fi
}

# Stop the Filesystem MCP server
stop_server() {
    info "Stopping Filesystem MCP server..."
    
    if ! is_server_running; then
        warn "Filesystem MCP server is not running"
        return 0
    fi
    
    local pid
    pid=$(cat "$PID_FILE")
    
    # Attempt graceful shutdown first
    info "Sending SIGTERM to process $pid..."
    if kill -TERM "$pid" 2>/dev/null; then
        # Wait up to 10 seconds for graceful shutdown
        local count=0
        while is_server_running && (( count < 10 )); do
            sleep 1
            ((count++))
        done
        
        if ! is_server_running; then
            info "Filesystem MCP server stopped gracefully ✓"
            rm -f "$PID_FILE"
            return 0
        fi
        
        # If still running, force kill
        warn "Graceful shutdown failed, forcing termination..."
        if kill -KILL "$pid" 2>/dev/null; then
            sleep 1
            info "Filesystem MCP server forcefully terminated ✓"
            rm -f "$PID_FILE"
            return 0
        else
            error "Failed to stop Filesystem MCP server"
            return 1
        fi
    else
        error "Failed to send signal to process $pid"
        # Clean up stale PID file
        rm -f "$PID_FILE"
        return 1
    fi
}

# Check server health
health_check() {
    info "Performing health check for Filesystem MCP server..."
    
    if ! is_server_running; then
        error "Filesystem MCP server is not running"
        return 1
    fi
    
    local pid
    pid=$(cat "$PID_FILE")
    info "Server process is running (PID: $pid) ✓"
    
    # Check if the process is responding (basic check)
    if ps -p "$pid" -o pid,ppid,etime,cmd | grep -q "$MCP_PACKAGE"; then
        info "Server process details verified ✓"
    else
        warn "Server process may not be the expected Filesystem MCP server"
    fi
    
    # Validate PROJECT_ROOT is still accessible
    if [[ -d "$PROJECT_ROOT" && -r "$PROJECT_ROOT" ]]; then
        info "PROJECT_ROOT is accessible: $PROJECT_ROOT ✓"
    else
        error "PROJECT_ROOT is no longer accessible: $PROJECT_ROOT"
    fi
    
    # Check recent log activity
    if [[ -f "$LOG_FILE" ]]; then
        local recent_logs
        recent_logs=$(tail -n 10 "$LOG_FILE" | grep -c "$(date '+%Y-%m-%d')" || true)
        
        if (( recent_logs > 0 )); then
            info "Recent log activity detected ✓"
        else
            warn "No recent log activity found"
        fi
        
        # Check for errors in recent logs
        local recent_errors
        recent_errors=$(tail -n 50 "$LOG_FILE" | grep -i error | wc -l || true)
        
        if (( recent_errors > 0 )); then
            warn "Found $recent_errors error(s) in recent logs"
            warn "Check $LOG_FILE for details"
        else
            info "No recent errors in logs ✓"
        fi
    fi
    
    info "Health check completed ✓"
    return 0
}

# Get server status
status() {
    info "Filesystem MCP Server Status"
    info "============================="
    
    if is_server_running; then
        local pid
        pid=$(cat "$PID_FILE")
        info "Status: RUNNING (PID: $pid)"
        
        # Get process info
        if command -v ps &> /dev/null; then
            local process_info
            process_info=$(ps -p "$pid" -o pid,ppid,etime,pmem,pcpu,cmd --no-headers 2>/dev/null || echo "Process info unavailable")
            info "Process: $process_info"
        fi
        
        # Get memory usage if available
        if [[ -f "/proc/$pid/status" ]]; then
            local mem_usage
            mem_usage=$(grep -E "VmRSS|VmSize" "/proc/$pid/status" 2>/dev/null || echo "Memory info unavailable")
            info "Memory: $mem_usage"
        fi
        
    else
        info "Status: STOPPED"
    fi
    
    # Log file info
    if [[ -f "$LOG_FILE" ]]; then
        local log_size
        log_size=$(du -h "$LOG_FILE" | cut -f1)
        local log_lines
        log_lines=$(wc -l < "$LOG_FILE")
        info "Log file: $LOG_FILE ($log_size, $log_lines lines)"
    else
        info "Log file: Not found"
    fi
    
    # Configuration check
    info ""
    info "Configuration:"
    info "  Package: $MCP_PACKAGE"
    info "  PROJECT_ROOT: ${PROJECT_ROOT:-NOT SET}"
    
    if [[ -n "${PROJECT_ROOT:-}" ]]; then
        local project_size
        project_size=$(du -sh "$PROJECT_ROOT" 2>/dev/null | cut -f1 || echo "Unknown")
        local file_count
        file_count=$(find "$PROJECT_ROOT" -type f 2>/dev/null | wc -l || echo "Unknown")
        info "  Directory size: $project_size"
        info "  File count: $file_count files"
    fi
    
    return 0
}

# View server logs
logs() {
    local lines=${1:-50}
    
    if [[ ! -f "$LOG_FILE" ]]; then
        warn "Log file not found: $LOG_FILE"
        return 1
    fi
    
    info "Showing last $lines lines from Filesystem MCP server logs:"
    info "========================================================"
    tail -n "$lines" "$LOG_FILE"
}

# Follow server logs
follow_logs() {
    if [[ ! -f "$LOG_FILE" ]]; then
        warn "Log file not found: $LOG_FILE"
        return 1
    fi
    
    info "Following Filesystem MCP server logs (Press Ctrl+C to stop):"
    info "==========================================================="
    tail -f "$LOG_FILE"
}

# Test filesystem operations
test_operations() {
    info "Testing Filesystem MCP server operations..."
    
    if ! is_server_running; then
        error "Server is not running. Start it first with: $0 start"
        return 1
    fi
    
    load_environment
    validate_environment
    
    local test_dir="$PROJECT_ROOT/mcp_test_$$"
    local test_file="$test_dir/test.txt"
    
    info "Creating test directory: $test_dir"
    if mkdir -p "$test_dir"; then
        info "Test directory created ✓"
        
        info "Creating test file: $test_file"
        if echo "MCP filesystem test $(date)" > "$test_file"; then
            info "Test file created ✓"
            
            info "Reading test file..."
            if cat "$test_file" > /dev/null; then
                info "Test file read successfully ✓"
            else
                error "Failed to read test file"
            fi
            
            info "Cleaning up test files..."
            rm -rf "$test_dir"
            info "Test cleanup completed ✓"
        else
            error "Failed to create test file"
            return 1
        fi
    else
        error "Failed to create test directory"
        return 1
    fi
    
    info "Filesystem operations test completed successfully ✓"
}

# Show usage information
usage() {
    echo "Usage: $0 {start|stop|restart|status|health|logs|follow|test|help}"
    echo ""
    echo "Commands:"
    echo "  start     Start the Filesystem MCP server"
    echo "  stop      Stop the Filesystem MCP server"
    echo "  restart   Restart the Filesystem MCP server"
    echo "  status    Show server status and information"
    echo "  health    Perform health check"
    echo "  logs [N]  Show last N lines of logs (default: 50)"
    echo "  follow    Follow logs in real-time"
    echo "  test      Test filesystem operations"
    echo "  help      Show this help message"
    echo ""
    echo "Environment:"
    echo "  PROJECT_ROOT: Directory to serve (default: parent of mcp dir)"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 logs 100"
    echo "  $0 test"
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
        start)
            start_server
            ;;
        stop)
            stop_server
            ;;
        restart)
            stop_server
            sleep 2
            start_server
            ;;
        status)
            status
            ;;
        health|healthcheck)
            health_check
            ;;
        logs)
            logs "${2:-50}"
            ;;
        follow|tail)
            follow_logs
            ;;
        test)
            test_operations
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            error "Unknown action: $action"
            usage
            exit 1
            ;;
    esac
}

# Handle cleanup on script exit
cleanup() {
    local exit_code=$?
    if (( exit_code != 0 )); then
        error "Script exited with code: $exit_code"
    fi
}

trap cleanup EXIT

# Run main function with all arguments
main "$@"