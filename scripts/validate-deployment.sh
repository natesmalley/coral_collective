#!/bin/bash
set -e

# Deployment validation script for CoralCollective
# Validates that deployment is working correctly across different environments

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
TIMEOUT=30
VERBOSE=false
ENVIRONMENT="production"
TARGET="docker"

# Test results
PASSED=0
FAILED=0
TESTS=()

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED++))
    TESTS+=("✓ $1")
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED++))
    TESTS+=("✗ $1")
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Show usage
show_usage() {
    cat << EOF
CoralCollective Deployment Validation Script

Usage: $0 [OPTIONS]

Options:
  -t, --target TARGET      Deployment target (docker, k8s, local)
  -e, --environment ENV    Environment (development, production, memory)
  -n, --namespace NS       Kubernetes namespace (default: coral-collective)
  -T, --timeout SECONDS   Timeout for tests (default: 30)
  -v, --verbose            Verbose output
  -h, --help               Show this help message

Examples:
  $0 -t docker -e production
  $0 -t k8s -n coral-dev -T 60
  $0 -t local -v
EOF
}

# Wait for service to be ready
wait_for_service() {
    local host=$1
    local port=$2
    local service=$3
    local timeout=${4:-$TIMEOUT}
    
    log_info "Waiting for ${service} at ${host}:${port}..."
    for i in $(seq 1 $timeout); do
        if nc -z $host $port 2>/dev/null; then
            log_success "${service} is responding"
            return 0
        fi
        if [ $VERBOSE = true ]; then
            echo -n "."
        fi
        sleep 1
    done
    log_error "${service} is not responding after ${timeout} seconds"
    return 1
}

# Test HTTP endpoint
test_http_endpoint() {
    local url=$1
    local description=$2
    local expected_status=${3:-200}
    
    log_info "Testing ${description}: ${url}"
    
    if command -v curl &> /dev/null; then
        local response=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$url")
        if [ "$response" -eq "$expected_status" ]; then
            log_success "${description} returned HTTP ${response}"
            return 0
        else
            log_error "${description} returned HTTP ${response}, expected ${expected_status}"
            return 1
        fi
    else
        log_warn "curl not available, skipping HTTP test for ${description}"
        return 0
    fi
}

# Test database connection
test_database() {
    local postgres_url=$1
    
    log_info "Testing database connection"
    
    if command -v psql &> /dev/null; then
        if psql "$postgres_url" -c "SELECT 1;" &>/dev/null; then
            log_success "Database connection successful"
            return 0
        else
            log_error "Database connection failed"
            return 1
        fi
    else
        log_warn "psql not available, skipping database test"
        return 0
    fi
}

# Test memory system
test_memory_system() {
    local chroma_url=$1
    
    log_info "Testing memory system (ChromaDB)"
    
    test_http_endpoint "${chroma_url}/api/v1/heartbeat" "ChromaDB heartbeat"
    
    # Test Python memory system integration
    if python3 -c "
try:
    from coral_collective.memory.memory_system import MemorySystem
    memory = MemorySystem()
    print('Memory system initialized successfully')
except ImportError:
    print('Memory system not available (optional)')
except Exception as e:
    print(f'Memory system error: {e}')
    exit(1)
" 2>/dev/null; then
        log_success "Memory system integration working"
        return 0
    else
        log_error "Memory system integration failed"
        return 1
    fi
}

# Test CoralCollective functionality
test_coral_collective() {
    local base_url=$1
    
    log_info "Testing CoralCollective core functionality"
    
    # Test basic import
    if python3 -c "import coral_collective; print(f'CoralCollective version: {coral_collective.__version__}')" 2>/dev/null; then
        log_success "CoralCollective import successful"
    else
        log_error "CoralCollective import failed"
        return 1
    fi
    
    # Test CLI
    if python3 -m coral_collective.cli.main --help &>/dev/null; then
        log_success "CoralCollective CLI working"
    else
        log_error "CoralCollective CLI failed"
        return 1
    fi
    
    # Test agent loading
    if python3 -c "
from coral_collective.agent_runner import AgentRunner
runner = AgentRunner()
agents = runner.list_agents()
print(f'Loaded {len(agents)} agents')
if len(agents) > 0:
    print('Agents loaded successfully')
else:
    exit(1)
" 2>/dev/null; then
        log_success "Agent system working"
    else
        log_error "Agent system failed"
        return 1
    fi
}

