# CI/CD Setup Guide for CoralCollective

This guide explains how to set up Continuous Integration and Continuous Deployment (CI/CD) for CoralCollective using GitHub Actions.

## Overview

CoralCollective includes a comprehensive CI/CD pipeline that:

- Runs tests across multiple Python versions and operating systems
- Performs code quality checks (linting, formatting, type checking)
- Builds and validates packages
- Runs security scans
- Automatically publishes releases to PyPI
- Builds and publishes Docker images
- Supports multiple deployment targets

## CI/CD Pipeline Structure

### Workflows

1. **CI Pipeline** (`.github/workflows/ci.yml`)
   - Multi-matrix testing (Python 3.8-3.11, Ubuntu/macOS/Windows)
   - Code quality checks (Black, Ruff, MyPy)
   - Security scanning (Bandit, Safety)
   - Package building and validation
   - Integration testing with services

2. **Release Pipeline** (`.github/workflows/release.yml`)
   - Automated on git tag push (`v*`)
   - Changelog generation
   - PyPI package publishing
   - Docker image building and pushing
   - GitHub release creation
   - Version bumping for development

## Setup Instructions

### 1. Repository Secrets

Configure the following secrets in your GitHub repository (Settings → Secrets and variables → Actions):

#### Required Secrets

```bash
# PyPI Publishing
PYPI_API_TOKEN=pypi-your-api-token-here
TEST_PYPI_API_TOKEN=pypi-your-test-api-token-here

# Docker Hub
DOCKER_USERNAME=your-docker-username
DOCKER_PASSWORD=your-docker-password-or-token

# API Keys for Testing
CLAUDE_API_KEY=your-claude-api-key-for-testing
GITHUB_TOKEN=github-token-for-mcp-testing  # Different from auto-generated one
```

#### Optional Secrets

```bash
# Codecov (for coverage reporting)
CODECOV_TOKEN=your-codecov-token

# Security Scanning
GITGUARDIAN_API_KEY=your-gitguardian-api-key

# Notification integrations
SLACK_WEBHOOK=your-slack-webhook-url
DISCORD_WEBHOOK=your-discord-webhook-url
```

### 2. PyPI Setup

