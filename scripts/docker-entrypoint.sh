#!/bin/bash
set -e

# Docker entrypoint script for CoralCollective
# Handles initialization and graceful startup

# Default values
: ${CORAL_ENV:=production}
: ${CORAL_DEBUG:=false}
: ${CORAL_MEMORY_ENABLED:=true}
: ${LOG_LEVEL:=INFO}

echo "Starting CoralCollective in ${CORAL_ENV} mode..."

# Function to wait for service
wait_for_service() {
    local host=$1
    local port=$2
    local service=$3
    local timeout=${4:-30}
    
    echo "Waiting for ${service} at ${host}:${port}..."
    for i in $(seq 1 $timeout); do
        if nc -z $host $port; then
            echo "${service} is ready!"
            return 0
        fi
        echo "Waiting for ${service}... (${i}/${timeout})"
        sleep 2
    done
    echo "Error: ${service} is not ready after ${timeout} attempts"
    return 1
}

# Function to initialize database
init_database() {
    if [ -n "$POSTGRES_URL" ]; then
        echo "Checking database connection..."
        python -c "
import os
import psycopg2
from urllib.parse import urlparse

url = os.environ['POSTGRES_URL']
result = urlparse(url)
try:
    conn = psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )
    conn.close()
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
"
    fi
}

# Function to initialize memory system
init_memory_system() {
    if [ "$CORAL_MEMORY_ENABLED" = "true" ]; then
        echo "Initializing memory system..."
        if [ -n "$CHROMA_HOST" ]; then
            wait_for_service $CHROMA_HOST ${CHROMA_PORT:-8000} "ChromaDB" 30
        fi
        
        python -c "
try:
    from coral_collective.memory.memory_system import MemorySystem
    memory = MemorySystem()
    print('Memory system initialized successfully')
except Exception as e:
    print(f'Memory system initialization failed: {e}')
    # Don't exit - memory system is optional
"
    fi
}

# Function to run health checks
health_check() {
    echo "Running health checks..."
    python -c "
import coral_collective
print(f'CoralCollective version: {coral_collective.__version__}')
print('Basic import test passed')
"
}

# Main initialization
main() {
    # Create necessary directories
    mkdir -p /app/data /app/logs /app/tmp
    
    # Set permissions
    chown -R coral:coral /app/data /app/logs /app/tmp || true
    
    # Wait for dependent services
    if [ -n "$POSTGRES_HOST" ]; then
        wait_for_service $POSTGRES_HOST ${POSTGRES_PORT:-5432} "PostgreSQL" 30
        init_database
    fi
    
    if [ -n "$REDIS_HOST" ]; then
        wait_for_service $REDIS_HOST ${REDIS_PORT:-6379} "Redis" 30
    fi
    
    # Initialize memory system
    init_memory_system
    
    # Run health checks
    health_check
    
    echo "Initialization complete. Starting application..."
    
    # Execute the main command
    exec "$@"
}

# Handle signals for graceful shutdown
cleanup() {
    echo "Received shutdown signal, cleaning up..."
    # Add any cleanup logic here
    exit 0
}

trap cleanup SIGTERM SIGINT

# Run main initialization if this script is the entrypoint
if [ "${1#-}" != "$1" ] || [ "${1%.py}" != "$1" ] || [ "$1" = "coral" ]; then
    main "$@"
else
    exec "$@"
fi