#!/bin/bash
set -e

# Simplified deployment script for CoralCollective
# Supports Docker and local deployment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
DEFAULT_ENVIRONMENT="production"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Usage function
usage() {
    cat << EOF
Usage: $0 [COMMAND] [OPTIONS]

Commands:
  docker          Deploy using Docker Compose
  local           Run locally with Python
  build           Build Docker image only
  
Options:
  -e, --env       Environment (development|staging|production)
  -t, --tag       Docker image tag (default: latest)
  -h, --help      Show this help message

Examples:
  $0 docker
  $0 local -e development
  $0 build -t v1.0.0

EOF
    exit 0
}

# Check dependencies
check_dependencies() {
    local target=$1
    
    case $target in
        docker)
            if ! command -v docker &> /dev/null; then
                log_error "Docker is not installed"
                exit 1
            fi
            if ! command -v docker-compose &> /dev/null; then
                log_warning "docker-compose not found, using docker compose"
                DOCKER_COMPOSE="docker compose"
            else
                DOCKER_COMPOSE="docker-compose"
            fi
            ;;
        local)
            if ! command -v python3 &> /dev/null; then
                log_error "Python 3 is not installed"
                exit 1
            fi
            ;;
    esac
}

# Load environment variables
load_env() {
    local env_file=".env"
    
    if [[ "$ENVIRONMENT" == "development" ]]; then
        env_file=".env.development"
    elif [[ "$ENVIRONMENT" == "staging" ]]; then
        env_file=".env.staging"
    fi
    
    if [[ -f "$PROJECT_ROOT/$env_file" ]]; then
        log_info "Loading environment from $env_file"
        export $(grep -v '^#' "$PROJECT_ROOT/$env_file" | xargs)
    else
        log_warning "Environment file $env_file not found"
    fi
}

# Deploy with Docker
deploy_docker() {
    log_info "Deploying with Docker..."
    
    cd "$PROJECT_ROOT"
    
    # Load environment
    load_env
    
    # Build image
    log_info "Building Docker image..."
    docker build -t coral-collective:$TAG .
    
    # Run with docker-compose
    log_info "Starting containers..."
    $DOCKER_COMPOSE up -d
    
    # Wait for health check
    log_info "Waiting for services to be healthy..."
    sleep 5
    
    if docker ps | grep -q coral-collective; then
        log_success "CoralCollective deployed successfully!"
        log_info "Access the application at http://localhost:8000"
    else
        log_error "Deployment failed. Check logs with: docker logs coral-collective"
        exit 1
    fi
}

# Deploy locally
deploy_local() {
    log_info "Running locally..."
    
    cd "$PROJECT_ROOT"
    
    # Load environment
    load_env
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]]; then
        log_info "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    log_info "Activating virtual environment..."
    source venv/bin/activate
    
    # Install dependencies
    log_info "Installing dependencies..."
    pip install -r requirements.txt
    
    # Run the application
    log_info "Starting CoralCollective..."
    python agent_runner.py
}

# Build Docker image
build_docker() {
    log_info "Building Docker image..."
    
    cd "$PROJECT_ROOT"
    
    docker build -t coral-collective:$TAG .
    
    log_success "Docker image built: coral-collective:$TAG"
}

# Main script
main() {
    # Parse command line arguments
    COMMAND=""
    ENVIRONMENT="$DEFAULT_ENVIRONMENT"
    TAG="latest"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            docker|local|build)
                COMMAND=$1
                shift
                ;;
            -e|--env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -t|--tag)
                TAG="$2"
                shift 2
                ;;
            -h|--help)
                usage
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                ;;
        esac
    done
    
    # Check if command is provided
    if [[ -z "$COMMAND" ]]; then
        log_error "No command specified"
        usage
    fi
    
    # Check dependencies
    check_dependencies $COMMAND
    
    # Execute command
    case $COMMAND in
        docker)
            deploy_docker
            ;;
        local)
            deploy_local
            ;;
        build)
            build_docker
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            usage
            ;;
    esac
}

# Run main function
main "$@"