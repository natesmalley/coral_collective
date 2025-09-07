# CoralCollective Deployment Validation Checklist

This document provides a comprehensive checklist for validating CoralCollective deployments after the file structure consolidation.

## Pre-Deployment Validation

### File Structure Verification
- [ ] **agent_runner.py** - Main orchestration script
- [ ] **claude_code_agents.json** - Agent registry configuration
- [ ] **claude_interface.py** - Claude integration interface
- [ ] **subagent_registry.py** - Subagent management system
- [ ] **agent_prompt_service.py** - Prompt service provider
- [ ] **codex_subagents.py** - Codex integration
- [ ] **coral_agents.yaml** - Agent configuration
- [ ] **project_manager.py** - Project management utilities
- [ ] **requirements.txt** - Python dependencies
- [ ] **start.sh** - Interactive startup script
- [ ] **deploy_coral.sh** - Deployment script
- [ ] **coral_drop.sh** - Drop-in installation script

### Directory Structure Verification
- [ ] **agents/** - Agent prompt definitions
  - [ ] **core/** - Core agents (Project Architect, Technical Writer)
  - [ ] **specialists/** - Specialist agents (20+ agents)
  - [ ] **assessment/** - Assessment and validation agents
- [ ] **config/** - Configuration files
  - [ ] **agents.yaml** - Agent registry
  - [ ] **model_assignments_2025.yaml** - Model optimization
- [ ] **tools/** - Utility scripts
  - [ ] **feedback_collector.py** - Feedback system
- [ ] **providers/** - Provider system
  - [ ] **claude.py** - Claude provider
  - [ ] **codex.py** - Codex provider
  - [ ] **provider_base.py** - Base provider class
- [ ] **mcp/** - Model Context Protocol integration
- [ ] **docs/** - Documentation

### Deleted Files Cleanup Verification
Ensure these files are NO LONGER referenced:
- [ ] ~~claude_agents_installer.py~~ - REMOVED
- [ ] ~~coral_claude_integration.py~~ - REMOVED
- [ ] ~~register_agents.py~~ - REMOVED
- [ ] ~~claude_code_agents.py~~ - REMOVED
- [ ] ~~claude_agents.json~~ - REMOVED
- [ ] ~~claude_subagents.json~~ - REMOVED
- [ ] ~~coral_subagents.json~~ - REMOVED
- [ ] ~~coral_agents_claude_code.json~~ - REMOVED
- [ ] ~~agents_claude/~~ - REMOVED
- [ ] ~~agents_claude_code/~~ - REMOVED
- [ ] ~~coral_installer.sh~~ - REMOVED

## Deployment Script Validation

### deploy_coral.sh Testing
```bash
# Test packaging functionality
./deploy_coral.sh package

# Verify package contents
tar -tzf coral_collective.tar.gz | head -20

# Test deployment to directory
./deploy_coral.sh deploy /tmp/test_deploy

# Test initialization in current directory
./deploy_coral.sh init
```

**Expected Results:**
- [ ] Package creates successfully
- [ ] All essential files included in package
- [ ] Directory deployment creates clean structure
- [ ] Initialization sets up necessary directories
- [ ] No references to deleted files

### coral_drop.sh Testing
```bash
# Create test project
mkdir -p /tmp/test_project
cd /tmp/test_project
echo '{"name": "test", "version": "1.0.0"}' > package.json

# Run drop-in installation
/path/to/coral_collective/coral_drop.sh

# Test coral wrapper
./coral help
./coral list
```

**Expected Results:**
- [ ] .coral/ directory created with all files
- [ ] coral wrapper script functional
- [ ] .coralrc configuration created
- [ ] Virtual environment setup works
- [ ] No conflicts with existing project files

## Functional Testing

### Core Functionality
- [ ] **Agent Runner**: `python3 agent_runner.py workflow`
- [ ] **Project Manager**: `python3 project_manager.py`
- [ ] **Start Script**: `./start.sh`
- [ ] **Coral Wrapper**: `./coral workflow` (in drop-in mode)

### Integration Testing
- [ ] **Claude Interface**: Agent prompts load correctly
- [ ] **Subagent Registry**: Agent registration functional
- [ ] **Provider System**: Multiple providers accessible
- [ ] **MCP Integration**: MCP servers configurable
- [ ] **Feedback System**: Feedback collection operational

### Error Handling
- [ ] Missing dependencies handled gracefully
- [ ] Invalid agent IDs produce helpful errors
- [ ] Configuration issues reported clearly
- [ ] Package corruption detected

## Performance Validation

### Package Size
- [ ] Package size reasonable (< 50MB)
- [ ] Only essential files included
- [ ] No redundant or deprecated files

### Installation Speed
- [ ] Packaging completes in < 30 seconds
- [ ] Drop-in installation completes in < 60 seconds
- [ ] Virtual environment setup completes in < 120 seconds

### Memory Usage
- [ ] Agent runner uses reasonable memory (< 100MB)
- [ ] No memory leaks during extended sessions
- [ ] Clean shutdown releases resources

## Security Validation

### File Permissions
- [ ] Scripts have execute permissions
- [ ] Configuration files have appropriate permissions
- [ ] No sensitive data in package

### Isolation
- [ ] Drop-in mode doesn't modify project files
- [ ] .coral/ directory properly isolated
- [ ] Virtual environment contained

## Documentation Validation

### User Documentation
- [ ] CLAUDE.md updated with current structure
- [ ] INTEGRATION_GUIDE.md reflects consolidated architecture
- [ ] README.md instructions accurate
- [ ] Installation instructions clear

### Developer Documentation
- [ ] Code comments updated
- [ ] API documentation current
- [ ] Architecture diagrams accurate

## Compatibility Testing

### Python Versions
- [ ] Python 3.8+
- [ ] Python 3.9
- [ ] Python 3.10
- [ ] Python 3.11
- [ ] Python 3.12

### Operating Systems
- [ ] macOS (Darwin)
- [ ] Linux (Ubuntu/CentOS)
- [ ] Windows (WSL/native)

### Project Types
- [ ] JavaScript/Node.js projects
- [ ] Python projects
- [ ] Ruby projects
- [ ] Java projects
- [ ] Rust projects
- [ ] Empty/new projects

## Regression Testing

### Existing Functionality
- [ ] All original agent workflows function
- [ ] Project management features intact
- [ ] Feedback system operational
- [ ] MCP integration functional

### Configuration Migration
- [ ] Old configurations handled gracefully
- [ ] New configurations properly formatted
- [ ] Default settings sensible

## Production Readiness Checklist

### Deployment Artifacts
- [ ] Clean package build
- [ ] All scripts executable
- [ ] Documentation complete
- [ ] Version tracking in place

### Support Systems
- [ ] Error logging functional
- [ ] Debug mode available
- [ ] Health checks operational
- [ ] Monitoring endpoints active

### Maintenance
- [ ] Update mechanism functional
- [ ] Backup procedures documented
- [ ] Rollback strategy defined
- [ ] Support escalation path clear

## Validation Commands Summary

```bash
# Quick validation suite
./deploy_coral.sh package && echo "✅ Packaging works"
tar -tzf coral_collective.tar.gz | grep -q "agent_runner.py" && echo "✅ Essential files present"
./deploy_coral.sh init && echo "✅ Initialization works"
python3 agent_runner.py list && echo "✅ Agent listing works"
./start.sh --version 2>/dev/null || echo "✅ Start script executable"

# Drop-in validation
mkdir -p /tmp/coral_test && cd /tmp/coral_test
echo '{}' > package.json
/path/to/coral_drop.sh && echo "✅ Drop-in installation works"
./coral help && echo "✅ Coral wrapper functional"
cd - && rm -rf /tmp/coral_test
```

## Sign-off Criteria

Deployment is validated and ready for production when:
- [ ] All functional tests pass
- [ ] All integration tests pass
- [ ] Performance benchmarks meet requirements
- [ ] Security audit completed
- [ ] Documentation review completed
- [ ] Compatibility testing completed
- [ ] No critical or high-severity issues remain

**Validated by:** ___________________  
**Date:** ___________________  
**Version:** ___________________