# Test Docker deployment
test_docker_deployment() {
    log_info "Validating Docker deployment"
    
    # Check if containers are running
    if docker-compose ps | grep -q "coral-collective.*Up"; then
        log_success "CoralCollective container is running"
    else
        log_error "CoralCollective container is not running"
        return 1
    fi
    
    # Test service endpoints
    wait_for_service localhost 8000 "CoralCollective API" 30
    wait_for_service localhost 5432 "PostgreSQL" 15
    wait_for_service localhost 8001 "ChromaDB" 15
    
    # Test HTTP endpoints
    test_http_endpoint "http://localhost:8000/health" "Health check"
    test_coral_collective "http://localhost:8000"
    
    # Test database
    test_database "postgresql://coral:coral@localhost:5432/coral_db"
    
    # Test memory system
    test_memory_system "http://localhost:8001"
}

# Test Kubernetes deployment
test_k8s_deployment() {
    local namespace=${1:-coral-collective}
    
    log_info "Validating Kubernetes deployment in namespace: $namespace"
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not available"
        return 1
    fi
    
    # Check namespace exists
    if kubectl get namespace $namespace &>/dev/null; then
        log_success "Namespace $namespace exists"
    else
        log_error "Namespace $namespace does not exist"
        return 1
    fi
    
    # Check pod status
    local pods=$(kubectl get pods -n $namespace -l app.kubernetes.io/name=coral-collective --no-headers)
    if echo "$pods" | grep -q "Running"; then
        log_success "CoralCollective pods are running"
    else
        log_error "CoralCollective pods are not running"
        if [ $VERBOSE = true ]; then
            echo "Pod status:"
            kubectl get pods -n $namespace -l app.kubernetes.io/name=coral-collective
        fi
        return 1
    fi
    
    # Check services
    if kubectl get service coral-collective-service -n $namespace &>/dev/null; then
        log_success "CoralCollective service exists"
    else
        log_error "CoralCollective service not found"
        return 1
    fi
    
    # Test service connectivity (if port-forward is possible)
    log_info "Testing service connectivity"
    kubectl port-forward -n $namespace service/coral-collective-service 8080:80 &
    local pf_pid=$!
    sleep 5
    
    if test_http_endpoint "http://localhost:8080/health" "Kubernetes service health check"; then
        log_success "Kubernetes service is accessible"
    else
        log_error "Kubernetes service is not accessible"
    fi
    
    kill $pf_pid 2>/dev/null || true
    
    # Check persistent volumes
    local pvcs=$(kubectl get pvc -n $namespace --no-headers)
    if echo "$pvcs" | grep -q "Bound"; then
        log_success "Persistent volumes are bound"
    else
        log_error "Persistent volumes are not bound"
        if [ $VERBOSE = true ]; then
            echo "PVC status:"
            kubectl get pvc -n $namespace
        fi
    fi
}

# Test local deployment
test_local_deployment() {
    log_info "Validating local deployment"
    
    # Check virtual environment
    if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
        log_success "Virtual environment exists"
    else
        log_warn "Virtual environment not found"
    fi
    
    # Test Python imports
    test_coral_collective ""
    
    # Check if services are available
    if nc -z localhost 5432 2>/dev/null; then
        test_database "postgresql://coral:coral@localhost:5432/coral_db"
    else
        log_warn "PostgreSQL not running locally (optional for development)"
    fi
    
    if nc -z localhost 8001 2>/dev/null; then
        test_memory_system "http://localhost:8001"
    else
        log_warn "ChromaDB not running locally (optional for development)"
    fi
}

# Generate report
generate_report() {
    echo ""
    echo "=========================================="
    echo "           VALIDATION REPORT"
    echo "=========================================="
    echo "Target: $TARGET"
    echo "Environment: $ENVIRONMENT"
    echo "Timestamp: $(date)"
    echo ""
    echo "Results:"
    for test in "${TESTS[@]}"; do
        echo "  $test"
    done
    echo ""
    echo "Summary: $PASSED passed, $FAILED failed"
    echo "=========================================="
    
    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}All tests passed! 🎉${NC}"
        return 0
    else
        echo -e "${RED}Some tests failed! ❌${NC}"
        return 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--target)
            TARGET="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -T|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
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

# Main execution
main() {
    log_info "CoralCollective Deployment Validation"
    log_info "Target: $TARGET, Environment: $ENVIRONMENT"
    echo ""
    
    cd "$PROJECT_ROOT"
    
    case $TARGET in
        docker)
            test_docker_deployment
            ;;
        k8s)
            test_k8s_deployment ${NAMESPACE:-coral-collective}
            ;;
        local)
            test_local_deployment
            ;;
        *)
            log_error "Unknown target: $TARGET"
            echo "Supported targets: docker, k8s, local"
            exit 1
            ;;
    esac
    
    generate_report
}

# Run main function
main