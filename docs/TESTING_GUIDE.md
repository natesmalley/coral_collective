# CoralCollective Testing Guide

Comprehensive testing documentation for the CoralCollective AI agent orchestration framework.

## Table of Contents

- [Overview](#overview)
- [Test Architecture](#test-architecture)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Writing Tests](#writing-tests)
- [Continuous Integration](#continuous-integration)
- [Performance Testing](#performance-testing)
- [Troubleshooting](#troubleshooting)

## Overview

CoralCollective employs a comprehensive testing strategy with multiple layers:

- **Unit Tests**: Individual component validation
- **Integration Tests**: Component interaction testing  
- **End-to-End Tests**: Complete workflow validation
- **Performance Tests**: Load and scalability testing
- **CLI Tests**: Command-line interface validation
- **Deployment Tests**: Container and infrastructure testing

### Test Coverage Goals

- **Overall Coverage**: 80%+ across all components
- **Critical Path Coverage**: 95%+ for core workflows
- **Integration Coverage**: 90%+ for component interactions
- **Performance Validation**: All major operations under performance thresholds

## Test Architecture

```
tests/
├── conftest.py                 # Global test configuration and fixtures
├── pytest.ini                 # PyTest configuration  
├── unit/                       # Unit tests (80ms max execution)
│   ├── test_agents.py         # Agent system tests
│   ├── test_agent_runner.py   # Agent execution tests
│   ├── test_memory_system.py  # Memory system tests
│   ├── test_mcp_client.py     # MCP integration tests
│   ├── test_project_manager.py # Project management tests
│   └── test_tools.py          # Utility tools tests
├── integration/                # Integration tests (5s max execution)
│   ├── test_agent_handoffs.py # Agent transition tests
│   ├── test_workflows.py      # Complete workflow tests
│   ├── test_mcp_integration.py # MCP server integration
│   └── test_memory_integration.py # Memory with agents
├── e2e/                       # End-to-end tests (30s max execution)
│   ├── test_full_pipeline.py  # Complete project lifecycle
│   ├── test_cli_commands.py   # CLI interface tests
│   └── test_docker_deployment.py # Container tests
└── fixtures/                  # Test data and utilities
    ├── test_data.py           # Sample data generators
    └── mock_services.py       # Mock implementations
```

### Key Design Principles

1. **Isolation**: Tests don't depend on external services
2. **Determinism**: Consistent results across environments
3. **Speed**: Fast feedback for development workflow
4. **Realism**: Tests reflect real usage patterns
5. **Maintainability**: Clear structure and documentation

## Running Tests

### Prerequisites

**IMPORTANT**: Always use a virtual environment for testing isolation:

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test category
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only  
pytest -m e2e            # End-to-end tests only

# Run specific test file
pytest tests/unit/test_agents.py

# Run specific test
pytest tests/unit/test_agents.py::TestAgentRunner::test_agent_execution
```

### Test Execution with Coverage

```bash
# Run with coverage report
pytest --cov=. --cov-report=html --cov-report=term-missing

# Coverage report will be generated in tests/coverage_html/
open tests/coverage_html/index.html
```

### Parallel Test Execution

```bash
# Install pytest-xdist for parallel execution
pip install pytest-xdist

# Run tests in parallel
pytest -n auto  # Auto-detect CPU count
pytest -n 4     # Use 4 parallel workers
```

### Environment-Specific Testing

```bash
# Development environment
CORAL_ENV=development pytest

# Production simulation  
CORAL_ENV=production pytest -m "not development"

# Skip external service tests
pytest -m "not requires_external"

# Run only fast tests
pytest -m "not slow"
```

## Test Categories

### Unit Tests (`pytest -m unit`)

**Purpose**: Test individual components in isolation

**Characteristics**:
- Max execution time: 80ms per test
- No external dependencies
- Extensive mocking
- High coverage of edge cases

**Key Test Files**:
- `test_agents.py`: Agent configuration and prompt loading
- `test_agent_runner.py`: Agent execution engine
- `test_memory_system.py`: Memory operations
- `test_mcp_client.py`: MCP tool integration
- `test_project_manager.py`: Project state management

### Integration Tests (`pytest -m integration`)

**Purpose**: Test component interactions and workflows

**Characteristics**:
- Max execution time: 5 seconds per test
- Multiple component interactions
- Realistic data flows
- End-to-end scenarios within subsystems

**Key Test Files**:
- `test_agent_handoffs.py`: Agent transition workflows
- `test_workflows.py`: Multi-agent orchestration
- `test_memory_integration.py`: Memory system with agents
- `test_mcp_integration.py`: MCP tools in workflows

### End-to-End Tests (`pytest -m e2e`)

**Purpose**: Validate complete system functionality

**Characteristics**:
- Max execution time: 30 seconds per test
- Full system integration
- Real-world scenarios
- Complete project lifecycles

**Key Test Files**:
- `test_full_pipeline.py`: Complete project development
- `test_cli_commands.py`: Command-line interfaces
- `test_docker_deployment.py`: Container deployment

### Performance Tests (`pytest -m performance`)

**Purpose**: Validate system performance under load

**Characteristics**:
- Load and stress testing
- Scalability validation
- Resource utilization monitoring
- Performance regression detection

**Thresholds**:
- Agent execution: <500ms average
- Memory operations: <100ms average
- Search operations: <1000ms average
- CLI commands: <2000ms average

## Writing Tests

### Test Structure

Follow the Arrange-Act-Assert pattern:

```python
def test_agent_execution_success():
    # Arrange
    agent_id = "backend_developer"
    task = "Create REST API"
    mock_runner = MockAgentRunner()
    
    # Act
    result = await mock_runner.run_agent(agent_id, task)
    
    # Assert
    assert result.success is True
    assert result.agent_id == agent_id
    assert "API" in result.outputs.get("result", "")
```

### Using Fixtures

Leverage provided fixtures for consistent test setup:

```python
def test_with_memory_system(mock_memory_system, sample_memory_items):
    # Use pre-configured mock memory system
    memory_system = mock_memory_system
    
    # Add sample memories
    for memory in sample_memory_items:
        memory_system.memories.append(memory)
    
    # Test memory operations
    results = await memory_system.search_memories("API development")
    assert len(results) > 0
```

### Async Test Support

For async operations, use `pytest-asyncio`:

```python
@pytest.mark.asyncio
async def test_async_agent_execution():
    runner = MockAgentRunner()
    result = await runner.run_agent("backend_developer", "Create API")
    assert result.success is True
```

### Test Markers

Use markers to categorize and filter tests:

```python
@pytest.mark.unit
@pytest.mark.agent
def test_agent_configuration():
    # Unit test for agent configuration
    pass

@pytest.mark.integration  
@pytest.mark.memory
@pytest.mark.slow
async def test_memory_integration():
    # Integration test for memory system
    pass

@pytest.mark.e2e
@pytest.mark.performance
@pytest.mark.requires_external
def test_full_deployment():
    # End-to-end deployment test
    pass
```

### Mock Usage Guidelines

1. **Use Comprehensive Mocks**: Leverage `mock_services.py` for realistic mocks
2. **Verify Interactions**: Assert that mocked methods were called correctly
3. **Simulate Realistic Behavior**: Include delays, failures, and variations
4. **Maintain Consistency**: Keep mock behavior consistent across tests

```python
def test_agent_with_memory_integration(mock_agent_runner, mock_memory_system):
    # Configure realistic mock behavior
    mock_agent_runner.set_execution_delay(0.1)  # 100ms execution
    mock_memory_system.search_delay = 0.05      # 50ms search
    
    # Test with configured mocks
    result = await mock_agent_runner.run_agent("backend_dev", "Create API")
    
    # Verify mock interactions
    assert mock_memory_system.add_memory.called
    assert result.duration > 100  # Includes execution delay
```

### Error Scenario Testing

Always test error conditions and edge cases:

```python
def test_agent_execution_failure():
    runner = MockAgentRunner()
    runner.set_failure_rate(1.0)  # Force failure
    
    result = await runner.run_agent("backend_dev", "Invalid task")
    
    assert result.success is False
    assert result.error is not None
    assert "failure" in result.error.lower()

def test_memory_system_under_load():
    memory_system = MockMemorySystem()
    
    # Test with many concurrent operations
    tasks = [
        memory_system.add_memory(f"Content {i}", "agent", "project")
        for i in range(100)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Verify most operations succeed
    successes = sum(1 for r in results if not isinstance(r, Exception))
    assert successes >= 95  # 95% success rate
```

## Continuous Integration

### GitHub Actions Workflow

The project includes CI/CD configuration in `.github/workflows/test.yml`:

```yaml
name: CoralCollective Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        source venv/bin/activate
        pytest -v --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### Pre-commit Hooks

Install pre-commit hooks for automatic testing:

```bash
pip install pre-commit
pre-commit install

# Manually run pre-commit on all files
pre-commit run --all-files
```

### Quality Gates

CI enforces these quality gates:

- **Test Coverage**: Minimum 75% overall coverage
- **Performance**: All tests complete within time limits
- **Code Quality**: No linting errors or security issues
- **Dependency Security**: No known vulnerabilities

## Performance Testing

### Load Testing Scenarios

```python
@pytest.mark.performance
async def test_high_load_agent_execution():
    """Test system under high agent execution load"""
    
    runner = MockAgentRunner()
    runner.set_execution_delay(0.1)  # 100ms per agent
    
    # Simulate 50 concurrent agent executions
    tasks = [
        runner.run_agent(f"agent_{i % 5}", f"Task {i}")
        for i in range(50)
    ]
    
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    execution_time = time.time() - start_time
    
    # Performance assertions
    assert execution_time < 10.0  # Complete within 10 seconds
    assert len(results) == 50
    
    # Verify success rate
    success_rate = sum(1 for r in results if r.success) / len(results)
    assert success_rate > 0.95  # 95% success rate
```

### Memory Usage Testing

```python
@pytest.mark.performance
def test_memory_usage_under_load():
    """Test memory usage doesn't exceed limits"""
    
    import psutil
    process = psutil.Process()
    
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Perform memory-intensive operations
    memory_system = MockMemorySystem()
    for i in range(1000):
        await memory_system.add_memory(
            content=f"Large content block {i}" * 100,
            agent_id="test_agent",
            project_id="memory_test"
        )
    
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory
    
    # Memory increase should be reasonable
    assert memory_increase < 100  # Less than 100MB increase
```

### Performance Benchmarking

```python
@pytest.mark.performance 
def test_search_performance_benchmark():
    """Benchmark search operation performance"""
    
    memory_system = MockMemorySystem()
    
    # Pre-populate with test data
    for i in range(10000):
        await memory_system.add_memory(
            content=f"Test content {i} with various keywords",
            agent_id=f"agent_{i % 10}",
            project_id="benchmark_test"
        )
    
    # Benchmark search operations
    search_times = []
    for _ in range(10):
        start_time = time.time()
        results = await memory_system.search_memories("keywords", limit=20)
        search_time = time.time() - start_time
        search_times.append(search_time)
    
    # Performance assertions
    avg_search_time = sum(search_times) / len(search_times)
    assert avg_search_time < 0.1  # Less than 100ms average
    assert max(search_times) < 0.2  # No search over 200ms
```

## Troubleshooting

### Common Issues

#### 1. Virtual Environment Issues

**Problem**: Tests fail due to missing dependencies

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate
# or on Windows: venv\Scripts\activate

# Verify Python path
which python  # Should show venv path

# Reinstall dependencies
pip install -r requirements.txt
```

#### 2. Async Test Failures

**Problem**: `RuntimeError: There is no current event loop`

**Solution**:
```python
# Add pytest-asyncio marker
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_operation()
    assert result is not None

# Or configure in pytest.ini
asyncio_mode = auto
```

#### 3. Mock Configuration Issues

**Problem**: Mocks not behaving as expected

**Solution**:
```python
# Reset mocks between tests
def test_with_fresh_mock(mock_service):
    mock_service.reset_mock()  # Clear previous calls
    
    # Configure mock for this test
    mock_service.some_method.return_value = expected_value
    
    # Run test
    result = system_under_test.call_mock()
    
    # Verify mock was called
    mock_service.some_method.assert_called_once_with(expected_args)
```

#### 4. Test Isolation Problems

**Problem**: Tests affect each other's state

**Solution**:
```python
# Use proper fixtures with cleanup
@pytest.fixture
def clean_environment():
    # Setup
    env = create_test_environment()
    yield env
    # Cleanup
    env.cleanup()

# Or use temporary directories
def test_with_temp_dir(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    # tmp_path is automatically cleaned up
```

#### 5. Performance Test Variability

**Problem**: Performance tests fail intermittently

**Solution**:
```python
# Use statistical validation instead of hard limits
def test_performance_with_statistics():
    execution_times = []
    
    for _ in range(10):  # Multiple runs
        start = time.time()
        perform_operation()
        execution_times.append(time.time() - start)
    
    # Use percentiles for validation
    p95_time = sorted(execution_times)[int(0.95 * len(execution_times))]
    assert p95_time < 0.5  # 95th percentile under 500ms
    
    avg_time = sum(execution_times) / len(execution_times)
    assert avg_time < 0.2  # Average under 200ms
```

### Debug Mode Testing

Enable debug mode for detailed test output:

```bash
# Run with debug logging
CORAL_ENV=test LOG_LEVEL=DEBUG pytest -v -s

# Stop on first failure
pytest -x

# Drop into debugger on failure
pytest --pdb

# Show local variables in tracebacks
pytest -l
```

### Test Data Generation

For debugging complex scenarios, generate test data:

```python
def test_with_generated_data():
    # Generate realistic test scenario
    project_data = generate_sample_project_data(
        agents_count=5,
        memories_per_agent=20,
        handoffs_count=10
    )
    
    # Use generated data in test
    result = run_workflow_with_data(project_data)
    
    # Detailed assertions for debugging
    assert result.success, f"Workflow failed: {result.error}"
    assert len(result.agent_results) == 5
    for agent_result in result.agent_results:
        assert agent_result.success, f"Agent {agent_result.agent_id} failed"
```

## Best Practices Summary

1. **Always Use Virtual Environments**: Ensure test isolation
2. **Write Descriptive Test Names**: Test purpose should be clear
3. **Test Both Success and Failure Paths**: Cover all scenarios
4. **Use Realistic Mock Data**: Reflect actual usage patterns
5. **Maintain Test Performance**: Keep tests fast for development workflow
6. **Document Complex Test Logic**: Explain non-obvious test scenarios
7. **Regular Test Maintenance**: Update tests with code changes
8. **Monitor Test Coverage**: Maintain high coverage standards
9. **Performance Testing**: Include load and stress scenarios
10. **CI/CD Integration**: Automate testing in deployment pipeline

## Resources

- [PyTest Documentation](https://docs.pytest.org/)
- [AsyncIO Testing](https://docs.python.org/3/library/asyncio-dev.html#testing)
- [Mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Performance Testing Guide](https://docs.python.org/3/library/timeit.html)

For questions about testing, see the development documentation or create an issue in the project repository.