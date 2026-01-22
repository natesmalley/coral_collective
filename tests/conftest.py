"""
CoralCollective Test Configuration and Shared Fixtures

This module provides common fixtures, mock objects, and test utilities
for the entire CoralCollective test suite.
"""

import pytest
import asyncio
import tempfile
import shutil
import json
import yaml
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock, MagicMock, patch

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test environment setup
os.environ.update({
    'TESTING': 'true',
    'LOG_LEVEL': 'ERROR',
    'DISABLE_ANALYTICS': 'true',
    'CORAL_ENV': 'test',
    'PYTHONPATH': str(project_root)
})


# ============================
# Session-scoped fixtures
# ============================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def virtual_env_check():
    """Ensure tests are running in a virtual environment."""
    in_venv = (
        hasattr(sys, 'real_prefix') or
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
        'VIRTUAL_ENV' in os.environ
    )
    
    if not in_venv:
        pytest.skip("Tests require virtual environment for isolation")
    
    return {
        "venv_path": os.environ.get('VIRTUAL_ENV', sys.prefix),
        "python_path": sys.executable,
        "site_packages": [p for p in sys.path if 'site-packages' in p]
    }


# ============================
# Temporary directories and files
# ============================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture 
def temp_project_dir():
    """Create a temporary project directory with basic structure."""
    temp_path = Path(tempfile.mkdtemp())
    
    # Create basic project structure
    (temp_path / 'src').mkdir()
    (temp_path / 'tests').mkdir()
    (temp_path / 'docs').mkdir()
    (temp_path / 'config').mkdir()
    (temp_path / '.coral').mkdir()
    (temp_path / '.coral' / 'memory').mkdir()
    (temp_path / '.coral' / 'state').mkdir()
    (temp_path / '.coral' / 'logs').mkdir()
    
    yield temp_path
    if temp_path.exists():
        shutil.rmtree(temp_path)


# ============================
# Mock configurations and data
# ============================

@pytest.fixture
def mock_agents_config():
    """Sample agents configuration for testing."""
    return {
        "version": 1,
        "agents": {
            "project_architect": {
                "role": "architect",
                "prompt_path": "agents/core/project_architect.md",
                "capabilities": ["planning", "architecture", "structure", "handoff"],
                "phase": 1
            },
            "backend_developer": {
                "role": "backend_developer",
                "prompt_path": "agents/specialists/backend_developer.md",
                "capabilities": ["api", "database", "server", "authentication"]
            },
            "frontend_developer": {
                "role": "frontend_developer",
                "prompt_path": "agents/specialists/frontend_developer.md", 
                "capabilities": ["ui", "components", "styling", "state"]
            },
            "qa_testing": {
                "role": "qa_testing",
                "prompt_path": "agents/specialists/qa_testing.md",
                "capabilities": ["testing", "validation", "quality", "automation"]
            },
            "technical_writer": {
                "role": "technical_writer",
                "prompt_path": "agents/core/technical_writer.md",
                "capabilities": ["documentation", "requirements", "api_specs"],
                "phases": [1, 2]
            }
        }
    }


@pytest.fixture
def mock_project_state():
    """Sample project state for testing."""
    return {
        "project": {
            "name": "test_project",
            "id": "test_project_123",
            "created_at": datetime.now().isoformat(),
            "current_phase": "development", 
            "status": "active"
        },
        "agents": {
            "completed": [
                {
                    "agent_id": "project_architect",
                    "task": "Design system architecture",
                    "success": True,
                    "started_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "completed_at": (datetime.now() - timedelta(hours=1)).isoformat(),
                    "duration_minutes": 60,
                    "outputs": {
                        "architecture_doc": "/docs/architecture.md",
                        "requirements": "/docs/requirements.md"
                    }
                }
            ],
            "active": None,
            "queue": ["backend_developer", "frontend_developer", "qa_testing"]
        },
        "handoffs": [],
        "artifacts": [],
        "metrics": {
            "total_agents_run": 1,
            "successful_completions": 1,
            "failed_completions": 0,
            "total_handoffs": 0,
            "artifacts_created": 0
        }
    }



