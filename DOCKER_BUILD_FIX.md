# Docker Build Fix for Dependency Resolution Issues

## Problem
The Docker build was failing with a "resolution-too-deep" error when trying to install all dependencies including the memory system components (chromadb, torch, transformers, etc.). This occurred because pip couldn't efficiently resolve the complex dependency graph of these ML libraries.

## Solution Applied

### 1. Updated pyproject.toml
- Added upper version bounds to memory dependencies to constrain the dependency search space
- This prevents pip from searching through too many version combinations

### 2. Modified Dockerfile
- Changed from `pip install -e .[all]` to `pip install -e .[mcp,dev,docs]`
- This excludes the heavy memory dependencies from the default build
- Memory dependencies can be installed separately when needed

### 3. Updated requirements.txt
- Commented out memory dependencies in the main requirements.txt
- Created a separate `requirements-memory.txt` with pinned versions

## How to Use

### Option 1: Basic Install (Recommended - Fast Build)
For core functionality without memory/ML features:
```bash
# Build and run the standard container
docker-compose up coral-collective
```
This installs: MCP tools, development tools, documentation tools
Build time: ~30 seconds

### Option 2: Full Install with Memory Dependencies
For applications requiring vector storage and ML features:

**Method A: Use the memory profile (Recommended for full install)**
```bash
# Build and run the memory-enabled container
docker-compose --profile memory up coral-memory
```
This includes: All core functionality + chromadb, torch, transformers, sentence-transformers, etc.
Build time: ~5-10 minutes

**Method B: Add to existing container**
```bash
# First, start the basic container
docker-compose up -d coral-collective

# Then install memory dependencies
docker exec -it coral-collective-dev pip install -r requirements-memory.txt
```

### Option 3: Local Development (No Docker)
```bash
# Install core dependencies
pip install -e .[mcp,dev,docs]

# Optionally add memory dependencies
pip install -r requirements-memory.txt
```

## Alternative Solutions

If you still encounter issues:

1. **Use Python 3.11 instead of 3.12**:
   Edit Dockerfile line 2:
   ```dockerfile
   FROM python:3.11-slim as base
   ```

2. **Install dependencies sequentially**:
   ```bash
   pip install chromadb==0.4.24
   pip install numpy==1.26.4
   pip install torch==2.4.1 --index-url https://download.pytorch.org/whl/cpu
   pip install sentence-transformers==2.7.0
   ```

3. **Use pre-built wheels**:
   For ARM64 (Apple Silicon), some packages may need platform-specific wheels:
   ```bash
   pip install --only-binary :all: chromadb numpy scipy
   ```

## Testing the Fix

1. Clean Docker build:
```bash
docker-compose down -v
docker-compose build --no-cache coral-collective
docker-compose up coral-collective
```

2. Verify the container is healthy:
```bash
docker ps
docker exec -it coral-collective-dev coral --help
```

## Notes for Marco's Environment

Based on the error log, Marco is using:
- macOS on Apple Silicon (ARM64/aarch64)
- Docker Compose with BuildKit
- Python 3.14 base image (from the error logs)

The fix should work on this setup, but if issues persist, consider:
- Using `--platform linux/amd64` for x86 emulation
- Using pre-built ARM64 wheels when available
- Building native dependencies inside the container