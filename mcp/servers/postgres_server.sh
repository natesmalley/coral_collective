#!/bin/bash
# PostgreSQL MCP Server wrapper script for CoralCollective
# Provides database operations, schema inspection, and query execution

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Script directory and paths
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly MCP_DIR="$(dirname "$SCRIPT_DIR")"
readonly LOG_FILE="$MCP_DIR/logs/postgres_server.log"
readonly PID_FILE="$MCP_DIR/logs/postgres_server.pid"

# Server configuration
readonly SERVER_NAME="postgres"
readonly MCP_PACKAGE="@modelcontextprotocol/server-postgres"
readonly REQUIRED_ENV_VARS=("DB_HOST" "DB_PORT" "DB_NAME" "DB_USER" "DB_PASSWORD")

# Ensure log directory exists
mkdir -p "$MCP_DIR/logs"

# Logging functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - [PostgreSQL] $1" | tee -a "$LOG_FILE"
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

# Validate environment and test database connection
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
        return 1
    fi
    
    # Construct DATABASE_URL
    export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
    
    # Test database connection
    info "Testing database connection..."
    if command -v psql &> /dev/null; then
        if timeout 10 psql "$DATABASE_URL" -c "SELECT 1;" > /dev/null 2>&1; then
            info "Database connection successful ✓"
        else
            error "Database connection failed"
            error "Please verify your database credentials and ensure PostgreSQL is running"
            return 1
        fi
    else
        warn "psql not found, skipping connection test"
        warn "Install postgresql-client to enable connection testing"
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

# Start the PostgreSQL MCP server
start_server() {
    info "Starting PostgreSQL MCP server..."
    
    if is_server_running; then
        warn "PostgreSQL MCP server is already running (PID: $(cat "$PID_FILE"))"
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
    
    info "Launching PostgreSQL MCP server process..."
    info "Connecting to: $DB_HOST:$DB_PORT/$DB_NAME"
    
    nohup bash -c "
        cd '$MCP_DIR' && 
        DATABASE_URL='$DATABASE_URL' npx '$MCP_PACKAGE' >> '$LOG_FILE' 2>&1
    " &
    
    local pid=$!
    echo "$pid" > "$PID_FILE"
    sleep 2
    
    if is_server_running; then
        info "PostgreSQL MCP server started successfully (PID: $pid) ✓"
        return 0
    else
        error "Failed to start PostgreSQL MCP server"
        return 1
    fi
}

# Stop the PostgreSQL MCP server
stop_server() {
    info "Stopping PostgreSQL MCP server..."
    
    if ! is_server_running; then
        warn "PostgreSQL MCP server is not running"
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
            info "PostgreSQL MCP server stopped gracefully ✓"
            rm -f "$PID_FILE"
        else
            warn "Graceful shutdown failed, forcing termination..."
            kill -KILL "$pid" 2>/dev/null
            rm -f "$PID_FILE"
            info "PostgreSQL MCP server forcefully terminated ✓"
        fi
    else
        error "Failed to send signal to process $pid"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Health check
health_check() {
    info "Performing health check for PostgreSQL MCP server..."
    
    if ! is_server_running; then
        error "PostgreSQL MCP server is not running"
        return 1
    fi
    
    local pid
    pid=$(cat "$PID_FILE")
    info "Server process is running (PID: $pid) ✓"
    
    # Test database connection
    load_environment
    if command -v psql &> /dev/null; then
        if timeout 5 psql "$DATABASE_URL" -c "SELECT current_timestamp;" > /dev/null 2>&1; then
            info "Database connectivity test passed ✓"
        else
            error "Database connectivity test failed"
        fi
    fi
    
    return 0
}

# Test database operations
test_operations() {
    info "Testing PostgreSQL MCP server operations..."
    
    if ! is_server_running; then
        error "Server is not running. Start it first with: $0 start"
        return 1
    fi
    
    load_environment
    
    if ! command -v psql &> /dev/null; then
        warn "psql not found, skipping database tests"
        return 0
    fi
    
    info "Running basic database queries..."
    
    # Test basic queries
    local queries=(
        "SELECT version();"
        "SELECT current_database();"
        "SELECT current_user;"
        "SELECT current_timestamp;"
    )
    
    for query in "${queries[@]}"; do
        info "Executing: $query"
        if timeout 10 psql "$DATABASE_URL" -c "$query" > /dev/null 2>&1; then
            info "Query executed successfully ✓"
        else
            error "Query failed: $query"
        fi
    done
    
    info "Database operations test completed"
}

# Get server status
status() {
    info "PostgreSQL MCP Server Status"
    info "============================"
    
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
    info "  Database: ${DB_HOST:-NOT SET}:${DB_PORT:-NOT SET}/${DB_NAME:-NOT SET}"
    info "  User: ${DB_USER:-NOT SET}"
}

# View logs
logs() {
    local lines=${1:-50}
    if [[ ! -f "$LOG_FILE" ]]; then
        warn "Log file not found: $LOG_FILE"
        return 1
    fi
    info "Showing last $lines lines from PostgreSQL MCP server logs:"
    tail -n "$lines" "$LOG_FILE"
}

# Follow logs
follow_logs() {
    if [[ ! -f "$LOG_FILE" ]]; then
        warn "Log file not found: $LOG_FILE"
        return 1
    fi
    info "Following PostgreSQL MCP server logs (Press Ctrl+C to stop):"
    tail -f "$LOG_FILE"
}

# Usage
usage() {
    echo "Usage: $0 {start|stop|restart|status|health|logs|follow|test|help}"
    echo ""
    echo "Commands:"
    echo "  start     Start the PostgreSQL MCP server"
    echo "  stop      Stop the PostgreSQL MCP server"
    echo "  restart   Restart the PostgreSQL MCP server"
    echo "  status    Show server status and information"
    echo "  health    Perform health check"
    echo "  logs [N]  Show last N lines of logs (default: 50)"
    echo "  follow    Follow logs in real-time"
    echo "  test      Test database operations"
    echo "  help      Show this help message"
    echo ""
    echo "Environment (required in $MCP_DIR/.env):"
    echo "  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD"
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
        help|--help|-h) usage ;;
        *) error "Unknown action: $action"; usage; exit 1 ;;
    esac
}

trap 'exit_code=$?; [[ $exit_code -ne 0 ]] && error "Script exited with code: $exit_code"' EXIT
main "$@"