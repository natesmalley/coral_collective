#!/bin/bash
set -e

# Deployment script for CoralCollective
# Supports multiple deployment targets: Docker, Kubernetes, local

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
DEFAULT_NAMESPACE="coral-collective"
DEFAULT_ENVIRONMENT="production"
DEFAULT_REPLICAS="2"

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

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Show usage
show_usage() {
    cat << EOF
CoralCollective Deployment Script

Usage: $0 [COMMAND] [OPTIONS]

Commands:
  docker          Deploy using Docker Compose
  k8s             Deploy to Kubernetes
  local           Deploy locally with virtual environment
  build           Build Docker images
  test            Run deployment tests
  clean           Clean up deployment artifacts

Options:
  -e, --environment ENV    Deployment environment (dev, staging, production)
  -n, --namespace NS       Kubernetes namespace (default: coral-collective)
  -r, --replicas NUM       Number of replicas (default: 2)
  -i, --image TAG          Docker image tag (default: latest)
  -f, --config-file FILE   Override config file
  -h, --help               Show this help message

Examples:
  $0 docker -e production
  $0 k8s -n my-namespace -r 3
  $0 build -i v1.0.0
  $0 local -e development
EOF
}

# Check prerequisites
check_prerequisites() {
    local target=$1
    
    case $target in
        docker)
            if ! command -v docker &> /dev/null; then
                log_error "Docker is not installed"
                exit 1
            fi
            if ! command -v docker-compose &> /dev/null; then
                log_error "Docker Compose is not installed"
                exit 1
            fi
            ;;
        k8s)
            if ! command -v kubectl &> /dev/null; then
                log_error "kubectl is not installed"
                exit 1
            fi
            if ! kubectl cluster-info &> /dev/null; then
                log_error "Cannot connect to Kubernetes cluster"
                exit 1
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

# Build Docker images
build_images() {
    local tag=${1:-latest}
    
    log_info "Building Docker images with tag: $tag"
    
    cd "$PROJECT_ROOT"
    
    # Build main image
    docker build -t coralcollective/coral-collective:$tag .
    
    # Build development image
    docker build --target development -t coralcollective/coral-collective:$tag-dev .
    
    # Build memory-enabled image
    docker build --target memory -t coralcollective/coral-collective:$tag-memory .
    
    log_success "Docker images built successfully"
}

# Deploy with Docker Compose
deploy_docker() {
    local environment=${1:-production}
    
    log_info "Deploying with Docker Compose (environment: $environment)"
    
    cd "$PROJECT_ROOT"
    
    # Create environment file if it doesn't exist
    if [ ! -f .env ]; then
        log_warn ".env file not found, creating from template"
        cat > .env << EOF
# CoralCollective Environment Configuration
CORAL_ENV=$environment
CORAL_DEBUG=false
POSTGRES_USER=coral
POSTGRES_PASSWORD=coral
POSTGRES_DB=coral_db
# Add your API keys here
GITHUB_TOKEN=
CLAUDE_API_KEY=
OPENAI_API_KEY=
EOF
    fi
    
    # Choose compose file based on environment
    local compose_file="docker-compose.yml"
    local profiles=""
    
    case $environment in
        development)
            profiles="--profile development"
            ;;
        production)
            profiles="--profile production"
            ;;
        memory)
            profiles="--profile memory"
            ;;
    esac
    
    # Deploy
    docker-compose -f $compose_file $profiles up -d
    
    log_success "Docker deployment completed"
    log_info "Services available at:"
    log_info "  - CoralCollective: http://localhost:8000"
    log_info "  - PostgreSQL: localhost:5432"
    log_info "  - ChromaDB: http://localhost:8001"
}