@pytest.fixture
def sample_agent_prompt():
    """Sample agent prompt content for testing."""
    return """
# Test Agent

You are a test AI agent for CoralCollective testing purposes.

## Role
Testing specialist for validating functionality

## Responsibilities
- Execute test scenarios
- Validate system behavior
- Report test results

## Capabilities
- Test execution
- Result validation
- Error reporting

## Deliverables
- Test results
- Validation reports
- Error logs
"""


# ============================
# Mock external dependencies
# ============================

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    client = Mock()
    client.chat = Mock()
    client.chat.completions = Mock()
    client.chat.completions.create = AsyncMock(return_value=Mock(
        choices=[Mock(message=Mock(content="Test response from mock OpenAI"))]
    ))
    return client



@pytest.fixture
def mock_mcp_client():
    """Mock MCP client for testing."""
    client = Mock()
    client.is_connected = True
    client.servers = ['filesystem', 'github']
    
    client.list_tools = AsyncMock(return_value=[
        {"name": "filesystem_read", "description": "Read files"},
        {"name": "filesystem_write", "description": "Write files"},
        {"name": "github_create_repo", "description": "Create repository"}
    ])
    
    client.call_tool = AsyncMock(return_value={
        "success": True,
        "result": "Mock tool execution result",
        "metadata": {"execution_time": 0.1}
    })
    
    client.connect = AsyncMock()
    client.close = AsyncMock()
    
    return client


# ============================
# Placeholder fixtures
# ============================

@pytest.fixture
def mock_placeholder():
    """Placeholder fixture for future use."""
    return {
        "recent_memories": [],
        "working_memory": {},
        "relevant_memories": [],
        "session_context": {}
    })
    memory_system.record_agent_handoff = AsyncMock()
    memory_system.get_memory_stats = Mock(return_value={
        "short_term_memories": 0,
        "long_term_memories": 0,
        "working_memory_keys": 0
    })
    return memory_system


# ============================
# CLI and argument fixtures
# ============================

@pytest.fixture
def mock_cli_args():
    """Mock CLI arguments for different commands."""
    return {
        "run": Mock(
            command="run",
            agent_id="backend_developer",
            task="Create REST API",
            project_id=None,
            mcp_enabled=False,
            streaming=True,
            model=None,
            validate_tokens=False
        ),
        "workflow": Mock(
            command="workflow",
            workflow_type="full_stack",
            task="Build web application",
            mcp_enabled=True,
            streaming=False
        ),
        "list": Mock(
            command="list",
            filter_role=None,
            filter_capabilities=None,
            show_paths=False
        )
    }


# ============================
# Performance testing fixtures
# ============================

@pytest.fixture
def performance_thresholds():
    """Performance testing thresholds."""
    return {
        "agent_load_time_ms": 500,
        "memory_add_time_ms": 100, 
        "search_time_ms": 1000,
        "handoff_time_ms": 200,
        "cli_response_time_ms": 2000,
        "max_memory_usage_mb": 512,
        "batch_operation_items": 100,
        "concurrent_operations": 10
    }


# ============================
# Helper classes and utilities
# ============================

class TestProjectSetup:
    """Helper class for setting up test project environments."""
    
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.coral_dir = temp_dir / '.coral'
        
    def create_coral_structure(self):
        """Create .coral directory structure."""
        self.coral_dir.mkdir(exist_ok=True)
        (self.coral_dir / 'memory').mkdir(exist_ok=True)
        (self.coral_dir / 'state').mkdir(exist_ok=True)
        (self.coral_dir / 'logs').mkdir(exist_ok=True)
        
    def create_project_state(self, state_data: Dict):
        """Create project state file."""
        state_file = self.coral_dir / 'project_state.yaml'
        with open(state_file, 'w') as f:
            yaml.dump(state_data, f)
            
    def create_memory_config(self, config_data: Dict):
        """Create memory configuration."""
        config_file = self.coral_dir / 'memory_config.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        return str(config_file)
        
    def create_agents_config(self, agents_data: Dict):
        """Create agents configuration."""
        config_dir = self.temp_dir / 'config'
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / 'agents.yaml'
        
        with open(config_file, 'w') as f:
            yaml.dump(agents_data, f)
            
    def create_sample_files(self):
        """Create sample project files."""
        # Create sample source files
        (self.temp_dir / 'src' / 'main.py').write_text('print("Hello World")')
        (self.temp_dir / 'README.md').write_text('# Test Project')
        (self.temp_dir / 'requirements.txt').write_text('requests==2.28.0\n')


