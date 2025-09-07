#!/bin/bash
# Docker MCP Server wrapper script for CoralCollective
# Provides container management, compose operations, and image building

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Script directory and paths
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly MCP_DIR="$(dirname "$SCRIPT_DIR")"
readonly LOG_FILE="$MCP_DIR/logs/docker_server.log"
readonly PID_FILE="$MCP_DIR/logs/docker_server.pid"

# Server configuration
readonly SERVER_NAME="docker"
readonly MCP_PACKAGE="@modelcontextprotocol/server-docker"

# Ensure log directory exists
mkdir -p "$MCP_DIR/logs"

# Logging functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - [Docker] $1" | tee -a "$LOG_FILE"
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
        warn "Environment file not found: $env_file"
        warn "Using default Docker configuration"
    fi
    
    # Set default DOCKER_HOST if not provided
    if [[ -z "${DOCKER_HOST:-}" ]]; then
        export DOCKER_HOST="unix:///var/run/docker.sock"
        info "Using default DOCKER_HOST: $DOCKER_HOST"
    fi
}

# Validate Docker installation and connectivity
validate_environment() {
    info "Validating Docker environment..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        error "Please install Docker: https://docs.docker.com/get-docker/"
        return 1
    fi
    
    local docker_version
    docker_version=$(docker --version | cut -d' ' -f3 | sed 's/,//')
    info "Docker version: $docker_version ✓"
    
    # Check if Docker daemon is running
    if ! timeout 10 docker info > /dev/null 2>&1; then
        error "Docker daemon is not running or not accessible"
        error "Please start Docker daemon and ensure current user has permission"
        error "Try: sudo systemctl start docker"
        return 1
    fi
    
    info "Docker daemon is running ✓"
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null; then
        local compose_version
        compose_version=$(docker-compose --version | cut -d' ' -f3 | sed 's/,//')
        info "Docker Compose version: $compose_version ✓"
    elif docker compose version &> /dev/null; then
        local compose_version
        compose_version=$(docker compose version --short)
        info "Docker Compose (plugin) version: $compose_version ✓"
    else
        warn "Docker Compose not found - compose operations will not be available"
    fi
    
    # Check Docker socket permissions
    if [[ -S "/var/run/docker.sock" ]]; then
        if [[ -r "/var/run/docker.sock" && -w "/var/run/docker.sock" ]]; then
            info "Docker socket permissions OK ✓"
        else
            warn "Docker socket permissions may be insufficient"
            warn "Consider adding user to docker group: sudo usermod -aG docker \$USER"
        fi
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

# Start the Docker MCP server
start_server() {
    info "Starting Docker MCP server..."
    
    if is_server_running; then
        warn "Docker MCP server is already running (PID: $(cat "$PID_FILE"))"
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
    
    info "Launching Docker MCP server process..."
    info "Using Docker host: $DOCKER_HOST"
    
    nohup bash -c "
        cd '$MCP_DIR' && 
        DOCKER_HOST='$DOCKER_HOST' npx '$MCP_PACKAGE' >> '$LOG_FILE' 2>&1
    " &
    
    local pid=$!
    echo "$pid" > "$PID_FILE"
    sleep 2
    
    if is_server_running; then
        info "Docker MCP server started successfully (PID: $pid) ✓"
        return 0
    else
        error "Failed to start Docker MCP server"
        return 1
    fi
}

# Stop the Docker MCP server
stop_server() {
    info "Stopping Docker MCP server..."
    
    if ! is_server_running; then
        warn "Docker MCP server is not running"
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
            info "Docker MCP server stopped gracefully ✓"
            rm -f "$PID_FILE"
        else
            warn "Graceful shutdown failed, forcing termination..."
            kill -KILL "$pid" 2>/dev/null
            rm -f "$PID_FILE"
            info "Docker MCP server forcefully terminated ✓"
        fi
    else
        error "Failed to send signal to process $pid"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Health check
health_check() {
    info "Performing health check for Docker MCP server..."
    
    if ! is_server_running; then
        error "Docker MCP server is not running"
        return 1
    fi
    
    local pid
    pid=$(cat "$PID_FILE")
    info "Server process is running (PID: $pid) ✓"
    
    # Test Docker connectivity
    load_environment
    if timeout 10 docker info > /dev/null 2>&1; then
        info "Docker daemon connectivity test passed ✓"
    else
        error "Docker daemon connectivity test failed"
    fi
    
    return 0
}

# Test Docker operations
test_operations() {
    info "Testing Docker MCP server operations..."
    
    if ! is_server_running; then
        error "Server is not running. Start it first with: $0 start"
        return 1
    fi
    
    load_environment
    
    info "Running basic Docker operations..."
    
    # Test Docker info
    if timeout 10 docker info > /dev/null 2>&1; then
        info "Docker info command successful ✓"
    else
        error "Docker info command failed"
        return 1
    fi
    
    # Test image listing
    if timeout 10 docker images > /dev/null 2>&1; then
        info "Docker images listing successful ✓"
    else
        error "Docker images listing failed"
    fi
    
    # Test container listing
    if timeout 10 docker ps -a > /dev/null 2>&1; then
        info "Docker container listing successful ✓"
    else
        error "Docker container listing failed"
    fi
    
    # Test running a simple container (hello-world)
    info "Testing container execution with hello-world..."
    if timeout 30 docker run --rm hello-world > /dev/null 2>&1; then
        info "Container execution test successful ✓"
    else
        warn "Container execution test failed (may need internet connectivity)"
    fi
    
    info "Docker operations test completed"
}

# Get Docker system information
docker_info() {
    info "Docker System Information"
    info "========================"
    
    if ! command -v docker &> /dev/null; then
        error "Docker not installed"
        return 1
    fi
    
    # Docker version
    local docker_version
    docker_version=$(docker --version 2>/dev/null || echo "Unknown")
    info "Docker Version: $docker_version"
    
    # Docker info
    if timeout 10 docker info > /dev/null 2>&1; then
        local containers_running containers_total images
        containers_running=$(docker info --format '{{.ContainersRunning}}' 2>/dev/null || echo "Unknown")
        containers_total=$(docker info --format '{{.Containers}}' 2>/dev/null || echo "Unknown")
        images=$(docker info --format '{{.Images}}' 2>/dev/null || echo "Unknown")
        
        info "Containers: $containers_running running, $containers_total total"
        info "Images: $images"
        
        local storage_driver
        storage_driver=$(docker info --format '{{.Driver}}' 2>/dev/null || echo "Unknown")
        info "Storage Driver: $storage_driver"
    else
        warn "Cannot connect to Docker daemon"
    fi
}

# Get server status
status() {
    info "Docker MCP Server Status"
    info "======================="
    
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
    info "  Docker Host: ${DOCKER_HOST:-NOT SET}"
    
    # Show Docker system info
    echo ""
    docker_info
}

# View logs
logs() {
    local lines=${1:-50}
    if [[ ! -f "$LOG_FILE" ]]; then
        warn "Log file not found: $LOG_FILE"
        return 1
    fi
    info "Showing last $lines lines from Docker MCP server logs:"
    tail -n "$lines" "$LOG_FILE"
}

# Follow logs
follow_logs() {
    if [[ ! -f "$LOG_FILE" ]]; then
        warn "Log file not found: $LOG_FILE"
        return 1
    fi
    info "Following Docker MCP server logs (Press Ctrl+C to stop):"
    tail -f "$LOG_FILE"
}

# Usage
usage() {
    echo "Usage: $0 {start|stop|restart|status|health|logs|follow|test|info|help}"
    echo ""
    echo "Commands:"
    echo "  start     Start the Docker MCP server"
    echo "  stop      Stop the Docker MCP server"
    echo "  restart   Restart the Docker MCP server"
    echo "  status    Show server status and information"
    echo "  health    Perform health check"
    echo "  logs [N]  Show last N lines of logs (default: 50)"
    echo "  follow    Follow logs in real-time"
    echo "  test      Test Docker operations"
    echo "  info      Show Docker system information"
    echo "  help      Show this help message"
    echo ""
    echo "Environment (optional in $MCP_DIR/.env):"
    echo "  DOCKER_HOST (default: unix:///var/run/docker.sock)"
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
        info) docker_info ;;
        help|--help|-h) usage ;;
        *) error "Unknown action: $action"; usage; exit 1 ;;
    esac
}

trap 'exit_code=$?; [[ $exit_code -ne 0 ]] && error "Script exited with code: $exit_code"' EXIT
main "$@"