# Deploy to Kubernetes
deploy_k8s() {
    local namespace=${1:-$DEFAULT_NAMESPACE}
    local replicas=${2:-$DEFAULT_REPLICAS}
    local image_tag=${3:-latest}
    
    log_info "Deploying to Kubernetes (namespace: $namespace, replicas: $replicas)"
    
    cd "$PROJECT_ROOT"
    
    # Create namespace if it doesn't exist
    kubectl create namespace $namespace --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply Kubernetes manifests
    log_info "Applying Kubernetes manifests..."
    
    # Replace placeholders in manifests
    local temp_dir=$(mktemp -d)
    trap "rm -rf $temp_dir" EXIT
    
    # Copy and modify manifests
    cp -r k8s/* $temp_dir/
    
    # Replace image tags
    find $temp_dir -name "*.yaml" -exec sed -i.bak "s/:latest/:$image_tag/g" {} \;
    
    # Replace namespace
    find $temp_dir -name "*.yaml" -exec sed -i.bak "s/namespace: coral-collective/namespace: $namespace/g" {} \;
    
    # Replace replicas
    sed -i.bak "s/replicas: 2/replicas: $replicas/g" $temp_dir/deployment.yaml
    
    # Apply manifests in order
    kubectl apply -f $temp_dir/namespace.yaml
    kubectl apply -f $temp_dir/pvc.yaml
    kubectl apply -f $temp_dir/configmap.yaml
    kubectl apply -f $temp_dir/secrets.yaml
    kubectl apply -f $temp_dir/deployment.yaml
    kubectl apply -f $temp_dir/service.yaml
    kubectl apply -f $temp_dir/hpa.yaml
    
    # Apply ingress if available
    if [ -f $temp_dir/ingress.yaml ]; then
        kubectl apply -f $temp_dir/ingress.yaml
    fi
    
    # Wait for deployment to be ready
    log_info "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/coral-collective -n $namespace
    
    log_success "Kubernetes deployment completed"
    
    # Show status
    kubectl get pods -n $namespace
    kubectl get services -n $namespace
}

# Deploy locally
deploy_local() {
    local environment=${1:-development}
    
    log_info "Deploying locally (environment: $environment)"
    
    cd "$PROJECT_ROOT"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    log_info "Installing dependencies..."
    pip install --upgrade pip setuptools wheel
    pip install -e .[all]
    
    # Set environment variables
    export CORAL_ENV=$environment
    export CORAL_DEBUG=true
    
    log_success "Local deployment completed"
    log_info "Virtual environment activated. Run 'coral --help' to get started."
}

# Run deployment tests
run_tests() {
    log_info "Running deployment tests..."
    
    cd "$PROJECT_ROOT"
    
    # Test Docker images
    if command -v docker &> /dev/null; then
        log_info "Testing Docker images..."
        docker run --rm coralcollective/coral-collective:latest coral --help
    fi
    
    # Test Kubernetes deployment
    if command -v kubectl &> /dev/null && kubectl cluster-info &> /dev/null; then
        log_info "Testing Kubernetes deployment..."
        kubectl run coral-test --image=coralcollective/coral-collective:latest --rm -it --restart=Never -- coral --help
    fi
    
    log_success "Deployment tests completed"
}

# Clean up deployment artifacts
clean_up() {
    log_info "Cleaning up deployment artifacts..."
    
    cd "$PROJECT_ROOT"
    
    # Clean Docker
    if command -v docker &> /dev/null; then
        docker system prune -f
        docker volume prune -f
    fi
    
    # Clean local artifacts
    rm -rf build/ dist/ *.egg-info/
    find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete
    
    log_success "Cleanup completed"
}

# Parse command line arguments
parse_args() {
    local command=""
    local environment="$DEFAULT_ENVIRONMENT"
    local namespace="$DEFAULT_NAMESPACE"
    local replicas="$DEFAULT_REPLICAS"
    local image_tag="latest"
    local config_file=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            docker|k8s|local|build|test|clean)
                command="$1"
                shift
                ;;
            -e|--environment)
                environment="$2"
                shift 2
                ;;
            -n|--namespace)
                namespace="$2"
                shift 2
                ;;
            -r|--replicas)
                replicas="$2"
                shift 2
                ;;
            -i|--image)
                image_tag="$2"
                shift 2
                ;;
            -f|--config-file)
                config_file="$2"
                shift 2
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Execute command
    case $command in
        docker)
            check_prerequisites docker
            deploy_docker $environment
            ;;
        k8s)
            check_prerequisites k8s
            deploy_k8s $namespace $replicas $image_tag
            ;;
        local)
            check_prerequisites local
            deploy_local $environment
            ;;
        build)
            check_prerequisites docker
            build_images $image_tag
            ;;
        test)
            run_tests
            ;;
        clean)
            clean_up
            ;;
        "")
            log_error "No command specified"
            show_usage
            exit 1
            ;;
        *)
            log_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Main function
main() {
    log_info "CoralCollective Deployment Script"
    parse_args "$@"
}

# Run main function
main "$@"