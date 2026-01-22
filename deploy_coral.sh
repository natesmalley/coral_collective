#!/bin/bash
# deploy_coral.sh - Package and deploy CoralCollective

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_NAME="coral_collective"
VERSION="1.0.0"

echo "🪸 CoralCollective Deployment Tool"
echo "=================================="
echo ""

# Function to show usage
usage() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  package    Create distributable package"
    echo "  docker     Build Docker image"
    echo "  deploy     Deploy to target directory"
    echo "  pip        Build pip package"
    echo ""
    echo "Options:"
    echo "  --output DIR    Output directory (default: ./dist)"
    echo "  --tag TAG       Docker tag (default: coral-collective:latest)"
    echo ""
    exit 1
}

# Package command - create tarball
package_coral() {
    OUTPUT_DIR="${OUTPUT_DIR:-./dist}"
    mkdir -p "$OUTPUT_DIR"
    
    echo "Creating package..."
    
    PACKAGE_FILE="$OUTPUT_DIR/${PACKAGE_NAME}_${VERSION}.tar.gz"
    
    tar czf "$PACKAGE_FILE" \
        --exclude='.git' \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='.env' \
        --exclude='venv' \
        --exclude='.coral' \
        --exclude='dist' \
        --exclude='build' \
        --exclude='*.egg-info' \
        agents/ \
        config/ \
        coral_collective/ \
        docs/ \
        mcp/ \
        tools/ \
        *.py \
        *.sh \
        *.md \
        requirements.txt \
        setup.py \
        Dockerfile \
        docker-compose.yml \
        .env.example
    
    echo "✓ Package created: $PACKAGE_FILE"
    echo "  Size: $(du -h "$PACKAGE_FILE" | cut -f1)"
    echo ""
    echo "To install:"
    echo "  tar xzf $PACKAGE_FILE"
    echo "  pip install -r requirements.txt"
    echo "  python agent_runner.py"
}

# Docker command - build image
docker_build() {
    TAG="${DOCKER_TAG:-coral-collective:latest}"
    
    echo "Building Docker image: $TAG"
    
    docker build -t "$TAG" .
    
    echo "✓ Docker image built: $TAG"
    echo ""
    echo "To run:"
    echo "  docker run -it --rm $TAG"
    echo "  docker-compose up"
}

# Deploy command - copy to directory
deploy_to() {
    if [ -z "$DEPLOY_PATH" ]; then
        echo "Error: Deploy path required"
        echo "Usage: $0 deploy /path/to/project"
        exit 1
    fi
    
    echo "Deploying to: $DEPLOY_PATH"
    
    # Create target directory if needed
    mkdir -p "$DEPLOY_PATH"
    
    # Copy essential files
    cp -r agents "$DEPLOY_PATH/"
    cp -r config "$DEPLOY_PATH/"
    cp -r coral_collective "$DEPLOY_PATH/"
    cp -r docs "$DEPLOY_PATH/"
    cp -r mcp "$DEPLOY_PATH/"
    cp -r tools "$DEPLOY_PATH/"
    
    cp agent_runner.py "$DEPLOY_PATH/"
    cp project_manager.py "$DEPLOY_PATH/"
    cp agent_prompt_service.py "$DEPLOY_PATH/"
    cp requirements.txt "$DEPLOY_PATH/"
    cp setup.py "$DEPLOY_PATH/"
    cp .env.example "$DEPLOY_PATH/"
    
    # Copy deployment scripts
    cp coral_drop.sh "$DEPLOY_PATH/"
    cp deploy_coral.sh "$DEPLOY_PATH/"
    [ -f start.sh ] && cp start.sh "$DEPLOY_PATH/"
    
    # Copy Docker files if they exist
    [ -f Dockerfile ] && cp Dockerfile "$DEPLOY_PATH/"
    [ -f docker-compose.yml ] && cp docker-compose.yml "$DEPLOY_PATH/"
    
    echo "✓ Deployed to $DEPLOY_PATH"
    echo ""
    echo "Next steps:"
    echo "  cd $DEPLOY_PATH"
    echo "  ./coral_drop.sh  # Initialize in project"
}

# Build pip package
build_pip() {
    echo "Building pip package..."
    
    # Clean previous builds
    rm -rf build dist *.egg-info
    
    # Build package
    python3 setup.py sdist bdist_wheel
    
    echo "✓ Pip package built in ./dist/"
    echo ""
    echo "To install locally:"
    echo "  pip install dist/${PACKAGE_NAME}-${VERSION}.tar.gz"
    echo ""
    echo "To upload to PyPI:"
    echo "  pip install twine"
    echo "  twine upload dist/*"
}

# Main command handling
case "${1:-help}" in
    package)
        shift
        while [[ $# -gt 0 ]]; do
            case $1 in
                --output) OUTPUT_DIR="$2"; shift 2 ;;
                *) shift ;;
            esac
        done
        package_coral
        ;;
        
    docker)
        shift
        while [[ $# -gt 0 ]]; do
            case $1 in
                --tag) DOCKER_TAG="$2"; shift 2 ;;
                *) shift ;;
            esac
        done
        docker_build
        ;;
        
    deploy)
        DEPLOY_PATH="$2"
        deploy_to
        ;;
        
    pip)
        build_pip
        ;;
        
    help|--help|-h)
        usage
        ;;
        
    *)
        echo "Unknown command: $1"
        usage
        ;;
esac