@pytest.fixture
def test_project_setup(temp_project_dir):
    """Create test project setup helper."""
    return TestProjectSetup(temp_project_dir)


# ============================
# Patching utilities
# ============================

@pytest.fixture
def patch_external_dependencies():
    """Patch external dependencies for testing."""
    with patch('openai.OpenAI'), \
         patch('chromadb.Client'), \
         patch('requests.get'), \
         patch('requests.post'):
        yield


@pytest.fixture
def patch_file_operations():
    """Patch file operations for testing."""
    with patch('builtins.open', mock_open()), \
         patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.mkdir'), \
         patch('shutil.rmtree'):
        yield


def mock_open(read_data=""):
    """Create a mock open function."""
    mock = MagicMock()
    mock.return_value.__enter__.return_value.read.return_value = read_data
    return mock


# ============================
# Test data generators
# ============================

def generate_test_memories(count: int = 5):
    """Generate test memory items."""
    memories = []
    for i in range(count):
        try:
            from memory.memory_system import MemoryItem, MemoryType, ImportanceLevel
            
            memory = MemoryItem(
                id=f"test_memory_{i}",
                content=f"Test memory content {i}",
                memory_type=MemoryType.SHORT_TERM,
                timestamp=datetime.now() - timedelta(minutes=i*10),
                agent_id=f"test_agent_{i % 3}",
                project_id="test_project",
                importance=ImportanceLevel.MEDIUM,
                context={"test": True, "index": i},
                tags=[f"test_{i}", "generated"]
            )
            memories.append(memory)
        except ImportError:
            break
    return memories


def generate_test_agent_sessions(count: int = 3):
    """Generate test agent sessions."""
    sessions = []
    for i in range(count):
        session = {
            "session_id": f"session_{i:03d}",
            "agent_id": f"test_agent_{i % 3}",
            "task": f"Test task {i}",
            "started_at": (datetime.now() - timedelta(hours=i+1)).isoformat(),
            "completed_at": (datetime.now() - timedelta(hours=i)).isoformat(),
            "success": i % 4 != 0,  # 75% success rate
            "duration_minutes": 30 + i*10,
            "outputs": {f"output_{i}": f"result_{i}"}
        }
        sessions.append(session)
    return sessions


# ============================
# Async utilities
# ============================

@pytest.fixture
def async_timeout():
    """Timeout for async operations in tests."""
    return 30  # seconds


def run_async_test(async_func, *args, **kwargs):
    """Helper to run async test functions."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(async_func(*args, **kwargs))
    finally:
        loop.close()


# ============================
# Cleanup utilities  
# ============================

def cleanup_test_files(*paths):
    """Clean up test files and directories."""
    for path in paths:
        path = Path(path)
        if path.exists():
            if path.is_file():
                path.unlink()
            else:
                shutil.rmtree(path)


@pytest.fixture(autouse=True)
def cleanup_environment():
    """Automatically cleanup test environment after each test."""
    yield
    # Cleanup any test artifacts
    cleanup_paths = [
        Path('.') / 'test_*',
        Path('.') / '*.test',
        Path('.') / '.coral_test'
    ]
    
    for pattern in cleanup_paths:
        for path in Path('.').glob(str(pattern.name)):
            if path.exists():
                cleanup_test_files(path)