1. Create accounts on [PyPI](https://pypi.org/) and [TestPyPI](https://test.pypi.org/)

2. Generate API tokens:
   ```bash
   # PyPI: Account settings → API tokens → Add API token
   # Scope: Entire account (initially), then limit to coral-collective project
   ```

3. Configure trusted publishing (recommended):
   ```bash
   # On PyPI, go to Publishing → Add a new trusted publisher
   # Repository: your-username/coral-collective
   # Workflow name: release.yml
   # Environment name: (leave empty)
   ```

### 3. Docker Hub Setup

1. Create a [Docker Hub](https://hub.docker.com/) account

2. Create a repository: `your-username/coral-collective`

3. Generate an access token:
   ```bash
   # Account Settings → Security → Access Tokens → New Access Token
   # Permissions: Read, Write, Delete
   ```

### 4. Code Quality Tools

#### Pre-commit Hooks

Set up pre-commit hooks for local development:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run on all files (optional)
pre-commit run --all-files
```

#### Development Dependencies

Install all development tools:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install with development dependencies
pip install -e .[dev]
```

### 5. Branch Protection

Configure branch protection rules for `main` branch:

1. Go to Settings → Branches → Add rule
2. Branch name pattern: `main`
3. Enable:
   - Require a pull request before merging
   - Require status checks to pass before merging
   - Require branches to be up to date before merging
   - Required status checks:
     - `test (ubuntu-latest, 3.8)`
     - `test (ubuntu-latest, 3.9)`
     - `test (ubuntu-latest, 3.10)`
     - `test (ubuntu-latest, 3.11)`
     - `security`
     - `build-package`
     - `integration-test`

### 6. Release Process

#### Semantic Versioning

CoralCollective uses semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes, backwards compatible

#### Creating a Release

1. **Update version** in `coral_collective/__init__.py`:
   ```python
   __version__ = "1.2.3"
   ```

2. **Update CHANGELOG.md** with release notes

3. **Commit changes**:
   ```bash
   git add coral_collective/__init__.py CHANGELOG.md
   git commit -m "Prepare release v1.2.3"
   git push origin main
   ```

4. **Create and push tag**:
   ```bash
   git tag -a v1.2.3 -m "Release version 1.2.3"
   git push origin v1.2.3
   ```

5. **Monitor workflow**: Check Actions tab for release progress

#### Pre-release Versions

For alpha/beta/rc versions:

```bash
# Tag as pre-release
git tag -a v1.2.3-alpha.1 -m "Pre-release version 1.2.3-alpha.1"
git push origin v1.2.3-alpha.1

# This will:
# - Publish to TestPyPI only
# - Mark GitHub release as pre-release
# - Skip production Docker image tags
```

### 7. Monitoring CI/CD

#### Workflow Status

Monitor your workflows:

1. **Actions tab**: View all workflow runs
2. **Status badges**: Add to README.md
   ```markdown
   [![CI](https://github.com/your-username/coral-collective/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/coral-collective/actions/workflows/ci.yml)
   [![Release](https://github.com/your-username/coral-collective/actions/workflows/release.yml/badge.svg)](https://github.com/your-username/coral-collective/actions/workflows/release.yml)
   ```

#### Coverage Tracking

Set up [Codecov](https://codecov.io/) for coverage tracking:

1. Connect your GitHub repository to Codecov
2. Add `CODECOV_TOKEN` to repository secrets
3. Coverage reports are automatically uploaded after tests

#### Notifications

Configure notifications for workflow failures:

```yaml
# Add to workflow files
- name: Notify on failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: failure
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### 8. Local Testing

Test CI/CD workflows locally using [act](https://github.com/nektos/act):

```bash
# Install act
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | bash

# Run CI workflow locally
act -j test

# Run with secrets file
act -j test --secret-file .secrets
```

### 9. Advanced Configuration

#### Matrix Testing

Customize test matrix in `.github/workflows/ci.yml`:

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    python-version: ["3.8", "3.9", "3.10", "3.11"]
    include:
      - os: ubuntu-latest
        python-version: "3.12"
    exclude:
      - os: windows-latest
        python-version: "3.8"
```

#### Conditional Steps

Add conditional logic for different scenarios:

```yaml
- name: Run memory tests
  if: matrix.python-version == '3.11' && matrix.os == 'ubuntu-latest'
  run: |
    source venv/bin/activate
    pytest tests/test_memory_system.py -v
```

#### Parallel Jobs

Split tests into parallel jobs for faster execution:

```yaml
jobs:
  test-unit:
    runs-on: ubuntu-latest
    steps:
      - name: Run unit tests
        run: pytest tests/unit/ -v

  test-integration:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        # ... postgres config
    steps:
      - name: Run integration tests
        run: pytest tests/integration/ -v
```

## Best Practices

### 1. Security

- Never commit secrets to the repository
- Use repository secrets for sensitive data
- Regularly rotate API keys and tokens
- Enable security scanning and vulnerability alerts
- Use trusted publishing for PyPI when possible

### 2. Performance

- Cache dependencies to speed up builds
- Use matrix testing efficiently
- Consider using self-hosted runners for large projects
- Optimize Docker image builds with multi-stage builds

### 3. Reliability

- Set appropriate timeouts for all steps
- Add retry logic for flaky network operations
- Use health checks for service dependencies
- Implement proper error handling and notifications

### 4. Maintenance

- Regularly update action versions
- Monitor for deprecated features
- Keep dependencies up to date
- Review and update branch protection rules

## Troubleshooting

### Common Issues

1. **Tests failing on Windows**:
   ```yaml
   # Use cross-platform path handling
   - name: Install dependencies (Windows)
     if: runner.os == 'Windows'
     run: |
       python -m pip install --upgrade pip
   ```

2. **Docker build failures**:
   ```bash
   # Check Docker context and ignore files
   # Verify .dockerignore is properly configured
   ```

3. **PyPI publishing errors**:
   ```bash
   # Ensure version is updated and unique
   # Check API token permissions
   # Verify package configuration in setup.py/pyproject.toml
   ```

4. **Memory issues in CI**:
   ```yaml
   # Increase available resources
   - name: Configure memory
     run: |
       export PYTEST_XVFB=0
       export MEMORY_PROFILER=0
   ```

### Debugging Steps

1. **Enable debug logging**:
   ```yaml
   - name: Debug step
     run: |
       set -x  # Enable debug output
       echo "Debug information"
     shell: bash
   ```

2. **SSH into runners** (for debugging):
   ```yaml
   - name: Setup tmate session
     uses: mxschmitt/action-tmate@v3
     if: failure()
   ```

3. **Check artifacts**:
   ```yaml
   - name: Upload logs
     if: always()
     uses: actions/upload-artifact@v3
     with:
       name: test-logs
       path: logs/
   ```

For more specific issues, check the GitHub Actions documentation and the CoralCollective issues page.